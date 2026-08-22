-- Preserve a source-supported observation/as-of axis separately from valid time.
-- This lets canonical Reality express "state is true as of T; onset unknown"
-- without fabricating valid_from=T. Observation precision remains explicit so a
-- day-level source is not silently reinterpreted as an exact instant.

ALTER TABLE research.canonical_fact_versions
    ADD COLUMN observed_at timestamptz,
    ADD COLUMN observed_at_precision text NOT NULL DEFAULT 'unknown',
    ADD COLUMN observed_at_text text;

ALTER TABLE research.canonical_fact_versions
    ADD CONSTRAINT canonical_fact_observed_at_precision_check CHECK (
        observed_at_precision IN (
            'instant', 'second', 'minute', 'hour', 'day', 'week', 'month',
            'quarter', 'half_year', 'year', 'range', 'approximate', 'unknown'
        )
    ),
    ADD CONSTRAINT canonical_fact_observed_at_shape_check CHECK (
        observed_at IS NOT NULL
        OR (observed_at_precision = 'unknown' AND observed_at_text IS NULL)
    ),
    ADD CONSTRAINT canonical_fact_observed_at_approximate_text_check CHECK (
        observed_at_precision <> 'approximate' OR observed_at_text IS NOT NULL
    );

UPDATE research.canonical_fact_versions canonical
SET observed_at = assertion.observed_at,
    observed_at_precision = COALESCE(
        assertion.metadata ->> '_longcycle_observed_at_precision',
        'unknown'
    ),
    observed_at_text = assertion.metadata ->> '_longcycle_observed_at_text'
FROM research.fact_resolution_assertions link
JOIN research.fact_assertions assertion ON assertion.id = link.assertion_id
WHERE link.resolution_id = canonical.resolution_id
  AND link.disposition = 'selected';

CREATE OR REPLACE FUNCTION research.inherit_canonical_fact_valid_time_precision()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    selected_kind text;
    selected_precision text;
    selected_text text;
    selected_observed_at timestamptz;
    selected_observed_precision text;
    selected_observed_text text;
BEGIN
    SELECT assertion.valid_time_kind,
           assertion.valid_time_precision,
           assertion.valid_time_text,
           assertion.observed_at,
           COALESCE(
               assertion.metadata ->> '_longcycle_observed_at_precision',
               'unknown'
           ),
           assertion.metadata ->> '_longcycle_observed_at_text'
      INTO selected_kind,
           selected_precision,
           selected_text,
           selected_observed_at,
           selected_observed_precision,
           selected_observed_text
      FROM research.fact_resolution_assertions link
      JOIN research.fact_assertions assertion ON assertion.id = link.assertion_id
     WHERE link.resolution_id = NEW.resolution_id
       AND link.disposition = 'selected'
     ORDER BY assertion.recorded_at DESC, assertion.id DESC
     LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'canonical fact resolution % has no selected assertion', NEW.resolution_id;
    END IF;

    NEW.valid_time_kind := selected_kind;
    NEW.valid_time_precision := selected_precision;
    NEW.valid_time_text := selected_text;
    NEW.observed_at := selected_observed_at;
    NEW.observed_at_precision := selected_observed_precision;
    NEW.observed_at_text := selected_observed_text;
    RETURN NEW;
END;
$$;
