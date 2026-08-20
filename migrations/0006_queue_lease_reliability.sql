-- Queue reliability upgrade. This intentionally replaces the function from
-- 0004 instead of mutating an already-published migration.
CREATE OR REPLACE FUNCTION ops.claim_collection_jobs(
    p_worker_id text,
    p_pools text[],
    p_limit integer,
    p_lease_seconds integer
)
RETURNS SETOF ops.collection_jobs
LANGUAGE sql
AS $$
    WITH exhausted_candidates AS MATERIALIZED (
        SELECT job.id, job.attempt_count, job.lease_token, job.status
        FROM ops.collection_jobs AS job
        WHERE job.pool = ANY (p_pools)
          AND job.available_at <= now()
          AND job.attempt_count >= job.max_attempts
          AND (
              job.status IN ('queued', 'retry')
              OR (job.status = 'leased' AND job.lease_expires_at <= now())
          )
        FOR UPDATE SKIP LOCKED
    ),
    dead_jobs AS (
        UPDATE ops.collection_jobs AS job
        SET status = 'dead',
            finished_at = now(),
            last_error_code = CASE
                WHEN exhausted.status = 'leased' THEN 'lease_expired'
                ELSE 'attempts_exhausted'
            END,
            last_error_message = CASE
                WHEN exhausted.status = 'leased' THEN 'lease expired after maximum attempts'
                ELSE 'maximum attempts exhausted'
            END,
            lease_owner = NULL,
            lease_token = NULL,
            lease_expires_at = NULL
        FROM exhausted_candidates AS exhausted
        WHERE job.id = exhausted.id
        RETURNING job.id, exhausted.attempt_count, exhausted.lease_token, exhausted.status
    ),
    closed_dead_attempts AS (
        UPDATE ops.job_attempts AS attempt
        SET status = 'dead',
            finished_at = now(),
            error_code = 'lease_expired',
            error_message = 'lease expired after maximum attempts'
        FROM dead_jobs
        WHERE attempt.job_id = dead_jobs.id
          AND attempt.attempt_number = dead_jobs.attempt_count
          AND attempt.lease_token = dead_jobs.lease_token
          AND attempt.status = 'running'
        RETURNING attempt.job_id
    ),
    inserted_dead_letters AS (
        INSERT INTO ops.dead_letters (job_id, final_error_code, final_error_message)
        SELECT
            dead_jobs.id,
            CASE WHEN dead_jobs.status = 'leased' THEN 'lease_expired' ELSE 'attempts_exhausted' END,
            CASE
                WHEN dead_jobs.status = 'leased' THEN 'lease expired after maximum attempts'
                ELSE 'maximum attempts exhausted'
            END
        FROM dead_jobs
        ON CONFLICT (job_id) DO UPDATE
        SET dead_at = now(),
            final_error_code = EXCLUDED.final_error_code,
            final_error_message = EXCLUDED.final_error_message
        RETURNING job_id
    ),
    candidates AS MATERIALIZED (
        SELECT job.id
        FROM ops.collection_jobs AS job
        WHERE job.pool = ANY (p_pools)
          AND job.available_at <= now()
          AND job.attempt_count < job.max_attempts
          AND (
              job.status IN ('queued', 'retry')
              OR (job.status = 'leased' AND job.lease_expires_at <= now())
          )
        ORDER BY job.priority DESC, job.available_at, job.created_at
        FOR UPDATE SKIP LOCKED
        LIMIT greatest(p_limit, 0)
    ),
    claimed AS (
        UPDATE ops.collection_jobs AS job
        SET status = 'leased',
            lease_owner = p_worker_id,
            lease_token = gen_random_uuid(),
            lease_expires_at = now() + make_interval(secs => greatest(p_lease_seconds, 1)),
            attempt_count = job.attempt_count + 1,
            started_at = coalesce(job.started_at, now())
        FROM candidates
        WHERE job.id = candidates.id
        RETURNING job.*
    ),
    closed_expired_attempts AS (
        UPDATE ops.job_attempts AS attempt
        SET status = 'retry',
            finished_at = now(),
            error_code = 'lease_expired',
            error_message = 'lease expired before acknowledgement'
        FROM claimed
        WHERE attempt.job_id = claimed.id
          AND attempt.attempt_number = claimed.attempt_count - 1
          AND attempt.status = 'running'
        RETURNING attempt.job_id
    )
    SELECT claimed.* FROM claimed;
$$;
