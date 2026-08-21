from __future__ import annotations

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


def build_http_source_definition(
    *,
    name: str,
    publisher_domain: str,
    kind: SourceKind = SourceKind.COMPANY,
    quality_grade: QualityGrade = QualityGrade.A,
    rate_limit_per_minute: int = 30,
) -> SourceDefinition:
    normalized_name = " ".join(name.split())
    if not normalized_name:
        raise ValueError("source name must not be blank")
    domain = normalize_publisher_domain(publisher_domain)
    if rate_limit_per_minute < 1:
        raise ValueError("rate_limit_per_minute must be positive")

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
            "allowed_domains": [domain],
            "user_agent": "LongcycleCollector/0.1",
        },
        syndication_cluster=f"publisher-domain:{domain}",
    )
