ALTER TABLE evidence.evidence_fragments
    ADD CONSTRAINT evidence_fragments_material_check
    CHECK (
        (excerpt IS NOT NULL AND btrim(excerpt) <> '')
        OR (
            structured_payload IS NOT NULL
            AND jsonb_typeof(structured_payload) = 'object'
            AND structured_payload <> '{}'::jsonb
        )
    ) NOT VALID;
