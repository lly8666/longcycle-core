-- 0029 introduced the representation-aware fetch trigger. Keep migration history immutable and
-- replace only the function body with unambiguous PL/pgSQL variable names before any application
-- fetch can invoke it.

CREATE OR REPLACE FUNCTION evidence.apply_source_representation_state_from_fetch()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_raw_materialized text;
    v_capture_state text;
    v_source_media_type text;
    v_verification_mode text;
    v_claim_content_preserved text;
BEGIN
    v_raw_materialized := NEW.response_headers ->> 'x-longcycle-raw-source-materialized';
    v_capture_state := NEW.response_headers ->> 'x-longcycle-source-capture-state';
    v_source_media_type := NEW.response_headers ->> 'x-longcycle-source-media-type';
    v_verification_mode := NEW.response_headers ->> 'x-longcycle-content-verification-mode';
    v_claim_content_preserved := NEW.response_headers ->> 'x-longcycle-claim-content-preserved';

    IF v_raw_materialized = 'false' THEN
        IF v_capture_state IS DISTINCT FROM 'content_verified'
           OR v_claim_content_preserved IS DISTINCT FROM 'true'
           OR v_verification_mode IS NULL
           OR btrim(v_verification_mode) = ''
           OR v_source_media_type IS NULL
           OR btrim(v_source_media_type) = '' THEN
            RAISE EXCEPTION
                'non-raw source representation lacks truthful content-verification provenance';
        END IF;

        UPDATE evidence.documents AS document
        SET source_media_type = coalesce(document.source_media_type, v_source_media_type),
            source_capture_state = CASE
                WHEN document.raw_materialized_document_version_id IS NOT NULL THEN 'materialized'
                ELSE 'content_verified'
            END,
            locator_verified_at = coalesce(document.locator_verified_at, NEW.retrieved_at),
            content_verified_at = coalesce(document.content_verified_at, NEW.retrieved_at),
            source_locator_metadata = document.source_locator_metadata || jsonb_build_object(
                'raw_source_materialized', false,
                'content_verification_mode', v_verification_mode,
                'claim_relevant_content_preserved', true,
                'source_media_type', v_source_media_type,
                'representation_content_blob_id', NEW.content_blob_id
            )
        WHERE document.id = NEW.document_id;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION evidence.apply_source_representation_state_from_fetch() IS
    'Keeps content-verified readable representations below raw materialized state. Internal x-longcycle headers are provenance markers emitted by trusted source adapters, not publisher headers or authority signals.';
