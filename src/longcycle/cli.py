from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from longcycle.adapters.models import JsonFixtureGateway
from longcycle.adapters.sources.http import HttpDocumentSource
from longcycle.adapters.sources.local import LocalFolderSource
from longcycle.adapters.sources.registry import SourceRegistry
from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.adapters.storage.postgres_scheduler import PostgresScheduler
from longcycle.application.pipeline import CollectionPipeline
from longcycle.application.research_orchestration import execute_research_orchestration_receipt
from longcycle.application.scheduling import SchedulePolicy
from longcycle.config import Settings
from longcycle.database import MigrationRunner
from longcycle.domain.enums import Cadence, QualityGrade, SourceKind
from longcycle.domain.models import CollectionPolicy, SourceDefinition, stable_uuid
from longcycle.ports.model import ExtractionTarget
from longcycle.ports.source import DiscoveryContext, FetchContext


def _default_migrations_dir() -> Path:
    repository_dir = Path(__file__).resolve().parents[2] / "migrations"
    if repository_dir.is_dir():
        return repository_dir
    return Path(__file__).resolve().with_name("sql_migrations")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="longcycle", description="Longcycle data and collection core")
    parser.add_argument("--json", action="store_true", dest="json_output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="validate configuration and optional dependencies")
    doctor.add_argument("--check-database", action="store_true")

    db = subparsers.add_parser("db", help="database operations")
    db_sub = db.add_subparsers(dest="db_command", required=True)
    upgrade = db_sub.add_parser("upgrade", help="apply PostgreSQL migrations")
    upgrade.add_argument("--migrations", type=Path, default=_default_migrations_dir())

    source = subparsers.add_parser("source", help="source plugin operations")
    source_sub = source.add_subparsers(dest="source_command", required=True)
    source_sub.add_parser("plugins", help="list installed source plugins")

    research = subparsers.add_parser("research", help="research execution operations")
    research_sub = research.add_subparsers(dest="research_command", required=True)
    research_run = research_sub.add_parser(
        "run",
        help="execute one repository-owned fail-closed research orchestration spec",
    )
    research_run.add_argument("spec", type=Path)
    research_run.add_argument("--source-pack", type=Path, required=True)
    research_run.add_argument("--work-dir", type=Path, required=True)
    research_run.add_argument("--output", type=Path, required=True)
    research_run.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="repository root used to resolve repo-owned Evidence/Reality/repair specs",
    )
    research_run.add_argument(
        "--skip-db-upgrade",
        action="store_true",
        help="skip database migration when PostgreSQL has already been upgraded",
    )

    schedule = subparsers.add_parser("schedule", help="explain dynamic cadence")
    schedule.add_argument("--industry-id", type=UUID, required=True)
    schedule.add_argument("--heat", type=float, required=True)
    schedule.add_argument("--risk", type=float, required=True)
    schedule.add_argument("--current", choices=[item.value for item in Cadence], default=Cadence.WEEKLY.value)
    schedule.add_argument("--low-days", type=int, default=0)

    scheduler_tick = subparsers.add_parser("scheduler-tick", help="atomically dispatch due collection policies")
    scheduler_tick.add_argument("--limit", type=int, default=100)

    subparsers.add_parser("demo", help="run an offline end-to-end golden-path collection")
    return parser


async def _doctor(settings: Settings, check_database: bool) -> dict[str, object]:
    settings.validate()
    result: dict[str, object] = {
        "python": sys.version.split()[0],
        "blob_backend": settings.blob_backend,
        "blob_root": str(settings.blob_root),
        "database_configured": bool(settings.database_url),
        "checks": {"pydantic": True, "httpx": True},
    }
    if check_database:
        if not settings.database_url:
            raise RuntimeError("LONGCYCLE_DATABASE_URL is not configured")
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("install longcycle-core[postgres]") from exc
        connection = await psycopg.AsyncConnection.connect(settings.database_url)
        try:
            cursor = await connection.execute("SELECT current_database(), current_setting('server_version')")
            row = await cursor.fetchone()
            if row is None:
                raise RuntimeError("database doctor query returned no row")
            result["database"] = {"name": row[0], "version": row[1]}
        finally:
            await connection.close()
    return result


async def _demo() -> dict[str, object]:
    industry_id = stable_uuid("industry", "vitamin-a")
    source_id = stable_uuid("source", "demo-json")
    sample = {
        "facts": [
            {
                "entity_type": "industry",
                "entity_id": str(industry_id),
                "field_name": "price.market_index",
                "value": "132",
                "value_type": "number",
                "number": "132",
                "unit": "unit",
                "dimensions": {
                    "product_spec_id": str(stable_uuid("product-spec", "vitamin-a-feed-500k")),
                    "geography_scheme": "internal",
                    "geography_code": "china",
                    "market_basis": "index",
                    "tax_basis": "included",
                    "freight_basis": "delivered",
                    "currency_code": "CNY",
                    "frequency": "daily",
                    "price_component": "average"
                },
                "valid_from": "2025-12-31",
                "valid_to": "2026-01-01",
                "locator": "$.facts[0]",
                "excerpt": "Vitamin A market index: 132",
                "confidence": 1,
                "corroboration": 0.9,
            }
        ]
    }
    with tempfile.TemporaryDirectory(prefix="longcycle-demo-") as temporary:
        root = Path(temporary)
        sample_path = root / "sample.json"
        sample_path.write_text(json.dumps(sample), encoding="utf-8")
        source = SourceDefinition(
            id=source_id,
            name="offline-demo",
            kind=SourceKind.MANUAL,
            plugin="local_folder",
            quality_grade=QualityGrade.A,
            config={"root": str(root), "patterns": ["*.json"]},
        )
        repository = InMemoryResearchRepository([source])
        plugin = LocalFolderSource(source)
        items = [item async for item in plugin.discover(DiscoveryContext(source=source, industry_id=industry_id))]
        pipeline = CollectionPipeline(
            repository=repository,
            archive=FileSystemArchiveStore(root / "blobs"),
            model=JsonFixtureGateway(source_quality=0.95, source_cluster="demo"),
        )
        report = await pipeline.ingest(
            plugin=plugin,
            item=items[0],
            target=ExtractionTarget(industry_ids=(industry_id,)),
            fetch_context=FetchContext(source=source),
        )
        return asdict(report)


async def _run(args: argparse.Namespace) -> dict[str, object] | list[object]:
    settings = Settings.from_env()
    if args.command == "doctor":
        return await _doctor(settings, args.check_database)
    if args.command == "db" and args.db_command == "upgrade":
        if not settings.database_url:
            raise RuntimeError("LONGCYCLE_DATABASE_URL is not configured")
        applied = await MigrationRunner(settings.database_url, args.migrations).upgrade()
        return [asdict(item) for item in applied]
    if args.command == "source" and args.source_command == "plugins":
        registry = SourceRegistry()
        registry.register("local_folder", LocalFolderSource)
        registry.register("http_document", HttpDocumentSource)
        registry.load_entry_points()
        return list(registry.names)
    if args.command == "research" and args.research_command == "run":
        payload = execute_research_orchestration_receipt(
            repo_root=args.repo_root,
            spec_path=args.spec,
            source_pack_path=args.source_pack,
            work_dir=args.work_dir,
            output_path=args.output,
            skip_db_upgrade=bool(args.skip_db_upgrade),
        )
        if payload.get("ok") is not True:
            error = payload.get("error")
            raise RuntimeError(error if isinstance(error, str) else "research orchestration failed")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("research orchestration returned no result object")
        return result
    if args.command == "schedule":
        collection_policy = CollectionPolicy(
            industry_id=args.industry_id,
            cadence=Cadence(args.current),
            heat_score=args.heat,
            data_risk_score=args.risk,
            consecutive_low_days=args.low_days,
        )
        policy = SchedulePolicy()
        now = datetime.now(UTC)
        return {
            "priority": collection_policy.priority,
            "cadence": policy.cadence_for(collection_policy, now).value,
            "next_run": policy.next_run(collection_policy, now).isoformat(),
        }
    if args.command == "scheduler-tick":
        if not settings.database_url:
            raise RuntimeError("LONGCYCLE_DATABASE_URL is not configured")
        jobs = await PostgresScheduler(settings.database_url).tick(limit=args.limit)
        return [job.model_dump(mode="json") for job in jobs]
    if args.command == "demo":
        return await _demo()
    raise RuntimeError("unhandled command")


def main() -> None:
    args = _parser().parse_args()
    try:
        result = asyncio.run(_run(args))
    except Exception as exc:
        if args.json_output:
            print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    if args.json_output:
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, default=str))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
