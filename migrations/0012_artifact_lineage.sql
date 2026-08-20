-- Parser-specific evidence remains distinct when two parser versions emit the
-- same locator and payload. NULL artifact_id preserves direct-source evidence.
DO $$ DECLARE old_constraint name; BEGIN
    SELECT constraint_row.conname
      INTO old_constraint
      FROM pg_constraint AS constraint_row
     WHERE constraint_row.conrelid = 'evidence.evidence_fragments'::regclass
       AND constraint_row.contype = 'u'
       AND pg_get_constraintdef(constraint_row.oid) =
           'UNIQUE (document_version_id, locator_type, locator_hash, fragment_sha256)';
    IF old_constraint IS NOT NULL THEN
        EXECUTE format(
            'ALTER TABLE evidence.evidence_fragments DROP CONSTRAINT %I',
            old_constraint
        );
    END IF;
END $$;

ALTER TABLE evidence.evidence_fragments
    ADD CONSTRAINT evidence_fragments_artifact_locator_unique
    UNIQUE NULLS NOT DISTINCT (
        document_version_id,
        artifact_id,
        locator_type,
        locator_hash,
        fragment_sha256
    );
