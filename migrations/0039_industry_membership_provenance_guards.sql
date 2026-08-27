-- Baseline v1 pre-freeze hardening.
--
-- CAP-0005 already treats model judgment runs as immutable execution provenance and
-- semantic decisions as stable conclusions that may only accumulate corroborating
-- support. The application store enforces that behavior, but direct SQL could still
-- rewrite or delete history. Lock the same semantics at the PostgreSQL boundary.

CREATE OR REPLACE FUNCTION research.reject_industry_membership_judgment_run_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'industry membership model judgment runs are append-only provenance; % is forbidden',
        TG_OP
        USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER industry_membership_judgment_runs_append_only
BEFORE UPDATE OR DELETE ON research.industry_membership_model_judgment_runs
FOR EACH ROW
EXECUTE FUNCTION research.reject_industry_membership_judgment_run_mutation();

CREATE OR REPLACE FUNCTION research.guard_industry_membership_semantic_decision_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION
            'industry membership semantic decisions are durable provenance; DELETE is forbidden'
            USING ERRCODE = '23514';
    END IF;

    -- The semantic identity/conclusion is immutable. Reaffirmation is represented only
    -- by additional equivalent support plus a later confirmation time.
    IF NEW.id IS DISTINCT FROM OLD.id
       OR NEW.resolution_id IS DISTINCT FROM OLD.resolution_id
       OR NEW.candidate_assertion_ids IS DISTINCT FROM OLD.candidate_assertion_ids
       OR NEW.selected_assertion_id IS DISTINCT FROM OLD.selected_assertion_id
       OR NEW.semantic_scope IS DISTINCT FROM OLD.semantic_scope
       OR NEW.decision_summary IS DISTINCT FROM OLD.decision_summary
       OR NEW.first_decided_at IS DISTINCT FROM OLD.first_decided_at
       OR NEW.evidence_fragment_ids IS DISTINCT FROM OLD.evidence_fragment_ids
       OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION
            'industry membership semantic decision identity is immutable'
            USING ERRCODE = '23514';
    END IF;

    -- Corroboration may grow but never shrink. Existing table CHECK constraints still
    -- ensure supporting assertions remain inside the selected candidate set.
    IF NOT (OLD.supporting_assertion_ids <@ NEW.supporting_assertion_ids) THEN
        RAISE EXCEPTION
            'industry membership supporting assertions may only accumulate'
            USING ERRCODE = '23514';
    END IF;

    IF NOT (OLD.supporting_judgment_run_ids <@ NEW.supporting_judgment_run_ids) THEN
        RAISE EXCEPTION
            'industry membership supporting judgment runs may only accumulate'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.last_confirmed_at < OLD.last_confirmed_at THEN
        RAISE EXCEPTION
            'industry membership last_confirmed_at may only move forward'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER industry_membership_semantic_decisions_monotonic
BEFORE UPDATE OR DELETE ON research.industry_membership_semantic_decisions
FOR EACH ROW
EXECUTE FUNCTION research.guard_industry_membership_semantic_decision_mutation();

COMMENT ON FUNCTION research.reject_industry_membership_judgment_run_mutation() IS
    'Baseline v1 guard: model judgment executions are append-only audit provenance.';

COMMENT ON FUNCTION research.guard_industry_membership_semantic_decision_mutation() IS
    'Baseline v1 guard: semantic decision identity is immutable; corroborating supports only grow and last_confirmed_at only advances.';
