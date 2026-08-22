from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import urlsplit

from longcycle.domain.memory import (
    AuthorityBasis,
    AuthorityClass,
    SourceAuthorityProfile,
)
from longcycle.domain.models import SourceDefinition


_UPSTREAM_ANNOUNCEMENT_FIELDS = ("issuer", "system", "external_id", "title")


def parse_source_authority_profiles(value: object) -> tuple[SourceAuthorityProfile, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("source authority_profiles must be a list")
    profiles: list[SourceAuthorityProfile] = []
    for row in value:
        if not isinstance(row, dict):
            raise ValueError("source authority profile entries must be objects")
        profiles.append(SourceAuthorityProfile.model_validate(row))
    return tuple(profiles)


def validate_redistributed_document_provenance(
    *,
    source: SourceDefinition,
    retrieval_url: str,
    retrieval_provenance: object,
    authority_profiles: Sequence[SourceAuthorityProfile],
) -> None:
    redistributed = [
        profile
        for profile in authority_profiles
        if profile.authority_class == AuthorityClass.AUTHORITATIVE_REDISTRIBUTOR
    ]
    if not redistributed:
        return

    for profile in redistributed:
        if profile.authority_basis != AuthorityBasis.VERBATIM_OFFICIAL_REDISTRIBUTION:
            raise ValueError(
                "authoritative redistributor profiles require verbatim_official_redistribution"
            )

    publisher_domain = source.publisher_domain
    if publisher_domain is None:
        raise ValueError("authoritative redistributor source requires publisher_domain")
    parsed = urlsplit(retrieval_url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    domain = publisher_domain.lower().rstrip(".")
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise ValueError("authoritative redistributor retrieval_url must be absolute HTTP(S)")
    if hostname != domain and not hostname.endswith(f".{domain}"):
        raise ValueError(
            "authoritative redistributor retrieval_url must belong to its publisher domain"
        )

    if not isinstance(retrieval_provenance, dict):
        raise ValueError("authoritative redistributor requires retrieval_provenance")
    upstream = retrieval_provenance.get("upstream_announcement")
    if not isinstance(upstream, dict):
        raise ValueError(
            "authoritative redistributor requires retrieval_provenance.upstream_announcement"
        )
    missing = [
        field
        for field in _UPSTREAM_ANNOUNCEMENT_FIELDS
        if not isinstance(upstream.get(field), str) or not str(upstream[field]).strip()
    ]
    if missing:
        raise ValueError(
            "authoritative redistributor upstream announcement is missing: "
            + ", ".join(missing)
        )
