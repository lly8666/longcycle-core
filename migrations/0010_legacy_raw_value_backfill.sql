-- 0007 could only reconstruct the typed representation for rows written
-- before raw_value existed.  Backfill that representation explicitly while
-- preserving the append-only trigger for normal application traffic.
ALTER TABLE research.fact_assertions
    DISABLE TRIGGER fact_assertions_immutable;

UPDATE research.fact_assertions
SET raw_value = CASE value_kind
    WHEN 'numeric' THEN value_numeric::text
    WHEN 'text' THEN value_text
    WHEN 'boolean' THEN value_boolean::text
    WHEN 'date' THEN value_date::text
    WHEN 'entity' THEN value_entity_id::text
    WHEN 'json' THEN value_json::text
END
WHERE raw_value = '';

ALTER TABLE research.fact_assertions
    ENABLE TRIGGER fact_assertions_immutable;
