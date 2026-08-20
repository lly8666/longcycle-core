ALTER TABLE core.predicate_definitions
    ADD COLUMN unit_dimension_name text;

ALTER TABLE core.predicate_definitions
    ADD CONSTRAINT predicate_unit_binding_check
    CHECK (
        (canonical_unit_code IS NULL OR unit_dimension_name IS NULL)
        AND (
            unit_dimension_name IS NULL
            OR unit_dimension_name = ANY(allowed_dimensions)
        )
    );
