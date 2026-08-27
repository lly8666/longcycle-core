-- 0026 remains intentionally unclaimed: the previously discussed Outcome implication-polarity
-- migration is still deferred. 0027 adds an orthogonal source-document lifecycle state.

ALTER TABLE evidence.documents
    ADD COLUMN source_media_type text,
    ADD COLUMN source_capture_state text NOT NULL DEFAULT 'materialized',
    ADD COLUMN source_locator_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN locator_verified_at timestamptz,
    ADD COLUMN content_verified_at timestamptz,
    ADD COLUMN materialized_at timestamptz;

ALTER TABLE evidence.documents
    ADD CONSTRAINT documents_source_capture_state_check
    CHECK (source_capture_state IN ('locator_verified', 'content_verified', 'materialized'));

CREATE INDEX evidence_documents_pending_materialization_idx
    ON evidence.documents (source_capture_state, source_media_type, created_at)
    WHERE source_capture_state <> 'materialized';

CREATE OR REPLACE FUNCTION evidence.mark_document_materialized_from_version()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE evidence.documents
    SET source_capture_state = 'materialized',
        materialized_at = coalesce(materialized_at, NEW.created_at)
    WHERE id = NEW.document_id;
    RETURN NEW;
END;
$$;

CREATE TRIGGER evidence_document_version_marks_materialized
AFTER INSERT ON evidence.document_versions
FOR EACH ROW
EXECUTE FUNCTION evidence.mark_document_materialized_from_version();

-- Every pre-0027 document row was created through the archived-content path, so the
-- default state is truthful. We intentionally do not manufacture historical verification
-- timestamps for those rows.
UPDATE evidence.documents document
SET source_capture_state = 'materialized'
WHERE EXISTS (
    SELECT 1
    FROM evidence.document_versions version
    WHERE version.document_id = document.id
);

COMMENT ON COLUMN evidence.documents.source_capture_state IS
    'Source-document completeness state: locator_verified, content_verified, or materialized. Claim grounding requires content_verified or materialized content, not locator existence alone.';

COMMENT ON COLUMN evidence.documents.source_locator_metadata IS
    'Source-derived locator/provenance metadata such as upstream PDF filename, original URL, verification mode and deferred-materialization notes. Transport metadata does not change claim authority.';
