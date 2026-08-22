from __future__ import annotations

import json
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one anchor, found {count}: {old[:100]!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def append_once(path: str, marker: str, addition: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if marker in text:
        raise SystemExit(f"{path}: marker already present: {marker}")
    target.write_text(text.rstrip() + "\n\n\n" + addition.strip() + "\n", encoding="utf-8")


replace_once(
    "src/longcycle/domain/models.py",
    """    observed_at: datetime | None = None
    source_published_at: datetime | None = None
""",
    """    observed_at: datetime | None = None
    observed_at_precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    observed_at_text: str | None = None
    source_published_at: datetime | None = None
""",
)

replace_once(
    "src/longcycle/domain/models.py",
    """        precision_key = "_longcycle_valid_time_precision"
        text_key = "_longcycle_valid_time_text"
        if "valid_time_precision" not in payload and precision_key in metadata:
            payload["valid_time_precision"] = metadata[precision_key]
        if "valid_time_text" not in payload and text_key in metadata:
            payload["valid_time_text"] = metadata[text_key]
        precision = payload.get("valid_time_precision", TemporalPrecision.UNKNOWN)
        precision_value = precision.value if isinstance(precision, TemporalPrecision) else str(precision)
        metadata[precision_key] = precision_value
        source_text = payload.get("valid_time_text")
        if source_text is not None:
            metadata[text_key] = source_text
        else:
            metadata.pop(text_key, None)
        payload["metadata"] = metadata
        return payload
""",
    """        precision_key = "_longcycle_valid_time_precision"
        text_key = "_longcycle_valid_time_text"
        if "valid_time_precision" not in payload and precision_key in metadata:
            payload["valid_time_precision"] = metadata[precision_key]
        if "valid_time_text" not in payload and text_key in metadata:
            payload["valid_time_text"] = metadata[text_key]
        precision = payload.get("valid_time_precision", TemporalPrecision.UNKNOWN)
        precision_value = precision.value if isinstance(precision, TemporalPrecision) else str(precision)
        metadata[precision_key] = precision_value
        source_text = payload.get("valid_time_text")
        if source_text is not None:
            metadata[text_key] = source_text
        else:
            metadata.pop(text_key, None)

        observed_precision_key = "_longcycle_observed_at_precision"
        observed_text_key = "_longcycle_observed_at_text"
        if "observed_at_precision" not in payload and observed_precision_key in metadata:
            payload["observed_at_precision"] = metadata[observed_precision_key]
        if "observed_at_text" not in payload and observed_text_key in metadata:
            payload["observed_at_text"] = metadata[observed_text_key]
        if payload.get("observed_at") is not None:
            observed_precision = payload.get(
                "observed_at_precision",
                TemporalPrecision.UNKNOWN,
            )
            observed_precision_value = (
                observed_precision.value
                if isinstance(observed_precision, TemporalPrecision)
                else str(observed_precision)
            )
            metadata[observed_precision_key] = observed_precision_value
            observed_text = payload.get("observed_at_text")
            if observed_text is not None:
                metadata[observed_text_key] = observed_text
            else:
                metadata.pop(observed_text_key, None)
        else:
            metadata.pop(observed_precision_key, None)
            metadata.pop(observed_text_key, None)
        payload["metadata"] = metadata
        return payload
""",
)

replace_once(
    "src/longcycle/domain/models.py",
    """        if self.valid_time_kind == ValidTimeKind.PERIOD and (
            self.valid_time.start is None and self.valid_time.end is None
        ):
            raise ValueError("period fact valid time requires a start and/or end bound")
        if not self.evidence:
""",
    """        if self.valid_time_kind == ValidTimeKind.PERIOD and (
            self.valid_time.start is None and self.valid_time.end is None
        ):
            raise ValueError("period fact valid time requires a start and/or end bound")
        if self.observed_at is None:
            if (
                self.observed_at_precision != TemporalPrecision.UNKNOWN
                or self.observed_at_text is not None
            ):
                raise ValueError("observed-at precision/text requires observed_at")
        elif (
            self.observed_at_precision == TemporalPrecision.APPROXIMATE
            and not self.observed_at_text
        ):
            raise ValueError("approximate observed-at time must preserve the source time text")
        if not self.evidence:
""",
)

replace_once(
    "src/longcycle/domain/epistemic.py",
    """    valid_time: TemporalExtent
    known_at: datetime
""",
    """    valid_time: TemporalExtent
    observed_time: TemporalExtent | None = None
    known_at: datetime
""",
)

replace_once(
    "src/longcycle/domain/epistemic.py",
    """        if len(set(self.evidence_fragment_ids)) != len(self.evidence_fragment_ids):
            raise ValueError("canonical Reality evidence references must be unique")
        return self
""",
    """        if len(set(self.evidence_fragment_ids)) != len(self.evidence_fragment_ids):
            raise ValueError("canonical Reality evidence references must be unique")
        if self.observed_time is not None and self.observed_time.kind != "instant":
            raise ValueError("canonical Reality observed_time must be an instant extent")
        return self
""",
)

replace_once(
    "src/longcycle/application/reality_projection.py",
    """    valid_time_kind: Literal[ValidTimeKind.PERIOD] = ValidTimeKind.PERIOD
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    valid_time_precision: TemporalPrecision
    valid_time_text: str | None = None
""",
    """    valid_time_kind: Literal[ValidTimeKind.PERIOD, ValidTimeKind.UNKNOWN] = ValidTimeKind.PERIOD
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    valid_time_precision: TemporalPrecision
    valid_time_text: str | None = None
    observed_at: datetime | None = None
    observed_at_precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    observed_at_text: str | None = None
""",
)

replace_once(
    "src/longcycle/application/reality_projection.py",
    """    @field_validator("valid_from", "valid_to")
""",
    """    @field_validator("valid_from", "valid_to", "observed_at")
""",
)

replace_once(
    "src/longcycle/application/reality_projection.py",
    """    @model_validator(mode="after")
    def has_valid_period(self) -> GroundedRealityProjectionItem:
        if self.valid_from is None and self.valid_to is None:
            raise ValueError("Reality projection period requires at least one valid-time bound")
        if self.valid_from is not None and self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("Reality projection valid_to must be after valid_from")
        if self.valid_time_precision == TemporalPrecision.APPROXIMATE and not self.valid_time_text:
            raise ValueError("approximate Reality projection must preserve source time text")
        return self
""",
    """    @model_validator(mode="after")
    def has_truthful_temporal_shape(self) -> GroundedRealityProjectionItem:
        if self.valid_time_kind == ValidTimeKind.PERIOD:
            if self.valid_from is None and self.valid_to is None:
                raise ValueError("Reality projection period requires at least one valid-time bound")
            if (
                self.valid_from is not None
                and self.valid_to is not None
                and self.valid_to <= self.valid_from
            ):
                raise ValueError("Reality projection valid_to must be after valid_from")
        else:
            if self.valid_from is not None or self.valid_to is not None:
                raise ValueError("unknown-onset Reality cannot carry valid-time bounds")
            if self.valid_time_precision != TemporalPrecision.UNKNOWN:
                raise ValueError("unknown-onset Reality cannot claim valid-time precision")
            if self.observed_at is None:
                raise ValueError("unknown-onset Reality requires a source-supported observed_at")
            if self.observed_at_precision == TemporalPrecision.UNKNOWN:
                raise ValueError("unknown-onset Reality requires observed-at source precision")
        if self.valid_time_precision == TemporalPrecision.APPROXIMATE and not self.valid_time_text:
            raise ValueError("approximate Reality projection must preserve source time text")
        if self.observed_at is None:
            if (
                self.observed_at_precision != TemporalPrecision.UNKNOWN
                or self.observed_at_text is not None
            ):
                raise ValueError("observed-at precision/text requires observed_at")
        elif (
            self.observed_at_precision == TemporalPrecision.APPROXIMATE
            and not self.observed_at_text
        ):
            raise ValueError("approximate observed-at time must preserve source time text")
        return self
""",
)

replace_once(
    "src/longcycle/application/reality_projection.py",
    """                valid_time_kind=ValidTimeKind.PERIOD,
                valid_time=TimeRange(start=item.valid_from, end=item.valid_to),
                valid_time_precision=item.valid_time_precision,
                valid_time_text=item.valid_time_text,
                source_published_at=cited.source_published_at,
""",
    """                valid_time_kind=item.valid_time_kind,
                valid_time=TimeRange(start=item.valid_from, end=item.valid_to),
                valid_time_precision=item.valid_time_precision,
                valid_time_text=item.valid_time_text,
                observed_at=item.observed_at,
                observed_at_precision=item.observed_at_precision,
                observed_at_text=item.observed_at_text,
                source_published_at=cited.source_published_at,
""",
)

replace_once(
    "src/longcycle/adapters/storage/postgres_epistemic.py",
    """def _judgment_target(row: dict[str, Any]) -> TemporalExtent:
""",
    """def _reality_observed_time(row: dict[str, Any]) -> TemporalExtent | None:
    if row["observed_at"] is None:
        return None
    return TemporalExtent(
        kind="instant",
        at=row["observed_at"],
        precision=TemporalPrecision(row["observed_at_precision"]),
        source_text=row["observed_at_text"],
    )


def _judgment_target(row: dict[str, Any]) -> TemporalExtent:
""",
)

replace_once(
    "src/longcycle/adapters/storage/postgres_epistemic.py",
    """                   canonical.valid_time_precision, canonical.valid_time_text,
                   canonical.market_known_at, canonical.confidence,
""",
    """                   canonical.valid_time_precision, canonical.valid_time_text,
                   canonical.observed_at, canonical.observed_at_precision,
                   canonical.observed_at_text,
                   canonical.market_known_at, canonical.confidence,
""",
)

replace_once(
    "src/longcycle/adapters/storage/postgres_epistemic.py",
    """            valid_time=_reality_time(row),
            known_at=row["market_known_at"],
""",
    """            valid_time=_reality_time(row),
            observed_time=_reality_observed_time(row),
            known_at=row["market_known_at"],
""",
)

replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """                valid_time_precision VARCHAR NOT NULL,
                valid_time_text VARCHAR,
                known_at TIMESTAMPTZ NOT NULL,
""",
    """                valid_time_precision VARCHAR NOT NULL,
                valid_time_text VARCHAR,
                observed_at TIMESTAMPTZ,
                observed_at_precision VARCHAR NOT NULL,
                observed_at_text VARCHAR,
                known_at TIMESTAMPTZ NOT NULL,
""",
)

replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""",
    """                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""",
)

replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """                    *_extent_values(reality_item.valid_time),
                    reality_item.known_at,
""",
    """                    *_extent_values(reality_item.valid_time),
                    (
                        reality_item.observed_time.at
                        if reality_item.observed_time is not None
                        else None
                    ),
                    (
                        reality_item.observed_time.precision.value
                        if reality_item.observed_time is not None
                        else TemporalPrecision.UNKNOWN.value
                    ),
                    (
                        reality_item.observed_time.source_text
                        if reality_item.observed_time is not None
                        else None
                    ),
                    reality_item.known_at,
""",
)

replace_once(
    "src/longcycle/adapters/storage/duckdb_epistemic.py",
    """            valid_time=cls._extent(row, "valid_time"),
            known_at=row["known_at"],
""",
    """            valid_time=cls._extent(row, "valid_time"),
            observed_time=(
                TemporalExtent(
                    kind="instant",
                    at=row["observed_at"],
                    precision=TemporalPrecision(row["observed_at_precision"]),
                    source_text=row["observed_at_text"],
                )
                if row["observed_at"] is not None
                else None
            ),
            known_at=row["known_at"],
""",
)

replace_once(
    "scripts/execute_grounded_reality_projection.py",
    """                   canonical.valid_time_precision, canonical.valid_time_text,
                   canonical.market_known_at, canonical.confidence,
""",
    """                   canonical.valid_time_precision, canonical.valid_time_text,
                   canonical.observed_at, canonical.observed_at_precision,
                   canonical.observed_at_text,
                   canonical.market_known_at, canonical.confidence,
""",
)

replace_once(
    "scripts/execute_grounded_reality_projection.py",
    """            "valid_time_semantics_preserved": all(
                row["valid_time_kind"] in {"period", "timeless", "unknown"}
                and row["valid_time_precision"] != "unknown"
                for row in canonical_rows
            ),
""",
    """            "valid_time_semantics_preserved": all(
                (
                    row["valid_time_kind"] == "period"
                    and (row["valid_from"] is not None or row["valid_to"] is not None)
                    and row["valid_time_precision"] != "unknown"
                )
                or (
                    row["valid_time_kind"] == "timeless"
                    and row["valid_from"] is None
                    and row["valid_to"] is None
                )
                or (
                    row["valid_time_kind"] == "unknown"
                    and row["valid_from"] is None
                    and row["valid_to"] is None
                )
                for row in canonical_rows
            ),
            "observation_semantics_preserved": all(
                row["valid_time_kind"] != "unknown"
                or (
                    row["observed_at"] is not None
                    and row["observed_at_precision"] != "unknown"
                )
                for row in canonical_rows
            ),
""",
)

replace_once(
    "tests/test_reality_projection.py",
    """from longcycle.domain.enums import EntityType, FactEvidenceRole, TemporalPrecision
""",
    """from longcycle.domain.enums import (
    EntityType,
    FactEvidenceRole,
    TemporalPrecision,
    ValidTimeKind,
)
""",
)

append_once(
    "tests/test_reality_projection.py",
    "test_unknown_onset_reality_uses_observation_without_fabricating_valid_from",
    r"""
def test_unknown_onset_reality_uses_observation_without_fabricating_valid_from() -> None:
    subject = RealityProjectionSubject(
        id=UUID(int=20),
        entity_type=EntityType.PRODUCTION_LINE,
        canonical_name="Kwinana Train 1",
    )
    observed_day = datetime(2022, 12, 3, tzinfo=UTC)
    known_upper_bound = datetime(2022, 12, 3, 23, 59, 59, tzinfo=UTC)
    evidence = GroundedRealityEvidence(
        fragment_key="continuous-production",
        evidence_fragment_id=UUID(int=21),
        document_version_id=UUID(int=22),
        source_connector_id=UUID(int=23),
        claim_role="project_status",
        known_time_upper_bound=known_upper_bound,
        source_published_at=observed_day,
        excerpt="The plant currently has continuous-production operating capability.",
    )
    spec = GroundedRealityProjectionSpec(
        schema_version="longcycle-reality-projection-spec/v1",
        task_id="kwinana-state-as-of-test",
        source_evidence_task_id="kwinana-evidence-test",
        allowed_claim_roles=("project_status",),
        subjects=(subject,),
        facts=(
            GroundedRealityProjectionItem(
                fact_key="continuous-production-as-of",
                evidence_fragment_key=evidence.fragment_key,
                subject_entity_id=subject.id,
                predicate_code="project.continuous_production_capability",
                value_text="had continuous-production operating capability",
                valid_time_kind=ValidTimeKind.UNKNOWN,
                valid_time_precision=TemporalPrecision.UNKNOWN,
                observed_at=observed_day,
                observed_at_precision=TemporalPrecision.DAY,
                observed_at_text="as of 2022-12-03",
            ),
        ),
    )

    fact = build_grounded_reality_facts(spec, (evidence,))[0]

    assert fact.valid_time_kind == ValidTimeKind.UNKNOWN
    assert fact.valid_time.start is None
    assert fact.valid_time.end is None
    assert fact.valid_time_precision == TemporalPrecision.UNKNOWN
    assert fact.observed_at == observed_day
    assert fact.observed_at_precision == TemporalPrecision.DAY
    assert fact.observed_at_text == "as of 2022-12-03"
    assert fact.known_at == known_upper_bound
""",
)

replace_once(
    "tests/test_epistemic_memory.py",
    """        valid_time=TemporalExtent(
            kind="period",
            start=datetime(2022, 7, 1, tzinfo=UTC),
            end=datetime(2022, 8, 1, tzinfo=UTC),
            precision=TemporalPrecision.MONTH,
            source_text="July 2022",
        ),
        known_at=OUTCOME_KNOWN,
""",
    """        valid_time=TemporalExtent(
            kind="period",
            start=datetime(2022, 7, 1, tzinfo=UTC),
            end=datetime(2022, 8, 1, tzinfo=UTC),
            precision=TemporalPrecision.MONTH,
            source_text="July 2022",
        ),
        observed_time=TemporalExtent(
            kind="instant",
            at=datetime(2022, 8, 3, tzinfo=UTC),
            precision=TemporalPrecision.DAY,
            source_text="as of 2022-08-03",
        ),
        known_at=OUTCOME_KNOWN,
""",
)

replace_once(
    "tests/test_epistemic_memory.py",
    """    assert at.reality[0].valid_time.source_text == "July 2022"
    assert at.outcomes[0].timing_delta_value == Decimal("2")
""",
    """    assert at.reality[0].valid_time.source_text == "July 2022"
    assert at.reality[0].observed_time is not None
    assert at.reality[0].observed_time.precision == TemporalPrecision.DAY
    assert at.reality[0].observed_time.source_text == "as of 2022-08-03"
    assert at.outcomes[0].timing_delta_value == Decimal("2")
""",
)

migration = r"""-- Preserve a source-supported observation/as-of axis separately from valid time.
-- This lets canonical Reality express "state is true as of T; onset unknown"
-- without fabricating valid_from=T. Observation precision remains explicit so a
-- day-level source is not silently reinterpreted as an exact instant.

ALTER TABLE research.canonical_fact_versions
    ADD COLUMN observed_at timestamptz,
    ADD COLUMN observed_at_precision text NOT NULL DEFAULT 'unknown',
    ADD COLUMN observed_at_text text;

ALTER TABLE research.canonical_fact_versions
    ADD CONSTRAINT canonical_fact_observed_at_precision_check CHECK (
        observed_at_precision IN (
            'instant', 'second', 'minute', 'hour', 'day', 'week', 'month',
            'quarter', 'half_year', 'year', 'range', 'approximate', 'unknown'
        )
    ),
    ADD CONSTRAINT canonical_fact_observed_at_shape_check CHECK (
        observed_at IS NOT NULL
        OR (observed_at_precision = 'unknown' AND observed_at_text IS NULL)
    ),
    ADD CONSTRAINT canonical_fact_observed_at_approximate_text_check CHECK (
        observed_at_precision <> 'approximate' OR observed_at_text IS NOT NULL
    );

UPDATE research.canonical_fact_versions canonical
SET observed_at = assertion.observed_at,
    observed_at_precision = COALESCE(
        assertion.metadata ->> '_longcycle_observed_at_precision',
        'unknown'
    ),
    observed_at_text = assertion.metadata ->> '_longcycle_observed_at_text'
FROM research.fact_resolution_assertions link
JOIN research.fact_assertions assertion ON assertion.id = link.assertion_id
WHERE link.resolution_id = canonical.resolution_id
  AND link.disposition = 'selected';

CREATE OR REPLACE FUNCTION research.inherit_canonical_fact_valid_time_precision()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    selected_kind text;
    selected_precision text;
    selected_text text;
    selected_observed_at timestamptz;
    selected_observed_precision text;
    selected_observed_text text;
BEGIN
    SELECT assertion.valid_time_kind,
           assertion.valid_time_precision,
           assertion.valid_time_text,
           assertion.observed_at,
           COALESCE(
               assertion.metadata ->> '_longcycle_observed_at_precision',
               'unknown'
           ),
           assertion.metadata ->> '_longcycle_observed_at_text'
      INTO selected_kind,
           selected_precision,
           selected_text,
           selected_observed_at,
           selected_observed_precision,
           selected_observed_text
      FROM research.fact_resolution_assertions link
      JOIN research.fact_assertions assertion ON assertion.id = link.assertion_id
     WHERE link.resolution_id = NEW.resolution_id
       AND link.disposition = 'selected'
     ORDER BY assertion.recorded_at DESC, assertion.id DESC
     LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'canonical fact resolution % has no selected assertion', NEW.resolution_id;
    END IF;

    NEW.valid_time_kind := selected_kind;
    NEW.valid_time_precision := selected_precision;
    NEW.valid_time_text := selected_text;
    NEW.observed_at := selected_observed_at;
    NEW.observed_at_precision := selected_observed_precision;
    NEW.observed_at_text := selected_observed_text;
    RETURN NEW;
END;
$$;
"""
Path("migrations/0024_canonical_observation_time.sql").write_text(migration, encoding="utf-8")

state_spec = {
    "schema_version": "longcycle-reality-projection-spec/v1",
    "task_id": "EVT-001-KWINANA-STATE-AS-OF-V1",
    "source_evidence_task_id": "EVT-001-KWINANA-EVIDENCE-V1",
    "allowed_claim_roles": ["project_status"],
    "subjects": [
        {
            "id": "02c2e600-9be2-5c09-95ab-b532249df05b",
            "entity_type": "production_line",
            "canonical_name": "Kwinana Train 1 lithium hydroxide plant",
        }
    ],
    "facts": [
        {
            "fact_key": "2022-train1-continuous-production-capability-as-of",
            "evidence_fragment_key": "2022-continuous-production-capability",
            "subject_entity_id": "02c2e600-9be2-5c09-95ab-b532249df05b",
            "predicate_code": "project.continuous_production_capability",
            "value_text": "had continuous-production operating capability",
            "valid_time_kind": "unknown",
            "valid_time_precision": "unknown",
            "observed_at": "2022-12-03T00:00:00Z",
            "observed_at_precision": "day",
            "observed_at_text": "as of 2022-12-03",
            "statistical_scope": "project operating capability",
            "extraction_confidence": 1.0,
            "source_quality": 1.0,
            "corroboration": 0.8,
            "metadata": {
                "semantic_guard": (
                    "The source supports that continuous-production operating capability "
                    "was true as of the 2022-12-03 disclosure day, but does not establish "
                    "when that state began. valid_time therefore remains unknown; "
                    "observed_at is not valid_from."
                ),
                "onset": "unspecified",
            },
        }
    ],
}
state_spec_path = Path(
    "research_data/memory/lithium-battery/2026-08-21-gpt-5.6-sol/"
    "self_verification/UP-CHEMICALS/run-001/tasks/"
    "EVT-001-kwinana-state-as-of-reality-v1.json"
)
state_spec_path.write_text(
    json.dumps(state_spec, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

runtime_workflow = r"""name: Kwinana state-as-of Reality runtime probe

on:
  push:
    branches:
      - design/industry-memory-runtime-probe2
  workflow_dispatch:

permissions:
  contents: read

jobs:
  state-as-of-reality:
    runs-on: ubuntu-24.04
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_USER: longcycle
          POSTGRES_PASSWORD: longcycle
          POSTGRES_DB: longcycle
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U longcycle -d longcycle"
          --health-interval=5s
          --health-timeout=5s
          --health-retries=20
    env:
      LONGCYCLE_DATABASE_URL: postgresql://longcycle:longcycle@127.0.0.1:5432/longcycle
      LONGCYCLE_BLOB_BACKEND: filesystem
      LONGCYCLE_BLOB_ROOT: ${{ github.workspace }}/.longcycle/action-blobs
      TASK_ROOT: research_data/memory/lithium-battery/2026-08-21-gpt-5.6-sol/self_verification/UP-CHEMICALS/run-001/tasks
      KWINANA_SUBJECT_ID: 02c2e600-9be2-5c09-95ab-b532249df05b
      PYTHONUNBUFFERED: "1"
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install exact Longcycle runtime
        shell: bash
        run: |
          set -euo pipefail
          python -m pip install --upgrade pip
          python -m pip install -e '.[postgres,duckdb]'

      - name: Apply repository migrations
        shell: bash
        run: |
          set -euo pipefail
          mkdir -p probe
          longcycle --json db upgrade | tee probe/migrations.json
          longcycle --json doctor --check-database | tee probe/doctor.json

      - name: Re-ground the locked Kwinana evidence set without discovery
        shell: bash
        run: |
          set -euo pipefail
          python scripts/execute_grounded_evidence_spec.py \
            "$TASK_ROOT/EVT-001-kwinana-evidence-spec-v1.json" \
            --output probe/kwinana-evidence-execution.json

      - name: Persist contemporaneous Judgments
        shell: bash
        run: |
          set -euo pipefail
          python scripts/execute_grounded_judgment_persistence.py \
            "$TASK_ROOT/EVT-001-kwinana-judgment-projection-v2.json" \
            probe/kwinana-evidence-execution.json \
            --output probe/kwinana-judgments.json

      - name: Persist existing commercial-production Reality
        shell: bash
        run: |
          set -euo pipefail
          python scripts/execute_grounded_reality_projection.py \
            "$TASK_ROOT/EVT-001-kwinana-reality-projection-v1.json" \
            probe/kwinana-evidence-execution.json \
            --output probe/kwinana-commercial-reality.json

      - name: Persist unknown-onset state-as-of Reality
        shell: bash
        run: |
          set -euo pipefail
          python scripts/execute_grounded_reality_projection.py \
            "$TASK_ROOT/EVT-001-kwinana-state-as-of-reality-v1.json" \
            probe/kwinana-evidence-execution.json \
            --output probe/kwinana-state-as-of-reality.json

      - name: Persist the existing related-milestone Outcome
        shell: bash
        run: |
          set -euo pipefail
          python scripts/execute_grounded_outcome_evaluation.py \
            probe/kwinana-judgments.json \
            probe/kwinana-commercial-reality.json \
            --judgment-key 2021-full-line-operation-by-year-end \
            --reality-fact-key 2022-train1-commercial-production-capability \
            --semantic-relation related_milestone \
            --output probe/kwinana-related-outcome.json

      - name: Seal typed PostgreSQL memory into portable DuckDB
        shell: bash
        run: |
          set -euo pipefail
          python scripts/export_integrated_replay_duckdb.py \
            probe/kwinana-state-as-of-memory.duckdb \
            --subject-id "$KWINANA_SUBJECT_ID" \
            --manifest-output probe/kwinana-state-as-of-memory-manifest.json

      - name: Verify typed state-as-of replay and no-lookahead
        shell: bash
        run: |
          set -euo pipefail
          python - <<'PY'
          import asyncio
          import json
          from datetime import datetime
          from pathlib import Path
          from uuid import UUID

          from longcycle.adapters.storage.duckdb_epistemic import DuckDBEpistemicMemoryReader
          from longcycle.domain.epistemic import MemorySubjectRef
          from longcycle.domain.enums import OutcomeSemanticRelation, TemporalPrecision

          database = Path('probe/kwinana-state-as-of-memory.duckdb')
          subject = MemorySubjectRef(
              entity_id=UUID('02c2e600-9be2-5c09-95ab-b532249df05b')
          )
          reader = DuckDBEpistemicMemoryReader(database)

          def dt(value: str) -> datetime:
              return datetime.fromisoformat(value.replace('Z', '+00:00'))

          async def load(cutoff: str):
              return await reader.snapshot((subject,), knowledge_cutoff=dt(cutoff))

          before_2022 = asyncio.run(load('2021-12-31T23:59:59Z'))
          pre_disclosure = asyncio.run(load('2022-12-02T23:59:59Z'))
          disclosed = asyncio.run(load('2022-12-03T23:59:59Z'))

          assert (len(before_2022.reality), len(before_2022.judgments), len(before_2022.outcomes)) == (0, 4, 0)
          assert (len(pre_disclosure.reality), len(pre_disclosure.judgments), len(pre_disclosure.outcomes)) == (0, 4, 0)
          assert (len(disclosed.reality), len(disclosed.judgments), len(disclosed.outcomes)) == (2, 5, 1)

          by_predicate = {item.predicate_code: item for item in disclosed.reality}
          commercial = by_predicate['project.commercial_production_capability']
          state_as_of = by_predicate['project.continuous_production_capability']

          assert commercial.valid_time.kind == 'period'
          assert commercial.valid_time.start == dt('2022-11-30T00:00:00Z')
          assert commercial.known_at == dt('2022-12-03T23:59:59Z')

          assert state_as_of.valid_time.kind == 'unknown'
          assert state_as_of.valid_time.start is None
          assert state_as_of.valid_time.end is None
          assert state_as_of.valid_time.precision == TemporalPrecision.UNKNOWN
          assert state_as_of.observed_time is not None
          assert state_as_of.observed_time.kind == 'instant'
          assert state_as_of.observed_time.at == dt('2022-12-03T00:00:00Z')
          assert state_as_of.observed_time.precision == TemporalPrecision.DAY
          assert state_as_of.observed_time.source_text == 'as of 2022-12-03'
          assert state_as_of.known_at == dt('2022-12-03T23:59:59Z')

          outcome = disclosed.outcomes[0]
          assert outcome.semantic_relation == OutcomeSemanticRelation.RELATED_MILESTONE
          assert outcome.evaluation_status == 'indeterminate'
          assert outcome.timing_relation == 'not_comparable'
          assert outcome.timing_delta_value is None
          assert outcome.timing_delta_unit is None

          payload = {
              'schema_version': 'longcycle-kwinana-state-as-of-replay-proof/v1',
              'before_2022_counts': {
                  'reality': len(before_2022.reality),
                  'judgments': len(before_2022.judgments),
                  'outcomes': len(before_2022.outcomes),
              },
              'pre_disclosure_counts': {
                  'reality': len(pre_disclosure.reality),
                  'judgments': len(pre_disclosure.judgments),
                  'outcomes': len(pre_disclosure.outcomes),
              },
              'disclosed': disclosed.model_dump(mode='json'),
              'verification': {
                  'unknown_onset_has_no_valid_bounds': True,
                  'observation_day_precision_preserved': True,
                  'known_time_remains_separate': True,
                  'no_lookahead_before_disclosure': True,
                  'existing_commercial_reality_unchanged': True,
                  'existing_related_outcome_unchanged': True,
                  'typed_duckdb_round_trip': True,
              },
          }
          Path('probe/kwinana-state-as-of-replay-proof.json').write_text(
              json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
              encoding='utf-8',
          )
          print(json.dumps(payload['verification'], indent=2))
          PY

      - name: Verify blind memory remained frozen and hash proof
        shell: bash
        run: |
          set -euo pipefail
          git diff --exit-code -- \
            research_data/memory/lithium-battery/2026-08-21-gpt-5.6-sol/blind/UP-CHEMICALS
          sha256sum \
            probe/kwinana-evidence-execution.json \
            probe/kwinana-commercial-reality.json \
            probe/kwinana-state-as-of-reality.json \
            probe/kwinana-related-outcome.json \
            probe/kwinana-state-as-of-memory.duckdb \
            probe/kwinana-state-as-of-replay-proof.json \
            | tee probe/SHA256SUMS.txt

      - name: Upload bounded runtime proof
        uses: actions/upload-artifact@v4
        with:
          name: kwinana-state-as-of-reality
          if-no-files-found: error
          retention-days: 30
          path: |
            probe/
            .longcycle/action-blobs/
"""
Path(".github/workflows/kwinana-state-as-of-runtime-probe.yml").write_text(
    runtime_workflow,
    encoding="utf-8",
)

print("STATE_AS_OF_PATCH_APPLIED")
