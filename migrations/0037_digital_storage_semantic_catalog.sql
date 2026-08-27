-- Extend the bounded EB repair into one durable digital-information quantity catalog.
-- Canonical symbols are case-sensitive: GB != Gb, KiB != Kib. Exact aliases below
-- carry common bit spellings; ambiguous casing is intentionally not guessed.

ALTER TABLE core.unit_conversion_versions
    ADD CONSTRAINT unit_conversion_multiplier_nonzero
    CHECK (multiplier <> 0);

ALTER TABLE core.unit_conversion_versions
    ADD CONSTRAINT unit_conversion_no_overlapping_valid_versions
    EXCLUDE USING gist (
        from_unit WITH =,
        to_unit WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&
    );

CREATE TABLE core.unit_alias_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias text NOT NULL,
    unit_code text NOT NULL REFERENCES core.units(code),
    match_mode text NOT NULL,
    alias_kind text NOT NULL DEFAULT 'name',
    valid_from date,
    valid_to date,
    source_assertion_id uuid REFERENCES research.fact_assertions(id),
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (alias, match_mode, valid_from),
    CHECK (alias = btrim(alias) AND alias <> ''),
    CHECK (match_mode IN ('exact', 'casefold')),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to > valid_from)
);

ALTER TABLE core.unit_alias_versions
    ADD CONSTRAINT unit_alias_exact_no_overlapping_valid_versions
    EXCLUDE USING gist (
        alias WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&
    ) WHERE (match_mode = 'exact');

ALTER TABLE core.unit_alias_versions
    ADD CONSTRAINT unit_alias_casefold_no_overlapping_valid_versions
    EXCLUDE USING gist (
        lower(alias) WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&
    ) WHERE (match_mode = 'casefold');

CREATE INDEX unit_alias_versions_unit_idx
    ON core.unit_alias_versions (unit_code, valid_from);

-- Keep all convertible bit/byte quantities in one dimension. Performance rates such
-- as MB/s and IOPS are deliberately different dimensions and are not seeded here.
INSERT INTO core.units (code, dimension, display_name, decimal_scale, attributes)
VALUES
    ('bit',  'digital_storage', 'bit',       6, '{"quantity_kind":"information","prefix_system":"base","canonical_base":false,"symbol_case_sensitive":true,"standard_family":"SI_IEC"}'::jsonb),
    ('B',    'digital_storage', 'byte',      6, '{"quantity_kind":"information","prefix_system":"base","canonical_base":true,"symbol_case_sensitive":true,"standard_family":"SI_IEC"}'::jsonb),
    ('kbit', 'digital_storage', 'kilobit',   6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":3,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('Mbit', 'digital_storage', 'megabit',   6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":6,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('Gbit', 'digital_storage', 'gigabit',   6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":9,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('Tbit', 'digital_storage', 'terabit',   6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":12,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('Pbit', 'digital_storage', 'petabit',   6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":15,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('Ebit', 'digital_storage', 'exabit',    6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":18,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('Zbit', 'digital_storage', 'zettabit',  6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":21,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('Ybit', 'digital_storage', 'yottabit',  6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":24,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('kB',   'digital_storage', 'kilobyte',  6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":3,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('MB',   'digital_storage', 'megabyte',  6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":6,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('GB',   'digital_storage', 'gigabyte',  6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":9,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('TB',   'digital_storage', 'terabyte',  6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":12,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('PB',   'digital_storage', 'petabyte',  6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":15,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('EB',   'digital_storage', 'exabyte',   6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":18,"symbol_case_sensitive":true,"standard_family":"SI","conversion_status":"declared_via_sparse_graph"}'::jsonb),
    ('ZB',   'digital_storage', 'zettabyte', 6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":21,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('YB',   'digital_storage', 'yottabyte', 6, '{"quantity_kind":"information","prefix_system":"si_decimal","prefix_exponent":24,"symbol_case_sensitive":true,"standard_family":"SI"}'::jsonb),
    ('Kibit','digital_storage', 'kibibit',    6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":10,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('Mibit','digital_storage', 'mebibit',    6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":20,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('Gibit','digital_storage', 'gibibit',    6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":30,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('Tibit','digital_storage', 'tebibit',    6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":40,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('Pibit','digital_storage', 'pebibit',    6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":50,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('Eibit','digital_storage', 'exbibit',    6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":60,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('Zibit','digital_storage', 'zebibit',    6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":70,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('Yibit','digital_storage', 'yobibit',    6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":80,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('KiB',  'digital_storage', 'kibibyte',   6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":10,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('MiB',  'digital_storage', 'mebibyte',   6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":20,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('GiB',  'digital_storage', 'gibibyte',   6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":30,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('TiB',  'digital_storage', 'tebibyte',   6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":40,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('PiB',  'digital_storage', 'pebibyte',   6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":50,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('EiB',  'digital_storage', 'exbibyte',   6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":60,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('ZiB',  'digital_storage', 'zebibyte',   6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":70,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb),
    ('YiB',  'digital_storage', 'yobibyte',   6, '{"quantity_kind":"information","prefix_system":"iec_binary","prefix_exponent":80,"symbol_case_sensitive":true,"standard_family":"IEC"}'::jsonb)
ON CONFLICT (code) DO UPDATE
SET attributes = core.units.attributes || EXCLUDED.attributes
WHERE core.units.dimension = EXCLUDED.dimension
  AND core.units.display_name = EXCLUDED.display_name;

DO $$
DECLARE
    incompatible text[];
BEGIN
    WITH expected(code, display_name) AS (
        VALUES
            ('bit','bit'),('B','byte'),('kbit','kilobit'),('Mbit','megabit'),
            ('Gbit','gigabit'),('Tbit','terabit'),('Pbit','petabit'),('Ebit','exabit'),
            ('Zbit','zettabit'),('Ybit','yottabit'),('kB','kilobyte'),('MB','megabyte'),
            ('GB','gigabyte'),('TB','terabyte'),('PB','petabyte'),('EB','exabyte'),
            ('ZB','zettabyte'),('YB','yottabyte'),('Kibit','kibibit'),('Mibit','mebibit'),
            ('Gibit','gibibit'),('Tibit','tebibit'),('Pibit','pebibit'),('Eibit','exbibit'),
            ('Zibit','zebibit'),('Yibit','yobibit'),('KiB','kibibyte'),('MiB','mebibyte'),
            ('GiB','gibibyte'),('TiB','tebibyte'),('PiB','pebibyte'),('EiB','exbibyte'),
            ('ZiB','zebibyte'),('YiB','yobibyte')
    )
    SELECT array_agg(expected.code ORDER BY expected.code)
      INTO incompatible
      FROM expected
      LEFT JOIN core.units u ON u.code = expected.code
     WHERE u.code IS NULL
        OR u.dimension <> 'digital_storage'
        OR u.display_name <> expected.display_name;

    IF incompatible IS NOT NULL THEN
        RAISE EXCEPTION 'digital storage unit catalog missing or incompatible: %', incompatible;
    END IF;
END $$;

-- Persist only adjacent authoritative edges. Runtime closure derives reverse and
-- transitive conversions, so adding a new prefix is O(1) catalog work.
INSERT INTO core.unit_conversion_versions (from_unit, to_unit, multiplier, additive_offset)
VALUES
    ('bit','B',0.125,0),
    ('kbit','bit',1000,0),('Mbit','kbit',1000,0),('Gbit','Mbit',1000,0),('Tbit','Gbit',1000,0),
    ('Pbit','Tbit',1000,0),('Ebit','Pbit',1000,0),('Zbit','Ebit',1000,0),('Ybit','Zbit',1000,0),
    ('kB','B',1000,0),('MB','kB',1000,0),('GB','MB',1000,0),('TB','GB',1000,0),
    ('PB','TB',1000,0),('EB','PB',1000,0),('ZB','EB',1000,0),('YB','ZB',1000,0),
    ('Kibit','bit',1024,0),('Mibit','Kibit',1024,0),('Gibit','Mibit',1024,0),('Tibit','Gibit',1024,0),
    ('Pibit','Tibit',1024,0),('Eibit','Pibit',1024,0),('Zibit','Eibit',1024,0),('Yibit','Zibit',1024,0),
    ('KiB','B',1024,0),('MiB','KiB',1024,0),('GiB','MiB',1024,0),('TiB','GiB',1024,0),
    ('PiB','TiB',1024,0),('EiB','PiB',1024,0),('ZiB','EiB',1024,0),('YiB','ZiB',1024,0)
ON CONFLICT DO NOTHING;

DO $$
DECLARE
    bad_count integer;
BEGIN
    WITH expected(from_unit, to_unit, multiplier) AS (
        VALUES
            ('bit','B',0.125::numeric),
            ('kbit','bit',1000::numeric),('Mbit','kbit',1000::numeric),('Gbit','Mbit',1000::numeric),('Tbit','Gbit',1000::numeric),
            ('Pbit','Tbit',1000::numeric),('Ebit','Pbit',1000::numeric),('Zbit','Ebit',1000::numeric),('Ybit','Zbit',1000::numeric),
            ('kB','B',1000::numeric),('MB','kB',1000::numeric),('GB','MB',1000::numeric),('TB','GB',1000::numeric),
            ('PB','TB',1000::numeric),('EB','PB',1000::numeric),('ZB','EB',1000::numeric),('YB','ZB',1000::numeric),
            ('Kibit','bit',1024::numeric),('Mibit','Kibit',1024::numeric),('Gibit','Mibit',1024::numeric),('Tibit','Gibit',1024::numeric),
            ('Pibit','Tibit',1024::numeric),('Eibit','Pibit',1024::numeric),('Zibit','Eibit',1024::numeric),('Yibit','Zibit',1024::numeric),
            ('KiB','B',1024::numeric),('MiB','KiB',1024::numeric),('GiB','MiB',1024::numeric),('TiB','GiB',1024::numeric),
            ('PiB','TiB',1024::numeric),('EiB','PiB',1024::numeric),('ZiB','EiB',1024::numeric),('YiB','ZiB',1024::numeric)
    )
    SELECT count(*)
      INTO bad_count
      FROM expected e
      LEFT JOIN core.unit_conversion_versions c
        ON c.from_unit = e.from_unit
       AND c.to_unit = e.to_unit
       AND c.valid_from IS NULL
       AND c.valid_to IS NULL
     WHERE c.id IS NULL
        OR c.multiplier <> e.multiplier
        OR c.additive_offset <> 0;

    IF bad_count <> 0 THEN
        RAISE EXCEPTION 'digital storage conversion graph has % incompatible authoritative edges', bad_count;
    END IF;
END $$;

-- Exact symbolic aliases protect byte/bit case semantics. In particular, canonical
-- GB is a gigabyte while exact Gb/gb aliases are gigabits. No KB alias is admitted.
INSERT INTO core.unit_alias_versions (alias, unit_code, match_mode, alias_kind, attributes)
VALUES
    ('b','bit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('kb','kbit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Mb','Mbit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Gb','Gbit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Tb','Tbit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Pb','Pbit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Eb','Ebit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Zb','Zbit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Yb','Ybit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Kib','Kibit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Mib','Mibit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Gib','Gibit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Tib','Tibit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Pib','Pibit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Eib','Eibit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Zib','Zibit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb),
    ('Yib','Yibit','exact','industry_symbol','{"ambiguity_policy":"case_sensitive"}'::jsonb)
ON CONFLICT DO NOTHING;

-- Full unit names are unambiguous and may be case-folded. Singular and plural are
-- generated from the canonical display name so the alias vocabulary stays aligned
-- with the unit registry rather than being maintained as a second hand-written list.
INSERT INTO core.unit_alias_versions (alias, unit_code, match_mode, alias_kind, attributes)
SELECT display_name, code, 'casefold', 'standard_name', '{"generated_from":"core.units.display_name"}'::jsonb
  FROM core.units
 WHERE dimension = 'digital_storage'
ON CONFLICT DO NOTHING;

INSERT INTO core.unit_alias_versions (alias, unit_code, match_mode, alias_kind, attributes)
SELECT display_name || 's', code, 'casefold', 'standard_name_plural', '{"generated_from":"core.units.display_name"}'::jsonb
  FROM core.units
 WHERE dimension = 'digital_storage'
ON CONFLICT DO NOTHING;
