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

CAPTURE_TEXT = (
    "Faithful visible-text capture says the transaction became effective in February 2024."
)
CAPTURE_BYTES = CAPTURE_TEXT.encode("utf-8")
CAPTURE_SHA256 = hashlib.sha256(CAPTURE_BYTES).hexdigest()


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
        capture_path = material_root / "capture.txt"
        capture_path.write_bytes(CAPTURE_BYTES)

        retrieval_url = (
            "https://www.prnewswire.com/news-releases/materialized-smoke-results-300000000.html"
        )
        upstream_url = "https://www.sec.gov/Archives/edgar/data/0/materialized-smoke.htm"
        upstream_accession = "0000000000-19-000001"
        capture_url = "https://example.com/source/captured.html"
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
                },
                {
                    "key": "direct-visible-capture",
                    "name": "Faithful direct-source visible-text capture smoke",
                    "publisher_domain": "example.com",
                    "kind": "company",
                    "quality_grade": "A",
                    "transport": "materialized",
                    "authority_profiles": [
                        {
                            "claim_scope": "self_statement",
                            "authority_class": "primary_self_statement",
                            "authority_basis": "direct_speaker_record",
                            "rationale": (
                                "The materialized bytes are a faithful visible-text transcription "
                                "of a directly readable publisher page; capture transport does not "
                                "change the publisher's claim-scoped authority."
                            ),
                        }
                    ],
                },
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
                },
                {
                    "key": "visible-text-capture",
                    "vintage_id": "VISIBLE-TEXT-CAPTURE-SMOKE-2024Q1",
                    "source_key": "direct-visible-capture",
                    "retrieval_url": capture_url,
                    "original_source_url": capture_url,
                    "external_id": "capture-smoke-2024-02",
                    "title": "Example Direct Source",
                    "published_at": "2024-02-13T12:00:00Z",
                    "first_known_at": "2024-02-13T12:00:30Z",
                    "expected_sha256": CAPTURE_SHA256,
                    "material_path": "capture.txt",
                    "content_type": "text/plain; charset=utf-8",
                    "retrieval_provenance": {
                        "mode": "faithful_visible_text_capture",
                        "capture_mode": "verbatim_visible_text_transcription",
                        "transport_is_not_source_authority": True,
                        "full_readable_source": True,
                        "capture_limitations": [],
                        "original_url": capture_url,
                    },
                },
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
                },
                {
                    "fragment_key": "visible-text-capture-event",
                    "document_key": "visible-text-capture",
                    "excerpt": CAPTURE_TEXT,
                    "claim_context": {
                        "claim_role": "historical_event",
                        "known_time": {
                            "upper_bound": "2024-02-13T12:00:30Z",
                            "precision": "minute",
                            "basis": "direct_source_visible_text_capture",
                        },
                    },
                },
            ],
            "acceptance": {
                "required_documents": 2,
                "required_fragments": 2,
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
        documents = {item["document_key"]: item for item in result["documents"]}
        document = documents["filing"]
        capture_document = documents["visible-text-capture"]
        artifact = next(item for item in result["artifacts"] if item["document_key"] == "filing")
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

        if capture_document["transport_plugin"] != "materialized_file":
            raise AssertionError("visible-text capture did not stay on materialized transport")
        if capture_document["canonical_retrieval_url"] != capture_url:
            raise AssertionError("visible-text capture lost direct source identity")
        if capture_document["content_sha256"] != CAPTURE_SHA256:
            raise AssertionError("visible-text capture bytes were not hash preserved")
        capture_profiles = capture_document["source_authority_profiles"]
        if (
            len(capture_profiles) != 1
            or capture_profiles[0]["authority_class"] != "primary_self_statement"
        ):
            raise AssertionError("visible-text capture lost source authority profile")
        capture_provenance = capture_document["retrieval_provenance"]
        if capture_provenance.get("capture_mode") != "verbatim_visible_text_transcription":
            raise AssertionError("visible-text capture mode was not preserved")
        if capture_provenance.get("transport_is_not_source_authority") is not True:
            raise AssertionError("capture transport was allowed to become source authority")

        if len(result["fragments"]) != 2:
            raise AssertionError("materialized Evidence fragment count mismatch")
        if acceptance["fact_assertions_created"] != 0:
            raise AssertionError("materialized Evidence execution promoted a FactAssertion")
        if acceptance["judgment_assertions_created"] != 0:
            raise AssertionError("materialized Evidence execution promoted a Judgment")

        with psycopg.connect(database_url) as connection:
            filing_row = connection.execute(
                """
                SELECT authority_class, authority_basis, claim_scope
                FROM evidence.source_authority_profiles
                WHERE source_connector_id = %s
                """,
                (document["source_id"],),
            ).fetchone()
            capture_row = connection.execute(
                """
                SELECT authority_class, authority_basis, claim_scope
                FROM evidence.source_authority_profiles
                WHERE source_connector_id = %s
                """,
                (capture_document["source_id"],),
            ).fetchone()
        if filing_row != (
            "authoritative_redistributor",
            "verbatim_official_redistribution",
            "legal_disclosure",
        ):
            raise AssertionError(
                f"source authority profile was not persisted correctly: {filing_row}"
            )
        if capture_row != (
            "primary_self_statement",
            "direct_speaker_record",
            "self_statement",
        ):
            raise AssertionError(
                f"visible-text capture authority profile was not persisted correctly: {capture_row}"
            )

        archived = blob_root / document["blob_key"]
        if archived.read_bytes() != HTML:
            raise AssertionError("content-addressed archive does not contain exact materialized bytes")
        archived_capture = blob_root / capture_document["blob_key"]
        if archived_capture.read_bytes() != CAPTURE_BYTES:
            raise AssertionError("archive does not contain exact visible-text capture bytes")

    print("MATERIALIZED_GROUNDED_EVIDENCE_SMOKE_PASS")


if __name__ == "__main__":
    main()
