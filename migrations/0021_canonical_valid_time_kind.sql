-- A canonical Fact must preserve whether its source-valid time was a period,
-- timeless, or unknown.  NULL bounds alone cannot distinguish timeless from
-- unknown and therefore are not a sufficient replay contract.

ALTER TABLE research.canonical_fact_versions
    ADD COLUMN valid_time_kind text NOT NULL DEFAULT 'unknown';

UPDATE research.canonical_fact_versions canonical
SET valid_time_kind = assertion.valid_time_kind
FROM research.fact_resolution_assertions link
JOIN research.fact_assertions assertion ON assertion.id = link.assertion_id
WHERE link.resolution_id = canonical.resolution_id
  AND link.disposition = 'selected';

ALTER TABLE research.canonical_fact_versions
    ADD CONSTRAINT canonical_fact_valid_time_kind_check CHECK (
        valid_time_kind IN ('period', 'timeless', 'unknown')
    ),
    ADD CONSTRAINT canonical_fact_period_bounds_check CHECK (
        valid_time_kind <> 'period' OR valid_from IS NOT NULL OR valid_to IS NOT NULL
    ),
    ADD CONSTRAINT canonical_fact_nonperiod_bounds_check CHECK (
        valid_time_kind = 'period' OR (valid_from IS NULL AND valid_to IS NULL)
    );

-- Replace the precision-only inheritance function with the complete temporal
-- inheritance contract.  The existing trigger from migration 0020 calls this
-- function by name, so all normal canonical inserts and carry-forward inserts
-- automatically inherit the selected assertion's semantics.
CREATE OR REPLACE FUNCTION research.inherit_canonical_fact_valid_time_precision()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    selected_kind text;
    selected_precision text;
    selected_text text;
BEGIN
    SELECT assertion.valid_time_kind,
           assertion.valid_time_precision,
           assertion.valid_time_text
      INTO selected_kind, selected_precision, selected_text
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
    RETURN NEW;
END;
$$;
