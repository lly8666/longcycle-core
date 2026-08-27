-- Model memory is a research lead generator, never source evidence.
-- Internet material is evaluated by claim-specific authority rather than by search rank.
-- A model prior can challenge the archive, but it can never publish or overwrite a fact.

CREATE TABLE evidence.source_authority_profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    publisher_id uuid REFERENCES evidence.publishers(id),
    source_connector_id uuid REFERENCES evidence.source_connectors(id),
    claim_scope text NOT NULL,
    authority_class text NOT NULL,
    authority_basis text NOT NULL,
    valid_from date,
    valid_to date,
    supersedes_profile_id uuid REFERENCES evidence.source_authority_profiles(id),
    rationale text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (publisher_id IS NOT NULL OR source_connector_id IS NOT NULL),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (supersedes_profile_id IS NULL OR supersedes_profile_id <> id),
    CHECK (claim_scope IN (
        'legal_disclosure', 'official_statistic', 'self_statement', 'management_guidance',
        'market_measurement', 'project_status', 'policy_text', 'third_party_fact',
        'industry_expectation', 'technical_specification', 'other'
    )),
    CHECK (authority_class IN (
        'authoritative_primary', 'primary_self_statement', 'methodological_primary',
        'reputable_secondary', 'secondary', 'discovery_only'
    )),
    CHECK (authority_basis IN (
        'legal_mandate', 'official_record', 'direct_speaker_record', 'published_methodology',
        'editorial_verification', 'secondary_citation', 'unknown'
    ))
);

CREATE TABLE research.model_prior_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    run_mode text NOT NULL,
    source_visibility text NOT NULL,
    model_provider text NOT NULL,
    model_name text NOT NULL,
    model_version text,
    protocol_version text NOT NULL,
    declared_knowledge_cutoff timestamptz,
    archive_knowledge_cutoff timestamptz,
    input_digest char(64),
    prompt_digest char(64) NOT NULL,
    output_digest char(64) NOT NULL,
    raw_output jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (run_mode IN ('blind_recall', 'gap_audit', 'conflict_audit', 'association_expansion')),
    CHECK (source_visibility IN ('none', 'archive_only', 'archive_summary', 'search_results')),
    CHECK (input_digest IS NULL OR input_digest ~ '^[0-9a-f]{64}$'),
    CHECK (prompt_digest ~ '^[0-9a-f]{64}$'),
    CHECK (output_digest ~ '^[0-9a-f]{64}$')
);

CREATE TABLE research.model_memory_leads (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    prior_run_id uuid NOT NULL REFERENCES research.model_prior_runs(id),
    ordinal integer NOT NULL,
    lead_kind text NOT NULL,
    subject_entity_id uuid REFERENCES core.entities(id),
    subject_industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    topic_code text,
    summary text NOT NULL,
    approximate_from timestamptz,
    approximate_to timestamptz,
    recalled_details jsonb NOT NULL DEFAULT '{}'::jsonb,
    suggested_queries text[] NOT NULL DEFAULT '{}',
    suggested_source_types text[] NOT NULL DEFAULT '{}',
    memory_confidence double precision NOT NULL,
    importance_score double precision NOT NULL,
    novelty_score double precision NOT NULL,
    searchability_score double precision NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (prior_run_id, ordinal),
    CHECK (ordinal >= 0),
    CHECK (approximate_to IS NULL OR approximate_from IS NULL OR approximate_to > approximate_from),
    CHECK (lead_kind IN (
        'landmark', 'missing_event', 'actor', 'terminology', 'metric', 'mechanism',
        'pricing_rule', 'contract_change', 'process_bottleneck', 'project_pattern',
        'inventory_pattern', 'capital_cycle', 'policy_shift', 'technology_shift',
        'cross_industry_dependency', 'narrative', 'causal_hypothesis', 'anomaly'
    )),
    CHECK (memory_confidence BETWEEN 0 AND 1),
    CHECK (importance_score BETWEEN 0 AND 1),
    CHECK (novelty_score BETWEEN 0 AND 1),
    CHECK (searchability_score BETWEEN 0 AND 1)
);

CREATE TABLE research.model_memory_lead_relations (
    from_lead_id uuid NOT NULL REFERENCES research.model_memory_leads(id),
    to_lead_id uuid NOT NULL REFERENCES research.model_memory_leads(id),
    relation_type text NOT NULL,
    explanation text,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (from_lead_id, to_lead_id, relation_type),
    CHECK (from_lead_id <> to_lead_id),
    CHECK (relation_type IN (
        'associated_with', 'possible_cause', 'possible_effect', 'predecessor', 'successor',
        'search_synonym', 'same_episode', 'cross_chain_link', 'possible_revision'
    ))
);

CREATE TABLE research.memory_lead_evidence_links (
    lead_id uuid NOT NULL REFERENCES research.model_memory_leads(id),
    evidence_fragment_id uuid NOT NULL REFERENCES evidence.evidence_fragments(id),
    authority_profile_id uuid REFERENCES evidence.source_authority_profiles(id),
    claim_scope text NOT NULL,
    stance text NOT NULL,
    scope_match boolean NOT NULL,
    authority_snapshot jsonb NOT NULL,
    evaluator_name text NOT NULL,
    evaluator_version text NOT NULL,
    linked_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (lead_id, evidence_fragment_id, evaluator_name, evaluator_version),
    CHECK (stance IN ('supports', 'contradicts', 'context', 'weak_match', 'unrelated')),
    CHECK (claim_scope IN (
        'legal_disclosure', 'official_statistic', 'self_statement', 'management_guidance',
        'market_measurement', 'project_status', 'policy_text', 'third_party_fact',
        'industry_expectation', 'technical_specification', 'other'
    ))
);

CREATE TABLE research.memory_disagreement_cases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id uuid NOT NULL REFERENCES research.model_memory_leads(id),
    claim_scope text NOT NULL,
    opened_reason text NOT NULL,
    opened_at timestamptz NOT NULL DEFAULT now(),
    CHECK (claim_scope IN (
        'legal_disclosure', 'official_statistic', 'self_statement', 'management_guidance',
        'market_measurement', 'project_status', 'policy_text', 'third_party_fact',
        'industry_expectation', 'technical_specification', 'other'
    ))
);

CREATE TABLE research.memory_disagreement_resolutions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    disagreement_case_id uuid NOT NULL REFERENCES research.memory_disagreement_cases(id),
    disposition text NOT NULL,
    evidence_fragment_ids uuid[] NOT NULL DEFAULT '{}',
    rationale text NOT NULL,
    resolver_name text NOT NULL,
    resolver_version text NOT NULL,
    resolved_at timestamptz NOT NULL DEFAULT now(),
    CHECK (disposition IN (
        'unresolved', 'seek_primary', 'primary_supports_lead', 'primary_contradicts_lead',
        'authoritative_conflict', 'secondary_only_support', 'secondary_only_contradiction',
        'scope_mismatch', 'retired'
    ))
);

-- Append-only guards. A memory lead may later be contradicted, but the original model
-- recollection is preserved; a separate resolution records what happened.
CREATE TRIGGER source_authority_profiles_immutable
    BEFORE UPDATE OR DELETE ON evidence.source_authority_profiles
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER model_prior_runs_immutable
    BEFORE UPDATE OR DELETE ON research.model_prior_runs
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER model_memory_leads_immutable
    BEFORE UPDATE OR DELETE ON research.model_memory_leads
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER model_memory_lead_relations_immutable
    BEFORE UPDATE OR DELETE ON research.model_memory_lead_relations
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER memory_lead_evidence_links_immutable
    BEFORE UPDATE OR DELETE ON research.memory_lead_evidence_links
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER memory_disagreement_cases_immutable
    BEFORE UPDATE OR DELETE ON research.memory_disagreement_cases
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER memory_disagreement_resolutions_immutable
    BEFORE UPDATE OR DELETE ON research.memory_disagreement_resolutions
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE INDEX source_authority_scope_idx
    ON evidence.source_authority_profiles (claim_scope, authority_class, created_at DESC);

CREATE INDEX model_prior_runs_industry_idx
    ON research.model_prior_runs (industry_node_id, created_at DESC);

CREATE INDEX model_memory_leads_topic_idx
    ON research.model_memory_leads (subject_industry_node_id, topic_code, lead_kind, created_at DESC);

CREATE INDEX memory_lead_evidence_lead_idx
    ON research.memory_lead_evidence_links (lead_id, stance, scope_match, linked_at DESC);

CREATE INDEX memory_disagreement_case_lead_idx
    ON research.memory_disagreement_cases (lead_id, opened_at DESC);
