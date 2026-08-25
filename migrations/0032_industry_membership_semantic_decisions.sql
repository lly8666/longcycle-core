CREATE TABLE research.industry_membership_semantic_decisions (
    id uuid PRIMARY KEY,
    resolution_id uuid NOT NULL REFERENCES research.fact_resolutions(id),
    candidate_assertion_ids uuid[] NOT NULL,
    selected_assertion_id uuid NOT NULL REFERENCES research.fact_assertions(id),
    reasoning_mode text NOT NULL,
    material_conflict_detected boolean NOT NULL DEFAULT false,
    reasoning_summary text NOT NULL,
    model_name text NOT NULL,
    model_version text,
    decided_at timestamptz NOT NULL,
    evidence_fragment_ids uuid[] NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (cardinality(candidate_assertion_ids) > 0),
    CHECK (selected_assertion_id = ANY(candidate_assertion_ids)),
    CHECK (cardinality(evidence_fragment_ids) > 0),
    CHECK (reasoning_mode IN ('standard', 'deep')),
    CHECK (NOT material_conflict_detected OR reasoning_mode = 'deep')
);

CREATE INDEX industry_membership_semantic_decisions_resolution_idx
    ON research.industry_membership_semantic_decisions (resolution_id, decided_at);

ALTER TABLE core.industry_entity_memberships
    ADD COLUMN semantic_decision_id uuid
        REFERENCES research.industry_membership_semantic_decisions(id);

CREATE UNIQUE INDEX industry_memberships_semantic_decision_idx
    ON core.industry_entity_memberships (semantic_decision_id)
    WHERE semantic_decision_id IS NOT NULL;
