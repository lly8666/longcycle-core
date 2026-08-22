from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import psycopg


TEXT = "Materialized filing says demand growth was slower than anticipated."
HTML = f"<html><body>{TEXT}</body></html>".encode()
RAW_SHA256 = hashlib.sha256(HTML).hexdigest()
VISIBLE_SHA256 = hashlib.sha256(TEXT.encode()).hexdigest()


def main() -> None:
    database_url = os.environ.get("LONGCYCLE_DATABASE_URL")
    if not database_url:
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    with tempfile.TemporaryDirectory(prefix="longcycle-materialized-smoke-") as temporary:
        root = Path(temporary)
        material_root = root / "material"
        blob_root = root / "blobs"
        material_root.mkdir()
        material_path = material_root / "filing.htm"
        material_path.write_bytes(HTML)

        retrieval_url = (
            "https://www.prnewswire.com/news-releases/materialized-smoke-results-300000000.html"
        )
        upstream_url = "https://www.sec.gov/Archives/edgar/data/0/materialized-smoke.htm"
        upstream_accession = "0000000000-19-000001"
        spec = {
            "schema_version": "longcycle-grounded-evidence-spec/v2",
            "task_id": "MATERIALIZED-GROUNDED-EVIDENCE-SMOKE-V2",
            "sources": [
                {
                    "key": "announcement-redistributor",
                    "name": "Materialized formal announcement redistributor smoke",
                    "publisher_domain": "prnewswire.com",
                    "kind": "company",
                    "quality_grade": "A",
                    "transport": "materialized",
                    "authority_profiles": [
                        {
                            "claim_scope": "legal_disclosure",
                            "authority_class": "authoritative_redistributor",
                            "authority_basis": "verbatim_official_redistribution",
                            "rationale": (
                                "Connector preserves issuer-supplied formal announcement bodies "
                                "with upstream filing identity."
                            ),
                        }
                    ],
                }
            ],
            "documents": [
                {
                    "key": "filing",
                    "vintage_id": "MATERIALIZED-SMOKE-2019Q1",
                    "source_key": "announcement-redistributor",
                    "retrieval_url": retrieval_url,
                    "original_source_url": upstream_url,
                    "external_id": upstream_accession,
                    "title": "Example Corporation Announces First Quarter Results",
                    "published_at": "2019-05-07T20:30:00Z",
                    "first_known_at": "2019-05-07T20:30:59Z",
                    "expected_sha256": RAW_SHA256,
                    "expected_visible_text_sha256": VISIBLE_SHA256,
                    "material_path": "filing.htm",
                    "content_type": "text/html",
                    "retrieval_provenance": {
                        "mode": "externally_acquired_sha_pinned_fixture",
                        "transport_is_not_source_authority": True,
                        "upstream_announcement": {
                            "issuer": "Example Corporation",
                            "system": "SEC EDGAR",
                            "external_id": upstream_accession,
                            "title": "Example Corporation Announces First Quarter Results",
                            "original_url": upstream_url,
                        },
                    },
                }
            ],
            "fragments": [
                {
                    "fragment_key": "slower-demand",
                    "document_key": "filing",
                    "excerpt": TEXT,
                    "claim_context": {
                        "claim_role": "management_expectation",
                        "known_time": {
                            "upper_bound": "2019-05-07T20:30:59Z",
                            "precision": "minute",
                            "basis": "authoritative_redistributor_publication_time",
                        },
                    },
                }
            ],
            "acceptance": {
                "required_documents": 1,
                "required_fragments": 1,
                "facts_created": 0,
                "judgments_created": 0,
            },
        }
        spec_path = root / "spec.json"
        output_path = root / "execution.json"
        spec_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

        environment = os.environ.copy()
        environment["LONGCYCLE_BLOB_BACKEND"] = "filesystem"
        environment["LONGCYCLE_BLOB_ROOT"] = str(blob_root)
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/execute_grounded_evidence_spec.py",
                str(spec_path),
                "--material-root",
                str(material_root),
                "--output",
                str(output_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "materialized grounded evidence execution failed:\n"
                + completed.stdout
                + "\n"
                + completed.stderr
            )

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        if payload.get("ok") is not True:
            raise AssertionError(f"materialized execution did not report success: {payload}")
        result = payload["result"]
        document = result["documents"][0]
        artifact = result["artifacts"][0]
        acceptance = result["acceptance"]
        if result["spec_schema_version"] != "longcycle-grounded-evidence-spec/v2":
            raise AssertionError("materialized execution lost v2 spec identity")
        if document["transport_plugin"] != "materialized_file":
            raise AssertionError("materialized transport identity was not preserved")
        if document["canonical_retrieval_url"] != retrieval_url:
            raise AssertionError("redistributor retrieval URL was replaced by upstream identity")
        if document["original_source_url"] != upstream_url:
            raise AssertionError("upstream original URL was not preserved separately")
        profiles = document["source_authority_profiles"]
        if len(profiles) != 1 or profiles[0]["authority_class"] != "authoritative_redistributor":
            raise AssertionError("redistributor authority profile was not returned by execution")
        if document["content_sha256"] != RAW_SHA256:
            raise AssertionError("raw materialized bytes were not hash preserved")
        if artifact["artifact_type"] != "html-visible-text":
            raise AssertionError("materialized HTML did not use the normal parser artifact path")
        if artifact["artifact_sha256"] != VISIBLE_SHA256:
            raise AssertionError("visible-text parser artifact hash was not preserved")
        if len(result["fragments"]) != 1:
            raise AssertionError("materialized Evidence fragment count mismatch")
        if acceptance["fact_assertions_created"] != 0:
            raise AssertionError("materialized Evidence execution promoted a FactAssertion")
        if acceptance["judgment_assertions_created"] != 0:
            raise AssertionError("materialized Evidence execution promoted a Judgment")

        with psycopg.connect(database_url) as connection:
            row = connection.execute(
                """
                SELECT authority_class, authority_basis, claim_scope
                FROM evidence.source_authority_profiles
                WHERE source_connector_id = %s
                """,
                (document["source_id"],),
            ).fetchone()
        if row != (
            "authoritative_redistributor",
            "verbatim_official_redistribution",
            "legal_disclosure",
        ):
            raise AssertionError(f"source authority profile was not persisted correctly: {row}")

        archived = blob_root / document["blob_key"]
        if archived.read_bytes() != HTML:
            raise AssertionError("content-addressed archive does not contain exact materialized bytes")

    print("MATERIALIZED_GROUNDED_EVIDENCE_SMOKE_PASS")


if __name__ == "__main__":
    main()
