CREATE OR REPLACE FUNCTION ops.reject_mutation_of_immutable_row()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION '% is append-only; write a new version instead', TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME;
END;
$$;

CREATE TRIGGER content_blobs_immutable
    BEFORE UPDATE OR DELETE ON evidence.content_blobs
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER document_fetches_immutable
    BEFORE UPDATE OR DELETE ON evidence.document_fetches
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER document_versions_immutable
    BEFORE UPDATE OR DELETE ON evidence.document_versions
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER evidence_fragments_immutable
    BEFORE UPDATE OR DELETE ON evidence.evidence_fragments
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER artifacts_immutable
    BEFORE UPDATE OR DELETE ON evidence.artifacts
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER extraction_runs_immutable
    BEFORE UPDATE OR DELETE ON evidence.extraction_runs
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER fact_dimension_sets_immutable
    BEFORE UPDATE OR DELETE ON research.fact_dimension_sets
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER fact_assertions_immutable
    BEFORE UPDATE OR DELETE ON research.fact_assertions
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER assertion_evidence_immutable
    BEFORE UPDATE OR DELETE ON research.assertion_evidence
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER reconciliation_evaluations_immutable
    BEFORE UPDATE OR DELETE ON research.reconciliation_evaluations
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER observation_assertions_immutable
    BEFORE UPDATE OR DELETE ON research.observation_assertions
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER project_milestones_immutable
    BEFORE UPDATE OR DELETE ON research.project_milestone_assertions
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER capacity_measurements_immutable
    BEFORE UPDATE OR DELETE ON research.capacity_measurement_assertions
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER event_claims_immutable
    BEFORE UPDATE OR DELETE ON research.event_claims
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER fact_resolutions_immutable
    BEFORE UPDATE OR DELETE ON research.fact_resolutions
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER resolution_assertions_immutable
    BEFORE UPDATE OR DELETE ON research.fact_resolution_assertions
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER audit_log_immutable
    BEFORE UPDATE OR DELETE ON ops.audit_log
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

CREATE TRIGGER document_processing_completions_immutable
    BEFORE UPDATE OR DELETE ON ops.document_processing_completions
    FOR EACH ROW EXECUTE FUNCTION ops.reject_mutation_of_immutable_row();

ALTER TABLE core.entity_names
    ADD CONSTRAINT entity_names_source_assertion_fk
    FOREIGN KEY (source_assertion_id) REFERENCES research.fact_assertions(id);

ALTER TABLE core.entity_identifiers
    ADD CONSTRAINT entity_identifiers_source_assertion_fk
    FOREIGN KEY (source_assertion_id) REFERENCES research.fact_assertions(id);

ALTER TABLE core.unit_conversion_versions
    ADD CONSTRAINT unit_conversions_source_assertion_fk
    FOREIGN KEY (source_assertion_id) REFERENCES research.fact_assertions(id);

ALTER TABLE core.entity_relation_versions
    ADD CONSTRAINT entity_relations_resolution_fk
    FOREIGN KEY (resolution_id) REFERENCES research.fact_resolutions(id);

ALTER TABLE core.industry_entity_memberships
    ADD CONSTRAINT industry_memberships_resolution_fk
    FOREIGN KEY (resolution_id) REFERENCES research.fact_resolutions(id);

ALTER TABLE research.canonical_fact_versions
    ADD CONSTRAINT canonical_fact_no_overlapping_bitemporal_versions
    EXCLUDE USING gist (
        fact_key_id WITH =,
        tstzrange(valid_from, valid_to, '[)') WITH &&,
        tstzrange(system_from, system_to, '[)') WITH &&
    ) WHERE (publication_status = 'trusted');

ALTER TABLE research.industry_relation_versions
    ADD CONSTRAINT industry_relation_no_overlapping_bitemporal_versions
    EXCLUDE USING gist (
        relation_id WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&,
        tstzrange(system_from, system_to, '[)') WITH &&
    );

ALTER TABLE core.entity_relation_versions
    ADD CONSTRAINT entity_relations_no_overlapping_bitemporal_versions
    EXCLUDE USING gist (
        from_entity_id WITH =,
        to_entity_id WITH =,
        relation_type WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&,
        tstzrange(system_from, system_to, '[)') WITH &&
    );

ALTER TABLE core.industry_entity_memberships
    ADD CONSTRAINT industry_memberships_no_overlapping_bitemporal_versions
    EXCLUDE USING gist (
        industry_node_id WITH =,
        entity_id WITH =,
        role WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&,
        tstzrange(system_from, system_to, '[)') WITH &&
    );

ALTER TABLE research.series_equivalence_versions
    ADD CONSTRAINT series_equivalence_no_overlapping_bitemporal_versions
    EXCLUDE USING gist (
        from_series_id WITH =,
        to_series_id WITH =,
        equivalence_type WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&,
        tstzrange(system_from, system_to, '[)') WITH &&
    );

ALTER TABLE research.project_status_versions
    ADD CONSTRAINT project_status_no_overlapping_bitemporal_versions
    EXCLUDE USING gist (
        project_id WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&,
        tstzrange(system_from, system_to, '[)') WITH &&
    );

ALTER TABLE research.capacity_ramp_assumption_versions
    ADD CONSTRAINT capacity_ramp_no_overlapping_system_versions
    EXCLUDE USING gist (
        project_id WITH =,
        scenario_code WITH =,
        month_offset WITH =,
        tstzrange(system_from, system_to, '[)') WITH &&
    );

ALTER TABLE research.company_exposure_versions
    ADD CONSTRAINT company_exposure_no_overlapping_bitemporal_versions
    EXCLUDE USING gist (
        issuer_entity_id WITH =,
        industry_node_id WITH =,
        exposure_type WITH =,
        daterange(valid_from, valid_to, '[)') WITH &&,
        tstzrange(system_from, system_to, '[)') WITH &&
    );

ALTER TABLE research.observation_versions
    ADD CONSTRAINT observation_no_overlapping_system_versions
    EXCLUDE USING gist (
        series_id WITH =,
        daterange(period_start, coalesce(period_end, period_start + 1), '[)') WITH =,
        vintage_at WITH =,
        tstzrange(system_from, system_to, '[)') WITH &&
    );

ALTER TABLE research.event_impact_versions
    ADD CONSTRAINT event_entity_impact_no_overlapping_bitemporal_versions
    EXCLUDE USING gist (
        event_id WITH =,
        target_entity_id WITH =,
        direction WITH =,
        tstzrange(valid_from, valid_to, '[)') WITH &&,
        tstzrange(system_from, system_to, '[)') WITH &&
    ) WHERE (target_entity_id IS NOT NULL);

ALTER TABLE research.event_impact_versions
    ADD CONSTRAINT event_industry_impact_no_overlapping_bitemporal_versions
    EXCLUDE USING gist (
        event_id WITH =,
        target_industry_node_id WITH =,
        direction WITH =,
        tstzrange(valid_from, valid_to, '[)') WITH &&,
        tstzrange(system_from, system_to, '[)') WITH &&
    ) WHERE (target_industry_node_id IS NOT NULL);

ALTER TABLE ops.collection_policies
    ADD CONSTRAINT collection_policies_cadence_check
    CHECK (cadence IN ('daily', 'every_three_days', 'weekly', 'source_native', 'event_driven'));

ALTER TABLE ops.pipeline_checkpoints
    ADD CONSTRAINT pipeline_checkpoints_stage_check
    CHECK (stage IN ('discover', 'fetch', 'archive', 'parse', 'extract', 'normalize', 'validate', 'reconcile', 'publish', 'derive'));

ALTER TABLE ops.job_attempts
    ADD CONSTRAINT job_attempts_status_check
    CHECK (status IN ('running', 'succeeded', 'retry', 'dead', 'cancelled'));

CREATE UNIQUE INDEX event_impacts_one_current_key_idx
    ON research.event_impact_versions (
        event_id, target_entity_id, target_industry_node_id, direction, valid_from
    ) NULLS NOT DISTINCT
    WHERE system_to IS NULL;

CREATE INDEX fact_assertions_entity_compare_gist
    ON research.fact_assertions USING gist (
        subject_entity_id,
        predicate_code,
        comparability_hash,
        tstzrange(valid_from, valid_to, '[)')
    )
    WHERE subject_entity_id IS NOT NULL AND valid_time_kind = 'period';

CREATE INDEX fact_assertions_industry_compare_gist
    ON research.fact_assertions USING gist (
        subject_industry_node_id,
        predicate_code,
        comparability_hash,
        tstzrange(valid_from, valid_to, '[)')
    )
    WHERE subject_industry_node_id IS NOT NULL AND valid_time_kind = 'period';

CREATE INDEX fact_assertions_recorded_brin ON research.fact_assertions USING brin (recorded_at);
CREATE INDEX document_fetches_retrieved_brin ON evidence.document_fetches USING brin (retrieved_at);
CREATE INDEX extraction_runs_started_brin ON evidence.extraction_runs USING brin (started_at);
CREATE INDEX job_attempts_started_brin ON ops.job_attempts USING brin (started_at);
CREATE INDEX audit_log_occurred_brin ON ops.audit_log USING brin (occurred_at);
CREATE INDEX cycle_snapshots_generated_brin ON research.cycle_snapshots USING brin (generated_at);
