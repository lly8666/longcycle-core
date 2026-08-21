from __future__ import annotations

import io
import json

from pypdf import PdfReader, __version__ as pypdf_version

from longcycle.domain.models import SourceDocument, canonical_json
from longcycle.ports.parser import ParsedOutput


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
