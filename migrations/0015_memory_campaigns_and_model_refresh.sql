-- Treat each high-capability model/version as a research-instrument vintage.
-- Historical recovery is memory-first but evidence-final: campaigns build sealed lead maps;
-- later verification/search runs may reference them but never rewrite them.

-- 0014 introduced a small audit-oriented run-mode set. Exhaustive recall needs to record
-- orthogonal recall passes, atlas refinement, self-search verification and model-refresh diffs.
ALTER TABLE research.model_prior_runs
    DROP CONSTRAINT model_prior_runs_run_mode_check;

ALTER TABLE research.model_prior_runs
    ADD CONSTRAINT model_prior_runs_run_mode_check CHECK (run_mode IN (
        'blind_recall', 'gap_audit', 'conflict_audit', 'association_expansion',
        'memory_exhaustion_pass', 'atlas_refinement', 'self_verification', 'refresh_diff'
    ));

CREATE TABLE research.model_memory_campaigns (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    campaign_kind text NOT NULL,
    period_from date,
    period_to date,
    model_provider text NOT NULL,
    model_name text NOT NULL,
    model_version text,
    declared_knowledge_cutoff timestamptz,
    protocol_version text NOT NULL,
    manifest_version text NOT NULL,
    manifest_digest char(64) NOT NULL,
    source_visibility text NOT NULL DEFAULT 'none',
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (campaign_kind IN ('historical_recall', 'model_refresh', 'benchmark', 'multi_model_compare')),
    CHECK (period_to IS NULL OR period_from IS NULL OR period_to >= period_from),
    CHECK (manifest_digest ~ '^[0-9a-f]{64}$'),
    CHECK (source_visibility IN ('none', 'archive_only', 'archive_summary', 'search_results'))
);

CREATE TABLE research.model_memory_campaign_runs (
    campaign_id uuid NOT NULL REFERENCES research.model_memory_campaigns(id),
    prior_run_id uuid NOT NULL REFERENCES research.model_prior_runs(id),
    pass_id text NOT NULL,
    pass_family text NOT NULL,
    round_no integer NOT NULL DEFAULT 1,
    parent_prior_run_id uuid REFERENCES research.model_prior_runs(id),
    run_phase text NOT NULL,
    novel_lead_count integer,
    duplicate_lead_count integer,
    high_importance_novel_count integer,
    coverage_delta jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (campaign_id, prior_run_id),
    UNIQUE (campaign_id, pass_id, round_no, run_phase),
    CHECK (round_no >= 1),
    CHECK (run_phase IN ('blind_recall', 'atlas_refinement', 'self_verification', 'gap_audit', 'refresh_diff')),
    CHECK (novel_lead_count IS NULL OR novel_lead_count >= 0),
    CHECK (duplicate_lead_count IS NULL OR duplicate_lead_count >= 0),
    CHECK (high_importance_novel_count IS NULL OR high_importance_novel_count >= 0)
);

-- The campaign row can exist before its runs. Sealing is a separate immutable event.
CREATE TABLE research.model_memory_campaign_seals (
    campaign_id uuid PRIMARY KEY REFERENCES research.model_memory_campaigns(id),
    sealed_at timestamptz NOT NULL DEFAULT now(),
    stop_reason text NOT NULL,
    coverage_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
    lead_count integer NOT NULL,
    high_importance_lead_count integer NOT NULL,
    output_digest char(64) NOT NULL,
    CHECK (lead_count >= 0),
    CHECK (high_importance_lead_count >= 0),
    CHECK (output_digest ~ '^[0-9a-f]{64}$')
);

-- Final or explicitly versioned coverage snapshots. Do not update a prior snapshot.
CREATE TABLE research.model_memory_coverage_cells (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id uuid NOT NULL REFERENCES research.model_memory_campaigns(id),
    snapshot_label text NOT NULL,
    dimension_type text NOT NULL,
    dimension_key text NOT NULL,
    period_from date,
    period_to date,
    coverage_state text NOT NULL,
    lead_count integer NOT NULL DEFAULT 0,
    high_importance_lead_count integer NOT NULL DEFAULT 0,
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (
        campaign_id, snapshot_label, dimension_type, dimension_key, period_from, period_to
    ),
    CHECK (dimension_type IN (
        'time', 'chain_node', 'actor', 'metric', 'mechanism', 'narrative',
        'terminology', 'failure', 'cross_industry', 'negative_space', 'other'
    )),
    CHECK (coverage_state IN ('unseen', 'thin', 'covered', 'dense', 'needs_review')),
    CHECK (lead_count >= 0),
    CHECK (high_importance_lead_count >= 0),
    CHECK (period_to IS NULL OR period_from IS NULL OR period_to >= period_from)
);

-- A model refresh compares two SEALED campaigns. It does not change the old campaign.
CREATE TABLE research.model_memory_refreshes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    baseline_campaign_id uuid NOT NULL REFERENCES research.model_memory_campaign_seals(campaign_id),
    refresh_campaign_id uuid NOT NULL REFERENCES research.model_memory_campaign_seals(campaign_id),
    comparison_method text NOT NULL,
    comparator_version text NOT NULL,
    archive_knowledge_cutoff timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (baseline_campaign_id <> refresh_campaign_id)
);

CREATE TABLE research.model_memory_refresh_lead_diffs (
    refresh_id uuid NOT NULL REFERENCES research.model_memory_refreshes(id),
    refresh_lead_id uuid NOT NULL REFERENCES research.model_memory_leads(id),
    baseline_lead_id uuid REFERENCES research.model_memory_leads(id),
    diff_kind text NOT NULL,
    semantic_similarity double precision,
    archive_coverage_state text NOT NULL,
    refinement_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    backfill_priority double precision NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (refresh_id, refresh_lead_id),
    CHECK (diff_kind IN ('known', 'refined', 'novel', 'possible_regression', 'ambiguous_match')),
    CHECK (semantic_similarity IS NULL OR semantic_similarity BETWEEN 0 AND 1),
    CHECK (archive_coverage_state IN ('unknown', 'uncovered', 'partial', 'well_covered', 'conflicted')),
    CHECK (backfill_priority BETWEEN 0 AND 1)
);

-- Delegated historical-verification task packet generated from a Memory Lead.
-- It can only be emitted after the blind campaign has been sealed, preventing search
-- feedback from contaminating unfinished recall passes.
CREATE TABLE ops.memory_verification_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id uuid NOT NULL REFERENCES research.model_memory_leads(id),
    campaign_id uuid NOT NULL REFERENCES research.model_memory_campaign_seals(campaign_id),
    task_version text NOT NULL,
    claim_scope text NOT NULL,
    lead_summary text NOT NULL,
    possible_actors text[] NOT NULL DEFAULT '{}',
    possible_aliases text[] NOT NULL DEFAULT '{}',
    query_families jsonb NOT NULL DEFAULT '[]'::jsonb,
    preferred_primary_sources text[] NOT NULL DEFAULT '{}',
    support_criteria text NOT NULL,
    contradiction_criteria text NOT NULL,
    minimum_search_depth jsonb NOT NULL,
    knowledge_cutoff timestamptz,
    status text NOT NULL DEFAULT 'queued',
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    CHECK (claim_scope IN (
        'legal_disclosure', 'official_statistic', 'self_statement', 'management_guidance',
        'market_measurement', 'project_status', 'policy_text', 'third_party_fact',
        'industry_expectation', 'technical_specification', 'other'
    )),
    CHECK (status IN ('queued', 'assigned', 'searching', 'primary_verified', 'primary_contradicted', 'unresolved', 'cancelled')),
    CHECK (completed_at IS NULL OR status IN ('primary_verified', 'primary_contradicted', 'unresolved', 'cancelled'))
);

-- Append-only research lineage. Operational verification-task status is mutable by design.
CREATE TRIGGER model_memory_campaigns_immutable
    BEFORE UPDATE OR DELETE ON research.model_memory_campaigns
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER model_memory_campaign_runs_immutable
    BEFORE UPDATE OR DELETE ON research.model_memory_campaign_runs
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER model_memory_campaign_seals_immutable
    BEFORE UPDATE OR DELETE ON research.model_memory_campaign_seals
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER model_memory_coverage_cells_immutable
    BEFORE UPDATE OR DELETE ON research.model_memory_coverage_cells
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER model_memory_refreshes_immutable
    BEFORE UPDATE OR DELETE ON research.model_memory_refreshes
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER model_memory_refresh_lead_diffs_immutable
    BEFORE UPDATE OR DELETE ON research.model_memory_refresh_lead_diffs
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE INDEX model_memory_campaign_industry_idx
    ON research.model_memory_campaigns (industry_node_id, created_at DESC);

CREATE INDEX model_memory_campaign_run_pass_idx
    ON research.model_memory_campaign_runs (campaign_id, pass_family, pass_id, round_no);

CREATE INDEX model_memory_coverage_campaign_idx
    ON research.model_memory_coverage_cells (campaign_id, snapshot_label, dimension_type);

CREATE INDEX model_memory_refresh_industry_idx
    ON research.model_memory_refreshes (industry_node_id, created_at DESC);

CREATE INDEX model_memory_refresh_diff_priority_idx
    ON research.model_memory_refresh_lead_diffs (refresh_id, backfill_priority DESC);

CREATE INDEX memory_verification_task_status_idx
    ON ops.memory_verification_tasks (status, created_at);

CREATE INDEX memory_verification_task_lead_idx
    ON ops.memory_verification_tasks (lead_id, created_at DESC);
