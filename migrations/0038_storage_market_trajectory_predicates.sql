-- Canonical predicate definitions needed by the TrendForce enterprise-SSD market trajectory.
-- Time/vintage belongs on Judgment/Fact rows and statistical scope belongs in FactDimensions;
-- neither quarter labels nor publisher names are encoded into predicate identity.

DO $$
DECLARE
    spec record;
BEGIN
    FOR spec IN
        SELECT * FROM (VALUES
            (
                'storage.qlc_enterprise_ssd_bit_shipments',
                'QLC enterprise SSD bit shipment volume',
                'EB',
                false
            ),
            (
                'storage.enterprise_ssd_procurement_volume_qoq_growth',
                'Enterprise SSD procurement volume quarter-over-quarter growth',
                'ratio',
                false
            ),
            (
                'storage.enterprise_ssd_revenue_qoq_growth',
                'Enterprise SSD revenue quarter-over-quarter growth',
                'ratio',
                false
            ),
            (
                'storage.enterprise_ssd_major_supplier_quarterly_revenue',
                'Enterprise SSD major-supplier quarterly revenue',
                'USD',
                false
            )
        ) AS rows(code, canonical_name, canonical_unit_code, high_impact)
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM core.units
            WHERE code = spec.canonical_unit_code
        ) THEN
            RAISE EXCEPTION 'required canonical unit % is missing', spec.canonical_unit_code;
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM core.predicate_definitions
            WHERE code = spec.code
              AND active
        ) THEN
            IF EXISTS (
                SELECT 1
                FROM core.predicate_definitions
                WHERE code = spec.code
            ) THEN
                RAISE EXCEPTION 'predicate % exists but has no active compatible definition', spec.code;
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
                spec.code,
                '1.0.0',
                spec.canonical_name,
                ARRAY['numeric']::text[],
                'period',
                'fact-dimensions/v1',
                ARRAY['statistical_scope']::text[],
                ARRAY['statistical_scope']::text[],
                spec.canonical_unit_code,
                spec.high_impact,
                '{}'::jsonb,
                true
            );
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM core.predicate_definitions
            WHERE code = spec.code
              AND active
              AND schema_version = '1.0.0'
              AND canonical_name = spec.canonical_name
              AND value_kinds = ARRAY['numeric']::text[]
              AND temporal_mode = 'period'
              AND dimension_schema_version = 'fact-dimensions/v1'
              AND required_dimensions = ARRAY['statistical_scope']::text[]
              AND allowed_dimensions = ARRAY['statistical_scope']::text[]
              AND canonical_unit_code = spec.canonical_unit_code
              AND unit_dimension_name IS NULL
        ) THEN
            RAISE EXCEPTION 'active predicate % is incompatible with storage market trajectory semantics', spec.code;
        END IF;
    END LOOP;
END $$;
