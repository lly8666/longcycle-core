-- The enterprise-SSD benchmark is the first source-grounded numeric storage-volume
-- Reality to reach canonical Fact persistence. Keep the source wording (EB/exabytes)
-- in Evidence/value_text while using one stable canonical unit code for comparison.
-- No byte-conversion chain is introduced here because the current catalog does not
-- yet own a canonical byte unit; add conversions only when a real cross-unit case
-- requires them.

INSERT INTO core.units (code, dimension, display_name, decimal_scale, attributes)
VALUES (
    'EB',
    'digital_storage',
    'exabyte',
    6,
    '{"semantic_basis":"source-reported storage volume","conversion_status":"not_declared"}'::jsonb
)
ON CONFLICT (code) DO NOTHING;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
          FROM core.units
         WHERE code = 'EB'
           AND dimension = 'digital_storage'
           AND display_name = 'exabyte'
    ) THEN
        RAISE EXCEPTION 'canonical EB unit is missing or incompatible';
    END IF;
END $$;
