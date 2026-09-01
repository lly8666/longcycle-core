from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_memory_seals.py"
SPEC = importlib.util.spec_from_file_location("audit_memory_seals", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)

ARTIFACT_PATH = "research_data/memory/shipping/atlas/atlas.json"
DECISION_PATH = "research_data/memory/shipping/atlas/seal-decision-v1.json"
NEGATIVE_REVIEW = "research_data/memory/shipping/atlas/negative-space-review-v1.json"
CHALLENGER_REVIEW = "research_data/memory/shipping/atlas/challenger-review-v1.json"
PASS_RECEIPTS = (
    "research_data/memory/shipping/atlas/pass-time-v1.json",
    "research_data/memory/shipping/atlas/pass-actors-v1.json",
    "research_data/memory/shipping/atlas/pass-terms-v1.json",
)


def _raw(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")


def _artifact() -> dict[str, Any]:
    return {
        "schema_version": "shipping-blind-memory-atlas/v1",
        "campaign_id": "shipping-1970-present-blind-v1",
        "authority_class": "research_only_model_memory",
        "seal_decision_ref": DECISION_PATH,
        "saturation": {"state": "sealed_for_this_model_vintage"},
    }


def _decision(artifact_raw: bytes) -> dict[str, Any]:
    return {
        "schema_version": audit.SEAL_DECISION_SCHEMA,
        "campaign_id": "shipping-1970-present-blind-v1",
        "shard_id": "whole-industry-atlas",
        "model_vintage": "gpt-5.6-sol@2026-08-31",
        "sealed_artifact_path": ARTIFACT_PATH,
        "sealed_artifact_sha256": hashlib.sha256(artifact_raw).hexdigest(),
        "source_visibility": "none",
        "review": {
            "campaign_stage": "seal_candidate",
            "negative_space_review_complete": True,
            "negative_space_review_ref": NEGATIVE_REVIEW,
            "independent_challenger_complete": True,
            "independent_challenger_ref": CHALLENGER_REVIEW,
            "fresh_search_used": False,
        },
        "has_major_coverage_gaps": False,
        "required_long_tail_families_missing": [],
        "recent_outcomes": [
            {
                "pass_id": "time-pass",
                "family": "time_slice",
                "receipt_ref": PASS_RECEIPTS[0],
                "novel_lead_count": 1,
                "duplicate_lead_count": 8,
                "high_importance_novel_count": 0,
            },
            {
                "pass_id": "actor-pass",
                "family": "actor_gap",
                "receipt_ref": PASS_RECEIPTS[1],
                "novel_lead_count": 1,
                "duplicate_lead_count": 8,
                "high_importance_novel_count": 0,
            },
            {
                "pass_id": "term-pass",
                "family": "terminology_gap",
                "receipt_ref": PASS_RECEIPTS[2],
                "novel_lead_count": 0,
                "duplicate_lead_count": 9,
                "high_importance_novel_count": 0,
            },
        ],
        "declared_result": {
            "saturated": True,
            "reason_codes": ["orthogonal_passes_reached_low_marginal_novelty"],
        },
    }


def _audit(
    artifact: dict[str, Any],
    *,
    decision: dict[str, Any] | None = None,
    supersession: dict[str, Any] | None = None,
) -> tuple[Any, ...]:
    artifact_raw = _raw(artifact)
    available = {
        NEGATIVE_REVIEW,
        CHALLENGER_REVIEW,
        *PASS_RECEIPTS,
        "research_data/memory/shipping/atlas/correction-v1.json",
    }
    payloads: dict[str, tuple[Mapping[str, Any], bytes]] = {
        ARTIFACT_PATH: (artifact, artifact_raw)
    }
    loadable: dict[str, tuple[Mapping[str, Any], bytes]] = dict(payloads)
    if decision is not None:
        decision_raw = _raw(decision)
        payloads[DECISION_PATH] = (decision, decision_raw)
        loadable[DECISION_PATH] = (decision, decision_raw)
        available.add(DECISION_PATH)
    if supersession is not None:
        path = "research_data/memory/shipping/atlas/seal-supersession-v1.json"
        payloads[path] = (supersession, _raw(supersession))
        loadable[path] = payloads[path]
        available.add(path)

    return audit.audit_memory_payloads(
        payloads=payloads,
        load_payload=lambda path: loadable[path],
        reference_exists=lambda path: path in available,
    )


def test_shipping_orientation_shape_is_rejected_without_a_decision() -> None:
    artifact = _artifact()
    artifact.pop("seal_decision_ref")
    findings = _audit(artifact)
    assert len(findings) == 1
    assert findings[0].status == "ERROR"
    assert findings[0].detail == "missing seal_decision_ref"


def test_exact_recomputed_seal_decision_is_authorized() -> None:
    artifact = _artifact()
    findings = _audit(artifact, decision=_decision(_raw(artifact)))
    assert len(findings) == 1
    assert findings[0].status == "AUTHORIZED"


def test_declared_green_cannot_hide_high_importance_novelty() -> None:
    artifact = _artifact()
    decision = _decision(_raw(artifact))
    decision["recent_outcomes"][-1]["high_importance_novel_count"] = 2
    findings = _audit(artifact, decision=decision)
    assert len(findings) == 1
    assert findings[0].status == "ERROR"
    assert "declared_result does not match" in findings[0].detail


def test_exact_append_only_supersession_neutralizes_a_premature_seal() -> None:
    artifact = _artifact()
    artifact.pop("seal_decision_ref")
    artifact_raw = _raw(artifact)
    supersession = {
        "schema_version": audit.SEAL_SUPERSESSION_SCHEMA,
        "campaign_id": "shipping-1970-present-blind-v1",
        "reason_code": "premature_orientation_seal",
        "replacement_stage": "orientation_only",
        "correction_ref": "research_data/memory/shipping/atlas/correction-v1.json",
        "superseded_seals": [
            {
                "artifact_path": ARTIFACT_PATH,
                "artifact_sha256": hashlib.sha256(artifact_raw).hexdigest(),
            }
        ],
    }
    findings = _audit(artifact, supersession=supersession)
    assert len(findings) == 1
    assert findings[0].status == "SUPERSEDED"
    assert "replacement=orientation_only" in findings[0].detail


def test_prose_and_downstream_checks_do_not_trigger_the_narrow_gate() -> None:
    artifact = {
        "note": "The old atlas was sealed and later corrected.",
        "blind_stage": "sealed",
        "checks": {"sealed": True},
        "next_step": "post-seal verification",
    }
    assert audit.find_seal_claims(artifact) == ()


def test_large_ordinary_memory_payload_is_not_a_seal_control_candidate() -> None:
    ordinary = b'{"lead_text":"' + (b"x" * (audit.MAX_MEMORY_CONTROL_BYTES + 1)) + b'"}'
    assert audit.is_memory_control_candidate(ordinary) is False


def test_decision_must_bind_the_exact_artifact_bytes() -> None:
    artifact = _artifact()
    decision = _decision(_raw(artifact))
    changed_artifact = copy.deepcopy(artifact)
    changed_artifact["new_unreviewed_claim"] = "material change after decision"
    findings = _audit(changed_artifact, decision=decision)
    assert len(findings) == 1
    assert findings[0].status == "ERROR"
    assert "exact artifact bytes" in findings[0].detail
