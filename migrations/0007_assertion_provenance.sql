-- Preserve exact source representation and explicit correction chains.
-- Rows written before this migration receive an empty legacy raw value;
-- every post-migration insert must supply the source representation.
ALTER TABLE research.fact_assertions
    ADD COLUMN raw_value text NOT NULL DEFAULT '',
    ADD COLUMN supersedes_assertion_id uuid
        REFERENCES research.fact_assertions(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE research.fact_assertions
    ALTER COLUMN raw_value DROP DEFAULT;

CREATE INDEX fact_assertions_supersedes_idx
    ON research.fact_assertions (supersedes_assertion_id)
    WHERE supersedes_assertion_id IS NOT NULL;
