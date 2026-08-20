-- A successfully accepted correction makes its predecessor historical rather
-- than an active trusted assertion.  The immutable assertion remains fully
-- queryable; only its derived current status changes.
DROP VIEW research.fact_assertions_with_status;

CREATE VIEW research.fact_assertions_with_status AS
SELECT
    assertion.*,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM research.fact_assertions successor
            WHERE successor.supersedes_assertion_id = assertion.id
              AND (
                  SELECT evaluation.decision
                  FROM research.reconciliation_evaluations evaluation
                  WHERE evaluation.assertion_id = successor.id
                  ORDER BY evaluation.evaluated_at DESC, evaluation.id DESC
                  LIMIT 1
              ) = 'accept'
        ) THEN 'superseded'
        WHEN latest.decision = 'accept' THEN 'trusted'
        WHEN latest.decision = 'quarantine' THEN 'quarantined'
        WHEN latest.decision IS NOT NULL THEN latest.decision
        ELSE assertion.ingest_status
    END AS status
FROM research.fact_assertions assertion
LEFT JOIN LATERAL (
    SELECT evaluation.decision
    FROM research.reconciliation_evaluations evaluation
    WHERE evaluation.assertion_id = assertion.id
    ORDER BY evaluation.evaluated_at DESC, evaluation.id DESC
    LIMIT 1
) latest ON true;
