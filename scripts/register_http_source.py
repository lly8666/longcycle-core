from __future__ import annotations

import argparse
import asyncio
import json

from longcycle.adapters.storage.postgres_sources import PostgresSourceRegistry
from longcycle.application.source_registration import build_http_source_definition
from longcycle.config import Settings
from longcycle.domain.enums import QualityGrade, SourceKind


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Idempotently register one publisher-backed HTTP source connector so archive-only "
            "evidence tasks can run without manual SQL."
        )
    )
    parser.add_argument("--name", required=True)
    parser.add_argument("--publisher-domain", required=True)
    parser.add_argument(
        "--kind",
        choices=[item.value for item in SourceKind],
        default=SourceKind.COMPANY.value,
    )
    parser.add_argument(
        "--quality-grade",
        choices=[item.value for item in QualityGrade],
        default=QualityGrade.A.value,
    )
    parser.add_argument("--rate-limit-per-minute", type=int, default=30)
    return parser


async def _run(args: argparse.Namespace) -> dict[str, object]:
    settings = Settings.from_env()
    settings.validate()
    if not settings.database_url:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required for source registration")

    source = build_http_source_definition(
        name=args.name,
        publisher_domain=args.publisher_domain,
        kind=SourceKind(args.kind),
        quality_grade=QualityGrade(args.quality_grade),
        rate_limit_per_minute=args.rate_limit_per_minute,
    )
    registry = PostgresSourceRegistry(settings.database_url)
    try:
        registered = await registry.register(source)
    finally:
        await registry.close()
    return {
        "source_id": str(registered.id),
        "name": registered.name,
        "publisher_domain": registered.publisher_domain,
        "plugin": registered.plugin,
        "source_kind": registered.kind.value,
        "quality_grade": registered.quality_grade.value,
        "rate_limit_per_minute": registered.rate_limit_per_minute,
        "allowed_domains": registered.config.get("allowed_domains", []),
    }


def main() -> None:
    args = _parser().parse_args()
    try:
        result = asyncio.run(_run(args))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        raise SystemExit(1) from exc
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
