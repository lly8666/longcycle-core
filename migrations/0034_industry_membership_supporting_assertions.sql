ALTER TABLE research.industry_membership_semantic_decisions
    ADD COLUMN supporting_assertion_ids uuid[];

-- Existing decisions only proved one representative source assertion at creation time.
-- Backfill exactly that provenance instead of guessing which other historical assertions
-- were semantically equivalent. A later projection may safely grow this set after applying
-- the deterministic membership-signature rule in CAP-0005.
UPDATE research.industry_membership_semantic_decisions
SET supporting_assertion_ids = ARRAY[selected_assertion_id]::uuid[]
WHERE supporting_assertion_ids IS NULL;

ALTER TABLE research.industry_membership_semantic_decisions
    ALTER COLUMN supporting_assertion_ids SET NOT NULL,
    ADD CHECK (cardinality(supporting_assertion_ids) > 0),
    ADD CHECK (supporting_assertion_ids <@ candidate_assertion_ids),
    ADD CHECK (selected_assertion_id = ANY(supporting_assertion_ids));

COMMENT ON COLUMN research.industry_membership_semantic_decisions.supporting_assertion_ids IS
    'CAP-0003-selected source assertions that deterministically share the chosen membership semantic signature; source corroboration provenance, not model-created truth.';
