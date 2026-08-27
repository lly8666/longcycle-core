-- 0027 introduced source locator/content/materialization lifecycle state, but its generic
-- document-version trigger was too broad: a faithful readable representation may legitimately
-- create a document version for Grounded Evidence while the upstream raw PDF bytes are still
-- pending. A document version therefore proves preserved source-derived material, not by itself
-- byte-identical raw-source materialization.

DROP TRIGGER IF EXISTS evidence_document_version_marks_materialized
    ON evidence.document_versions;
DROP FUNCTION IF EXISTS evidence.mark_document_materialized_from_version();

ALTER TABLE evidence.documents
    ADD COLUMN raw_materialized_document_version_id uuid
        REFERENCES evidence.document_versions(id);

COMMENT ON COLUMN evidence.documents.raw_materialized_document_version_id IS
    'Optional document-version id whose archived bytes were explicitly verified as the raw upstream source material. A readable representation document version must not populate this field.';

COMMENT ON COLUMN evidence.documents.materialized_at IS
    'Time raw upstream source bytes were explicitly materialized/verified. Creating a readable source representation or Evidence document version does not set this timestamp.';

COMMENT ON COLUMN evidence.documents.source_capture_state IS
    'Source-document completeness state: locator_verified, content_verified, or materialized. content_verified may already have preserved readable Evidence material; materialized means raw upstream source bytes were explicitly verified, not merely that any document_version exists.';
