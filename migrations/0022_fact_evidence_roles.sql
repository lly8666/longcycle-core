-- Fact provenance is a first-class immutable relation.  One FactAssertion may cite
-- multiple fragments from its own extraction document, with explicit roles.  Cross-
-- source corroboration remains multiple assertions so source/known-time semantics do
-- not get collapsed into one claim.

ALTER TABLE research.assertion_evidence
    ADD CONSTRAINT assertion_evidence_role_check CHECK (
        evidence_role IN ('supporting', 'context', 'caveat', 'contradicting')
    );

CREATE INDEX assertion_evidence_role_idx
    ON research.assertion_evidence (assertion_id, evidence_role, evidence_fragment_id);
