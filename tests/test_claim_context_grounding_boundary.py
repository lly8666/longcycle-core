from __future__ import annotations

import unittest
from datetime import UTC, datetime

from longcycle.application.pipeline import CollectionPipeline
from longcycle.domain.models import EvidenceFragment, RawPayload, SourceDocument, stable_uuid


class ClaimContextGroundingBoundaryTest(unittest.TestCase):
    def _document(self, content: bytes) -> SourceDocument:
        return SourceDocument.from_payload(
            source_id=stable_uuid("source", "claim-context-grounding-boundary"),
            payload=RawPayload(
                content=content,
                content_type="text/html",
                canonical_url="https://example.com/primary",
                retrieved_at=datetime(2026, 8, 22, tzinfo=UTC),
            ),
            blob_key="sha256/test",
            first_known_at=datetime(2022, 12, 3, 23, 59, 59, tzinfo=UTC),
        )

    def test_pipeline_default_does_not_treat_claim_context_as_grounded_structure(self) -> None:
        excerpt = "production is expected to ramp from December 2022"
        content = f"<html><body><p>{excerpt}</p></body></html>".encode()
        document = self._document(content)
        fragment = EvidenceFragment.create(
            document_id=document.id,
            locator="visible-text:0:1",
            excerpt=excerpt,
            structured_payload={
                "claim_context": {
                    "claim_role": "expectation",
                    "known_time": {"upper_bound": "2022-12-03", "precision": "day"},
                }
            },
        )

        with self.assertRaisesRegex(ValueError, "structured evidence requires"):
            CollectionPipeline._validate_textual_grounding(document, (fragment,), content)

        CollectionPipeline._validate_textual_grounding(
            document,
            (fragment,),
            content,
            allow_claim_context_annotation=True,
        )

    def test_annotation_opt_in_rejects_extra_structured_payload(self) -> None:
        excerpt = "commissioning remains uncertain"
        content = f"<html><body><p>{excerpt}</p></body></html>".encode()
        document = self._document(content)
        fragment = EvidenceFragment.create(
            document_id=document.id,
            locator="visible-text:0:1",
            excerpt=excerpt,
            structured_payload={
                "claim_context": {"claim_role": "uncertainty"},
                "model_extracted_value": {"status": "delayed"},
            },
        )

        with self.assertRaisesRegex(ValueError, "structured evidence requires"):
            CollectionPipeline._validate_textual_grounding(
                document,
                (fragment,),
                content,
                allow_claim_context_annotation=True,
            )

    def test_annotation_opt_in_does_not_relax_excerpt_grounding(self) -> None:
        document = self._document(b"<html><body><p>actual archived wording</p></body></html>")
        fragment = EvidenceFragment.create(
            document_id=document.id,
            locator="visible-text:0:1",
            excerpt="unarchived wording",
            structured_payload={"claim_context": {"claim_role": "expectation"}},
        )

        with self.assertRaisesRegex(ValueError, "excerpt is not grounded"):
            CollectionPipeline._validate_textual_grounding(
                document,
                (fragment,),
                b"<html><body><p>actual archived wording</p></body></html>",
                allow_claim_context_annotation=True,
            )


if __name__ == "__main__":
    unittest.main()
