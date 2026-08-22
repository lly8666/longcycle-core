from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlsplit

from longcycle.domain.enums import QualityGrade, SourceKind
from longcycle.domain.models import SourceDefinition, stable_uuid_exact


def normalize_publisher_domain(value: str) -> str:
    domain = value.strip().lower().rstrip(".")
    if not domain:
        raise ValueError("publisher domain must not be blank")
    parsed = urlsplit(f"//{domain}")
    if parsed.hostname != domain or parsed.port is not None or parsed.username is not None:
        raise ValueError("publisher domain must be a bare DNS hostname")
    if any(character in domain for character in "/?#@"):
        raise ValueError("publisher domain must be a bare DNS hostname")
    if "." not in domain:
        raise ValueError("publisher domain must contain at least one dot")
    return domain


def _normalize_source_name(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError("source name must not be blank")
    return normalized


def build_http_source_definition(
    *,
    name: str,
    publisher_domain: str,
    kind: SourceKind = SourceKind.COMPANY,
    quality_grade: QualityGrade = QualityGrade.A,
    rate_limit_per_minute: int = 30,
    allowed_domains: Iterable[str] | None = None,
) -> SourceDefinition:
    normalized_name = _normalize_source_name(name)
    domain = normalize_publisher_domain(publisher_domain)
    if rate_limit_per_minute < 1:
        raise ValueError("rate_limit_per_minute must be positive")

    normalized_allowed_domains: tuple[str, ...]
    if allowed_domains is None:
        normalized_allowed_domains = (domain,)
    else:
        normalized_allowed_domains = tuple(
            dict.fromkeys(normalize_publisher_domain(item) for item in allowed_domains)
        )
        if not normalized_allowed_domains:
            raise ValueError("allowed_domains must contain at least one domain when supplied")

    source_id = stable_uuid_exact(
        "http-source-connector-v1",
        domain,
        normalized_name,
        "http_document",
    )
    return SourceDefinition(
        id=source_id,
        name=normalized_name,
        kind=kind,
        plugin="http_document",
        quality_grade=quality_grade,
        publisher_domain=domain,
        rate_limit_per_minute=rate_limit_per_minute,
        config={
            "urls": [],
            "allowed_domains": list(normalized_allowed_domains),
            "user_agent": "LongcycleCollector/0.1",
        },
        syndication_cluster=f"publisher-domain:{domain}",
    )


def build_materialized_source_definition(
    *,
    name: str,
    publisher_domain: str,
    kind: SourceKind = SourceKind.COMPANY,
    quality_grade: QualityGrade = QualityGrade.A,
) -> SourceDefinition:
    """Build a publisher-backed connector whose bytes arrive through a local material root."""

    normalized_name = _normalize_source_name(name)
    domain = normalize_publisher_domain(publisher_domain)
    source_id = stable_uuid_exact(
        "materialized-source-connector-v1",
        domain,
        normalized_name,
        "materialized_file",
    )
    return SourceDefinition(
        id=source_id,
        name=normalized_name,
        kind=kind,
        plugin="materialized_file",
        quality_grade=quality_grade,
        publisher_domain=domain,
        config={},
        syndication_cluster=f"publisher-domain:{domain}",
    )
