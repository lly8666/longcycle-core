CREATE TABLE ops.collection_policies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    industry_node_id uuid NOT NULL REFERENCES core.taxonomy_nodes(id),
    connector_id uuid NOT NULL REFERENCES evidence.source_connectors(id),
    target_code text NOT NULL,
    cadence text NOT NULL,
    heat_score double precision NOT NULL DEFAULT 0,
    data_risk_score double precision NOT NULL DEFAULT 0,
    consecutive_low_days integer NOT NULL DEFAULT 0,
    event_override_until timestamptz,
    timezone text NOT NULL DEFAULT 'Asia/Shanghai',
    policy_version text NOT NULL,
    enabled boolean NOT NULL DEFAULT true,
    next_run_at timestamptz,
    last_run_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (industry_node_id, connector_id, target_code),
    CHECK (heat_score BETWEEN 0 AND 100),
    CHECK (data_risk_score BETWEEN 0 AND 100),
    CHECK (consecutive_low_days >= 0)
);

CREATE TABLE ops.discovery_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id uuid NOT NULL REFERENCES evidence.source_subscriptions(id),
    cursor_before jsonb,
    cursor_after jsonb,
    status text NOT NULL,
    items_found integer NOT NULL DEFAULT 0,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    trace_id uuid NOT NULL,
    CHECK (items_found >= 0),
    CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE ops.discovered_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    discovery_run_id uuid NOT NULL REFERENCES ops.discovery_runs(id),
    connector_id uuid NOT NULL REFERENCES evidence.source_connectors(id),
    external_id text,
    canonical_url text NOT NULL,
    title_hint text,
    published_at_hint timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    idempotency_key char(64) NOT NULL UNIQUE,
    discovered_at timestamptz NOT NULL DEFAULT now(),
    fetch_job_id uuid,
    CHECK (idempotency_key ~ '^[0-9a-f]{64}$')
);

CREATE TABLE ops.collection_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    pool text NOT NULL,
    stage text NOT NULL,
    source_connector_id uuid REFERENCES evidence.source_connectors(id),
    industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'queued',
    priority double precision NOT NULL DEFAULT 0,
    available_at timestamptz NOT NULL DEFAULT now(),
    lease_owner text,
    lease_token uuid,
    lease_expires_at timestamptz,
    attempt_count integer NOT NULL DEFAULT 0,
    max_attempts integer NOT NULL DEFAULT 5,
    idempotency_key char(64) NOT NULL UNIQUE,
    parent_job_id uuid REFERENCES ops.collection_jobs(id),
    trace_id uuid NOT NULL DEFAULT gen_random_uuid(),
    correlation_id uuid,
    causation_id uuid,
    last_error_code text,
    last_error_message text,
    created_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    finished_at timestamptz,
    CHECK (stage IN ('discover', 'fetch', 'archive', 'parse', 'extract', 'normalize', 'validate', 'reconcile', 'publish', 'derive')),
    CHECK (status IN ('queued', 'leased', 'succeeded', 'retry', 'dead', 'cancelled')),
    CHECK (priority BETWEEN 0 AND 100),
    CHECK (attempt_count >= 0),
    CHECK (max_attempts > 0),
    CHECK (idempotency_key ~ '^[0-9a-f]{64}$'),
    CHECK (finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at),
    CHECK (
        (status = 'leased' AND lease_owner IS NOT NULL AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL)
        OR status <> 'leased'
    )
);

ALTER TABLE ops.discovered_items
    ADD CONSTRAINT discovered_items_fetch_job_fk FOREIGN KEY (fetch_job_id) REFERENCES ops.collection_jobs(id);

CREATE TABLE ops.job_attempts (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES ops.collection_jobs(id),
    attempt_number integer NOT NULL,
    worker_id text NOT NULL,
    lease_token uuid NOT NULL,
    status text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    error_code text,
    error_message text,
    error_details jsonb,
    metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (job_id, attempt_number),
    CHECK (attempt_number > 0),
    CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE ops.dead_letters (
    job_id uuid PRIMARY KEY REFERENCES ops.collection_jobs(id),
    dead_at timestamptz NOT NULL DEFAULT now(),
    final_error_code text,
    final_error_message text,
    replay_count integer NOT NULL DEFAULT 0,
    last_replayed_at timestamptz,
    CHECK (replay_count >= 0)
);

CREATE TABLE ops.pipeline_checkpoints (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id uuid NOT NULL REFERENCES ops.collection_jobs(id),
    stage text NOT NULL,
    input_hash char(64) NOT NULL,
    output_reference jsonb NOT NULL,
    producer_version text NOT NULL,
    completed_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (job_id, stage, input_hash, producer_version),
    CHECK (input_hash ~ '^[0-9a-f]{64}$')
);

CREATE TABLE ops.document_processing_completions (
    extraction_run_id uuid PRIMARY KEY REFERENCES evidence.extraction_runs(id),
    completed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ops.review_cases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_type text NOT NULL,
    subject_id uuid NOT NULL,
    status text NOT NULL DEFAULT 'open',
    severity text NOT NULL,
    reason_codes text[] NOT NULL,
    assigned_to text,
    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz,
    resolution_note text,
    CHECK (status IN ('open', 'in_review', 'approved', 'rejected', 'resolved')), 
    CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CHECK (resolved_at IS NULL OR resolved_at >= created_at)
);

CREATE TABLE ops.review_actions (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_case_id uuid NOT NULL REFERENCES ops.review_cases(id),
    action text NOT NULL,
    actor_type text NOT NULL,
    actor_id text NOT NULL,
    note text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ops.trigger_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type text NOT NULL,
    deduplication_key char(64) NOT NULL UNIQUE,
    correlation_id uuid NOT NULL,
    causation_id uuid,
    source_job_id uuid REFERENCES ops.collection_jobs(id),
    industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    impact_level text NOT NULL,
    payload jsonb NOT NULL,
    fanout_depth integer NOT NULL DEFAULT 0,
    emitted_at timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz,
    CHECK (deduplication_key ~ '^[0-9a-f]{64}$'),
    CHECK (fanout_depth BETWEEN 0 AND 8)
);

CREATE TABLE ops.outbox_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    idempotency_key char(64) NOT NULL UNIQUE,
    aggregate_type text NOT NULL,
    aggregate_id uuid NOT NULL,
    event_type text NOT NULL,
    payload jsonb NOT NULL,
    correlation_id uuid,
    causation_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,
    publish_attempts integer NOT NULL DEFAULT 0,
    last_error text,
    CHECK (idempotency_key ~ '^[0-9a-f]{64}$'),
    CHECK (publish_attempts >= 0)
);

CREATE TABLE ops.cost_ledger (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    incurred_at timestamptz NOT NULL DEFAULT now(),
    job_id uuid REFERENCES ops.collection_jobs(id),
    extraction_run_id uuid REFERENCES evidence.extraction_runs(id),
    industry_node_id uuid REFERENCES core.taxonomy_nodes(id),
    source_connector_id uuid REFERENCES evidence.source_connectors(id),
    provider text NOT NULL,
    model_name text,
    cost_type text NOT NULL,
    quantity numeric(30, 6) NOT NULL,
    unit text NOT NULL,
    cost_microunits bigint NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    CHECK (quantity >= 0),
    CHECK (cost_microunits >= 0)
);

CREATE TABLE ops.budget_policies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_type text NOT NULL,
    scope_id text NOT NULL,
    period text NOT NULL,
    limit_microunits bigint NOT NULL,
    soft_limit_ratio double precision NOT NULL DEFAULT 0.8,
    hard_stop boolean NOT NULL DEFAULT true,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (scope_type, scope_id, period),
    CHECK (limit_microunits >= 0),
    CHECK (soft_limit_ratio BETWEEN 0 AND 1)
);

CREATE TABLE ops.industry_heat_snapshots (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    industry_node_id uuid NOT NULL REFERENCES core.taxonomy_nodes(id),
    snapshot_date date NOT NULL,
    user_attention double precision NOT NULL DEFAULT 0,
    market_anomaly double precision NOT NULL DEFAULT 0,
    event_density double precision NOT NULL DEFAULT 0,
    player_change double precision NOT NULL DEFAULT 0,
    related_industry_signal double precision NOT NULL DEFAULT 0,
    heat_score double precision NOT NULL,
    data_risk_score double precision NOT NULL,
    calculation_version text NOT NULL,
    components jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (industry_node_id, snapshot_date, calculation_version),
    CHECK (heat_score BETWEEN 0 AND 100),
    CHECK (data_risk_score BETWEEN 0 AND 100)
);

CREATE TABLE ops.source_health_daily (
    connector_id uuid NOT NULL REFERENCES evidence.source_connectors(id),
    health_date date NOT NULL,
    requests integer NOT NULL DEFAULT 0,
    successes integer NOT NULL DEFAULT 0,
    not_modified integer NOT NULL DEFAULT 0,
    failures integer NOT NULL DEFAULT 0,
    rate_limited integer NOT NULL DEFAULT 0,
    changed_documents integer NOT NULL DEFAULT 0,
    duplicate_documents integer NOT NULL DEFAULT 0,
    p95_latency_ms integer,
    circuit_state text NOT NULL DEFAULT 'closed',
    PRIMARY KEY (connector_id, health_date),
    CHECK (requests >= 0 AND successes >= 0 AND not_modified >= 0 AND failures >= 0),
    CHECK (rate_limited >= 0 AND changed_documents >= 0 AND duplicate_documents >= 0),
    CHECK (p95_latency_ms IS NULL OR p95_latency_ms >= 0)
);

CREATE TABLE ops.audit_log (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    actor_type text NOT NULL,
    actor_id text NOT NULL,
    action text NOT NULL,
    object_type text NOT NULL,
    object_id text NOT NULL,
    before_hash text,
    after_hash text,
    trace_id uuid,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE evidence.document_fetches
    ADD CONSTRAINT document_fetches_job_fk FOREIGN KEY (job_id) REFERENCES ops.collection_jobs(id);
ALTER TABLE evidence.extraction_runs
    ADD CONSTRAINT extraction_runs_job_fk FOREIGN KEY (job_id) REFERENCES ops.collection_jobs(id);

CREATE INDEX collection_policies_due_idx ON ops.collection_policies (next_run_at, enabled) WHERE enabled;
CREATE INDEX collection_jobs_claim_idx ON ops.collection_jobs (pool, status, available_at, priority DESC)
    WHERE status IN ('queued', 'retry', 'leased');
CREATE INDEX collection_jobs_expired_lease_idx
    ON ops.collection_jobs (lease_expires_at, priority DESC)
    WHERE status = 'leased';
CREATE INDEX collection_jobs_trace_idx ON ops.collection_jobs (trace_id, created_at);
CREATE INDEX job_attempts_job_idx ON ops.job_attempts (job_id, attempt_number DESC);
CREATE INDEX review_cases_queue_idx ON ops.review_cases (status, severity, created_at) WHERE status IN ('open', 'in_review');
CREATE UNIQUE INDEX review_cases_one_active_subject_idx
    ON ops.review_cases (subject_type, subject_id)
    WHERE status IN ('open', 'in_review');
CREATE INDEX trigger_events_pending_idx ON ops.trigger_events (emitted_at) WHERE processed_at IS NULL;
CREATE INDEX outbox_pending_idx ON ops.outbox_events (id) WHERE published_at IS NULL;
CREATE INDEX cost_ledger_scope_idx ON ops.cost_ledger (incurred_at, industry_node_id, provider);
CREATE INDEX heat_snapshots_industry_idx ON ops.industry_heat_snapshots (industry_node_id, snapshot_date DESC);

CREATE OR REPLACE FUNCTION ops.claim_collection_jobs(
    p_worker_id text,
    p_pools text[],
    p_limit integer,
    p_lease_seconds integer
)
RETURNS SETOF ops.collection_jobs
LANGUAGE sql
AS $$
    WITH candidates AS (
        SELECT id
        FROM ops.collection_jobs
        WHERE pool = ANY (p_pools)
          AND available_at <= now()
          AND (
              status IN ('queued', 'retry')
              OR (status = 'leased' AND lease_expires_at <= now())
          )
        ORDER BY priority DESC, available_at, created_at
        FOR UPDATE SKIP LOCKED
        LIMIT greatest(p_limit, 0)
    )
    UPDATE ops.collection_jobs AS job
    SET status = 'leased',
        lease_owner = p_worker_id,
        lease_token = gen_random_uuid(),
        lease_expires_at = now() + make_interval(
            secs => greatest(p_lease_seconds, 1)
        ),
        attempt_count = job.attempt_count + 1,
        started_at = coalesce(job.started_at, now())
    FROM candidates
    WHERE job.id = candidates.id
    RETURNING job.*;
$$;
