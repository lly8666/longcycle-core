-- Trusted announcement archives can preserve a formal disclosure even when the
-- retrieval host is not the issuer, exchange or regulator. Keep this distinct
-- from ordinary secondary reporting so claim-scoped authority and provenance
-- remain truthful.

ALTER TABLE evidence.source_authority_profiles
    DROP CONSTRAINT IF EXISTS source_authority_profiles_authority_class_check;

ALTER TABLE evidence.source_authority_profiles
    ADD CONSTRAINT source_authority_profiles_authority_class_check
    CHECK (authority_class IN (
        'authoritative_primary', 'authoritative_redistributor',
        'primary_self_statement', 'methodological_primary',
        'reputable_secondary', 'secondary', 'discovery_only'
    ));

ALTER TABLE evidence.source_authority_profiles
    DROP CONSTRAINT IF EXISTS source_authority_profiles_authority_basis_check;

ALTER TABLE evidence.source_authority_profiles
    ADD CONSTRAINT source_authority_profiles_authority_basis_check
    CHECK (authority_basis IN (
        'legal_mandate', 'official_record', 'direct_speaker_record',
        'published_methodology', 'verbatim_official_redistribution',
        'editorial_verification', 'secondary_citation', 'unknown'
    ));
