from __future__ import annotations

import io
import json
from html.parser import HTMLParser

from pypdf import PdfReader, __version__ as pypdf_version

from longcycle.domain.models import SourceDocument, canonical_json
from longcycle.ports.parser import ParsedOutput


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


class CanonicalJsonParser:
    parser_name = "canonical-json"
    parser_version = "1.0.0"
    supported_media_types = frozenset({"application/json"})

    async def parse(
        self,
        document: SourceDocument,
        content: bytes,
    ) -> tuple[ParsedOutput, ...]:
        del document
        parsed = json.loads(content.decode("utf-8"))
        canonical = canonical_json(parsed).encode("utf-8")
        return (
            ParsedOutput(
                artifact_type="canonical-json",
                content=canonical,
                content_type="application/json",
            ),
        )


class HtmlVisibleTextParser:
    """Extract deterministic visible text while excluding transport/UI script noise."""

    parser_name = "html-visible-text"
    parser_version = "1.0.0"
    supported_media_types = frozenset({"text/html", "application/xhtml+xml"})

    async def parse(
        self,
        document: SourceDocument,
        content: bytes,
    ) -> tuple[ParsedOutput, ...]:
        del document
        parser = _VisibleTextParser()
        parser.feed(content.decode("utf-8", errors="replace"))
        normalized = " ".join(" ".join(parser.parts).split())
        return (
            ParsedOutput(
                artifact_type="html-visible-text",
                content=normalized.encode("utf-8"),
                content_type="text/plain",
            ),
        )


class PdfTextParser:
    """Extract deterministic page-scoped text into a versioned JSON artifact."""

    parser_name = "pypdf-text"
    parser_version = f"1.0.0+pypdf-{pypdf_version}"
    supported_media_types = frozenset({"application/pdf"})

    async def parse(
        self,
        document: SourceDocument,
        content: bytes,
    ) -> tuple[ParsedOutput, ...]:
        del document
        reader = PdfReader(io.BytesIO(content), strict=False)
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise ValueError("encrypted PDF cannot be parsed without a password")

        pages = [
            {
                "page": index,
                "text": page.extract_text() or "",
            }
            for index, page in enumerate(reader.pages, start=1)
        ]
        payload = {
            "schema_version": "longcycle-pdf-text/v1",
            "page_count": len(pages),
            "pages": pages,
        }
        return (
            ParsedOutput(
                artifact_type="pdf-text-pages",
                content=canonical_json(payload).encode("utf-8"),
                content_type="application/json",
            ),
        )
