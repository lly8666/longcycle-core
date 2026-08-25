-- Seed the canonical units already owned by AssertionNormalizer so a fresh
-- PostgreSQL catalog has the same stable unit vocabulary as in-memory use.
-- Source-facing aliases such as '%' and 'percent' remain parser/normalizer
-- inputs; canonical persisted percentage values use the dimensionless ratio unit.

INSERT INTO core.units (code, dimension, display_name, decimal_scale, attributes)
VALUES
    ('t', 'mass', 'tonne', 6, '{"bootstrap":"longcycle-defaults-v1"}'::jsonb),
    ('kg', 'mass', 'kilogram', 6, '{"bootstrap":"longcycle-defaults-v1"}'::jsonb),
    ('lb', 'mass', 'pound', 6, '{"bootstrap":"longcycle-defaults-v1"}'::jsonb),
    ('m3', 'volume', 'cubic metre', 6, '{"bootstrap":"longcycle-defaults-v1"}'::jsonb),
    ('unit', 'count', 'unit', 6, '{"bootstrap":"longcycle-defaults-v1"}'::jsonb),
    ('day', 'duration', 'day', 6, '{"bootstrap":"longcycle-defaults-v1"}'::jsonb),
    ('ratio', 'ratio', 'ratio', 9, '{"bootstrap":"longcycle-defaults-v1"}'::jsonb),
    ('CNY', 'currency', 'Chinese yuan', 6, '{"bootstrap":"longcycle-defaults-v1"}'::jsonb),
    ('USD', 'currency', 'US dollar', 6, '{"bootstrap":"longcycle-defaults-v1"}'::jsonb)
ON CONFLICT (code) DO NOTHING;

DO $$
DECLARE
    conflicting_code text;
BEGIN
    SELECT expected.code
      INTO conflicting_code
      FROM (VALUES
          ('t', 'mass'),
          ('kg', 'mass'),
          ('lb', 'mass'),
          ('m3', 'volume'),
          ('unit', 'count'),
          ('day', 'duration'),
          ('ratio', 'ratio'),
          ('CNY', 'currency'),
          ('USD', 'currency')
      ) AS expected(code, dimension)
      JOIN core.units actual ON actual.code = expected.code
     WHERE actual.dimension <> expected.dimension
     LIMIT 1;

    IF conflicting_code IS NOT NULL THEN
        RAISE EXCEPTION 'canonical unit % already exists with an incompatible dimension', conflicting_code;
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
