-- Preserve high-value model-memory hypotheses when direct claim evidence cannot be
-- recovered, without promoting inference into Fact/Judgment/Reality.
-- Supporting evidence here is indirect by construction; direct claim evidence must
-- still enter the normal Evidence / Assertion / Reconciliation pipeline.

CREATE TABLE research.memory_hypothesis_assessments (
    id uuid PRIMARY KEY,
    lead_id uuid NOT NULL REFERENCES research.model_memory_leads(id),
    disposition text NOT NULL,
    direct_source_search_status text NOT NULL,
    inference_confidence double precision NOT NULL,
    reasoning_summary text NOT NULL,
    alternative_explanations text[] NOT NULL DEFAULT '{}',
    falsification_conditions text[] NOT NULL DEFAULT '{}',
    search_receipt jsonb NOT NULL DEFAULT '{}'::jsonb,
    assessor_name text NOT NULL,
    assessor_version text NOT NULL,
    assessed_at timestamptz NOT NULL DEFAULT now(),
    CHECK (disposition IN (
        'unresolved', 'indirectly_corroborated', 'indirectly_contradicted',
        'mixed', 'insufficient_basis'
    )),
    CHECK (direct_source_search_status IN (
        'not_attempted', 'ongoing', 'exhausted_not_found',
        'blocked_closed_source', 'partially_recovered'
    )),
    CHECK (inference_confidence BETWEEN 0 AND 1),
    CHECK (
        disposition <> 'indirectly_corroborated'
        OR direct_source_search_status IN (
            'exhausted_not_found', 'blocked_closed_source', 'partially_recovered'
        )
    ),
    CHECK (
        disposition <> 'indirectly_corroborated'
        OR (
            cardinality(alternative_explanations) > 0
            AND cardinality(falsification_conditions) > 0
            AND search_receipt <> '{}'::jsonb
        )
    )
);

CREATE TABLE research.memory_hypothesis_evidence_links (
    assessment_id uuid NOT NULL REFERENCES research.memory_hypothesis_assessments(id),
    evidence_fragment_id uuid NOT NULL REFERENCES evidence.evidence_fragments(id),
    stance text NOT NULL,
    PRIMARY KEY (assessment_id, evidence_fragment_id, stance),
    CHECK (stance IN ('supports', 'contradicts', 'context'))
);

CREATE TABLE research.memory_hypothesis_lead_links (
    assessment_id uuid NOT NULL REFERENCES research.memory_hypothesis_assessments(id),
    related_lead_id uuid NOT NULL REFERENCES research.model_memory_leads(id),
    relation_role text NOT NULL,
    PRIMARY KEY (assessment_id, related_lead_id, relation_role),
    CHECK (relation_role IN ('supporting_memory', 'alternative_memory', 'contradicting_memory'))
);

CREATE TRIGGER memory_hypothesis_assessments_immutable
    BEFORE UPDATE OR DELETE ON research.memory_hypothesis_assessments
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER memory_hypothesis_evidence_links_immutable
    BEFORE UPDATE OR DELETE ON research.memory_hypothesis_evidence_links
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER memory_hypothesis_lead_links_immutable
    BEFORE UPDATE OR DELETE ON research.memory_hypothesis_lead_links
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE INDEX memory_hypothesis_lead_idx
    ON research.memory_hypothesis_assessments (lead_id, assessed_at DESC);

CREATE INDEX memory_hypothesis_disposition_idx
    ON research.memory_hypothesis_assessments (
        disposition, direct_source_search_status, assessed_at DESC
    );
