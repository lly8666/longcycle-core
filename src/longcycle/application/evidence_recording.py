from __future__ import annotations

import hashlib
from dataclasses import dataclass
from html.parser import HTMLParser

from longcycle.domain.models import EvidenceFragment, SourceDocument
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
    was_new_fragment: bool


class ArchivedEvidenceRecorder:
    """Persist one claim-scoped excerpt only after grounding it in archived bytes.

    This is intentionally narrower than the normal extraction pipeline. Historical
    evidence tasks may already know which primary document and short passage they
    need. The recorder proves the passage exists in the immutable archived version,
    creates a deterministic locator, and persists only EvidenceFragment. It never
    creates FactAssertions or Judgments.
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
    ) -> RecordedEvidenceResult:
        normalized_excerpt = " ".join(excerpt.split())
        if not normalized_excerpt:
            raise ValueError("evidence excerpt must not be blank")
        if occurrence is not None and occurrence < 0:
            raise ValueError("occurrence must be non-negative")
        if not await self.archive.exists(document.blob_key):
            raise ValueError("source document blob is missing from the archive")

        content = await self.archive.get(document.blob_key)
        if hashlib.sha256(content).hexdigest() != document.content_sha256:
            raise ValueError("archived source bytes do not match SourceDocument digest")
        if len(content) != document.byte_length:
            raise ValueError("archived source byte length does not match SourceDocument")

        corpus = self._normalized_visible_text(document, content)
        starts = self._occurrences(corpus, normalized_excerpt)
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

        start = starts[selected]
        end = start + len(normalized_excerpt)
        locator = f"visible-text:{start}:{end}"
        fragment = EvidenceFragment.create(
            document_id=document.id,
            locator=locator,
            excerpt=excerpt,
        )

        # Reuse the same textual-grounding guardrail as the full collection pipeline.
        # The locator is deterministic convenience; the excerpt must still be proven
        # against the archived bytes before persistence.
        CollectionPipeline._validate_textual_grounding(
            document,
            (fragment,),
            content,
        )

        evidence_store = getattr(self.repository, "evidence", None)
        was_new_fragment = not (
            isinstance(evidence_store, dict) and fragment.id in evidence_store
        )
        await self.repository.save_evidence((fragment,))
        return RecordedEvidenceResult(
            fragment=fragment,
            was_new_fragment=was_new_fragment,
        )

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
