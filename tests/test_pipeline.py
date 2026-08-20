from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from longcycle.adapters.models import JsonFixtureGateway, NoopModelGateway
from longcycle.adapters.sources.local import LocalFolderSource
from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.application.pipeline import CollectionPipeline
from longcycle.application.reconciliation import Reconciler
from longcycle.domain.enums import FactStatus, QualityGrade, SourceKind
from longcycle.domain.models import (
    DiscoveryItem,
    EvidenceFragment,
    ExtractionEnvelope,
    RawPayload,
    SourceDefinition,
    SourceDocument,
    stable_uuid,
)
from longcycle.ports.archive import ArchivedObject
from longcycle.ports.model import ExtractionTarget
from longcycle.ports.source import DiscoveryContext, FetchContext


class PipelineTest(unittest.IsolatedAsyncioTestCase):
    async def test_pipeline_rejects_an_inconsistent_archive_receipt(self) -> None:
        class Plugin:
            plugin_name = "receipt-test"

            async def discover(self, context):  # type: ignore[no-untyped-def]
                del context
                if False:
                    yield None

            async def fetch(self, item, context):  # type: ignore[no-untyped-def]
                del item, context
                return RawPayload(
                    content=b"real bytes",
                    content_type="text/plain",
                    canonical_url="https://example.test/receipt",
                )

        class BadArchive:
            async def put_if_absent(self, **kwargs):  # type: ignore[no-untyped-def]
                del kwargs
                return ArchivedObject(
                    key="raw/wrong",
                    sha256="0" * 64,
                    size=0,
                    content_type="text/plain",
                    created=True,
                )

            async def get(self, key):  # type: ignore[no-untyped-def]
                raise KeyError(key)

            async def exists(self, key):  # type: ignore[no-untyped-def]
                del key
                return False

        source = SourceDefinition(
            id=stable_uuid("source", "receipt-test"),
            name="receipt-test",
            kind=SourceKind.MANUAL,
            plugin="receipt-test",
            quality_grade=QualityGrade.A,
        )
        pipeline = CollectionPipeline(
            repository=InMemoryResearchRepository([source]),
            archive=BadArchive(),
            model=NoopModelGateway(),
        )
        item = DiscoveryItem(
            source_id=source.id,
            url="https://example.test/receipt",
        )

        with self.assertRaisesRegex(ValueError, "archive receipt"):
            await pipeline.ingest(
                plugin=Plugin(),
                item=item,
                target=ExtractionTarget(),
                fetch_context=FetchContext(source=source),
            )

    async def test_html_evidence_must_be_grounded_in_visible_source_text(self) -> None:
        document = SourceDocument(
            id=stable_uuid("document", "html-grounding"),
            source_id=stable_uuid("source", "html-grounding"),
            canonical_url="https://example.test/grounding.html",
            first_known_at=datetime.now(UTC),
            retrieved_at=datetime.now(UTC),
            content_type="text/html; charset=utf-8",
            content_sha256="b" * 64,
            blob_key="raw/sha256/bb/" + "b" * 64,
            byte_length=24,
        )
        fragment = EvidenceFragment.create(document.id, "css:main", "invented price 999")
        envelope = ExtractionEnvelope(
            run_id=stable_uuid("run", "html-grounding"),
            document_id=document.id,
            extractor_name="test",
            extractor_version="1",
            schema_version="fact-v1",
            evidence=(fragment,),
            candidates=(),
        )
        with self.assertRaisesRegex(ValueError, "not grounded"):
            CollectionPipeline._validate_envelope(
                document,
                envelope,
                content=b"<html><main>reported price 100</main></html>",
            )

    async def test_structured_json_evidence_must_match_its_locator(self) -> None:
        document = SourceDocument(
            id=stable_uuid("document", "structured-grounding"),
            source_id=stable_uuid("source", "structured-grounding"),
            canonical_url="https://example.test/grounding.json",
            first_known_at=datetime.now(UTC),
            retrieved_at=datetime.now(UTC),
            content_type="application/json",
            content_sha256="c" * 64,
            blob_key="raw/sha256/cc/" + "c" * 64,
            byte_length=24,
        )
        fragment = EvidenceFragment.create(
            document.id,
            "$.value",
            None,
            {"amount": 999},
        )
        envelope = ExtractionEnvelope(
            run_id=stable_uuid("run", "structured-grounding"),
            document_id=document.id,
            extractor_name="test",
            extractor_version="1",
            schema_version="fact-v1",
            evidence=(fragment,),
            candidates=(),
        )
        with self.assertRaisesRegex(ValueError, "JSON locator"):
            CollectionPipeline._validate_envelope(
                document,
                envelope,
                content=b'{"value":{"amount":100}}',
            )

    async def test_json_excerpt_must_match_the_located_subtree(self) -> None:
        document = SourceDocument(
            id=stable_uuid("document", "json-locator-excerpt"),
            source_id=stable_uuid("source", "json-locator-excerpt"),
            canonical_url="https://example.test/locator.json",
            first_known_at=datetime.now(UTC),
            retrieved_at=datetime.now(UTC),
            content_type="application/json",
            content_sha256="d" * 64,
            blob_key="raw/sha256/dd/" + "d" * 64,
            byte_length=50,
        )
        fragment = EvidenceFragment.create(document.id, "$.facts[0]", "second")
        envelope = ExtractionEnvelope(
            run_id=stable_uuid("run", "json-locator-excerpt"),
            document_id=document.id,
            extractor_name="test",
            extractor_version="1",
            schema_version="fact-v1",
            evidence=(fragment,),
            candidates=(),
        )

        with self.assertRaisesRegex(ValueError, "JSON locator"):
            CollectionPipeline._validate_envelope(
                document,
                envelope,
                content=b'{"facts":[{"e":"first"},{"e":"second"}]}',
            )

    async def test_non_json_structured_evidence_requires_parser_lineage(self) -> None:
        document = SourceDocument(
            id=stable_uuid("document", "html-structured"),
            source_id=stable_uuid("source", "html-structured"),
            canonical_url="https://example.test/structured.html",
            first_known_at=datetime.now(UTC),
            retrieved_at=datetime.now(UTC),
            content_type="text/html",
            content_sha256="e" * 64,
            blob_key="raw/sha256/ee/" + "e" * 64,
            byte_length=18,
        )
        fragment = EvidenceFragment.create(
            document.id,
            "css:p",
            None,
            {"price": 999},
        )
        envelope = ExtractionEnvelope(
            run_id=stable_uuid("run", "html-structured"),
            document_id=document.id,
            extractor_name="test",
            extractor_version="1",
            schema_version="fact-v1",
            evidence=(fragment,),
            candidates=(),
        )

        with self.assertRaisesRegex(ValueError, "parser artifact"):
            CollectionPipeline._validate_envelope(
                document,
                envelope,
                content=b"<p>price 1</p>",
            )

        grounded = EvidenceFragment.create(
            document.id,
            "css:p",
            None,
            {"price": 1},
            artifact_id=uuid4(),
        )
        artifact_envelope = envelope.model_copy(update={"evidence": (grounded,)})
        CollectionPipeline._validate_envelope(
            document,
            artifact_envelope,
            content=b"<p>price 1</p>",
        )

    async def test_noncompliant_plugin_cannot_bypass_payload_limit(self) -> None:
        class OversizedPlugin:
            plugin_name = "oversized"

            async def discover(self, context):  # type: ignore[no-untyped-def]
                del context
                if False:
                    yield None

            async def fetch(self, item, context):  # type: ignore[no-untyped-def]
                del item, context
                return RawPayload(
                    content=b"too large",
                    content_type="text/plain",
                    canonical_url="https://example.test/large",
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = SourceDefinition(
                id=stable_uuid("source", "oversized"),
                name="oversized",
                kind=SourceKind.MANUAL,
                plugin="oversized",
                quality_grade=QualityGrade.A,
            )
            repository = InMemoryResearchRepository([source])
            pipeline = CollectionPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(root / "archive"),
                model=NoopModelGateway(),
            )
            item = DiscoveryItem(
                source_id=source.id,
                url="https://example.test/large",
            )
            with self.assertRaisesRegex(ValueError, "maximum_bytes"):
                await pipeline.ingest(
                    plugin=OversizedPlugin(),
                    item=item,
                    target=ExtractionTarget(),
                    fetch_context=FetchContext(source=source, maximum_bytes=3),
                )

    async def test_textual_evidence_must_be_grounded_in_source(self) -> None:
        document = SourceDocument(
            id=stable_uuid("document", "grounding"),
            source_id=stable_uuid("source", "grounding"),
            canonical_url="https://example.test/grounding.json",
            first_known_at=datetime.now(UTC),
            retrieved_at=datetime.now(UTC),
            content_type="application/json",
            content_sha256="a" * 64,
            blob_key="raw/sha256/aa/" + "a" * 64,
            byte_length=12,
        )
        fragment = EvidenceFragment.create(document.id, "$.value", "invented excerpt")
        envelope = ExtractionEnvelope(
            run_id=stable_uuid("run", "grounding"),
            document_id=document.id,
            extractor_name="test",
            extractor_version="1",
            schema_version="fact-v1",
            evidence=(fragment,),
            candidates=(),
        )
        with self.assertRaisesRegex(ValueError, "not grounded"):
            CollectionPipeline._validate_envelope(
                document,
                envelope,
                content=b'{"value": 12}',
            )

    async def test_noop_gateway_returns_a_deterministic_empty_envelope(self) -> None:
        source_id = stable_uuid("source", "noop")
        document = SourceDocument(
            id=stable_uuid("document", "noop"),
            source_id=source_id,
            canonical_url="https://example.test/noop",
            first_known_at=datetime.now(UTC),
            retrieved_at=datetime.now(UTC),
            content_type="text/plain",
            content_sha256="a" * 64,
            blob_key="raw/sha256/aa/" + "a" * 64,
            byte_length=0,
        )
        first = await NoopModelGateway().extract(
            document=document,
            content=b"",
            target=ExtractionTarget(industry_ids=()),
        )
        second = await NoopModelGateway().extract(
            document=document,
            content=b"",
            target=ExtractionTarget(industry_ids=()),
        )
        self.assertEqual(first.run_id, second.run_id)
        self.assertEqual(first.candidates, ())

    async def test_offline_end_to_end_and_replay_idempotency(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            industry_id = stable_uuid("industry", "vitamin-a")
            source_id = stable_uuid("source", "fixture")
            payload = {
                "facts": [
                    {
                        "entity_type": "industry",
                        "entity_id": str(industry_id),
                        "field_name": "price.market_index",
                        "value": "132",
                        "value_type": "number",
                        "number": "132",
                        "unit": "unit",
                        "dimensions": {
                            "product_spec_id": str(stable_uuid("product-spec", "vitamin-a-feed-500k")),
                            "geography_scheme": "internal",
                            "geography_code": "china",
                            "market_basis": "index",
                            "tax_basis": "included",
                            "freight_basis": "delivered",
                            "currency_code": "CNY",
                            "frequency": "daily",
                            "price_component": "average",
                        },
                        "valid_from": "2025-12-31",
                        "valid_to": "2026-01-01",
                        "locator": "$.facts[0]",
                        "excerpt": "Market index 132",
                        "confidence": 1,
                        "corroboration": 1,
                    }
                ]
            }
            (root / "facts.json").write_text(json.dumps(payload), encoding="utf-8")
            source = SourceDefinition(
                id=source_id,
                name="fixture",
                kind=SourceKind.MANUAL,
                plugin="local_folder",
                quality_grade=QualityGrade.A,
                config={"root": str(root), "patterns": ["*.json"]},
            )
            repository = InMemoryResearchRepository([source])
            plugin = LocalFolderSource(source)
            item = [item async for item in plugin.discover(DiscoveryContext(source=source))][0]
            pipeline = CollectionPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(root / "archive"),
                model=JsonFixtureGateway(source_quality=1),
            )
            target = ExtractionTarget(industry_ids=(industry_id,))
            first = await pipeline.ingest(
                plugin=plugin,
                item=item,
                target=target,
                fetch_context=FetchContext(source=source),
            )
            second = await pipeline.ingest(
                plugin=plugin,
                item=item,
                target=target,
                fetch_context=FetchContext(source=source),
            )
            self.assertTrue(first.was_new_document)
            self.assertFalse(second.was_new_document)
            self.assertEqual(first.accepted, 1)
            self.assertEqual(second.extracted, 0)
            self.assertEqual(second.cost_microunits, 0)
            self.assertEqual(len(repository.documents), 1)
            self.assertEqual(len(repository.assertions), 1)
            self.assertEqual(len(repository.extractions), 1)
            stored_assertion = next(iter(repository.assertions.values()))
            self.assertEqual(stored_assertion.quality.corroboration, 0)
            self.assertEqual(stored_assertion.quality.source_quality, 1)

    async def test_earlier_backfill_creates_new_provenance_with_earlier_known_time(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            industry_id = stable_uuid("industry", "knowledge-backfill")
            source_id = stable_uuid("source", "knowledge-backfill")
            (root / "facts.json").write_text(
                json.dumps(
                    {
                        "facts": [
                            {
                                "entity_type": "industry",
                                "entity_id": str(industry_id),
                                "field_name": "capacity.nameplate",
                                "value": "100 t",
                                "value_type": "number",
                                "number": "999",
                                "unit": "t",
                                "valid_from": "2026-01-01",
                                "valid_to": "2027-01-01",
                                "locator": "$.facts[0]",
                                "excerpt": "Capacity 100 t",
                                "confidence": 1,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            source = SourceDefinition(
                id=source_id,
                name="knowledge-backfill",
                kind=SourceKind.MANUAL,
                plugin="local_folder",
                quality_grade=QualityGrade.A,
                config={"root": str(root), "patterns": ["*.json"]},
            )
            repository = InMemoryResearchRepository([source])
            plugin = LocalFolderSource(source)
            discovered = [
                item async for item in plugin.discover(DiscoveryContext(source=source))
            ][0]
            later = discovered.model_copy(
                update={"discovered_at": datetime(2026, 8, 20, tzinfo=UTC)}
            )
            earlier = discovered.model_copy(
                update={"discovered_at": datetime(2025, 8, 20, tzinfo=UTC)}
            )
            pipeline = CollectionPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(root / "archive"),
                model=JsonFixtureGateway(),
            )
            target = ExtractionTarget(industry_ids=(industry_id,))

            first = await pipeline.ingest(
                plugin=plugin,
                item=later,
                target=target,
                fetch_context=FetchContext(source=source),
            )
            backfill = await pipeline.ingest(
                plugin=plugin,
                item=earlier,
                target=target,
                fetch_context=FetchContext(source=source),
            )

            self.assertEqual(first.extracted, 1)
            self.assertEqual(backfill.extracted, 1)
            self.assertEqual(len(repository.extractions), 2)
            self.assertEqual(
                min(assertion.known_at for assertion in repository.assertions.values()),
                earlier.discovered_at,
            )

    async def test_caller_cannot_upgrade_persisted_source_quality(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "facts.json").write_text('{"facts": []}', encoding="utf-8")
            source_id = stable_uuid("source", "quality-boundary")
            persisted = SourceDefinition(
                id=source_id,
                name="quality-boundary",
                kind=SourceKind.MANUAL,
                plugin="local_folder",
                quality_grade=QualityGrade.D,
                config={"root": str(root), "patterns": ["*.json"]},
            )
            forged = persisted.model_copy(update={"quality_grade": QualityGrade.A})
            repository = InMemoryResearchRepository([persisted])
            plugin = LocalFolderSource(persisted)
            item = [item async for item in plugin.discover(DiscoveryContext(source=persisted))][0]
            pipeline = CollectionPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(root / "archive"),
                model=JsonFixtureGateway(),
            )
            with self.assertRaisesRegex(ValueError, "persisted source definition"):
                await pipeline.ingest(
                    plugin=plugin,
                    item=item,
                    target=ExtractionTarget(),
                    fetch_context=FetchContext(source=forged),
                )

    async def test_reconciler_version_creates_a_distinct_audited_run(self) -> None:
        class ReconcilerV3(Reconciler):
            evaluator_version = "3.0.0"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            industry_id = stable_uuid("industry", "reconciler-version")
            source_id = stable_uuid("source", "reconciler-version")
            (root / "facts.json").write_text(
                json.dumps(
                    {
                        "facts": [
                            {
                                "entity_type": "industry",
                                "entity_id": str(industry_id),
                                "field_name": "capacity.nameplate",
                                "value": "100",
                                "value_type": "number",
                                "number": "100",
                                "unit": "t",
                                "valid_from": "2026-01-01",
                                "valid_to": "2027-01-01",
                                "locator": "$.facts[0]",
                                "excerpt": "Capacity 100 t",
                                "confidence": 1,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            source = SourceDefinition(
                id=source_id,
                name="reconciler-version",
                kind=SourceKind.MANUAL,
                plugin="local_folder",
                quality_grade=QualityGrade.A,
                config={"root": str(root), "patterns": ["*.json"]},
            )
            repository = InMemoryResearchRepository([source])
            plugin = LocalFolderSource(source)
            item = [item async for item in plugin.discover(DiscoveryContext(source=source))][0]
            target = ExtractionTarget(industry_ids=(industry_id,))
            first = CollectionPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(root / "archive"),
                model=JsonFixtureGateway(),
            )
            second = CollectionPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(root / "archive"),
                model=JsonFixtureGateway(),
                reconciler=ReconcilerV3(),
            )
            await first.ingest(
                plugin=plugin,
                item=item,
                target=target,
                fetch_context=FetchContext(source=source),
            )
            await second.ingest(
                plugin=plugin,
                item=item,
                target=target,
                fetch_context=FetchContext(source=source),
            )
            self.assertEqual(len(repository.extractions), 2)
            self.assertTrue(
                any(result.evaluator_version == "3.0.0" for result in repository.reconciliations)
            )

    async def test_same_document_can_be_extracted_for_a_new_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            industry_id = stable_uuid("industry", "target-test")
            source_id = stable_uuid("source", "target-test")
            (root / "facts.json").write_text(
                json.dumps(
                    {
                        "facts": [
                            {
                                "entity_type": "industry",
                                "entity_id": str(industry_id),
                                "field_name": "price.market_index",
                                "value": "100",
                                "value_type": "number",
                                "number": "100",
                                "unit": "unit",
                                "valid_from": "2026-01-01",
                                "valid_to": "2026-01-02",
                                "locator": "$.facts[0]",
                                "excerpt": "Index 100",
                                "confidence": 1,
                                "corroboration": 1,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            source = SourceDefinition(
                id=source_id,
                name="target-test",
                kind=SourceKind.MANUAL,
                plugin="local_folder",
                quality_grade=QualityGrade.A,
                config={"root": str(root), "patterns": ["*.json"]},
            )
            repository = InMemoryResearchRepository([source])
            plugin = LocalFolderSource(source)
            item = [item async for item in plugin.discover(DiscoveryContext(source=source))][0]
            pipeline = CollectionPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(root / "archive"),
                model=JsonFixtureGateway(),
            )
            ignored = await pipeline.ingest(
                plugin=plugin,
                item=item,
                target=ExtractionTarget(
                    industry_ids=(industry_id,),
                    predicate_allowlist=("capacity.nameplate",),
                ),
                fetch_context=FetchContext(source=source),
            )
            later_item = item.model_copy(update={"discovered_at": item.discovered_at + timedelta(days=10)})
            extracted = await pipeline.ingest(
                plugin=plugin,
                item=later_item,
                target=ExtractionTarget(
                    industry_ids=(industry_id,),
                    predicate_allowlist=("price.market_index",),
                ),
                fetch_context=FetchContext(source=source),
            )

            self.assertEqual(ignored.extracted, 0)
            self.assertEqual(extracted.extracted, 1)
            self.assertFalse(extracted.was_new_document)
            self.assertEqual(len(repository.extractions), 2)
            self.assertEqual(len(repository.assertions), 1)
            self.assertEqual(next(iter(repository.assertions.values())).known_at, item.discovered_at)

    async def test_partial_processing_is_resumed_instead_of_skipped(self) -> None:
        class FailOnceRepository(InMemoryResearchRepository):
            fail_once = True

            async def append_assertions(self, assertions):  # type: ignore[no-untyped-def]
                if self.fail_once:
                    self.fail_once = False
                    raise RuntimeError("simulated crash after extraction persistence")
                await super().append_assertions(assertions)

        class SingleCallGateway(JsonFixtureGateway):
            calls = 0

            async def extract(self, **kwargs):  # type: ignore[no-untyped-def]
                self.calls += 1
                if self.calls > 1:
                    raise AssertionError("model was called again during recovery")
                return await super().extract(**kwargs)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            industry_id = stable_uuid("industry", "resume-test")
            source_id = stable_uuid("source", "resume-test")
            (root / "facts.json").write_text(
                json.dumps(
                    {
                        "facts": [
                            {
                                "entity_type": "industry",
                                "entity_id": str(industry_id),
                                "field_name": "price.market_index",
                                "value": "100",
                                "value_type": "number",
                                "number": "100",
                                "unit": "unit",
                                "dimensions": {
                                    "product_spec_id": str(stable_uuid("product-spec", "resume")),
                                    "geography_scheme": "internal",
                                    "geography_code": "china",
                                    "market_basis": "index",
                                    "tax_basis": "included",
                                    "freight_basis": "delivered",
                                    "currency_code": "CNY",
                                    "frequency": "daily",
                                    "price_component": "average",
                                },
                                "valid_from": "2026-01-01",
                                "valid_to": "2026-01-02",
                                "locator": "$.facts[0]",
                                "excerpt": "Index 100",
                                "confidence": 1,
                                "corroboration": 1,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            source = SourceDefinition(
                id=source_id,
                name="resume-test",
                kind=SourceKind.MANUAL,
                plugin="local_folder",
                quality_grade=QualityGrade.A,
                config={"root": str(root), "patterns": ["*.json"]},
            )
            repository = FailOnceRepository([source])
            plugin = LocalFolderSource(source)
            item = [item async for item in plugin.discover(DiscoveryContext(source=source))][0]
            gateway = SingleCallGateway()
            pipeline = CollectionPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(root / "archive"),
                model=gateway,
            )
            target = ExtractionTarget(industry_ids=(industry_id,))

            with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                await pipeline.ingest(
                    plugin=plugin,
                    item=item,
                    target=target,
                    fetch_context=FetchContext(source=source),
                )
            self.assertEqual(len(repository.extractions), 1)
            self.assertEqual(repository.completed_processing, set())

            resumed = await pipeline.ingest(
                plugin=plugin,
                item=item,
                target=target,
                fetch_context=FetchContext(source=source),
            )
            self.assertEqual(resumed.extracted, 1)
            self.assertEqual(resumed.accepted, 1)
            self.assertEqual(len(repository.completed_processing), 1)
            self.assertEqual(gateway.calls, 1)

    async def test_replay_uses_the_persisted_evaluation_for_follow_up_actions(self) -> None:
        class CrashAfterEvaluationRepository(InMemoryResearchRepository):
            fail_once = True

            async def save_reconciliation(self, result):  # type: ignore[no-untyped-def]
                effective = await super().save_reconciliation(result)
                if self.fail_once:
                    self.fail_once = False
                    raise RuntimeError("simulated crash after evaluation commit")
                return effective

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            industry_id = stable_uuid("industry", "effective-evaluation")
            source_id = stable_uuid("source", "effective-evaluation")
            (root / "facts.json").write_text(
                json.dumps(
                    {
                        "facts": [
                            {
                                "entity_type": "industry",
                                "entity_id": str(industry_id),
                                "field_name": "price.market_index",
                                "value": "100",
                                "value_type": "number",
                                "number": "100",
                                "unit": "unit",
                                "dimensions": {
                                    "product_spec_id": str(
                                        stable_uuid("product-spec", "effective-evaluation")
                                    ),
                                    "geography_scheme": "internal",
                                    "geography_code": "china",
                                    "market_basis": "index",
                                    "tax_basis": "included",
                                    "freight_basis": "delivered",
                                    "currency_code": "CNY",
                                    "frequency": "daily",
                                    "price_component": "average",
                                },
                                "valid_from": "2026-01-01",
                                "valid_to": "2026-01-02",
                                "locator": "$.facts[0]",
                                "excerpt": "Index 100",
                                "confidence": 1,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            source = SourceDefinition(
                id=source_id,
                name="effective-evaluation",
                kind=SourceKind.MANUAL,
                plugin="local_folder",
                quality_grade=QualityGrade.A,
                config={"root": str(root), "patterns": ["*.json"]},
            )
            repository = CrashAfterEvaluationRepository([source])
            plugin = LocalFolderSource(source)
            item = [item async for item in plugin.discover(DiscoveryContext(source=source))][0]
            pipeline = CollectionPipeline(
                repository=repository,
                archive=FileSystemArchiveStore(root / "archive"),
                model=JsonFixtureGateway(),
            )
            target = ExtractionTarget(industry_ids=(industry_id,))

            with self.assertRaisesRegex(RuntimeError, "after evaluation commit"):
                await pipeline.ingest(
                    plugin=plugin,
                    item=item,
                    target=target,
                    fetch_context=FetchContext(source=source),
                )

            original = next(iter(repository.assertions.values()))
            conflicting = original.model_copy(
                update={
                    "id": uuid4(),
                    "value": "200",
                    "normalized_number": original.normalized_number * 2,
                    "source_id": uuid4(),
                    "document_id": uuid4(),
                    "evidence_fragment_id": uuid4(),
                    "extraction_run_id": uuid4(),
                    "source_cluster": "independent-conflict",
                    "status": FactStatus.TRUSTED,
                }
            )
            await repository.append_assertions((conflicting,))

            resumed = await pipeline.ingest(
                plugin=plugin,
                item=item,
                target=target,
                fetch_context=FetchContext(source=source),
            )

            self.assertEqual(resumed.accepted, 1)
            self.assertEqual(resumed.conflicted, 0)
            self.assertEqual(repository.reviews, {})
            self.assertEqual(len(repository.reconciliations), 1)
            self.assertEqual(repository.assertions[original.id].status, FactStatus.TRUSTED)
