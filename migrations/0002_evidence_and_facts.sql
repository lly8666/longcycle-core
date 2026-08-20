CREATE TABLE evidence.publishers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name text NOT NULL,
    publisher_domain text,
    source_kind text NOT NULL,
    quality_grade char(1) NOT NULL,
    independence_cluster text,
    country_code char(2),
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (canonical_name, publisher_domain),
    CHECK (quality_grade IN ('A', 'B', 'C', 'D'))
);

CREATE TABLE evidence.source_connectors (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    publisher_id uuid REFERENCES evidence.publishers(id),
    name text NOT NULL,
    plugin_name text NOT NULL,
    endpoint_base_url text,
    enabled boolean NOT NULL DEFAULT true,
    rate_limit_per_minute integer NOT NULL DEFAULT 30,
    authentication_secret_ref text,
    robots_policy text NOT NULL DEFAULT 'respect',
    config jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (name),
    CHECK (rate_limit_per_minute > 0),
    CHECK (robots_policy IN ('respect', 'api_contract', 'manual_only', 'not_applicable'))
);

CREATE TABLE evidence.source_subscriptions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_id uuid NOT NULL REFERENCES evidence.source_connectors(id),
    industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    target_code text NOT NULL,
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    cursor jsonb,
    active boolean NOT NULL DEFAULT true,
    last_success_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (connector_id, industry_node_id, target_code)
);

CREATE TABLE evidence.content_blobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sha256 char(64) NOT NULL UNIQUE,
    bucket_name text NOT NULL,
    object_key text NOT NULL,
    object_version text,
    byte_length bigint NOT NULL,
    content_type text NOT NULL,
    compression text,
    encryption_key_ref text,
    created_at timestamptz NOT NULL DEFAULT now(),
    verified_at timestamptz,
    UNIQUE NULLS NOT DISTINCT (bucket_name, object_key, object_version),
    CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CHECK (byte_length >= 0)
);

CREATE TABLE evidence.documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    publisher_id uuid REFERENCES evidence.publishers(id),
    identity_owner_key text NOT NULL,
    canonical_url text NOT NULL,
    external_id text,
    logical_title text,
    document_type text,
    language_code text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (identity_owner_key, canonical_url, external_id)
);

CREATE TABLE evidence.document_fetches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_id uuid NOT NULL REFERENCES evidence.source_connectors(id),
    document_id uuid NOT NULL REFERENCES evidence.documents(id),
    requested_url text NOT NULL,
    final_url text NOT NULL,
    retrieved_at timestamptz NOT NULL,
    published_at timestamptz,
    first_known_at timestamptz NOT NULL,
    http_status integer,
    etag text,
    last_modified text,
    response_headers jsonb NOT NULL DEFAULT '{}'::jsonb,
    content_blob_id uuid REFERENCES evidence.content_blobs(id),
    fetch_error_code text,
    job_id uuid,
    trace_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, document_id, content_blob_id),
    CHECK (http_status IS NULL OR http_status BETWEEN 100 AND 599)
);

CREATE TABLE evidence.document_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id uuid NOT NULL REFERENCES evidence.documents(id),
    content_blob_id uuid NOT NULL REFERENCES evidence.content_blobs(id),
    first_fetch_id uuid NOT NULL,
    version_ordinal integer NOT NULL,
    effective_from timestamptz,
    effective_to timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, content_blob_id),
    UNIQUE (document_id, version_ordinal),
    FOREIGN KEY (first_fetch_id, document_id, content_blob_id)
        REFERENCES evidence.document_fetches(id, document_id, content_blob_id),
    CHECK (version_ordinal > 0),
    CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from)
);

CREATE TABLE evidence.artifacts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id uuid NOT NULL REFERENCES evidence.document_versions(id),
    artifact_type text NOT NULL,
    content_blob_id uuid NOT NULL REFERENCES evidence.content_blobs(id),
    producer_name text NOT NULL,
    producer_version text NOT NULL,
    input_hash text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_version_id, artifact_type, producer_name, producer_version, input_hash),
    UNIQUE (id, document_version_id)
);

CREATE TABLE evidence.evidence_fragments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id uuid NOT NULL REFERENCES evidence.document_versions(id),
    artifact_id uuid,
    locator_type text NOT NULL,
    locator jsonb NOT NULL,
    locator_hash char(64) NOT NULL,
    excerpt text,
    structured_payload jsonb,
    fragment_sha256 char(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_version_id, locator_type, locator_hash, fragment_sha256),
    FOREIGN KEY (artifact_id, document_version_id)
        REFERENCES evidence.artifacts(id, document_version_id),
    CHECK (locator_hash ~ '^[0-9a-f]{64}$'),
    CHECK (fragment_sha256 ~ '^[0-9a-f]{64}$'),
    CHECK (excerpt IS NOT NULL OR structured_payload IS NOT NULL)
);

CREATE TABLE evidence.prompt_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_code text NOT NULL,
    version text NOT NULL,
    template_sha256 char(64) NOT NULL,
    template_blob_id uuid REFERENCES evidence.content_blobs(id),
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (prompt_code, version)
);

CREATE TABLE evidence.extraction_schema_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_code text NOT NULL,
    version text NOT NULL,
    json_schema jsonb NOT NULL,
    schema_sha256 char(64) NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (schema_code, version)
);

CREATE TABLE evidence.model_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    provider text NOT NULL,
    model_name text NOT NULL,
    model_tier text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (provider, model_name)
);

CREATE TABLE evidence.extraction_runs (
    id uuid PRIMARY KEY,
    document_version_id uuid NOT NULL REFERENCES evidence.document_versions(id),
    artifact_id uuid REFERENCES evidence.artifacts(id),
    extractor_name text NOT NULL,
    extractor_version text NOT NULL,
    prompt_version_id uuid REFERENCES evidence.prompt_versions(id),
    schema_version_id uuid REFERENCES evidence.extraction_schema_versions(id),
    model_id uuid REFERENCES evidence.model_definitions(id),
    prompt_version_text text,
    schema_version_text text NOT NULL,
    model_name_text text,
    input_hash text NOT NULL,
    envelope_payload jsonb NOT NULL,
    output_blob_id uuid REFERENCES evidence.content_blobs(id),
    raw_response_object_key text,
    status text NOT NULL,
    tokens_in integer NOT NULL DEFAULT 0,
    tokens_out integer NOT NULL DEFAULT 0,
    cost_microunits bigint NOT NULL DEFAULT 0,
    started_at timestamptz NOT NULL,
    finished_at timestamptz,
    job_id uuid,
    trace_id uuid,
    error jsonb,
    UNIQUE (document_version_id, extractor_name, extractor_version, input_hash),
    CHECK (tokens_in >= 0 AND tokens_out >= 0 AND cost_microunits >= 0),
    CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE research.fact_dimension_sets (
    comparability_hash char(64) PRIMARY KEY,
    schema_version text NOT NULL,
    product_spec_id uuid REFERENCES core.product_specs(id),
    geography_scheme text,
    geography_code text,
    market_basis text,
    contract_basis text,
    tax_basis text,
    freight_basis text,
    incoterm text,
    currency_code char(3),
    frequency text,
    price_component text,
    statistical_scope text,
    canonical_payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (comparability_hash ~ '^[0-9a-f]{64}$'),
    CHECK ((geography_scheme IS NULL) = (geography_code IS NULL)),
    CHECK (market_basis IS NULL OR market_basis IN ('spot', 'contract', 'list', 'auction', 'index', 'assessment')),
    CHECK (tax_basis IS NULL OR tax_basis IN ('included', 'excluded', 'not_applicable', 'unknown')),
    CHECK (freight_basis IS NULL OR freight_basis IN ('included', 'excluded', 'ex_works', 'delivered', 'unknown')),
    CHECK (frequency IS NULL OR frequency IN ('instant', 'daily', 'weekly', 'monthly', 'quarterly', 'annual')),
    CHECK (price_component IS NULL OR price_component IN ('low', 'high', 'mid', 'average', 'settlement', 'close'))
);

CREATE TABLE research.fact_assertions (
    id uuid PRIMARY KEY,
    subject_entity_id uuid REFERENCES core.entities(id),
    subject_industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    predicate_code text NOT NULL,
    comparability_hash char(64) NOT NULL REFERENCES research.fact_dimension_sets(comparability_hash),
    dimensions_complete boolean NOT NULL,
    valid_time_kind text NOT NULL,
    value_kind text NOT NULL,
    value_numeric numeric(40, 12),
    value_text text,
    value_boolean boolean,
    value_date date,
    value_entity_id uuid REFERENCES core.entities(id),
    value_json jsonb,
    unit_code text REFERENCES core.units(code),
    valid_from timestamptz,
    valid_to timestamptz,
    observed_at timestamptz,
    source_published_at timestamptz,
    first_known_at timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    extraction_run_id uuid NOT NULL REFERENCES evidence.extraction_runs(id),
    normalizer_name text NOT NULL,
    normalizer_version text NOT NULL,
    source_connector_id uuid NOT NULL REFERENCES evidence.source_connectors(id),
    source_cluster text,
    confidence double precision NOT NULL,
    source_quality double precision NOT NULL,
    extraction_certainty double precision NOT NULL,
    entity_match double precision NOT NULL,
    time_unit_completeness double precision NOT NULL,
    corroboration double precision NOT NULL,
    freshness double precision NOT NULL,
    conflict_penalty double precision NOT NULL DEFAULT 0,
    high_impact boolean NOT NULL DEFAULT false,
    ingest_status text NOT NULL DEFAULT 'candidate',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (valid_time_kind IN ('period', 'timeless', 'unknown')),
    CHECK (valid_time_kind <> 'period' OR valid_from IS NOT NULL OR valid_to IS NOT NULL),
    CHECK (valid_time_kind <> 'timeless' OR (valid_from IS NULL AND valid_to IS NULL)),
    CHECK (num_nonnulls(subject_entity_id, subject_industry_node_id) = 1),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (source_quality BETWEEN 0 AND 1),
    CHECK (extraction_certainty BETWEEN 0 AND 1),
    CHECK (entity_match BETWEEN 0 AND 1),
    CHECK (time_unit_completeness BETWEEN 0 AND 1),
    CHECK (corroboration BETWEEN 0 AND 1),
    CHECK (freshness BETWEEN 0 AND 1),
    CHECK (conflict_penalty BETWEEN 0 AND 1),
    CHECK (ingest_status IN ('candidate', 'quarantined')),
    CHECK (
        num_nonnulls(value_numeric, value_text, value_boolean, value_date, value_entity_id, value_json) = 1
    ),
    CHECK (
        (value_kind = 'numeric' AND value_numeric IS NOT NULL)
        OR (value_kind = 'text' AND value_text IS NOT NULL)
        OR (value_kind = 'boolean' AND value_boolean IS NOT NULL)
        OR (value_kind = 'date' AND value_date IS NOT NULL)
        OR (value_kind = 'entity' AND value_entity_id IS NOT NULL)
        OR (value_kind = 'json' AND value_json IS NOT NULL)
    )
);

CREATE TABLE research.assertion_evidence (
    assertion_id uuid NOT NULL REFERENCES research.fact_assertions(id),
    evidence_fragment_id uuid NOT NULL REFERENCES evidence.evidence_fragments(id),
    evidence_role text NOT NULL DEFAULT 'supporting',
    PRIMARY KEY (assertion_id, evidence_fragment_id)
);

CREATE TABLE research.fact_keys (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_entity_id uuid REFERENCES core.entities(id),
    subject_industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    predicate_code text NOT NULL,
    comparability_hash char(64) NOT NULL REFERENCES research.fact_dimension_sets(comparability_hash),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (
        subject_entity_id, subject_industry_node_id, predicate_code, comparability_hash
    ),
    CHECK (num_nonnulls(subject_entity_id, subject_industry_node_id) = 1)
);

CREATE TABLE research.reconciliation_evaluations (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    assertion_id uuid NOT NULL REFERENCES research.fact_assertions(id),
    decision text NOT NULL,
    score double precision NOT NULL,
    reason_codes text[] NOT NULL DEFAULT '{}',
    conflicting_assertion_ids uuid[] NOT NULL DEFAULT '{}',
    evaluator_name text NOT NULL,
    evaluator_version text NOT NULL,
    evaluated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (assertion_id, evaluator_name, evaluator_version),
    CHECK (decision IN ('accept', 'review', 'conflict', 'quarantine')),
    CHECK (score BETWEEN 0 AND 1)
);

CREATE TABLE research.conflict_cases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fact_key_id uuid NOT NULL REFERENCES research.fact_keys(id),
    valid_from timestamptz,
    valid_to timestamptz,
    status text NOT NULL DEFAULT 'open',
    severity text NOT NULL,
    opened_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz,
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (closed_at IS NULL OR closed_at >= opened_at)
);

CREATE TABLE research.conflict_members (
    conflict_case_id uuid NOT NULL REFERENCES research.conflict_cases(id),
    assertion_id uuid NOT NULL REFERENCES research.fact_assertions(id),
    PRIMARY KEY (conflict_case_id, assertion_id)
);

CREATE TABLE research.fact_resolutions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fact_key_id uuid NOT NULL REFERENCES research.fact_keys(id),
    conflict_case_id uuid REFERENCES research.conflict_cases(id),
    decision_type text NOT NULL,
    selected_assertion_ids uuid[] NOT NULL DEFAULT '{}',
    rejected_assertion_ids uuid[] NOT NULL DEFAULT '{}',
    rationale_codes text[] NOT NULL DEFAULT '{}',
    resolver_type text NOT NULL,
    resolver_id text NOT NULL,
    resolver_version text NOT NULL,
    confidence double precision NOT NULL,
    resolved_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (id, fact_key_id),
    CHECK (confidence BETWEEN 0 AND 1)
);

CREATE TABLE research.fact_resolution_assertions (
    resolution_id uuid NOT NULL REFERENCES research.fact_resolutions(id),
    assertion_id uuid NOT NULL REFERENCES research.fact_assertions(id),
    disposition text NOT NULL,
    PRIMARY KEY (resolution_id, assertion_id),
    CHECK (disposition IN ('selected', 'rejected'))
);

CREATE TABLE research.canonical_fact_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fact_key_id uuid NOT NULL REFERENCES research.fact_keys(id),
    resolution_id uuid NOT NULL,
    value_kind text NOT NULL,
    value_numeric numeric(40, 12),
    value_text text,
    value_boolean boolean,
    value_date date,
    value_entity_id uuid REFERENCES core.entities(id),
    value_json jsonb,
    unit_code text REFERENCES core.units(code),
    valid_from timestamptz,
    valid_to timestamptz,
    system_from timestamptz NOT NULL DEFAULT now(),
    system_to timestamptz,
    market_known_at timestamptz,
    confidence double precision NOT NULL,
    publication_status text NOT NULL DEFAULT 'trusted',
    FOREIGN KEY (resolution_id, fact_key_id)
        REFERENCES research.fact_resolutions(id, fact_key_id),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from),
    CHECK (system_to IS NULL OR system_to > system_from),
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (
        num_nonnulls(value_numeric, value_text, value_boolean, value_date, value_entity_id, value_json) = 1
    ),
    CHECK (
        (value_kind = 'numeric' AND value_numeric IS NOT NULL)
        OR (value_kind = 'text' AND value_text IS NOT NULL)
        OR (value_kind = 'boolean' AND value_boolean IS NOT NULL)
        OR (value_kind = 'date' AND value_date IS NOT NULL)
        OR (value_kind = 'entity' AND value_entity_id IS NOT NULL)
        OR (value_kind = 'json' AND value_json IS NOT NULL)
    )
);

CREATE INDEX documents_url_idx ON evidence.documents (canonical_url);
CREATE INDEX document_fetches_document_time_idx ON evidence.document_fetches (document_id, retrieved_at DESC);
CREATE INDEX document_fetches_connector_time_idx ON evidence.document_fetches (connector_id, retrieved_at DESC);
CREATE INDEX evidence_fragments_document_idx ON evidence.evidence_fragments (document_version_id);
CREATE INDEX extraction_runs_document_idx ON evidence.extraction_runs (document_version_id, started_at DESC);
CREATE INDEX assertions_subject_predicate_idx
    ON research.fact_assertions (subject_entity_id, predicate_code, comparability_hash, valid_from DESC);
CREATE INDEX assertions_industry_predicate_idx
    ON research.fact_assertions (subject_industry_node_id, predicate_code, comparability_hash, valid_from DESC);
CREATE INDEX assertions_ingest_idx ON research.fact_assertions (ingest_status, recorded_at DESC);
CREATE INDEX assertions_extraction_idx ON research.fact_assertions (extraction_run_id);
CREATE INDEX canonical_fact_current_idx ON research.canonical_fact_versions (fact_key_id, valid_from DESC)
    WHERE system_to IS NULL;

CREATE VIEW research.trusted_fact_current AS
SELECT version.*
FROM research.canonical_fact_versions version
WHERE version.system_to IS NULL
  AND version.publication_status = 'trusted';

CREATE VIEW research.fact_assertions_with_status AS
SELECT
    assertion.*,
    CASE
        WHEN latest.decision = 'accept' THEN 'trusted'
        WHEN latest.decision = 'quarantine' THEN 'quarantined'
        WHEN latest.decision IS NOT NULL THEN latest.decision
        ELSE assertion.ingest_status
    END AS status
FROM research.fact_assertions assertion
LEFT JOIN LATERAL (
    SELECT evaluation.decision
    FROM research.reconciliation_evaluations evaluation
    WHERE evaluation.assertion_id = assertion.id
    ORDER BY evaluation.evaluated_at DESC, evaluation.id DESC
    LIMIT 1
) latest ON true;
