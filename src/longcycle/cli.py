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
from longcycle.adapters.storage.duckdb_epistemic import DuckDBEpistemicMemoryReader
from longcycle.adapters.storage.filesystem import FileSystemArchiveStore
from longcycle.adapters.storage.memory import InMemoryResearchRepository
from longcycle.adapters.storage.postgres_epistemic import PostgresEpistemicMemoryReader
from longcycle.adapters.storage.postgres_evidence import PostgresEvidenceDrilldownReader
from longcycle.adapters.storage.postgres_open_states import PostgresOpenStateReader
from longcycle.adapters.storage.postgres_orientation import PostgresIndustryOrientationReader
from longcycle.adapters.storage.postgres_scheduler import PostgresScheduler
from longcycle.application.epistemic_trajectory import execute_epistemic_trajectory_receipt
from longcycle.application.evidence_drilldown import build_researcher_evidence_drilldown
from longcycle.application.industry_orientation import build_researcher_industry_orientation
from longcycle.application.open_state_view import build_researcher_open_state_view
from longcycle.application.pipeline import CollectionPipeline
from longcycle.application.research_orchestration import execute_research_orchestration_receipt
from longcycle.application.scheduling import SchedulePolicy
from longcycle.application.trajectory_view import build_researcher_trajectory_view
from longcycle.config import Settings
from longcycle.database import MigrationRunner
from longcycle.domain.enums import Cadence, QualityGrade, SourceKind
from longcycle.domain.epistemic import MemorySubjectRef
from longcycle.domain.models import (
    CollectionPolicy,
    SourceDefinition,
    require_aware_datetime,
    stable_uuid,
)
from longcycle.ports.model import ExtractionTarget
from longcycle.ports.source import DiscoveryContext, FetchContext


_EPISTEMIC_TRAJECTORY_V1 = "longcycle-epistemic-trajectory/v1"
_RESEARCH_ORCHESTRATION_VERSIONS = {
    "longcycle-research-orchestration/v1",
    "longcycle-research-orchestration/v2",
}


def _default_migrations_dir() -> Path:
    repository_dir = Path(__file__).resolve().parents[2] / "migrations"
    if repository_dir.is_dir():
        return repository_dir
    return Path(__file__).resolve().with_name("sql_migrations")


def _parse_aware_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    checked = require_aware_datetime(parsed, "knowledge_cutoff")
    assert checked is not None
    return checked


def _research_spec_schema_version(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("research run spec must be a JSON object")
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version:
        raise ValueError("research run spec has no schema_version")
    return schema_version


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

    research = subparsers.add_parser("research", help="research execution and replay operations")
    research_sub = research.add_subparsers(dest="research_command", required=True)
    research_run = research_sub.add_parser(
        "run",
        help=(
            "execute one repository-owned fail-closed research-orchestration or "
            "epistemic-trajectory spec"
        ),
    )
    research_run.add_argument("spec", type=Path)
    research_run.add_argument(
        "--source-pack",
        type=Path,
        help=(
            "legacy research-orchestration/v1 source-pack ZIP. New v2 orchestration and "
            "epistemic trajectories use --material-root instead; raw PDF download/Release "
            "packaging is not an epistemic prerequisite"
        ),
    )
    research_run.add_argument(
        "--material-root",
        type=Path,
        help=(
            "transport-neutral local root containing preserved source material declared by "
            "the Grounded Evidence spec"
        ),
    )
    research_run.add_argument("--work-dir", type=Path, required=True)
    research_run.add_argument("--output", type=Path, required=True)
    research_run.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="repository root used to resolve repo-owned Evidence/Reality/Judgment/trajectory specs",
    )
    research_run.add_argument(
        "--skip-db-upgrade",
        action="store_true",
        help="skip database migration when PostgreSQL has already been upgraded",
    )
    research_replay = research_sub.add_parser(
        "replay",
        help="render a no-lookahead researcher trajectory view from portable industrial memory",
    )
    research_replay.add_argument("database", type=Path)
    research_replay.add_argument("cutoff", type=_parse_aware_datetime)
    research_replay.add_argument(
        "--subject-id",
        action="append",
        default=[],
        help="entity UUID to include in the point-in-time trajectory",
    )
    research_replay.add_argument(
        "--industry-node-id",
        action="append",
        default=[],
        help="industry taxonomy-node UUID to include in the point-in-time trajectory",
    )
    research_evidence = research_sub.add_parser(
        "evidence",
        help="read one claim-scoped Evidence fragment and its truthful source provenance",
    )
    research_evidence.add_argument("evidence_fragment_id", type=UUID)
    research_evidence.add_argument("cutoff", type=_parse_aware_datetime)
    research_orient = research_sub.add_parser(
        "orient",
        help="enter an industry through source-grounded membership and no-lookahead memory",
    )
    research_orient.add_argument("industry_node_id", type=UUID)
    research_orient.add_argument("cutoff", type=_parse_aware_datetime)
    research_open_states = research_sub.add_parser(
        "open-states",
        help="separate historical controversy from opt-in current research-only uncertainty",
    )
    research_open_states.add_argument("industry_node_id", type=UUID)
    research_open_states.add_argument("cutoff", type=_parse_aware_datetime)
    research_open_states.add_argument(
        "--include-current-research",
        action="store_true",
        help=(
            "include current Memory disagreement/hypothesis/model-memory coverage state; "
            "this overlay is not historical market knowledge and is not cutoff-filtered"
        ),
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
                    "price_component": "average",
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
        items = [
            item
            async for item in plugin.discover(
                DiscoveryContext(source=source, industry_id=industry_id)
            )
        ]
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


async def _research_replay(args: argparse.Namespace) -> dict[str, object]:
    subjects = tuple(
        [MemorySubjectRef(entity_id=UUID(value)) for value in args.subject_id]
        + [MemorySubjectRef(industry_node_id=UUID(value)) for value in args.industry_node_id]
    )
    if not subjects:
        raise ValueError("research replay requires at least one --subject-id or --industry-node-id")
    reader = DuckDBEpistemicMemoryReader(args.database)
    snapshot = await reader.snapshot(subjects, knowledge_cutoff=args.cutoff)
    return build_researcher_trajectory_view(snapshot)


async def _research_evidence(args: argparse.Namespace, settings: Settings) -> dict[str, object]:
    if not settings.database_url:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is not configured")
    reader = PostgresEvidenceDrilldownReader(settings.database_url)
    try:
        return await build_researcher_evidence_drilldown(
            reader=reader,
            evidence_fragment_id=args.evidence_fragment_id,
            knowledge_cutoff=args.cutoff,
        )
    finally:
        await reader.close()


async def _research_orient(args: argparse.Namespace, settings: Settings) -> dict[str, object]:
    if not settings.database_url:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is not configured")
    catalog_reader = PostgresIndustryOrientationReader(settings.database_url)
    memory_reader = PostgresEpistemicMemoryReader(settings.database_url)
    try:
        return await build_researcher_industry_orientation(
            catalog_reader=catalog_reader,
            memory_reader=memory_reader,
            industry_node_id=args.industry_node_id,
            knowledge_cutoff=args.cutoff,
        )
    finally:
        await catalog_reader.close()
        await memory_reader.close()


async def _research_open_states(args: argparse.Namespace, settings: Settings) -> dict[str, object]:
    if not settings.database_url:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is not configured")
    catalog_reader = PostgresIndustryOrientationReader(settings.database_url)
    memory_reader = PostgresEpistemicMemoryReader(settings.database_url)
    open_state_reader = PostgresOpenStateReader(settings.database_url)
    try:
        return await build_researcher_open_state_view(
            catalog_reader=catalog_reader,
            memory_reader=memory_reader,
            conflict_reader=open_state_reader,
            current_research_reader=open_state_reader,
            industry_node_id=args.industry_node_id,
            knowledge_cutoff=args.cutoff,
            include_current_research=bool(args.include_current_research),
        )
    finally:
        await catalog_reader.close()
        await memory_reader.close()
        await open_state_reader.close()


def _research_run(args: argparse.Namespace) -> dict[str, object]:
    schema_version = _research_spec_schema_version(args.spec)
    if schema_version == _EPISTEMIC_TRAJECTORY_V1:
        if args.source_pack is not None:
            raise ValueError(
                "epistemic trajectory is transport-neutral and does not accept --source-pack; "
                "prepare source material outside the runner and use --material-root"
            )
        if args.material_root is None:
            raise ValueError("epistemic trajectory requires --material-root")
        payload = execute_epistemic_trajectory_receipt(
            repo_root=args.repo_root,
            spec_path=args.spec,
            material_root_path=args.material_root,
            work_dir=args.work_dir,
            output_path=args.output,
            skip_db_upgrade=bool(args.skip_db_upgrade),
        )
    elif schema_version in _RESEARCH_ORCHESTRATION_VERSIONS:
        payload = execute_research_orchestration_receipt(
            repo_root=args.repo_root,
            spec_path=args.spec,
            source_pack_path=args.source_pack,
            material_root_path=args.material_root,
            work_dir=args.work_dir,
            output_path=args.output,
            skip_db_upgrade=bool(args.skip_db_upgrade),
        )
    else:
        raise ValueError(f"unsupported research run schema_version: {schema_version}")

    if payload.get("ok") is not True:
        error = payload.get("error")
        raise RuntimeError(error if isinstance(error, str) else "research run failed")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("research run returned no result object")
    return result


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
        return _research_run(args)
    if args.command == "research" and args.research_command == "replay":
        return await _research_replay(args)
    if args.command == "research" and args.research_command == "evidence":
        return await _research_evidence(args, settings)
    if args.command == "research" and args.research_command == "orient":
        return await _research_orient(args, settings)
    if args.command == "research" and args.research_command == "open-states":
        return await _research_open_states(args, settings)
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
