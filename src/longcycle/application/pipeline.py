from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from html.parser import HTMLParser
from uuid import UUID

from longcycle.domain.enums import (
    Decision,
    EntityType,
    QualityGrade,
    ReviewSeverity,
    ValidTimeKind,
)
from longcycle.domain.models import (
    DiscoveryItem,
    EvidenceFragment,
    ExtractionEnvelope,
    FactAssertion,
    QualityComponents,
    ReviewItem,
    SourceDefinition,
    SourceDocument,
    canonical_json,
    stable_uuid,
)
from longcycle.ports.archive import ArchiveStore
from longcycle.ports.model import ExtractionTarget, ModelGateway, planned_extraction_run_id
from longcycle.ports.repository import ResearchRepository
from longcycle.ports.source import FetchContext, SourcePlugin
from longcycle.ports.telemetry import NullTelemetry, Telemetry

from .normalization import AssertionNormalizer
from .reconciliation import Reconciler


_JSON_MISSING = object()


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
class PipelineReport:
    document_id: UUID
    content_sha256: str
    was_new_document: bool
    extracted: int
    accepted: int
    review: int
    conflicted: int
    quarantined: int
    cost_microunits: int


class CollectionPipeline:
    def __init__(
        self,
        *,
        repository: ResearchRepository,
        archive: ArchiveStore,
        model: ModelGateway,
        normalizer: AssertionNormalizer | None = None,
        reconciler: Reconciler | None = None,
        telemetry: Telemetry | None = None,
        max_assertions_per_document: int = 2_000,
        max_evidence_per_document: int = 5_000,
        max_evidence_bytes_per_document: int = 10 * 1024 * 1024,
    ) -> None:
        if max_assertions_per_document < 1:
            raise ValueError("max_assertions_per_document must be positive")
        if max_evidence_per_document < 1:
            raise ValueError("max_evidence_per_document must be positive")
        if max_evidence_bytes_per_document < 1:
            raise ValueError("max_evidence_bytes_per_document must be positive")
        self.repository = repository
        self.archive = archive
        self.model = model
        self.normalizer = normalizer or AssertionNormalizer()
        self.reconciler = reconciler or Reconciler()
        self.telemetry = telemetry or NullTelemetry()
        self.max_assertions_per_document = max_assertions_per_document
        self.max_evidence_per_document = max_evidence_per_document
        self.max_evidence_bytes_per_document = max_evidence_bytes_per_document

    async def ingest(
        self,
        *,
        plugin: SourcePlugin,
        item: DiscoveryItem,
        target: ExtractionTarget,
        fetch_context: FetchContext,
    ) -> PipelineReport:
        with self.telemetry.span("collection.ingest", source_id=str(item.source_id), url=item.url):
            if item.source_id != fetch_context.source.id:
                raise ValueError("discovery item and fetch context use different sources")
            source = await self.repository.get_source(item.source_id)
            if not source.enabled:
                raise ValueError(f"source is disabled: {source.id}")
            if source.plugin != plugin.plugin_name:
                raise ValueError("persisted source plugin does not match the supplied plugin")
            if fetch_context.source != source:
                raise ValueError("fetch context must use the persisted source definition")
            plugin_definition = getattr(plugin, "definition", None)
            if isinstance(plugin_definition, SourceDefinition) and plugin_definition != source:
                raise ValueError("plugin must be constructed from the persisted source definition")

            payload = await plugin.fetch(item, fetch_context)
            if len(payload.content) > fetch_context.maximum_bytes:
                raise ValueError("source payload exceeds configured maximum_bytes")
            archived = await self.archive.put_if_absent(
                content=payload.content,
                content_type=payload.content_type,
                metadata={},
            )
            if (
                archived.sha256 != payload.sha256
                or archived.size != len(payload.content)
                or archived.content_type != payload.content_type
                or not archived.key
            ):
                raise ValueError("archive receipt does not match the fetched payload")
            existing_document = await self.repository.document_by_hash(
                item.source_id,
                payload.canonical_url,
                payload.sha256,
                item.external_id,
            )
            document = SourceDocument.from_payload(
                source_id=item.source_id,
                payload=payload,
                blob_key=archived.key,
                external_id=item.external_id,
                title=item.title_hint,
                published_at=item.published_at_hint,
                first_known_at=item.discovered_at,
                metadata={**item.metadata, "requested_url": item.url},
            )
            document = await self.repository.save_document(document)

            extraction_identity = planned_extraction_run_id(
                document=document,
                gateway=self.model,
                target=target,
            )
            planned_run_id = stable_uuid(
                "pipeline-run-v4",
                str(extraction_identity),
                document.first_known_at.isoformat(),
                self.normalizer.normalizer_name,
                self.normalizer.normalizer_version,
                self.reconciler.evaluator_name,
                self.reconciler.evaluator_version,
                canonical_json(source.model_dump(mode="json")),
            )
            if await self.repository.processing_completed(planned_run_id):
                self.telemetry.increment(
                    "collection.documents_unchanged",
                    source_id=str(item.source_id),
                )
                return PipelineReport(
                    document_id=document.id,
                    content_sha256=document.content_sha256,
                    was_new_document=False,
                    extracted=0,
                    accepted=0,
                    review=0,
                    conflicted=0,
                    quarantined=0,
                    cost_microunits=0,
                )

            extraction = await self.repository.get_extraction(planned_run_id)
            attempt_cost_microunits = 0
            if extraction is None:
                generated = await self.model.extract(
                    document=document,
                    content=payload.content,
                    target=target,
                )
                attempt_cost_microunits = generated.cost_microunits
                if len(generated.candidates) > self.max_assertions_per_document:
                    raise ValueError("extraction exceeds assertion safety limit")
                self._validate_evidence_limits(generated.evidence)
                generated = self._bind_provenance(
                    document=document,
                    extraction=generated,
                    target=target,
                    source=source,
                    planned_run_id=planned_run_id,
                )
                self._validate_envelope(document, generated, content=payload.content)
                normalized = tuple(
                    self._bind_application_quality(
                        self.normalizer.normalize(candidate),
                        document=document,
                        target=target,
                    )
                    for candidate in generated.candidates
                )
                self._validate_candidate_consistency(normalized)
                generated = generated.model_copy(update={"candidates": normalized})
                # First immutable envelope wins if two workers race. Both then
                # continue from exactly the same persisted candidates.
                extraction = await self.repository.save_extraction(generated)
            if len(extraction.candidates) > self.max_assertions_per_document:
                raise ValueError("persisted extraction exceeds assertion safety limit")
            self._validate_evidence_limits(extraction.evidence)
            self._validate_envelope(document, extraction, content=payload.content)
            normalized = extraction.candidates
            self._validate_candidate_consistency(normalized)

            await self.repository.save_evidence(extraction.evidence)
            await self.repository.append_assertions(normalized)

            counts = {
                Decision.ACCEPT: 0,
                Decision.REVIEW: 0,
                Decision.CONFLICT: 0,
                Decision.QUARANTINE: 0,
            }
            for assertion in normalized:
                effective_result = await self.repository.reconcile_assertion(
                    assertion,
                    self.reconciler,
                )
                counts[effective_result.decision] += 1
                if effective_result.decision in {Decision.REVIEW, Decision.CONFLICT}:
                    severity = (
                        ReviewSeverity.CRITICAL if assertion.high_impact else ReviewSeverity.MEDIUM
                    )
                    await self.repository.enqueue_review(
                        ReviewItem(
                            id=stable_uuid(
                                "review-item-v1",
                                str(assertion.id),
                                effective_result.decision.value,
                                *effective_result.reason_codes,
                            ),
                            assertion_id=assertion.id,
                            severity=severity,
                            reason_codes=effective_result.reason_codes,
                            related_assertion_ids=effective_result.conflicting_assertion_ids,
                        )
                    )

            await self.repository.complete_processing(planned_run_id)

            self.telemetry.increment("collection.documents", source_id=str(item.source_id))
            self.telemetry.increment(
                "collection.assertions",
                value=len(normalized),
                source_id=str(item.source_id),
            )
            self.telemetry.observe(
                "collection.cost_microunits",
                attempt_cost_microunits,
                source_id=str(item.source_id),
            )
            return PipelineReport(
                document_id=document.id,
                content_sha256=document.content_sha256,
                was_new_document=existing_document is None,
                extracted=len(normalized),
                accepted=counts[Decision.ACCEPT],
                review=counts[Decision.REVIEW],
                conflicted=counts[Decision.CONFLICT],
                quarantined=counts[Decision.QUARANTINE],
                cost_microunits=attempt_cost_microunits,
            )

    @staticmethod
    def _validate_envelope(
        document: SourceDocument,
        extraction: ExtractionEnvelope,
        *,
        content: bytes | None = None,
    ) -> None:
        candidates = extraction.candidates
        evidence = extraction.evidence
        if extraction.document_id != document.id:
            raise ValueError("extraction envelope references a different document")
        evidence_ids = {fragment.id for fragment in evidence}
        candidate_ids = {candidate.id for candidate in candidates}
        for fragment in evidence:
            if fragment.document_id != document.id:
                raise ValueError("evidence references a different document")
            expected_fragment = EvidenceFragment.create(
                document_id=fragment.document_id,
                locator=fragment.locator,
                excerpt=fragment.excerpt,
                structured_payload=fragment.structured_payload,
                artifact_id=fragment.artifact_id,
            )
            if (
                fragment.id != expected_fragment.id
                or fragment.fragment_sha256 != expected_fragment.fragment_sha256
            ):
                raise ValueError("evidence fragment identity does not match its content")
        CollectionPipeline._validate_textual_grounding(document, evidence, content)
        for candidate in candidates:
            if candidate.document_id != document.id:
                raise ValueError("assertion references a different document")
            if candidate.evidence_fragment_id not in evidence_ids:
                raise ValueError("assertion has no evidence fragment in this extraction")
            if candidate.extraction_run_id != extraction.run_id:
                raise ValueError("assertion extraction_run_id does not match envelope")
            if candidate.supersedes_id in candidate_ids:
                raise ValueError("one extraction cannot supersede another candidate in the same envelope")

    @staticmethod
    def _validate_textual_grounding(
        document: SourceDocument,
        evidence: Sequence[object],
        content: bytes | None,
    ) -> None:
        media_type = document.content_type.split(";", 1)[0].strip().lower()
        if content is None or media_type not in {
            "text/plain",
            "text/csv",
            "text/html",
            "application/xhtml+xml",
            "application/json",
            "application/xml",
        }:
            return
        decoded = content.decode("utf-8", errors="replace")
        corpus: list[str] = []
        parsed: object = _JSON_MISSING
        if media_type == "application/json":
            try:
                parsed = json.loads(decoded)
            except json.JSONDecodeError:
                parsed = _JSON_MISSING
        elif media_type in {"text/html", "application/xhtml+xml"}:
            parser = _VisibleTextParser()
            parser.feed(decoded)
            corpus.append(" ".join(parser.parts))
        else:
            corpus.append(decoded)
        normalized_corpus = tuple(" ".join(item.split()) for item in corpus)
        for fragment in evidence:
            excerpt = getattr(fragment, "excerpt", None)
            structured_payload = getattr(fragment, "structured_payload", None)
            if media_type == "application/json":
                if parsed is _JSON_MISSING:
                    raise ValueError("evidence cannot be grounded in invalid JSON")
                located = CollectionPipeline._resolve_json_locator(
                    parsed,
                    getattr(fragment, "locator", ""),
                )
                if located is _JSON_MISSING:
                    raise ValueError("evidence JSON locator does not resolve")
                located_corpus = [canonical_json(located)]

                def collect_strings(value: object, corpus: list[str] = located_corpus) -> None:
                    if isinstance(value, str):
                        corpus.append(value)
                    elif isinstance(value, list):
                        for item in value:
                            collect_strings(item, corpus)
                    elif isinstance(value, dict):
                        for item in value.values():
                            collect_strings(item, corpus)

                collect_strings(located)
                if excerpt is not None:
                    normalized_excerpt = " ".join(excerpt.split())
                    normalized_located = tuple(
                        " ".join(item.split()) for item in located_corpus
                    )
                    if normalized_excerpt and not any(
                        normalized_excerpt in candidate for candidate in normalized_located
                    ):
                        raise ValueError("evidence excerpt is not grounded at its JSON locator")
                if structured_payload is not None and not CollectionPipeline._json_contains(
                    located, structured_payload
                ):
                    raise ValueError("structured evidence is not grounded at its JSON locator")
                continue
            if structured_payload is not None and getattr(fragment, "artifact_id", None) is None:
                raise ValueError(
                    "structured evidence requires JSON or a persisted parser artifact"
                )
            if excerpt is not None:
                normalized_excerpt = " ".join(excerpt.split())
                if normalized_excerpt and not any(
                    normalized_excerpt in candidate for candidate in normalized_corpus
                ):
                    raise ValueError("evidence excerpt is not grounded in the textual source")

    def _validate_evidence_limits(self, evidence: Sequence[EvidenceFragment]) -> None:
        if len(evidence) > self.max_evidence_per_document:
            raise ValueError("extraction exceeds evidence count safety limit")
        total_bytes = sum(
            len(fragment.locator.encode("utf-8"))
            + len((fragment.excerpt or "").encode("utf-8"))
            + len(canonical_json(fragment.structured_payload).encode("utf-8"))
            for fragment in evidence
        )
        if total_bytes > self.max_evidence_bytes_per_document:
            raise ValueError("extraction exceeds evidence byte safety limit")

    @staticmethod
    def _validate_candidate_consistency(assertions: Sequence[FactAssertion]) -> None:
        by_scope: dict[str, list[FactAssertion]] = {}
        for assertion in assertions:
            by_scope.setdefault(assertion.scope_key, []).append(assertion)
        for scoped in by_scope.values():
            for index, left in enumerate(scoped):
                for right in scoped[index + 1 :]:
                    explicitly_superseded = (
                        left.supersedes_id == right.id or right.supersedes_id == left.id
                    )
                    if (
                        not explicitly_superseded
                        and Reconciler._valid_times_overlap(left, right)
                        and left.value_fingerprint != right.value_fingerprint
                    ):
                        raise ValueError(
                            "extraction contains contradictory candidates for one fact scope"
                        )

    @staticmethod
    def _resolve_json_locator(root: object, locator: str) -> object:
        if locator == "$":
            return root
        if locator.startswith("/"):
            current = root
            for token in locator[1:].split("/"):
                token = token.replace("~1", "/").replace("~0", "~")
                if isinstance(current, dict) and token in current:
                    current = current[token]
                elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
                    current = current[int(token)]
                else:
                    return _JSON_MISSING
            return current
        if not locator.startswith("$"):
            return _JSON_MISSING
        current = root
        cursor = 1
        while cursor < len(locator):
            if locator[cursor] == ".":
                start = cursor + 1
                cursor = start
                while cursor < len(locator) and locator[cursor] not in ".[":
                    cursor += 1
                key = locator[start:cursor]
                if not key or not isinstance(current, dict) or key not in current:
                    return _JSON_MISSING
                current = current[key]
            elif locator[cursor] == "[":
                end = locator.find("]", cursor + 1)
                if end < 0:
                    return _JSON_MISSING
                token = locator[cursor + 1 : end]
                if not token.isdigit() or not isinstance(current, list):
                    return _JSON_MISSING
                index = int(token)
                if index >= len(current):
                    return _JSON_MISSING
                current = current[index]
                cursor = end + 1
            else:
                return _JSON_MISSING
        return current

    @staticmethod
    def _json_contains(actual: object, expected: object) -> bool:
        if isinstance(expected, dict):
            return isinstance(actual, dict) and all(
                key in actual and CollectionPipeline._json_contains(actual[key], value)
                for key, value in expected.items()
            )
        if isinstance(expected, list):
            return isinstance(actual, list) and actual == expected
        return actual == expected

    def _bind_provenance(
        self,
        *,
        document: SourceDocument,
        extraction: ExtractionEnvelope,
        target: ExtractionTarget,
        source: SourceDefinition,
        planned_run_id: UUID,
    ) -> ExtractionEnvelope:
        if source.id != document.source_id:
            raise ValueError("fetch context source does not match document source")

        source_quality = {
            QualityGrade.A: 1.0,
            QualityGrade.B: 0.85,
            QualityGrade.C: 0.65,
            QualityGrade.D: 0.40,
        }[source.quality_grade]
        if extraction.extractor_name != self.model.extractor_name:
            raise ValueError("extraction envelope uses an unexpected extractor name")
        if extraction.extractor_version != self.model.extractor_version:
            raise ValueError("extraction envelope uses an unexpected extractor version")
        if extraction.model_name != self.model.model_name:
            raise ValueError("extraction envelope uses an unexpected model name")
        candidates = []
        source_cluster = source.syndication_cluster or (
            f"publisher-domain:{source.publisher_domain.lower()}"
            if source.publisher_domain
            else f"connector:{source.id}"
        )
        for candidate in extraction.candidates:
            if target.predicate_allowlist and candidate.field_name not in target.predicate_allowlist:
                raise ValueError(f"model returned predicate outside allowlist: {candidate.field_name}")
            if (
                candidate.entity_type == EntityType.INDUSTRY
                and target.industry_ids
                and candidate.entity_id not in target.industry_ids
            ):
                raise ValueError("model returned an industry outside the extraction target")
            quality = QualityComponents(
                source_quality=source_quality,
                extraction_certainty=candidate.confidence,
                entity_match=0,
                time_unit_completeness=0,
                corroboration=0,
                freshness=self._freshness(document),
                conflict_penalty=0,
            )
            candidates.append(
                candidate.model_copy(
                    update={
                        "source_id": source.id,
                        "document_id": document.id,
                        "extraction_run_id": planned_run_id,
                        "extractor_name": extraction.extractor_name,
                        "extractor_version": extraction.extractor_version,
                        "source_cluster": source_cluster,
                        "source_published_at": document.published_at,
                        "known_at": document.first_known_at,
                        "quality": quality,
                        "high_impact": candidate.high_impact
                        or target.risk_tier.lower() in {"high", "critical"},
                    }
                )
            )
        return extraction.model_copy(
            update={
                "run_id": planned_run_id,
                "document_id": document.id,
                "schema_version": target.schema_version,
                "prompt_version": target.prompt_version,
                "candidates": tuple(candidates),
            }
        )

    @staticmethod
    def _freshness(document: SourceDocument) -> float:
        if document.published_at is None:
            return 0.5
        lag_seconds = (document.first_known_at - document.published_at).total_seconds()
        if lag_seconds < -86_400:
            return 0.2
        lag_days = max(0.0, lag_seconds / 86_400)
        if lag_days <= 7:
            return 1.0
        if lag_days <= 30:
            return 0.9
        if lag_days <= 365:
            return 0.75
        return 0.5

    @staticmethod
    def _bind_application_quality(
        assertion: FactAssertion,
        *,
        document: SourceDocument,
        target: ExtractionTarget,
    ) -> FactAssertion:
        entity_verified = (
            assertion.entity_type == EntityType.INDUSTRY
            and bool(target.industry_ids)
            and assertion.entity_id in target.industry_ids
        )
        time_score = 1.0 if assertion.valid_time_kind != ValidTimeKind.UNKNOWN else 0.0
        unit_score = 1.0
        if assertion.normalized_number is not None and assertion.normalized_unit is None:
            unit_score = 0.0
        dimension_score = 1.0 if assertion.dimensions_complete else 0.0
        completeness = (time_score + unit_score + dimension_score) / 3
        quality = assertion.quality.model_copy(
            update={
                "source_quality": assertion.quality.source_quality,
                "extraction_certainty": assertion.confidence,
                "entity_match": 1.0 if entity_verified else 0.5,
                "time_unit_completeness": completeness,
                "corroboration": 0.0,
                "freshness": CollectionPipeline._freshness(document),
                "conflict_penalty": 0.0,
            }
        )
        return assertion.model_copy(update={"quality": quality})
