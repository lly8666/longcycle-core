-- Extend the existing semantic catalog seeded by 0003_research_domains.sql.
-- Source-facing percentage aliases remain an AssertionNormalizer concern;
-- canonical persisted percentage values use the pre-existing `ratio` unit.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM core.units
         WHERE code = 'ratio'
           AND dimension = 'ratio'
    ) THEN
        RAISE EXCEPTION 'canonical ratio unit is missing or incompatible';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM core.predicate_definitions
         WHERE code = 'market.pc_shipments_yoy_growth'
           AND active
    ) THEN
        IF EXISTS (
            SELECT 1
              FROM core.predicate_definitions
             WHERE code = 'market.pc_shipments_yoy_growth'
        ) THEN
            RAISE EXCEPTION 'market.pc_shipments_yoy_growth exists but has no active compatible definition';
        END IF;

        INSERT INTO core.predicate_definitions (
            code,
            schema_version,
            canonical_name,
            value_kinds,
            temporal_mode,
            dimension_schema_version,
            required_dimensions,
            allowed_dimensions,
            canonical_unit_code,
            high_impact,
            reconciliation_policy,
            active
        ) VALUES (
            'market.pc_shipments_yoy_growth',
            '1.0.0',
            'PC shipments year-over-year growth',
            ARRAY['numeric']::text[],
            'period',
            'fact-dimensions/v1',
            ARRAY['statistical_scope']::text[],
            ARRAY['statistical_scope']::text[],
            'ratio',
            false,
            '{}'::jsonb,
            true
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM core.predicate_definitions
         WHERE code = 'market.pc_shipments_yoy_growth'
           AND active
           AND value_kinds = ARRAY['numeric']::text[]
           AND temporal_mode = 'period'
           AND dimension_schema_version = 'fact-dimensions/v1'
           AND required_dimensions = ARRAY['statistical_scope']::text[]
           AND allowed_dimensions = ARRAY['statistical_scope']::text[]
           AND canonical_unit_code = 'ratio'
    ) THEN
        RAISE EXCEPTION 'active market.pc_shipments_yoy_growth definition is incompatible with canonical ratio semantics';
    END IF;
END $$;
