-- Source capture state must not be inferred from the mere existence of a document version.
-- 0028 removed the broad trigger; 0031 completes the contract by removing the legacy
-- materialized default and requiring every new archived version to declare whether its bytes are
-- the raw upstream source or a non-raw readable representation.

-- Repair any representation rows that could have been promoted by the pre-0028 trigger. The
-- trusted representation adapter already left an explicit false marker on its fetch provenance.
UPDATE evidence.documents AS document
SET source_capture_state = 'content_verified',
    materialized_at = NULL,
    raw_materialized_document_version_id = NULL,
    content_verified_at = coalesce(
        document.content_verified_at,
        (
            SELECT min(fetch.retrieved_at)
            FROM evidence.document_fetches AS fetch
            WHERE fetch.document_id = document.id
              AND fetch.response_headers ->> 'x-longcycle-raw-source-materialized' = 'false'
        )
    )
WHERE document.source_capture_state = 'materialized'
  AND document.raw_materialized_document_version_id IS NULL
  AND EXISTS (
      SELECT 1
      FROM evidence.document_fetches AS fetch
      WHERE fetch.document_id = document.id
        AND fetch.response_headers ->> 'x-longcycle-raw-source-materialized' = 'false'
  );

-- Pre-0031 materialized rows were created by the historical raw archive path unless they carried
-- the explicit representation marker handled above. Bind one deterministic archived raw version
-- so old data satisfies the new explicit invariant without rewriting the version history.
WITH legacy_raw_version AS (
    SELECT DISTINCT ON (version.document_id)
        version.document_id,
        version.id AS document_version_id,
        version.created_at
    FROM evidence.document_versions AS version
    JOIN evidence.document_fetches AS fetch
      ON fetch.id = version.first_fetch_id
     AND fetch.document_id = version.document_id
     AND fetch.content_blob_id = version.content_blob_id
    WHERE coalesce(
        fetch.response_headers ->> 'x-longcycle-raw-source-materialized',
        'legacy-raw'
    ) <> 'false'
    ORDER BY version.document_id, version.version_ordinal, version.created_at, version.id
)
UPDATE evidence.documents AS document
SET raw_materialized_document_version_id = legacy.document_version_id,
    materialized_at = coalesce(document.materialized_at, legacy.created_at)
FROM legacy_raw_version AS legacy
WHERE document.id = legacy.document_id
  AND document.source_capture_state = 'materialized'
  AND document.raw_materialized_document_version_id IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM evidence.documents
        WHERE source_capture_state = 'materialized'
          AND raw_materialized_document_version_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'materialized source document has no archived raw document version; repair before 0031';
    END IF;
END;
$$;

ALTER TABLE evidence.documents
    ALTER COLUMN source_capture_state SET DEFAULT 'locator_verified';

ALTER TABLE evidence.documents
    ADD CONSTRAINT documents_raw_materialization_state_consistency_check
    CHECK (
        (source_capture_state = 'materialized' AND raw_materialized_document_version_id IS NOT NULL)
        OR
        (source_capture_state <> 'materialized' AND raw_materialized_document_version_id IS NULL)
    );

CREATE OR REPLACE FUNCTION evidence.apply_raw_source_materialization_from_version()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_raw_materialized text;
    v_retrieved_at timestamptz;
    v_content_type text;
BEGIN
    SELECT
        fetch.response_headers ->> 'x-longcycle-raw-source-materialized',
        fetch.retrieved_at,
        blob.content_type
    INTO v_raw_materialized, v_retrieved_at, v_content_type
    FROM evidence.document_fetches AS fetch
    JOIN evidence.content_blobs AS blob ON blob.id = fetch.content_blob_id
    WHERE fetch.id = NEW.first_fetch_id
      AND fetch.document_id = NEW.document_id
      AND fetch.content_blob_id = NEW.content_blob_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'document version % has no matching first fetch provenance', NEW.id;
    END IF;

    IF v_raw_materialized = 'true' THEN
        UPDATE evidence.documents AS document
        SET source_media_type = coalesce(document.source_media_type, v_content_type),
            source_capture_state = 'materialized',
            locator_verified_at = coalesce(document.locator_verified_at, v_retrieved_at),
            materialized_at = coalesce(document.materialized_at, NEW.created_at),
            raw_materialized_document_version_id = NEW.id,
            source_locator_metadata = document.source_locator_metadata || jsonb_build_object(
                'raw_source_materialized', true,
                'raw_materialized_document_version_id', NEW.id
            )
        WHERE document.id = NEW.document_id;
    ELSIF v_raw_materialized = 'false' THEN
        -- 0029/0030 already validated the representation provenance when its fetch was inserted and
        -- kept the logical document at content_verified unless a raw version existed beforehand.
        NULL;
    ELSE
        RAISE EXCEPTION
            'document version % lacks explicit x-longcycle-raw-source-materialized provenance',
            NEW.id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER evidence_document_version_applies_explicit_raw_materialization
AFTER INSERT ON evidence.document_versions
FOR EACH ROW
EXECUTE FUNCTION evidence.apply_raw_source_materialization_from_version();

COMMENT ON FUNCTION evidence.apply_raw_source_materialization_from_version() IS
    'Binds a logical document to an explicitly declared raw-source document version. Missing provenance fails closed; non-raw readable representations remain content_verified through the representation fetch contract.';

COMMENT ON COLUMN evidence.documents.source_capture_state IS
    'Source-document completeness state. New rows start locator_verified. content_verified requires actually read/preserved claim content. materialized requires raw_materialized_document_version_id bound from an explicit raw=true source fetch; document-version existence alone is insufficient.';
