from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


TEXT = "Materialized filing says demand growth was slower than anticipated."
HTML = f"<html><body>{TEXT}</body></html>".encode()
RAW_SHA256 = hashlib.sha256(HTML).hexdigest()
VISIBLE_SHA256 = hashlib.sha256(TEXT.encode()).hexdigest()


def main() -> None:
    if not os.environ.get("LONGCYCLE_DATABASE_URL"):
        raise RuntimeError("LONGCYCLE_DATABASE_URL is required")

    with tempfile.TemporaryDirectory(prefix="longcycle-materialized-smoke-") as temporary:
        root = Path(temporary)
        material_root = root / "material"
        blob_root = root / "blobs"
        material_root.mkdir()
        material_path = material_root / "filing.htm"
        material_path.write_bytes(HTML)

        source_url = "https://www.sec.gov/Archives/edgar/data/0/materialized-smoke.htm"
        spec = {
            "schema_version": "longcycle-grounded-evidence-spec/v2",
            "task_id": "MATERIALIZED-GROUNDED-EVIDENCE-SMOKE-V1",
            "sources": [
                {
                    "key": "regulator",
                    "name": "Materialized grounded evidence smoke regulator",
                    "publisher_domain": "sec.gov",
                    "kind": "regulator",
                    "quality_grade": "A",
                    "transport": "materialized",
                }
            ],
            "documents": [
                {
                    "key": "filing",
                    "vintage_id": "MATERIALIZED-SMOKE-2019Q1",
                    "source_key": "regulator",
                    "retrieval_url": source_url,
                    "original_source_url": source_url,
                    "external_id": "materialized-smoke-2019q1",
                    "title": "Materialized grounded evidence smoke filing",
                    "published_at": "2019-05-07T00:00:00Z",
                    "first_known_at": "2019-05-07T23:59:59Z",
                    "expected_sha256": RAW_SHA256,
                    "expected_visible_text_sha256": VISIBLE_SHA256,
                    "material_path": "filing.htm",
                    "content_type": "text/html",
                    "retrieval_provenance": {
                        "mode": "externally_acquired_sha_pinned_fixture",
                        "transport_is_not_source_authority": True,
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
                            "upper_bound": "2019-05-07T23:59:59Z",
                            "precision": "day",
                            "basis": "source_availability_fixture",
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
        if document["canonical_retrieval_url"] != source_url:
            raise AssertionError("canonical source URL was replaced by transport path")
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

        archived = blob_root / document["blob_key"]
        if archived.read_bytes() != HTML:
            raise AssertionError("content-addressed archive does not contain exact materialized bytes")

    print("MATERIALIZED_GROUNDED_EVIDENCE_SMOKE_PASS")


if __name__ == "__main__":
    main()
