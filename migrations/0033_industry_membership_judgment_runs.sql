CREATE TABLE research.industry_membership_model_judgment_runs (
    id uuid PRIMARY KEY,
    resolution_id uuid NOT NULL REFERENCES research.fact_resolutions(id),
    candidate_assertion_ids uuid[] NOT NULL,
    input_assertion_hashes text[] NOT NULL,
    reasoning_mode text NOT NULL,
    provider_name text NOT NULL,
    model_name text NOT NULL,
    model_version text,
    started_at timestamptz NOT NULL,
    completed_at timestamptz NOT NULL,
    selected_assertion_id uuid REFERENCES research.fact_assertions(id),
    alternative_assertion_ids uuid[] NOT NULL DEFAULT '{}'::uuid[],
    material_conflict_detected boolean NOT NULL DEFAULT false,
    confidence numeric(6,5),
    can_materialize boolean NOT NULL DEFAULT false,
    reasoning_summary text NOT NULL,
    triggered_deep boolean NOT NULL DEFAULT false,
    deep_trigger_reasons text[] NOT NULL DEFAULT '{}'::text[],
    evidence_fragment_ids uuid[] NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (cardinality(candidate_assertion_ids) > 0),
    CHECK (cardinality(input_assertion_hashes) = cardinality(candidate_assertion_ids)),
    CHECK (selected_assertion_id IS NULL OR selected_assertion_id = ANY(candidate_assertion_ids)),
    CHECK (cardinality(evidence_fragment_ids) > 0),
    CHECK (reasoning_mode IN ('standard', 'deep')),
    CHECK (completed_at >= started_at),
    CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    CHECK (triggered_deep = (cardinality(deep_trigger_reasons) > 0))
);

CREATE INDEX industry_membership_judgment_runs_resolution_idx
    ON research.industry_membership_model_judgment_runs (resolution_id, completed_at, id);

-- Preserve pre-0033 decision provenance as an explicitly legacy run before removing
-- model-execution fields from the durable semantic decision table. The old schema did not
-- preserve input hashes or start time, so the backfill labels those facts honestly rather
-- than inventing precision.
INSERT INTO research.industry_membership_model_judgment_runs (
    id,
    resolution_id,
    candidate_assertion_ids,
    input_assertion_hashes,
    reasoning_mode,
    provider_name,
    model_name,
    model_version,
    started_at,
    completed_at,
    selected_assertion_id,
    alternative_assertion_ids,
    material_conflict_detected,
    confidence,
    can_materialize,
    reasoning_summary,
    triggered_deep,
    deep_trigger_reasons,
    evidence_fragment_ids
)
SELECT decision.id,
       decision.resolution_id,
       decision.candidate_assertion_ids,
       array_fill(
           'legacy_input_hash_unavailable'::text,
           ARRAY[cardinality(decision.candidate_assertion_ids)]
       ),
       decision.reasoning_mode,
       'legacy_unrecorded_provider',
       decision.model_name,
       decision.model_version,
       decision.decided_at,
       decision.decided_at,
       decision.selected_assertion_id,
       array_remove(decision.candidate_assertion_ids, decision.selected_assertion_id),
       decision.material_conflict_detected,
       NULL,
       true,
       decision.reasoning_summary,
       decision.reasoning_mode = 'deep',
       CASE
           WHEN decision.reasoning_mode = 'deep'
           THEN ARRAY['legacy_deep_trigger_unavailable']::text[]
           ELSE '{}'::text[]
       END,
       decision.evidence_fragment_ids
FROM research.industry_membership_semantic_decisions decision
ON CONFLICT (id) DO NOTHING;

ALTER TABLE research.industry_membership_semantic_decisions
    ADD COLUMN semantic_scope text NOT NULL DEFAULT 'industry.membership',
    ADD COLUMN supporting_judgment_run_ids uuid[],
    ADD COLUMN last_confirmed_at timestamptz;

UPDATE research.industry_membership_semantic_decisions
SET supporting_judgment_run_ids = ARRAY[id]::uuid[],
    last_confirmed_at = decided_at
WHERE supporting_judgment_run_ids IS NULL
   OR last_confirmed_at IS NULL;

ALTER TABLE research.industry_membership_semantic_decisions
    ALTER COLUMN supporting_judgment_run_ids SET NOT NULL,
    ALTER COLUMN last_confirmed_at SET NOT NULL;

-- PostgreSQL RENAME COLUMN is a standalone ALTER TABLE action; it cannot be mixed with
-- comma-separated ALTER COLUMN actions in the same statement.
ALTER TABLE research.industry_membership_semantic_decisions
    RENAME COLUMN reasoning_summary TO decision_summary;

ALTER TABLE research.industry_membership_semantic_decisions
    RENAME COLUMN decided_at TO first_decided_at;

ALTER TABLE research.industry_membership_semantic_decisions
    DROP COLUMN reasoning_mode,
    DROP COLUMN material_conflict_detected,
    DROP COLUMN model_name,
    DROP COLUMN model_version;

ALTER TABLE research.industry_membership_semantic_decisions
    ADD CHECK (semantic_scope = 'industry.membership'),
    ADD CHECK (cardinality(supporting_judgment_run_ids) > 0),
    ADD CHECK (last_confirmed_at >= first_decided_at);
