-- Outcome evaluation must not manufacture day-level timing error when either the
-- original Judgment target or realized outcome is only known at month/quarter/year
-- precision. Keep legacy timing_error_days nullable, and add precision-aware fields.

ALTER TABLE research.judgment_outcome_evaluations
    ADD COLUMN outcome_evidence_fragment_id uuid REFERENCES evidence.evidence_fragments(id),
    ADD COLUMN outcome_from timestamptz,
    ADD COLUMN outcome_to timestamptz,
    ADD COLUMN outcome_precision text NOT NULL DEFAULT 'unknown',
    ADD COLUMN outcome_text text,
    ADD COLUMN outcome_first_known_at timestamptz,
    ADD COLUMN timing_relation text NOT NULL DEFAULT 'not_comparable',
    ADD COLUMN timing_delta_value numeric(40, 12),
    ADD COLUMN timing_delta_unit text;

ALTER TABLE research.judgment_outcome_evaluations
    ADD CONSTRAINT judgment_outcome_occurrence_order_check CHECK (
        outcome_to IS NULL OR outcome_from IS NULL OR outcome_to > outcome_from
    ),
    ADD CONSTRAINT judgment_outcome_precision_check CHECK (outcome_precision IN (
        'instant', 'second', 'minute', 'hour', 'day', 'week', 'month',
        'quarter', 'half_year', 'year', 'range', 'approximate', 'unknown'
    )),
    ADD CONSTRAINT judgment_outcome_approximate_text_check CHECK (
        outcome_precision <> 'approximate' OR outcome_text IS NOT NULL
    ),
    ADD CONSTRAINT judgment_outcome_timing_relation_check CHECK (timing_relation IN (
        'within_target_window', 'before_target_window', 'after_target_window',
        'overlaps_target_window', 'not_comparable'
    )),
    ADD CONSTRAINT judgment_outcome_timing_delta_pair_check CHECK (
        (timing_delta_value IS NULL) = (timing_delta_unit IS NULL)
    ),
    ADD CONSTRAINT judgment_outcome_timing_delta_unit_check CHECK (
        timing_delta_unit IS NULL OR timing_delta_unit IN (
            'days', 'weeks', 'calendar_months', 'calendar_quarters',
            'half_years', 'calendar_years'
        )
    ),
    ADD CONSTRAINT judgment_outcome_noncomparable_delta_check CHECK (
        timing_relation <> 'not_comparable' OR timing_delta_value IS NULL
    );

CREATE INDEX judgment_outcome_known_at_idx
    ON research.judgment_outcome_evaluations (outcome_first_known_at, evaluated_at DESC)
    WHERE outcome_first_known_at IS NOT NULL;
