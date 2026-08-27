-- A materialized_file fetch can represent either byte-identical upstream source bytes or a
-- faithful readable representation of content that was actually read. The adapter emits explicit
-- internal response headers for the latter. Preserve that distinction on the logical document so
-- creating an Evidence document version never lies about raw PDF materialization.

CREATE OR REPLACE FUNCTION evidence.apply_source_representation_state_from_fetch()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    raw_materialized text;
    capture_state text;
    source_media_type text;
    verification_mode text;
    claim_content_preserved text;
BEGIN
    raw_materialized := NEW.response_headers ->> 'x-longcycle-raw-source-materialized';
    capture_state := NEW.response_headers ->> 'x-longcycle-source-capture-state';
    source_media_type := NEW.response_headers ->> 'x-longcycle-source-media-type';
    verification_mode := NEW.response_headers ->> 'x-longcycle-content-verification-mode';
    claim_content_preserved := NEW.response_headers ->> 'x-longcycle-claim-content-preserved';

    IF raw_materialized = 'false' THEN
        IF capture_state IS DISTINCT FROM 'content_verified'
           OR claim_content_preserved IS DISTINCT FROM 'true'
           OR verification_mode IS NULL
           OR btrim(verification_mode) = ''
           OR source_media_type IS NULL
           OR btrim(source_media_type) = '' THEN
            RAISE EXCEPTION
                'non-raw source representation lacks truthful content-verification provenance';
        END IF;

        UPDATE evidence.documents
        SET source_media_type = coalesce(evidence.documents.source_media_type, source_media_type),
            source_capture_state = CASE
                WHEN raw_materialized_document_version_id IS NOT NULL THEN 'materialized'
                ELSE 'content_verified'
            END,
            locator_verified_at = coalesce(locator_verified_at, NEW.retrieved_at),
            content_verified_at = coalesce(content_verified_at, NEW.retrieved_at),
            source_locator_metadata = source_locator_metadata || jsonb_build_object(
                'raw_source_materialized', false,
                'content_verification_mode', verification_mode,
                'claim_relevant_content_preserved', true,
                'source_media_type', source_media_type,
                'representation_content_blob_id', NEW.content_blob_id
            )
        WHERE id = NEW.document_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER evidence_fetch_applies_source_representation_state
AFTER INSERT ON evidence.document_fetches
FOR EACH ROW
EXECUTE FUNCTION evidence.apply_source_representation_state_from_fetch();

COMMENT ON FUNCTION evidence.apply_source_representation_state_from_fetch() IS
    'Keeps content-verified readable representations below raw materialized state. Internal x-longcycle headers are provenance markers emitted by trusted source adapters, not publisher headers or authority signals.';
