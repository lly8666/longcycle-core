from __future__ import annotations

import json

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
