-- Real blind-memory output exposed a semantic gap in 0014/0015.
-- Recall strength, precision risk, entity resolution, and falsification/search archaeology
-- need first-class fields. These remain research-lead metadata, never evidence truth scores.

ALTER TABLE research.model_memory_leads
    DROP CONSTRAINT model_memory_leads_lead_kind_check;

ALTER TABLE research.model_memory_leads
    ADD CONSTRAINT model_memory_leads_lead_kind_check CHECK (lead_kind IN (
        'landmark', 'missing_event', 'actor', 'terminology', 'metric', 'mechanism',
        'pricing_rule', 'contract_change', 'process_bottleneck', 'project_pattern',
        'inventory_pattern', 'capital_cycle', 'policy_shift', 'technology_shift',
        'cross_industry_dependency', 'narrative', 'causal_hypothesis', 'anomaly',
        'failure_dead_end'
    ));

ALTER TABLE research.model_memory_leads
    ADD COLUMN memory_basis text NOT NULL DEFAULT 'mixed',
    ADD COLUMN precision_risk text NOT NULL DEFAULT 'unknown',
    ADD COLUMN entity_resolution_state text NOT NULL DEFAULT 'unresolved',
    ADD COLUMN uncertain_fields text[] NOT NULL DEFAULT '{}',
    ADD COLUMN aliases_or_old_terms text[] NOT NULL DEFAULT '{}',
    ADD COLUMN why_search_may_miss_it text,
    ADD COLUMN disconfirmation_queries text[] NOT NULL DEFAULT '{}',
    ADD COLUMN disconfirmation_source_types text[] NOT NULL DEFAULT '{}',
    ADD COLUMN satellite_trigger text;

ALTER TABLE research.model_memory_leads
    ADD CONSTRAINT model_memory_leads_memory_basis_check CHECK (memory_basis IN (
        'remembered_event',
        'remembered_actor_or_name',
        'remembered_mechanism',
        'associative_inference',
        'mixed'
    )),
    ADD CONSTRAINT model_memory_leads_precision_risk_check CHECK (precision_risk IN (
        'low', 'medium', 'high', 'unknown'
    )),
    ADD CONSTRAINT model_memory_leads_entity_resolution_state_check CHECK (entity_resolution_state IN (
        'stable', 'partially_resolved', 'ambiguous', 'unresolved'
    ));

-- A pass belongs to a concrete recall shard. Keeping shard_id on campaign membership
-- allows atomic checkpoint/restart without encoding all topology into pass_id strings.
ALTER TABLE research.model_memory_campaign_runs
    ADD COLUMN shard_id text;

CREATE INDEX model_memory_campaign_run_shard_idx
    ON research.model_memory_campaign_runs (campaign_id, shard_id, pass_family, pass_id, round_no);

CREATE INDEX model_memory_leads_precision_idx
    ON research.model_memory_leads (precision_risk, entity_resolution_state, created_at DESC);
