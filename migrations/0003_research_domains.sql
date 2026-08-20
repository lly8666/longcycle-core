INSERT INTO core.units (code, dimension, display_name, decimal_scale)
VALUES
    ('t', 'mass', 'tonne', 6),
    ('kg', 'mass', 'kilogram', 6),
    ('lb', 'mass', 'pound', 6),
    ('m3', 'volume', 'cubic metre', 6),
    ('unit', 'count', 'unit', 0),
    ('day', 'time', 'day', 4),
    ('ratio', 'ratio', 'ratio', 9),
    ('CNY', 'currency', 'Chinese yuan', 6),
    ('USD', 'currency', 'US dollar', 6)
ON CONFLICT (code) DO NOTHING;

INSERT INTO core.predicate_definitions (
    code, schema_version, canonical_name, value_kinds, temporal_mode,
    dimension_schema_version, required_dimensions, allowed_dimensions,
    high_impact, reconciliation_policy
) VALUES (
    'price.*',
    '1.0.0',
    'Comparable market price namespace',
    ARRAY['numeric'],
    'period',
    'fact-dimensions/v1',
    ARRAY[
        'product_spec_id', 'geography_scheme', 'geography_code', 'market_basis',
        'tax_basis', 'freight_basis', 'currency_code', 'frequency', 'price_component'
    ],
    ARRAY[
        'product_spec_id', 'geography_scheme', 'geography_code', 'market_basis',
        'contract_basis', 'tax_basis', 'freight_basis', 'incoterm', 'currency_code',
        'frequency', 'price_component', 'statistical_scope'
    ],
    true,
    '{"numeric_relative_tolerance":"0.01"}'::jsonb
) ON CONFLICT (code, schema_version) DO NOTHING;

CREATE TABLE research.metric_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text NOT NULL UNIQUE,
    canonical_name text NOT NULL,
    metric_kind text NOT NULL,
    stock_flow_type text NOT NULL,
    default_aggregation text NOT NULL,
    default_frequency text,
    description text,
    schema_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE research.metric_series (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_definition_id uuid NOT NULL REFERENCES research.metric_definitions(id),
    industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    product_spec_id uuid REFERENCES core.product_specs(id),
    facility_id uuid REFERENCES core.facilities(id),
    organization_entity_id uuid REFERENCES core.entities(id),
    geography_code text,
    market_basis text,
    contract_basis text,
    tax_basis text,
    freight_basis text,
    incoterm text,
    currency_code char(3),
    unit_code text NOT NULL REFERENCES core.units(code),
    frequency text NOT NULL,
    seasonal_adjustment text,
    statistical_scope text,
    comparability_hash char(64) NOT NULL,
    dimensions jsonb NOT NULL DEFAULT '{}'::jsonb,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (metric_definition_id, comparability_hash)
);

CREATE TABLE research.series_equivalence_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    from_series_id uuid NOT NULL REFERENCES research.metric_series(id),
    to_series_id uuid NOT NULL REFERENCES research.metric_series(id),
    equivalence_type text NOT NULL,
    conversion_expression text,
    valid_from date,
    valid_to date,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    confidence double precision NOT NULL,
    resolution_id uuid REFERENCES research.fact_resolutions(id),
    CHECK (from_series_id <> to_series_id),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (system_to IS NULL OR system_to > system_from)
);

CREATE TABLE research.observation_assertions (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    series_id uuid NOT NULL REFERENCES research.metric_series(id),
    fact_assertion_id uuid NOT NULL REFERENCES research.fact_assertions(id),
    period_start date NOT NULL,
    period_end date,
    value_numeric numeric(40, 12),
    low_value numeric(40, 12),
    high_value numeric(40, 12),
    raw_value text,
    raw_unit text,
    vintage_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (series_id, period_start, vintage_at, fact_assertion_id),
    CHECK (period_end IS NULL OR period_end > period_start),
    CHECK (value_numeric IS NOT NULL OR (low_value IS NOT NULL AND high_value IS NOT NULL)),
    CHECK (low_value IS NULL OR high_value IS NULL OR low_value <= high_value)
);

CREATE TABLE research.observation_versions (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    series_id uuid NOT NULL REFERENCES research.metric_series(id),
    period_start date NOT NULL,
    period_end date,
    value_numeric numeric(40, 12),
    low_value numeric(40, 12),
    high_value numeric(40, 12),
    unit_code text NOT NULL REFERENCES core.units(code),
    vintage_at timestamptz NOT NULL,
    market_known_at timestamptz,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    resolution_id uuid NOT NULL REFERENCES research.fact_resolutions(id),
    confidence double precision NOT NULL,
    quality_flags text[] NOT NULL DEFAULT '{}',
    CHECK (period_end IS NULL OR period_end > period_start),
    CHECK (system_to IS NULL OR system_to > system_from),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (value_numeric IS NOT NULL OR (low_value IS NOT NULL AND high_value IS NOT NULL)),
    CHECK (low_value IS NULL OR high_value IS NULL OR low_value <= high_value)
);

CREATE TABLE research.capacity_projects (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_entity_id uuid NOT NULL UNIQUE REFERENCES core.entities(id),
    industry_node_id uuid NOT NULL REFERENCES core.taxonomy_nodes(id),
    organization_entity_id uuid REFERENCES core.entities(id),
    facility_id uuid REFERENCES core.facilities(id),
    product_spec_id uuid REFERENCES core.product_specs(id),
    project_code text,
    canonical_name text NOT NULL,
    announced_at timestamptz,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE research.project_milestone_assertions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES research.capacity_projects(id),
    milestone_type text NOT NULL,
    milestone_at_low date,
    milestone_at_high date,
    fact_assertion_id uuid NOT NULL REFERENCES research.fact_assertions(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, milestone_type, fact_assertion_id),
    CHECK (milestone_at_high IS NULL OR milestone_at_low IS NULL OR milestone_at_high >= milestone_at_low)
);

CREATE TABLE research.project_status_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES research.capacity_projects(id),
    stage text NOT NULL,
    expected_start_low date,
    expected_start_high date,
    success_probability double precision NOT NULL,
    ramp_months integer,
    valid_from date,
    valid_to date,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    market_known_at timestamptz,
    resolution_id uuid NOT NULL REFERENCES research.fact_resolutions(id),
    CHECK (success_probability BETWEEN 0 AND 1),
    CHECK (ramp_months IS NULL OR ramp_months >= 0),
    CHECK (expected_start_high IS NULL OR expected_start_low IS NULL OR expected_start_high >= expected_start_low),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (system_to IS NULL OR system_to > system_from)
);

CREATE TABLE research.capacity_measurement_assertions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id uuid REFERENCES core.facilities(id),
    production_line_id uuid REFERENCES core.production_lines(id),
    project_id uuid REFERENCES research.capacity_projects(id),
    product_spec_id uuid NOT NULL REFERENCES core.product_specs(id),
    capacity_type text NOT NULL,
    capacity_value numeric(40, 12) NOT NULL,
    unit_code text NOT NULL REFERENCES core.units(code),
    valid_from date,
    valid_to date,
    fact_assertion_id uuid NOT NULL REFERENCES research.fact_assertions(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (num_nonnulls(facility_id, production_line_id, project_id) = 1),
    CHECK (capacity_value >= 0),
    CHECK (capacity_type IN ('design', 'nameplate', 'effective', 'approved', 'under_construction', 'announced')),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from)
);

CREATE TABLE research.capacity_ramp_assumption_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES research.capacity_projects(id),
    scenario_code text NOT NULL,
    month_offset integer NOT NULL,
    effective_ratio double precision NOT NULL,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    model_version text NOT NULL,
    rationale text,
    UNIQUE (project_id, scenario_code, month_offset, system_from),
    CHECK (month_offset >= 0),
    CHECK (effective_ratio BETWEEN 0 AND 1),
    CHECK (system_to IS NULL OR system_to > system_from)
);

CREATE TABLE research.event_clusters (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_entity_id uuid NOT NULL UNIQUE REFERENCES core.entities(id),
    event_type text NOT NULL,
    canonical_title text NOT NULL,
    occurrence_start timestamptz,
    occurrence_end timestamptz,
    time_precision text NOT NULL DEFAULT 'unknown',
    deduplication_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (occurrence_end IS NULL OR occurrence_start IS NULL OR occurrence_end >= occurrence_start)
);

CREATE TABLE research.event_claims (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NOT NULL REFERENCES research.event_clusters(id),
    fact_assertion_id uuid NOT NULL REFERENCES research.fact_assertions(id),
    claim_type text NOT NULL,
    claim_summary text NOT NULL,
    source_published_at timestamptz,
    first_known_at timestamptz NOT NULL,
    UNIQUE (event_id, fact_assertion_id, claim_type)
);

CREATE TABLE research.event_entity_links (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id uuid NOT NULL REFERENCES research.event_clusters(id),
    entity_id uuid REFERENCES core.entities(id),
    industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    relation_role text NOT NULL,
    UNIQUE NULLS NOT DISTINCT (event_id, entity_id, industry_node_id, relation_role),
    CHECK (entity_id IS NOT NULL OR industry_node_id IS NOT NULL)
);

CREATE TABLE research.event_impact_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id uuid NOT NULL REFERENCES research.event_clusters(id),
    target_entity_id uuid REFERENCES core.entities(id),
    target_industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    direction text NOT NULL,
    strength double precision,
    lag_low_days integer,
    lag_high_days integer,
    duration_low_days integer,
    duration_high_days integer,
    mechanism text NOT NULL,
    valid_from timestamptz,
    valid_to timestamptz,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    resolution_id uuid NOT NULL REFERENCES research.fact_resolutions(id),
    confidence double precision NOT NULL,
    CHECK (num_nonnulls(target_entity_id, target_industry_node_id) = 1),
    CHECK (strength IS NULL OR strength BETWEEN 0 AND 1),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (lag_high_days IS NULL OR lag_low_days IS NULL OR lag_high_days >= lag_low_days),
    CHECK (duration_high_days IS NULL OR duration_low_days IS NULL OR duration_high_days >= duration_low_days),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (system_to IS NULL OR system_to > system_from)
);

CREATE TABLE research.financial_reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    issuer_entity_id uuid NOT NULL REFERENCES core.entities(id),
    report_type text NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    published_at timestamptz NOT NULL,
    accounting_standard text,
    currency_code char(3),
    revision_ordinal integer NOT NULL DEFAULT 1,
    document_version_id uuid NOT NULL REFERENCES evidence.document_versions(id),
    supersedes_report_id uuid REFERENCES research.financial_reports(id),
    UNIQUE (issuer_entity_id, report_type, period_end, revision_ordinal),
    CHECK (period_end >= period_start),
    CHECK (revision_ordinal > 0)
);

CREATE TABLE research.reporting_segments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id uuid NOT NULL REFERENCES research.financial_reports(id),
    parent_segment_id uuid,
    segment_code text,
    segment_name text NOT NULL,
    segment_basis text NOT NULL,
    UNIQUE (report_id, segment_code, segment_name),
    UNIQUE (id, report_id),
    FOREIGN KEY (parent_segment_id, report_id)
        REFERENCES research.reporting_segments(id, report_id)
);

CREATE TABLE research.segment_financial_facts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id uuid NOT NULL REFERENCES research.reporting_segments(id),
    metric_code text NOT NULL,
    value_numeric numeric(40, 6) NOT NULL,
    unit_code text NOT NULL REFERENCES core.units(code),
    fact_assertion_id uuid NOT NULL REFERENCES research.fact_assertions(id),
    UNIQUE (segment_id, metric_code, fact_assertion_id)
);

CREATE TABLE research.company_exposure_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    issuer_entity_id uuid NOT NULL REFERENCES core.entities(id),
    industry_node_id uuid NOT NULL REFERENCES core.taxonomy_nodes(id),
    report_id uuid REFERENCES research.financial_reports(id),
    exposure_type text NOT NULL,
    revenue_share_low double precision,
    revenue_share_high double precision,
    profit_share_low double precision,
    profit_share_high double precision,
    cost_share_low double precision,
    cost_share_high double precision,
    capacity_share_low double precision,
    capacity_share_high double precision,
    sensitivity text,
    methodology text NOT NULL,
    valid_from date,
    valid_to date,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    resolution_id uuid NOT NULL REFERENCES research.fact_resolutions(id),
    confidence double precision NOT NULL,
    CHECK (revenue_share_low IS NULL OR revenue_share_low BETWEEN 0 AND 1),
    CHECK (revenue_share_high IS NULL OR revenue_share_high BETWEEN 0 AND 1),
    CHECK (profit_share_low IS NULL OR profit_share_low BETWEEN 0 AND 1),
    CHECK (profit_share_high IS NULL OR profit_share_high BETWEEN 0 AND 1),
    CHECK (cost_share_low IS NULL OR cost_share_low BETWEEN 0 AND 1),
    CHECK (cost_share_high IS NULL OR cost_share_high BETWEEN 0 AND 1),
    CHECK (capacity_share_low IS NULL OR capacity_share_low BETWEEN 0 AND 1),
    CHECK (capacity_share_high IS NULL OR capacity_share_high BETWEEN 0 AND 1),
    CHECK (revenue_share_high IS NULL OR revenue_share_low IS NULL OR revenue_share_high >= revenue_share_low),
    CHECK (profit_share_high IS NULL OR profit_share_low IS NULL OR profit_share_high >= profit_share_low),
    CHECK (cost_share_high IS NULL OR cost_share_low IS NULL OR cost_share_high >= cost_share_low),
    CHECK (capacity_share_high IS NULL OR capacity_share_low IS NULL OR capacity_share_high >= capacity_share_low),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (system_to IS NULL OR system_to > system_from)
);

CREATE TABLE research.industry_relations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    from_industry_node_id uuid NOT NULL REFERENCES core.taxonomy_nodes(id),
    to_industry_node_id uuid NOT NULL REFERENCES core.taxonomy_nodes(id),
    relation_type text NOT NULL,
    stable_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (from_industry_node_id, to_industry_node_id, relation_type),
    CHECK (from_industry_node_id <> to_industry_node_id)
);

CREATE TABLE research.industry_relation_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    relation_id uuid NOT NULL REFERENCES research.industry_relations(id),
    direction text NOT NULL,
    strength double precision NOT NULL,
    lag_low_days integer,
    lag_high_days integer,
    mechanism text NOT NULL,
    activation_condition text,
    valid_from date,
    valid_to date,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    resolution_id uuid NOT NULL REFERENCES research.fact_resolutions(id),
    confidence double precision NOT NULL,
    CHECK (strength BETWEEN 0 AND 1),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (lag_high_days IS NULL OR lag_low_days IS NULL OR lag_high_days >= lag_low_days),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (system_to IS NULL OR system_to > system_from)
);

CREATE TABLE research.cycle_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    industry_node_id uuid NOT NULL REFERENCES core.taxonomy_nodes(id),
    snapshot_at timestamptz NOT NULL,
    knowledge_cutoff timestamptz NOT NULL,
    model_code text NOT NULL,
    model_version text NOT NULL,
    data_version text NOT NULL,
    phase text NOT NULL,
    direction text NOT NULL,
    phase_probabilities jsonb NOT NULL,
    cycle_score double precision,
    price_percentile double precision,
    utilization double precision,
    inventory_days double precision,
    capacity_pressure double precision,
    data_completeness double precision NOT NULL,
    confidence double precision NOT NULL,
    explanation text NOT NULL,
    falsifiers jsonb NOT NULL DEFAULT '[]'::jsonb,
    generated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (industry_node_id, snapshot_at, knowledge_cutoff, model_code, model_version, data_version),
    CHECK (cycle_score IS NULL OR cycle_score BETWEEN 0 AND 100),
    CHECK (price_percentile IS NULL OR price_percentile BETWEEN 0 AND 100),
    CHECK (utilization IS NULL OR utilization BETWEEN 0 AND 1.5),
    CHECK (capacity_pressure IS NULL OR capacity_pressure BETWEEN 0 AND 1),
    CHECK (data_completeness BETWEEN 0 AND 1),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (snapshot_at <= knowledge_cutoff),
    CHECK (knowledge_cutoff <= generated_at)
);

CREATE INDEX metric_series_industry_kind_idx ON research.metric_series (industry_node_id, metric_definition_id);
CREATE INDEX observation_assertions_series_period_idx ON research.observation_assertions (series_id, period_start DESC, vintage_at DESC);
CREATE INDEX observation_versions_series_period_idx ON research.observation_versions (series_id, period_start DESC, system_from DESC)
    INCLUDE (value_numeric, low_value, high_value, confidence);
CREATE UNIQUE INDEX observation_versions_current_unique
    ON research.observation_versions (series_id, period_start, period_end, vintage_at) NULLS NOT DISTINCT
    WHERE system_to IS NULL;
CREATE INDEX capacity_projects_industry_idx ON research.capacity_projects (industry_node_id, announced_at DESC);
CREATE INDEX project_status_pipeline_idx ON research.project_status_versions (stage, expected_start_low)
    WHERE system_to IS NULL;
CREATE INDEX event_claims_known_idx ON research.event_claims (first_known_at DESC);
CREATE INDEX event_entity_links_entity_idx ON research.event_entity_links (entity_id, event_id);
CREATE INDEX event_entity_links_industry_idx ON research.event_entity_links (industry_node_id, event_id);
CREATE INDEX company_exposure_current_idx ON research.company_exposure_versions (issuer_entity_id, industry_node_id, valid_from DESC)
    WHERE system_to IS NULL;
CREATE INDEX industry_relations_from_idx ON research.industry_relations (from_industry_node_id, relation_type);
CREATE INDEX cycle_snapshots_industry_time_idx ON research.cycle_snapshots (industry_node_id, snapshot_at DESC, knowledge_cutoff DESC);

CREATE VIEW research.observation_current_per_vintage AS
SELECT observation.*
FROM research.observation_versions observation
WHERE observation.system_to IS NULL;

CREATE VIEW research.observation_current AS
SELECT DISTINCT ON (observation.series_id, observation.period_start, observation.period_end)
    observation.*
FROM research.observation_versions observation
WHERE observation.system_to IS NULL
ORDER BY
    observation.series_id,
    observation.period_start,
    observation.period_end,
    observation.vintage_at DESC,
    observation.system_from DESC;

CREATE VIEW research.company_exposure_current AS
SELECT exposure.*
FROM research.company_exposure_versions exposure
WHERE exposure.system_to IS NULL;
