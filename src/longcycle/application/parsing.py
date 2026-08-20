from __future__ import annotations

import hashlib

from longcycle.domain.models import DocumentArtifact, SourceDocument
from longcycle.ports.archive import ArchiveStore
from longcycle.ports.parser import DocumentParser
from longcycle.ports.repository import ResearchRepository


class ArtifactPipeline:
    def __init__(
        self,
        *,
        repository: ResearchRepository,
        archive: ArchiveStore,
        max_artifacts: int = 64,
        max_total_bytes: int = 100 * 1024 * 1024,
    ) -> None:
        if max_artifacts < 1 or max_total_bytes < 1:
            raise ValueError("artifact limits must be positive")
        self.repository = repository
        self.archive = archive
        self.max_artifacts = max_artifacts
        self.max_total_bytes = max_total_bytes

    async def parse(
        self,
        *,
        document: SourceDocument,
        content: bytes,
        parser: DocumentParser,
    ) -> tuple[DocumentArtifact, ...]:
        input_sha256 = hashlib.sha256(content).hexdigest()
        if input_sha256 != document.content_sha256 or len(content) != document.byte_length:
            raise ValueError("parser input does not match the persisted document version")
        media_type = document.content_type.split(";", 1)[0].strip().lower()
        if media_type not in parser.supported_media_types:
            raise ValueError(f"parser does not support media type: {media_type}")

        outputs = await parser.parse(document, content)
        if len(outputs) > self.max_artifacts:
            raise ValueError("parser exceeds artifact count safety limit")
        if len({output.artifact_type for output in outputs}) != len(outputs):
            raise ValueError("one parser run cannot emit duplicate artifact types")
        if sum(len(output.content) for output in outputs) > self.max_total_bytes:
            raise ValueError("parser exceeds artifact byte safety limit")

        artifacts: list[DocumentArtifact] = []
        for output in outputs:
            receipt = await self.archive.put_if_absent(
                content=output.content,
                content_type=output.content_type,
                metadata={
                    "document_version_id": str(document.id),
                    "artifact_type": output.artifact_type,
                    "producer_name": parser.parser_name,
                    "producer_version": parser.parser_version,
                },
            )
            expected_sha256 = hashlib.sha256(output.content).hexdigest()
            if receipt.sha256 != expected_sha256 or receipt.size != len(output.content):
                raise ValueError("archive receipt does not match parser output")
            artifact = DocumentArtifact.create(
                document_id=document.id,
                artifact_type=output.artifact_type,
                producer_name=parser.parser_name,
                producer_version=parser.parser_version,
                input_sha256=input_sha256,
                content_sha256=receipt.sha256,
                blob_key=receipt.key,
                byte_length=receipt.size,
                content_type=receipt.content_type,
            )
            artifacts.append(await self.repository.save_artifact(artifact))
        return tuple(artifacts)
