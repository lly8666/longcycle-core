-- Preserve what people believed at the time, separately from what later became true.
-- Judgments are append-only source claims about the future or about uncertain states.
-- They are not canonical facts and must never be reconciled into truth merely because
-- several speakers agreed.

CREATE TABLE research.judgment_assertions (
    id uuid PRIMARY KEY,
    speaker_entity_id uuid REFERENCES core.entities(id),
    speaker_name_text text,
    speaker_role text,
    speaker_affiliation_entity_id uuid REFERENCES core.entities(id),
    subject_entity_id uuid REFERENCES core.entities(id),
    subject_industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    topic_code text NOT NULL,
    predicate_code text,
    comparability_hash char(64) REFERENCES research.fact_dimension_sets(comparability_hash),
    dimensions_complete boolean NOT NULL DEFAULT false,
    judgment_kind text NOT NULL,
    target_time_kind text NOT NULL,
    target_at timestamptz,
    target_from timestamptz,
    target_to timestamptz,
    value_kind text NOT NULL,
    value_numeric numeric(40, 12),
    value_low numeric(40, 12),
    value_high numeric(40, 12),
    value_text text,
    value_boolean boolean,
    value_date date,
    value_entity_id uuid REFERENCES core.entities(id),
    value_json jsonb,
    direction text,
    unit_code text REFERENCES core.units(code),
    expressed_probability double precision,
    summary text NOT NULL,
    source_published_at timestamptz,
    first_known_at timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    extraction_run_id uuid NOT NULL REFERENCES evidence.extraction_runs(id),
    source_connector_id uuid NOT NULL REFERENCES evidence.source_connectors(id),
    extractor_name text NOT NULL,
    extractor_version text NOT NULL,
    extraction_confidence double precision NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    CHECK (speaker_entity_id IS NOT NULL OR speaker_name_text IS NOT NULL),
    CHECK (num_nonnulls(subject_entity_id, subject_industry_node_id) = 1),
    CHECK ((predicate_code IS NULL) = (comparability_hash IS NULL)),
    CHECK (judgment_kind IN (
        'forecast', 'target', 'guidance', 'scenario', 'probability',
        'risk', 'thesis', 'commitment', 'consensus_statement'
    )),
    CHECK (target_time_kind IN ('instant', 'period', 'timeless', 'unknown')),
    CHECK (
        (target_time_kind = 'instant' AND target_at IS NOT NULL AND target_from IS NULL AND target_to IS NULL)
        OR (target_time_kind = 'period' AND target_at IS NULL AND (target_from IS NOT NULL OR target_to IS NOT NULL))
        OR (target_time_kind IN ('timeless', 'unknown') AND target_at IS NULL AND target_from IS NULL AND target_to IS NULL)
    ),
    CHECK (target_to IS NULL OR target_from IS NULL OR target_to > target_from),
    CHECK (value_kind IN ('numeric', 'numeric_range', 'text', 'boolean', 'date', 'entity', 'json', 'direction')),
    CHECK (
        (value_kind = 'numeric' AND value_numeric IS NOT NULL
            AND num_nonnulls(value_low, value_high, value_text, value_boolean, value_date, value_entity_id, value_json, direction) = 0)
        OR (value_kind = 'numeric_range' AND value_low IS NOT NULL AND value_high IS NOT NULL
            AND num_nonnulls(value_numeric, value_text, value_boolean, value_date, value_entity_id, value_json, direction) = 0)
        OR (value_kind = 'text' AND value_text IS NOT NULL
            AND num_nonnulls(value_numeric, value_low, value_high, value_boolean, value_date, value_entity_id, value_json, direction) = 0)
        OR (value_kind = 'boolean' AND value_boolean IS NOT NULL
            AND num_nonnulls(value_numeric, value_low, value_high, value_text, value_date, value_entity_id, value_json, direction) = 0)
        OR (value_kind = 'date' AND value_date IS NOT NULL
            AND num_nonnulls(value_numeric, value_low, value_high, value_text, value_boolean, value_entity_id, value_json, direction) = 0)
        OR (value_kind = 'entity' AND value_entity_id IS NOT NULL
            AND num_nonnulls(value_numeric, value_low, value_high, value_text, value_boolean, value_date, value_json, direction) = 0)
        OR (value_kind = 'json' AND value_json IS NOT NULL
            AND num_nonnulls(value_numeric, value_low, value_high, value_text, value_boolean, value_date, value_entity_id, direction) = 0)
        OR (value_kind = 'direction' AND direction IS NOT NULL
            AND num_nonnulls(value_numeric, value_low, value_high, value_text, value_boolean, value_date, value_entity_id, value_json) = 0)
    ),
    CHECK (value_low IS NULL OR value_high IS NULL OR value_low <= value_high),
    CHECK (direction IS NULL OR direction IN ('up', 'down', 'flat', 'positive', 'negative', 'mixed', 'uncertain')),
    CHECK (expressed_probability IS NULL OR expressed_probability BETWEEN 0 AND 1),
    CHECK (extraction_confidence BETWEEN 0 AND 1)
);

CREATE TABLE research.judgment_evidence (
    judgment_id uuid NOT NULL REFERENCES research.judgment_assertions(id),
    evidence_fragment_id uuid NOT NULL REFERENCES evidence.evidence_fragments(id),
    evidence_role text NOT NULL DEFAULT 'statement',
    PRIMARY KEY (judgment_id, evidence_fragment_id, evidence_role),
    CHECK (evidence_role IN ('statement', 'rationale', 'condition', 'caveat', 'context'))
);

CREATE TABLE research.judgment_rationales (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    judgment_id uuid NOT NULL REFERENCES research.judgment_assertions(id),
    rationale_kind text NOT NULL,
    summary text NOT NULL,
    linked_fact_assertion_id uuid REFERENCES research.fact_assertions(id),
    linked_judgment_id uuid REFERENCES research.judgment_assertions(id),
    evidence_fragment_id uuid REFERENCES evidence.evidence_fragments(id),
    ordinal integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (rationale_kind IN ('premise', 'mechanism', 'condition', 'risk', 'caveat', 'counterargument')),
    CHECK (linked_judgment_id IS NULL OR linked_judgment_id <> judgment_id),
    CHECK (ordinal >= 0)
);

CREATE TABLE research.judgment_relations (
    from_judgment_id uuid NOT NULL REFERENCES research.judgment_assertions(id),
    to_judgment_id uuid NOT NULL REFERENCES research.judgment_assertions(id),
    relation_type text NOT NULL,
    reason_summary text,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (from_judgment_id, to_judgment_id, relation_type),
    CHECK (from_judgment_id <> to_judgment_id),
    CHECK (relation_type IN (
        'revises', 'reaffirms', 'withdraws', 'narrows', 'widens',
        'depends_on', 'supports', 'contradicts'
    ))
);

-- Derived point-in-time consensus. A snapshot is a historical research artifact,
-- not a fact. `knowledge_cutoff` is the latest information allowed into the aggregate.
CREATE TABLE research.expectation_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_entity_id uuid REFERENCES core.entities(id),
    subject_industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    topic_code text NOT NULL,
    predicate_code text,
    comparability_hash char(64) REFERENCES research.fact_dimension_sets(comparability_hash),
    target_time_kind text NOT NULL,
    target_at timestamptz,
    target_from timestamptz,
    target_to timestamptz,
    knowledge_cutoff timestamptz NOT NULL,
    aggregation_method text NOT NULL,
    producer_name text NOT NULL,
    producer_version text NOT NULL,
    value_kind text NOT NULL,
    value_numeric numeric(40, 12),
    value_low numeric(40, 12),
    value_high numeric(40, 12),
    value_text text,
    direction text,
    unit_code text REFERENCES core.units(code),
    member_count integer NOT NULL,
    dispersion double precision,
    confidence double precision NOT NULL,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    CHECK (num_nonnulls(subject_entity_id, subject_industry_node_id) = 1),
    CHECK ((predicate_code IS NULL) = (comparability_hash IS NULL)),
    CHECK (target_time_kind IN ('instant', 'period', 'timeless', 'unknown')),
    CHECK (
        (target_time_kind = 'instant' AND target_at IS NOT NULL AND target_from IS NULL AND target_to IS NULL)
        OR (target_time_kind = 'period' AND target_at IS NULL AND (target_from IS NOT NULL OR target_to IS NOT NULL))
        OR (target_time_kind IN ('timeless', 'unknown') AND target_at IS NULL AND target_from IS NULL AND target_to IS NULL)
    ),
    CHECK (target_to IS NULL OR target_from IS NULL OR target_to > target_from),
    CHECK (value_kind IN ('numeric', 'numeric_range', 'text', 'direction')),
    CHECK (
        (value_kind = 'numeric' AND value_numeric IS NOT NULL AND value_low IS NULL AND value_high IS NULL AND value_text IS NULL AND direction IS NULL)
        OR (value_kind = 'numeric_range' AND value_numeric IS NULL AND value_low IS NOT NULL AND value_high IS NOT NULL AND value_text IS NULL AND direction IS NULL)
        OR (value_kind = 'text' AND value_numeric IS NULL AND value_low IS NULL AND value_high IS NULL AND value_text IS NOT NULL AND direction IS NULL)
        OR (value_kind = 'direction' AND value_numeric IS NULL AND value_low IS NULL AND value_high IS NULL AND value_text IS NULL AND direction IS NOT NULL)
    ),
    CHECK (value_low IS NULL OR value_high IS NULL OR value_low <= value_high),
    CHECK (direction IS NULL OR direction IN ('up', 'down', 'flat', 'positive', 'negative', 'mixed', 'uncertain')),
    CHECK (member_count >= 0),
    CHECK (dispersion IS NULL OR dispersion >= 0),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (system_to IS NULL OR system_to > system_from)
);

CREATE TABLE research.expectation_snapshot_members (
    snapshot_id uuid NOT NULL REFERENCES research.expectation_snapshots(id),
    judgment_id uuid NOT NULL REFERENCES research.judgment_assertions(id),
    weight double precision NOT NULL DEFAULT 1,
    inclusion_reason text,
    PRIMARY KEY (snapshot_id, judgment_id),
    CHECK (weight >= 0)
);

-- Outcome evaluation is deliberately separate from the original judgment. It can be
-- recomputed as canonical facts are revised without rewriting what the speaker said.
CREATE TABLE research.judgment_outcome_evaluations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    judgment_id uuid NOT NULL REFERENCES research.judgment_assertions(id),
    canonical_fact_version_id uuid REFERENCES research.canonical_fact_versions(id),
    evaluation_status text NOT NULL,
    numeric_error numeric(40, 12),
    relative_error double precision,
    timing_error_days integer,
    direction_correct boolean,
    explanation text,
    evaluator_name text NOT NULL,
    evaluator_version text NOT NULL,
    evaluated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (
        judgment_id, canonical_fact_version_id, evaluator_name, evaluator_version
    ),
    CHECK (evaluation_status IN (
        'realized', 'partially_realized', 'not_realized', 'not_yet_evaluable', 'invalidated'
    ))
);

CREATE TRIGGER judgment_assertions_immutable
    BEFORE UPDATE OR DELETE ON research.judgment_assertions
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER judgment_evidence_immutable
    BEFORE UPDATE OR DELETE ON research.judgment_evidence
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER judgment_rationales_immutable
    BEFORE UPDATE OR DELETE ON research.judgment_rationales
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER judgment_relations_immutable
    BEFORE UPDATE OR DELETE ON research.judgment_relations
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER expectation_snapshot_members_immutable
    BEFORE UPDATE OR DELETE ON research.expectation_snapshot_members
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER judgment_outcome_evaluations_immutable
    BEFORE UPDATE OR DELETE ON research.judgment_outcome_evaluations
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE INDEX judgment_known_at_brin
    ON research.judgment_assertions USING brin (first_known_at);

CREATE INDEX judgment_subject_topic_idx
    ON research.judgment_assertions (
        subject_entity_id, subject_industry_node_id, topic_code, first_known_at DESC
    );

CREATE INDEX judgment_speaker_idx
    ON research.judgment_assertions (
        speaker_entity_id, speaker_affiliation_entity_id, first_known_at DESC
    );

CREATE INDEX judgment_predicate_target_idx
    ON research.judgment_assertions (
        predicate_code, comparability_hash, target_from, target_at, first_known_at DESC
    )
    WHERE predicate_code IS NOT NULL;

CREATE INDEX expectation_knowledge_cutoff_brin
    ON research.expectation_snapshots USING brin (knowledge_cutoff);

CREATE INDEX judgment_outcome_judgment_idx
    ON research.judgment_outcome_evaluations (judgment_id, evaluated_at DESC);
