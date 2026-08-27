-- Preserve source-supported occurrence/valid-time precision through the normal
-- FactAssertion -> reconciliation -> canonical Reality path.  Legacy rows stay
-- explicitly unknown rather than being silently assigned finer precision.

ALTER TABLE research.fact_assertions
    ADD COLUMN valid_time_precision text GENERATED ALWAYS AS (
        COALESCE(metadata ->> '_longcycle_valid_time_precision', 'unknown')
    ) STORED,
    ADD COLUMN valid_time_text text GENERATED ALWAYS AS (
        metadata ->> '_longcycle_valid_time_text'
    ) STORED;

ALTER TABLE research.fact_assertions
    ADD CONSTRAINT fact_assertions_valid_time_precision_check CHECK (
        valid_time_precision IN (
            'instant', 'second', 'minute', 'hour', 'day', 'week', 'month',
            'quarter', 'half_year', 'year', 'range', 'approximate', 'unknown'
        )
    ),
    ADD CONSTRAINT fact_assertions_approximate_time_text_check CHECK (
        valid_time_precision <> 'approximate' OR valid_time_text IS NOT NULL
    );

-- PostgreSQL expands SELECT assertion.* when a view is created, so recreate the
-- status view after adding the generated precision columns.
DROP VIEW research.fact_assertions_with_status;

CREATE VIEW research.fact_assertions_with_status AS
SELECT
    assertion.*,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM research.fact_assertions successor
            WHERE successor.supersedes_assertion_id = assertion.id
              AND (
                  SELECT evaluation.decision
                  FROM research.reconciliation_evaluations evaluation
                  WHERE evaluation.assertion_id = successor.id
                  ORDER BY evaluation.evaluated_at DESC, evaluation.id DESC
                  LIMIT 1
              ) = 'accept'
        ) THEN 'superseded'
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

ALTER TABLE research.canonical_fact_versions
    ADD COLUMN valid_time_precision text NOT NULL DEFAULT 'unknown',
    ADD COLUMN valid_time_text text;

ALTER TABLE research.canonical_fact_versions
    ADD CONSTRAINT canonical_fact_valid_time_precision_check CHECK (
        valid_time_precision IN (
            'instant', 'second', 'minute', 'hour', 'day', 'week', 'month',
            'quarter', 'half_year', 'year', 'range', 'approximate', 'unknown'
        )
    ),
    ADD CONSTRAINT canonical_fact_approximate_time_text_check CHECK (
        valid_time_precision <> 'approximate' OR valid_time_text IS NOT NULL
    );

CREATE OR REPLACE FUNCTION research.inherit_canonical_fact_valid_time_precision()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    selected_precision text;
    selected_text text;
BEGIN
    SELECT assertion.valid_time_precision, assertion.valid_time_text
      INTO selected_precision, selected_text
      FROM research.fact_resolution_assertions link
      JOIN research.fact_assertions assertion ON assertion.id = link.assertion_id
     WHERE link.resolution_id = NEW.resolution_id
       AND link.disposition = 'selected'
     ORDER BY assertion.recorded_at DESC, assertion.id DESC
     LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'canonical fact resolution % has no selected assertion', NEW.resolution_id;
    END IF;

    NEW.valid_time_precision := selected_precision;
    NEW.valid_time_text := selected_text;
    RETURN NEW;
END;
$$;

CREATE TRIGGER canonical_fact_inherit_valid_time_precision
    BEFORE INSERT ON research.canonical_fact_versions
    FOR EACH ROW EXECUTE FUNCTION research.inherit_canonical_fact_valid_time_precision();
