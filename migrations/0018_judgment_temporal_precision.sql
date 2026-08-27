-- Historical expectations often name a month, quarter, half-year, year, or a phrase
-- such as "late 2021" rather than an exact day. Preserve that source precision instead
-- of manufacturing false timestamp accuracy for ordering or presentation.

ALTER TABLE research.judgment_assertions
    ADD COLUMN target_precision text NOT NULL DEFAULT 'unknown',
    ADD COLUMN target_text text;

ALTER TABLE research.judgment_assertions
    ADD CONSTRAINT judgment_assertions_target_precision_check CHECK (target_precision IN (
        'instant', 'second', 'minute', 'hour', 'day', 'week', 'month',
        'quarter', 'half_year', 'year', 'range', 'approximate', 'unknown'
    )),
    ADD CONSTRAINT judgment_assertions_approximate_target_text_check CHECK (
        target_precision <> 'approximate' OR target_text IS NOT NULL
    );

ALTER TABLE research.expectation_snapshots
    ADD COLUMN target_precision text NOT NULL DEFAULT 'unknown',
    ADD COLUMN target_text text;

ALTER TABLE research.expectation_snapshots
    ADD CONSTRAINT expectation_snapshots_target_precision_check CHECK (target_precision IN (
        'instant', 'second', 'minute', 'hour', 'day', 'week', 'month',
        'quarter', 'half_year', 'year', 'range', 'approximate', 'unknown'
    )),
    ADD CONSTRAINT expectation_snapshots_approximate_target_text_check CHECK (
        target_precision <> 'approximate' OR target_text IS NOT NULL
    );

CREATE INDEX judgment_target_precision_idx
    ON research.judgment_assertions (target_precision, first_known_at DESC);
