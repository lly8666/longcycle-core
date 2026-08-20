from __future__ import annotations

import asyncio
import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from longcycle.application.quality import quality_score
from longcycle.application.reconciliation import Reconciler
from longcycle.application.pipeline import CollectionPipeline
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.domain.enums import Decision, EntityType, FactStatus, MarketBasis, ValidTimeKind
from longcycle.domain.models import (
    EvidenceFragment,
    ExtractionEnvelope,
    FactAssertion,
    FactDimensions,
    QualityComponents,
    ReconciliationResult,
    SourceDocument,
    TimeRange,
)


def assertion(
    *,
    number: str = "100",
    source_id=None,
    cluster: str = "primary-a",
    source_quality: float = 1,
    corroboration: float = 1,
    high_impact: bool = False,
) -> FactAssertion:
    source_id = source_id or uuid4()
    return FactAssertion(
        entity_type=EntityType.INDUSTRY,
        entity_id=uuid4(),
        field_name="price.market",
        value=number,
        value_type="number",
        normalized_number=Decimal(number),
        normalized_unit="unit",
        dimensions_complete=True,
        valid_time_kind=ValidTimeKind.PERIOD,
        valid_time=TimeRange(start=datetime(2025, 1, 1, tzinfo=UTC)),
        source_id=source_id,
        document_id=uuid4(),
        evidence_fragment_id=uuid4(),
        extraction_run_id=uuid4(),
        extractor_name="test",
        extractor_version="1",
        source_cluster=cluster,
        confidence=0.99,
        quality=QualityComponents(
            source_quality=source_quality,
            extraction_certainty=0.98,
            entity_match=1,
            time_unit_completeness=1,
            corroboration=corroboration,
            freshness=1,
        ),
        high_impact=high_impact,
    )


class QualityAndReconciliationTest(unittest.TestCase):
    def test_one_envelope_cannot_publish_contradictory_candidates_by_order(self) -> None:
        first = assertion(number="100")
        second = first.model_copy(
            update={
                "id": uuid4(),
                "value": "200",
                "normalized_number": Decimal("200"),
            }
        )
        with self.assertRaisesRegex(ValueError, "contradictory candidates"):
            CollectionPipeline._validate_candidate_consistency((first, second))

    def test_weighted_quality_score(self) -> None:
        item = assertion()
        self.assertGreaterEqual(quality_score(item.quality), 0.95)

    def test_high_quality_fact_is_accepted(self) -> None:
        result = Reconciler().reconcile(assertion(), [])
        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertEqual(result.status, FactStatus.TRUSTED)

    def test_conflicting_value_is_preserved_for_review(self) -> None:
        existing = assertion(number="100", cluster="primary-a").model_copy(update={"status": FactStatus.TRUSTED})
        candidate = existing.model_copy(
            update={
                "id": uuid4(),
                "normalized_number": Decimal("130"),
                "value": "130",
                "source_id": uuid4(),
                "source_cluster": "primary-b",
                "document_id": uuid4(),
                "evidence_fragment_id": uuid4(),
            }
        )
        result = Reconciler().reconcile(candidate, [existing])
        self.assertEqual(result.decision, Decision.CONFLICT)
        self.assertIn(existing.id, result.conflicting_assertion_ids)

    def test_explicit_correction_supersedes_instead_of_self_conflicting(self) -> None:
        existing = assertion(number="100").model_copy(update={"status": FactStatus.TRUSTED})
        corrected = existing.model_copy(
            update={
                "id": uuid4(),
                "value": "120",
                "normalized_number": Decimal("120"),
                "supersedes_id": existing.id,
                "document_id": uuid4(),
                "known_at": existing.known_at + timedelta(seconds=1),
                "status": FactStatus.CANDIDATE,
            }
        )

        result = Reconciler().reconcile(corrected, (existing,))

        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertIn("explicit_supersession", result.reason_codes)

    def test_cross_source_cannot_claim_supersession_to_bypass_conflict(self) -> None:
        existing = assertion(number="100").model_copy(update={"status": FactStatus.TRUSTED})
        attempted = existing.model_copy(
            update={
                "id": uuid4(),
                "value": "120",
                "normalized_number": Decimal("120"),
                "supersedes_id": existing.id,
                "source_id": uuid4(),
                "document_id": uuid4(),
                "known_at": existing.known_at + timedelta(seconds=1),
                "status": FactStatus.CANDIDATE,
            }
        )

        result = Reconciler().reconcile(attempted, (existing,))

        self.assertEqual(result.decision, Decision.REVIEW)
        self.assertIn("supersession_cross_source_requires_review", result.reason_codes)

    def test_superseded_history_does_not_create_a_stale_conflict(self) -> None:
        original = assertion(number="100").model_copy(update={"status": FactStatus.TRUSTED})
        correction = original.model_copy(
            update={
                "id": uuid4(),
                "value": "120",
                "normalized_number": Decimal("120"),
                "supersedes_id": original.id,
                "document_id": uuid4(),
                "known_at": original.known_at + timedelta(seconds=1),
                "status": FactStatus.TRUSTED,
            }
        )
        corroboration = correction.model_copy(
            update={
                "id": uuid4(),
                "supersedes_id": None,
                "source_id": uuid4(),
                "source_cluster": "primary-b",
                "document_id": uuid4(),
                "known_at": correction.known_at + timedelta(seconds=1),
                "status": FactStatus.CANDIDATE,
            }
        )

        result = Reconciler().reconcile(corroboration, (original, correction))

        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertNotIn(original.id, result.conflicting_assertion_ids)

    def test_partial_period_cannot_globally_supersede_a_longer_fact(self) -> None:
        original = assertion(number="100").model_copy(
            update={
                "status": FactStatus.TRUSTED,
                "valid_time": TimeRange(
                    start=datetime(2025, 1, 1, tzinfo=UTC),
                    end=datetime(2026, 1, 1, tzinfo=UTC),
                ),
            }
        )
        partial = original.model_copy(
            update={
                "id": uuid4(),
                "value": "120",
                "normalized_number": Decimal("120"),
                "valid_time": TimeRange(
                    start=datetime(2025, 6, 1, tzinfo=UTC),
                    end=datetime(2025, 7, 1, tzinfo=UTC),
                ),
                "supersedes_id": original.id,
                "document_id": uuid4(),
                "known_at": original.known_at + timedelta(seconds=1),
                "status": FactStatus.CANDIDATE,
            }
        )

        result = Reconciler().reconcile(partial, (original,))

        self.assertEqual(result.decision, Decision.REVIEW)
        self.assertIn("supersession_time_range_mismatch", result.reason_codes)

    def test_low_grade_high_impact_fact_does_not_auto_publish(self) -> None:
        candidate = assertion(source_quality=0.5, corroboration=0.5, high_impact=True)
        result = Reconciler().reconcile(candidate, [])
        self.assertEqual(result.decision, Decision.REVIEW)
        self.assertIn("high_impact_requires_stronger_evidence", result.reason_codes)

    def test_different_market_basis_is_not_compared(self) -> None:
        existing = assertion().model_copy(
            update={"dimensions": FactDimensions(market_basis=MarketBasis.SPOT)}
        )
        candidate = existing.model_copy(
            update={
                "id": uuid4(),
                "dimensions": FactDimensions(market_basis=MarketBasis.CONTRACT),
                "normalized_number": Decimal("200"),
                "value": "200",
            }
        )
        result = Reconciler().reconcile(candidate, [existing])
        self.assertEqual(result.decision, Decision.ACCEPT)

    def test_non_overlapping_period_is_not_a_conflict(self) -> None:
        existing = assertion().model_copy(
            update={
                "valid_time": TimeRange(
                    start=datetime(2025, 1, 1, tzinfo=UTC),
                    end=datetime(2026, 1, 1, tzinfo=UTC),
                )
            }
        )
        candidate = existing.model_copy(
            update={
                "id": uuid4(),
                "valid_time": TimeRange(
                    start=datetime(2026, 1, 1, tzinfo=UTC),
                    end=datetime(2027, 1, 1, tzinfo=UTC),
                ),
                "normalized_number": Decimal("200"),
                "value": "200",
            }
        )
        result = Reconciler().reconcile(candidate, [existing])
        self.assertEqual(result.decision, Decision.ACCEPT)

    def test_incomplete_dimensions_require_review(self) -> None:
        candidate = assertion().model_copy(update={"dimensions_complete": False})
        result = Reconciler().reconcile(candidate, [])
        self.assertEqual(result.decision, Decision.REVIEW)
        self.assertIn("incomplete_dimensions", result.reason_codes)

    def test_quarantined_assertion_cannot_corroborate_or_conflict(self) -> None:
        bad = assertion(number="999", cluster="bad-source").model_copy(
            update={"status": FactStatus.QUARANTINED}
        )
        candidate = bad.model_copy(
            update={
                "id": uuid4(),
                "value": "100",
                "normalized_number": Decimal("100"),
                "status": FactStatus.CANDIDATE,
                "source_id": uuid4(),
                "source_cluster": "good-source",
            }
        )
        result = Reconciler().reconcile(candidate, [bad])
        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertNotIn("conflicting_values", result.reason_codes)
        self.assertNotIn("independent_corroboration", result.reason_codes)


class RepositoryReconciliationContractTest(unittest.IsolatedAsyncioTestCase):
    async def test_extraction_cannot_supersede_a_candidate_from_the_same_envelope(self) -> None:
        document_id = uuid4()
        run_id = uuid4()
        fragment = EvidenceFragment.create(document_id, "row:1", "price 100")
        original = assertion(number="100").model_copy(
            update={
                "document_id": document_id,
                "evidence_fragment_id": fragment.id,
                "extraction_run_id": run_id,
            }
        )
        correction = original.model_copy(
            update={
                "id": uuid4(),
                "value": "120",
                "normalized_number": Decimal("120"),
                "supersedes_id": original.id,
            }
        )
        document = SourceDocument(
            id=document_id,
            source_id=original.source_id,
            canonical_url="https://example.test/same-envelope",
            first_known_at=original.known_at,
            retrieved_at=original.known_at,
            content_type="text/plain",
            content_sha256="a" * 64,
            blob_key="raw/sha256/aa/" + "a" * 64,
            byte_length=9,
        )
        envelope = ExtractionEnvelope(
            run_id=run_id,
            document_id=document_id,
            extractor_name="test",
            extractor_version="1",
            schema_version="fact-v1",
            evidence=(fragment,),
            candidates=(original, correction),
        )

        with self.assertRaisesRegex(ValueError, "same envelope"):
            CollectionPipeline._validate_envelope(
                document,
                envelope,
                content=b"price 100",
            )

    async def test_assertion_batch_cannot_create_an_internal_supersession_chain(self) -> None:
        repository = InMemoryResearchRepository()
        original = assertion(number="100")
        correction = original.model_copy(
            update={
                "id": uuid4(),
                "value": "120",
                "normalized_number": Decimal("120"),
                "supersedes_id": original.id,
            }
        )

        with self.assertRaisesRegex(ValueError, "own supersession target"):
            await repository.append_assertions((original, correction))

    async def test_assertion_cannot_reference_a_missing_supersession_target(self) -> None:
        repository = InMemoryResearchRepository()
        correction = assertion().model_copy(update={"supersedes_id": uuid4()})

        with self.assertRaisesRegex(ValueError, "unknown supersession target"):
            await repository.append_assertions((correction,))

    async def test_atomic_reconcile_requires_the_persisted_immutable_candidate(self) -> None:
        repository = InMemoryResearchRepository()
        candidate = assertion()
        with self.assertRaises(KeyError):
            await repository.reconcile_assertion(candidate, Reconciler())

        await repository.append_assertions((candidate,))
        forged = candidate.model_copy(update={"value": "999"})
        with self.assertRaisesRegex(ValueError, "persisted immutable assertion"):
            await repository.reconcile_assertion(forged, Reconciler())

    async def test_atomic_reconcile_replay_does_not_rerun_the_evaluator(self) -> None:
        class CountingReconciler(Reconciler):
            calls = 0

            def reconcile(self, candidate, existing):  # type: ignore[no-untyped-def]
                self.calls += 1
                return super().reconcile(candidate, existing)

        repository = InMemoryResearchRepository()
        candidate = assertion()
        evaluator = CountingReconciler()
        await repository.append_assertions((candidate,))

        first = await repository.reconcile_assertion(candidate, evaluator)
        second = await repository.reconcile_assertion(candidate, evaluator)

        self.assertEqual(first, second)
        self.assertEqual(evaluator.calls, 1)

    async def test_same_fact_reconciliation_is_serialized(self) -> None:
        repository = InMemoryResearchRepository()
        first = assertion(number="100", cluster="source-a")
        second = first.model_copy(
            update={
                "id": uuid4(),
                "value": "200",
                "normalized_number": Decimal("200"),
                "source_id": uuid4(),
                "source_cluster": "source-b",
                "document_id": uuid4(),
                "evidence_fragment_id": uuid4(),
            }
        )
        await repository.append_assertions((first, second))

        results = await asyncio.gather(
            repository.reconcile_assertion(first, Reconciler()),
            repository.reconcile_assertion(second, Reconciler()),
        )

        self.assertEqual(
            sorted(result.decision.value for result in results),
            [Decision.ACCEPT.value, Decision.CONFLICT.value],
        )
        self.assertEqual(
            sorted(repository.assertions[item.id].status.value for item in (first, second)),
            [FactStatus.CONFLICT.value, FactStatus.TRUSTED.value],
        )

    async def test_accepted_correction_marks_predecessor_superseded(self) -> None:
        repository = InMemoryResearchRepository()
        original = assertion(number="100").model_copy(update={"status": FactStatus.TRUSTED})
        correction = original.model_copy(
            update={
                "id": uuid4(),
                "value": "120",
                "normalized_number": Decimal("120"),
                "supersedes_id": original.id,
                "document_id": uuid4(),
                "known_at": original.known_at + timedelta(seconds=1),
                "status": FactStatus.CANDIDATE,
            }
        )
        await repository.append_assertions((original,))
        await repository.append_assertions((correction,))
        result = Reconciler().reconcile(
            correction,
            await repository.assertions_for_comparison(correction),
        )

        await repository.save_reconciliation(result)

        self.assertEqual(repository.assertions[original.id].status, FactStatus.SUPERSEDED)
        self.assertEqual(repository.assertions[correction.id].status, FactStatus.TRUSTED)

    async def test_decision_and_status_must_agree(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires status trusted"):
            ReconciliationResult(
                assertion_id=uuid4(),
                decision=Decision.ACCEPT,
                score=1,
                reason_codes=("invalid",),
                status=FactStatus.CONFLICT,
            )

    async def test_duplicate_evaluation_cannot_change_assertion_status(self) -> None:
        repository = InMemoryResearchRepository()
        candidate = assertion()
        await repository.append_assertions((candidate,))

        review = ReconciliationResult(
            assertion_id=candidate.id,
            decision=Decision.REVIEW,
            score=0.80,
            reason_codes=("quality_review",),
            status=FactStatus.REVIEW,
            evaluator_name="rule_reconciler",
            evaluator_version="2.0.0",
        )
        accept_same_identity = review.model_copy(
            update={
                "decision": Decision.ACCEPT,
                "score": 0.95,
                "reason_codes": ("quality_accepted",),
                "status": FactStatus.TRUSTED,
            }
        )

        await repository.save_reconciliation(review)
        await repository.save_reconciliation(accept_same_identity)

        self.assertEqual(len(repository.reconciliations), 1)
        self.assertEqual(repository.reconciliations[0].decision, Decision.REVIEW)
        self.assertEqual(repository.assertions[candidate.id].status, FactStatus.REVIEW)

        accept_new_policy = accept_same_identity.model_copy(update={"evaluator_version": "3.0.0"})
        await repository.save_reconciliation(accept_new_policy)

        self.assertEqual(len(repository.reconciliations), 2)
        self.assertEqual(repository.assertions[candidate.id].status, FactStatus.TRUSTED)
