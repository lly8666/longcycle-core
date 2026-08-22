from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

from longcycle.domain.models import DocumentArtifact, EvidenceFragment, SourceDocument
from longcycle.ports.archive import ArchiveStore
from longcycle.ports.repository import ResearchRepository

from .pipeline import CollectionPipeline


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() in {"script", "style", "noscript"}:
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._hidden_depth:
            self.parts.append(data)


@dataclass(frozen=True, slots=True)
class RecordedEvidenceResult:
    fragment: EvidenceFragment


class ArchivedEvidenceRecorder:
    """Persist claim-scoped evidence only after grounding it in archived material.

    Historical evidence tasks may already know which primary document and short
    passage they need. Direct textual sources can be checked against immutable raw
    source bytes. Transport-volatile HTML can instead be grounded against a persisted,
    deterministic ``html-visible-text`` artifact. Binary sources such as PDF must first
    produce a persisted parser artifact; excerpts are then checked against one explicit
    page in that immutable artifact. None of these paths creates FactAssertions or
    Judgments.

    Optional ``claim_context`` is evidence annotation, not a promoted fact. It is used
    to preserve distinctions such as known-time precision, valid/effective time and
    expectation horizon while the task is still at the grounded EvidenceFragment stage.
    """

    def __init__(
        self,
        *,
        repository: ResearchRepository,
        archive: ArchiveStore,
    ) -> None:
        self.repository = repository
        self.archive = archive

    async def record_excerpt(
        self,
        *,
        document: SourceDocument,
        excerpt: str,
        occurrence: int | None = None,
        claim_context: dict[str, Any] | None = None,
    ) -> RecordedEvidenceResult:
        normalized_excerpt = self._validated_excerpt(excerpt, occurrence)
        normalized_context = self._validated_claim_context(claim_context)
        content = await self._verified_archived_bytes(
            key=document.blob_key,
            expected_sha256=document.content_sha256,
            expected_length=document.byte_length,
            missing_message="source document blob is missing from the archive",
            digest_message="archived source bytes do not match SourceDocument digest",
            length_message="archived source byte length does not match SourceDocument",
        )

        corpus = self._normalized_visible_text(document, content)
        selected, start = self._select_occurrence(corpus, normalized_excerpt, occurrence)
        del selected
        end = start + len(normalized_excerpt)
        locator = f"visible-text:{start}:{end}"
        structured_payload = (
            {"claim_context": normalized_context} if normalized_context is not None else None
        )
        fragment = EvidenceFragment.create(
            document_id=document.id,
            locator=locator,
            excerpt=excerpt,
            structured_payload=structured_payload,
        )

        CollectionPipeline._validate_textual_grounding(
            document,
            (fragment,),
            content,
            allow_claim_context_annotation=True,
        )
        await self.repository.save_evidence((fragment,))
        return RecordedEvidenceResult(fragment=fragment)

    async def record_html_visible_text_excerpt(
        self,
        *,
        document: SourceDocument,
        artifact: DocumentArtifact,
        excerpt: str,
        occurrence: int | None = None,
        claim_context: dict[str, Any] | None = None,
    ) -> RecordedEvidenceResult:
        """Ground HTML evidence in a stable artifact while retaining raw snapshot lineage."""

        normalized_excerpt = self._validated_excerpt(excerpt, occurrence)
        normalized_context = self._validated_claim_context(claim_context)
        if artifact.document_id != document.id:
            raise ValueError("parser artifact belongs to a different source document")
        if artifact.artifact_type != "html-visible-text":
            raise ValueError("HTML artifact evidence requires an html-visible-text parser artifact")
        if artifact.content_type.split(";", 1)[0].strip().lower() != "text/plain":
            raise ValueError("html-visible-text artifact must be text/plain")

        artifact_bytes = await self._verified_archived_bytes(
            key=artifact.blob_key,
            expected_sha256=artifact.content_sha256,
            expected_length=artifact.byte_length,
            missing_message="HTML parser artifact blob is missing from the archive",
            digest_message="archived HTML parser artifact does not match artifact digest",
            length_message="archived HTML parser artifact length does not match metadata",
        )
        try:
            corpus = artifact_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("html-visible-text artifact is not valid UTF-8") from exc
        corpus = " ".join(corpus.split())
        selected, start = self._select_occurrence(corpus, normalized_excerpt, occurrence)
        end = start + len(normalized_excerpt)
        locator = f"text:{start}:{end}"
        structured_payload: dict[str, Any] = {
            "occurrence": selected,
            "parser_name": artifact.producer_name,
            "parser_version": artifact.producer_version,
        }
        if normalized_context is not None:
            structured_payload["claim_context"] = normalized_context
        fragment = EvidenceFragment.create(
            document_id=document.id,
            artifact_id=artifact.id,
            locator=locator,
            excerpt=excerpt,
            structured_payload=structured_payload,
        )
        await self.repository.save_evidence((fragment,))
        return RecordedEvidenceResult(fragment=fragment)

    async def record_pdf_page_excerpt(
        self,
        *,
        document: SourceDocument,
        artifact: DocumentArtifact,
        page: int,
        excerpt: str,
        occurrence: int | None = None,
        claim_context: dict[str, Any] | None = None,
    ) -> RecordedEvidenceResult:
        normalized_excerpt = self._validated_excerpt(excerpt, occurrence)
        normalized_context = self._validated_claim_context(claim_context)
        if page < 1:
            raise ValueError("page must be one-based and positive")
        if artifact.document_id != document.id:
            raise ValueError("parser artifact belongs to a different source document")
        if artifact.artifact_type != "pdf-text-pages":
            raise ValueError("PDF evidence requires a pdf-text-pages parser artifact")
        if artifact.content_type.split(";", 1)[0].strip().lower() != "application/json":
            raise ValueError("pdf-text-pages artifact must be application/json")

        artifact_bytes = await self._verified_archived_bytes(
            key=artifact.blob_key,
            expected_sha256=artifact.content_sha256,
            expected_length=artifact.byte_length,
            missing_message="parser artifact blob is missing from the archive",
            digest_message="archived parser artifact does not match artifact digest",
            length_message="archived parser artifact length does not match metadata",
        )
        try:
            artifact_payload = json.loads(artifact_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("pdf-text-pages artifact is not valid UTF-8 JSON") from exc
        if (
            not isinstance(artifact_payload, dict)
            or artifact_payload.get("schema_version") != "longcycle-pdf-text/v1"
        ):
            raise ValueError("unexpected pdf-text-pages artifact schema")
        pages = artifact_payload.get("pages")
        if not isinstance(pages, list):
            raise ValueError("pdf-text-pages artifact has no pages array")
        page_entry = next(
            (
                item
                for item in pages
                if isinstance(item, dict) and item.get("page") == page
            ),
            None,
        )
        if page_entry is None:
            raise ValueError("requested PDF page does not exist in parser artifact")
        page_text = page_entry.get("text")
        if not isinstance(page_text, str):
            raise ValueError("requested PDF page has no textual content")

        corpus = " ".join(page_text.split())
        selected, _ = self._select_occurrence(corpus, normalized_excerpt, occurrence)
        page_index = pages.index(page_entry)
        locator = f"$.pages[{page_index}].text"
        structured_payload: dict[str, Any] = {
            "page": page,
            "occurrence": selected,
            "parser_name": artifact.producer_name,
            "parser_version": artifact.producer_version,
        }
        if normalized_context is not None:
            structured_payload["claim_context"] = normalized_context
        fragment = EvidenceFragment.create(
            document_id=document.id,
            artifact_id=artifact.id,
            locator=locator,
            excerpt=excerpt,
            structured_payload=structured_payload,
        )
        await self.repository.save_evidence((fragment,))
        return RecordedEvidenceResult(fragment=fragment)

    async def _verified_archived_bytes(
        self,
        *,
        key: str,
        expected_sha256: str,
        expected_length: int,
        missing_message: str,
        digest_message: str,
        length_message: str,
    ) -> bytes:
        if not await self.archive.exists(key):
            raise ValueError(missing_message)
        content = await self.archive.get(key)
        if hashlib.sha256(content).hexdigest() != expected_sha256:
            raise ValueError(digest_message)
        if len(content) != expected_length:
            raise ValueError(length_message)
        return content

    @staticmethod
    def _validated_excerpt(excerpt: str, occurrence: int | None) -> str:
        normalized_excerpt = " ".join(excerpt.split())
        if not normalized_excerpt:
            raise ValueError("evidence excerpt must not be blank")
        if occurrence is not None and occurrence < 0:
            raise ValueError("occurrence must be non-negative")
        return normalized_excerpt

    @staticmethod
    def _validated_claim_context(
        claim_context: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if claim_context is None:
            return None
        if not isinstance(claim_context, dict) or not claim_context:
            raise ValueError("claim_context must be a non-empty JSON object")
        try:
            normalized = json.loads(
                json.dumps(claim_context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("claim_context must contain only JSON-compatible values") from exc
        if not isinstance(normalized, dict) or not normalized:
            raise ValueError("claim_context must be a non-empty JSON object")
        return normalized

    @staticmethod
    def _select_occurrence(
        corpus: str,
        excerpt: str,
        occurrence: int | None,
    ) -> tuple[int, int]:
        starts = ArchivedEvidenceRecorder._occurrences(corpus, excerpt)
        if not starts:
            raise ValueError("evidence excerpt is not present in archived source text")
        if occurrence is None:
            if len(starts) != 1:
                raise ValueError(
                    "evidence excerpt occurs multiple times; choose an explicit occurrence"
                )
            selected = 0
        else:
            if occurrence >= len(starts):
                raise ValueError("requested evidence occurrence does not exist")
            selected = occurrence
        return selected, starts[selected]

    @staticmethod
    def _normalized_visible_text(document: SourceDocument, content: bytes) -> str:
        media_type = document.content_type.split(";", 1)[0].strip().lower()
        decoded = content.decode("utf-8", errors="replace")
        if media_type in {"text/html", "application/xhtml+xml"}:
            parser = _VisibleTextParser()
            parser.feed(decoded)
            decoded = " ".join(parser.parts)
        elif media_type not in {"text/plain", "text/csv", "application/xml"}:
            raise ValueError(
                "manual excerpt recording currently requires textual or HTML source bytes"
            )
        return " ".join(decoded.split())

    @staticmethod
    def _occurrences(corpus: str, excerpt: str) -> tuple[int, ...]:
        starts: list[int] = []
        cursor = 0
        while True:
            index = corpus.find(excerpt, cursor)
            if index < 0:
                break
            starts.append(index)
            cursor = index + 1
        return tuple(starts)
