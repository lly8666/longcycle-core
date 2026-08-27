-- Later reality may be related to a historical Judgment without being the same
-- milestone. Preserve that semantic distinction explicitly so replay cannot turn
-- "a related later event happened" into "the original target was realized".

ALTER TABLE research.judgment_outcome_evaluations
    DROP CONSTRAINT IF EXISTS judgment_outcome_evaluations_evaluation_status_check;

ALTER TABLE research.judgment_outcome_evaluations
    ADD COLUMN semantic_relation text NOT NULL DEFAULT 'direct_match';

ALTER TABLE research.judgment_outcome_evaluations
    ADD CONSTRAINT judgment_outcome_evaluation_status_check CHECK (
        evaluation_status IN (
            'realized', 'partially_realized', 'not_realized',
            'not_yet_evaluable', 'invalidated', 'indeterminate'
        )
    ),
    ADD CONSTRAINT judgment_outcome_semantic_relation_check CHECK (
        semantic_relation IN ('direct_match', 'related_milestone', 'not_comparable')
    ),
    ADD CONSTRAINT judgment_outcome_non_direct_semantics_check CHECK (
        semantic_relation = 'direct_match'
        OR (
            evaluation_status = 'indeterminate'
            AND timing_relation = 'not_comparable'
            AND timing_delta_value IS NULL
            AND timing_delta_unit IS NULL
        )
    );
