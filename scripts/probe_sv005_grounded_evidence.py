from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from collections import defaultdict
from html import unescape
from pathlib import Path

from pypdf import PdfReader

SPEC = Path(
    "research_data/memory/innovative-drugs-adc/2026-08-22-gpt-5.6-sol/"
    "self_verification/run-001/evidence/SV-005-grounded-evidence-spec-v1.json"
)
RELEASE_TAG = "longcycle-dev-binary-cache"
RELEASE_ASSET = "longcycle-adc-sv005-blenrep-pdf-acquisition-v1-run32630536037.zip"
RELEASE_SHA256 = "eb7d858415c0404064364f0fafbcbf4a7bdd7bbf2b4a820696330423c663b998"
MATERIAL_ROOT = Path(".artifacts/sv005-materials")
OUTPUT = Path(".artifacts/SV-005-grounded-evidence-execution.json")
OUT_DIR = Path(".artifacts/out")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def restore_release() -> None:
    release_dir = Path(".artifacts/release")
    shutil.rmtree(release_dir, ignore_errors=True)
    (MATERIAL_ROOT / "pdf").mkdir(parents=True, exist_ok=True)
    (MATERIAL_ROOT / "web").mkdir(parents=True, exist_ok=True)
    release_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "gh",
            "release",
            "download",
            RELEASE_TAG,
            "--repo",
            os.environ["GITHUB_REPOSITORY"],
            "--pattern",
            RELEASE_ASSET,
            "--dir",
            str(release_dir),
        ],
        check=True,
    )
    pack = release_dir / RELEASE_ASSET
    actual = sha256(pack)
    print(f"SV005_RELEASE_SHA actual={actual} expected={RELEASE_SHA256}")
    assert actual == RELEASE_SHA256
    unpacked = release_dir / "unpacked"
    with zipfile.ZipFile(pack) as archive:
        archive.extractall(unpacked)
    shutil.copy2(
        unpacked / "federal-register-blenrep-revocation-2023.pdf",
        MATERIAL_ROOT / "pdf/federal-register-blenrep-revocation-2023.pdf",
    )
    shutil.copy2(
        unpacked / "gsk-dreamm7-readout-2024-02-05.pdf",
        MATERIAL_ROOT / "pdf/gsk-dreamm7-readout-2024-02-05.pdf",
    )


def visible_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "LongcycleEvidenceProbe/0.1 lly8666@users.noreply.github.com",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        assert response.status == 200, (url, response.status)
        raw = response.read()
    decoded = raw.decode("utf-8", errors="replace")
    decoded = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\\1>", " ", decoded)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", decoded)).split())


def materialize_web(spec: dict[str, object]) -> None:
    documents = {row["key"]: row for row in spec["documents"]}  # type: ignore[index]
    fragments_by_doc: dict[str, list[dict[str, object]]] = defaultdict(list)
    for fragment in spec["fragments"]:  # type: ignore[index]
        fragments_by_doc[fragment["document_key"]].append(fragment)

    for key in (
        "fda-initial-approval-2020",
        "gsk-dreamm3-2022",
        "gsk-withdrawal-judgment-2022",
    ):
        document = documents[key]
        page = visible_text(str(document["retrieval_url"]))
        normalized_page = page.casefold()
        excerpts: list[str] = []
        for fragment in fragments_by_doc[key]:
            excerpt = str(fragment["excerpt"])
            normalized_excerpt = " ".join(excerpt.split()).casefold()
            assert normalized_excerpt in normalized_page, (key, fragment["fragment_key"], excerpt)
            excerpts.append(excerpt)
        path = MATERIAL_ROOT / str(document["material_path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(excerpts), encoding="utf-8")
        actual = sha256(path)
        assert actual == document["expected_sha256"], (key, actual, document["expected_sha256"])
        print(f"SV005_WEB_REVERIFY_PASS key={key} sha={actual}")


def verify_material(spec: dict[str, object]) -> None:
    documents = {row["key"]: row for row in spec["documents"]}  # type: ignore[index]
    for document in documents.values():
        path = MATERIAL_ROOT / str(document["material_path"])
        assert path.is_file(), path
        actual = sha256(path)
        assert actual == document["expected_sha256"], (path, actual, document["expected_sha256"])

    for fragment in spec["fragments"]:  # type: ignore[index]
        document = documents[fragment["document_key"]]
        path = MATERIAL_ROOT / str(document["material_path"])
        excerpt = " ".join(str(fragment["excerpt"]).split())
        if document["content_type"] != "application/pdf":
            assert str(fragment["excerpt"]) in path.read_text(encoding="utf-8")
            continue
        reader = PdfReader(io.BytesIO(path.read_bytes()), strict=False)
        page_number = int(fragment["page"])
        page_text = " ".join((reader.pages[page_number - 1].extract_text() or "").split())
        assert excerpt.casefold() in page_text.casefold(), (fragment["fragment_key"], page_number, excerpt)
    print("SV005_MATERIAL_INTEGRITY_PASS")


def execute() -> dict[str, object]:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "scripts/execute_grounded_evidence_spec.py",
            str(SPEC),
            "--material-root",
            str(MATERIAL_ROOT),
            "--output",
            str(OUTPUT),
        ],
        check=True,
    )
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["ok"] is True, payload
    result = payload["result"]
    assert len(result["documents"]) == 5, result
    assert len(result["fragments"]) == 9, result
    assert result["acceptance"] == {
        "persisted_document_versions": 5,
        "persisted_evidence_fragments": 9,
        "fact_assertions_created": 0,
        "judgment_assertions_created": 0,
    }, result["acceptance"]
    documents = {row["document_key"]: row for row in result["documents"]}
    assert documents["fda-initial-approval-2020"]["source_authority_profiles"][0]["authority_class"] == "authoritative_primary"
    assert documents["federal-register-revocation-2023"]["source_authority_profiles"][0]["authority_class"] == "authoritative_primary"
    for key in ("gsk-dreamm3-2022", "gsk-withdrawal-judgment-2022", "gsk-dreamm7-2024"):
        assert documents[key]["source_authority_profiles"][0]["authority_class"] == "primary_self_statement"
    print("SV005_GROUNDED_EVIDENCE_PASS")
    return payload


def build_artifact() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SPEC, OUT_DIR / SPEC.name)
    shutil.copy2(OUTPUT, OUT_DIR / OUTPUT.name)
    files = []
    for path in sorted(OUT_DIR.glob("*.json")):
        files.append({"file_name": path.name, "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest = {
        "schema_version": "longcycle-sv005-evidence-probe-artifact/v1",
        "head_sha": os.environ["SV005_EXPECTED_HEAD"],
        "run_id": int(os.environ["GITHUB_RUN_ID"]),
        "files": files,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    restore_release()
    materialize_web(spec)
    verify_material(spec)
    execute()
    build_artifact()


if __name__ == "__main__":
    main()
