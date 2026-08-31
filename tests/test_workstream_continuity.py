from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from longcycle.application.workstream_continuity import (
    RemoteAncestryEdge,
    RemoteReferenceFact,
    RemoteWorkstreamFacts,
    WorkstreamContinuityResult,
    WorkstreamCursorV2,
    WorkstreamReservationIdentity,
    WorkstreamReservationV2,
    evaluate_workstream_continuity,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_workstream_continuity.py"
SPEC = importlib.util.spec_from_file_location("audit_workstream_continuity", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
audit_script = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_script)

WORKSTREAM_ID = "banking-domain-v1"
BRANCH = f"workstream/{WORKSTREAM_ID}"
WORKSTREAM_ROOT = f".longcycle/workstreams/{WORKSTREAM_ID}"
CURSOR_PATH = f"{WORKSTREAM_ROOT}/cursor.json"
VERIFICATION_REF = f"{WORKSTREAM_ROOT}/receipts/verification.json"
RECEIPT_REF = f"{WORKSTREAM_ROOT}/receipts/delivery.json"

SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40
SHA_D = "d" * 40
OID = "e" * 40

PARENT_REFS = (
    "terminal_mission=STRATEGIC_COMPASS.md#terminal-mission",
    "long_term_direction=STRATEGIC_COMPASS.md#long-term-direction",
    "medium_term_goal=.longcycle/handoff/current.json#strategic_horizon.medium_term_goal",
    "short_term_goal=.longcycle/handoff/current.json#strategic_horizon.short_term_goal",
    f"workstream_goal={WORKSTREAM_ROOT}/reservation.json#goal",
)


def _reservation(*, assignment_epoch: int = 1) -> WorkstreamReservationV2:
    return WorkstreamReservationV2(
        schema_version="longcycle-workstream-reservation/v2",
        workstream_id=WORKSTREAM_ID,
        kind="industry",
        branch=BRANCH,
        base_main_sha=SHA_D,
        baseline="architecture-v1",
        intent_id="BANKING-DOMAIN-V1-001",
        change_contract_path=f"{WORKSTREAM_ROOT}/change-contract.json",
        capability_admission_path=f"{WORKSTREAM_ROOT}/capability-admission.json",
        integration_lane="parallel",
        parent_goal_ref=".longcycle/handoff/current.json#strategic_horizon.medium_term_goal",
        goal="Prove one bounded banking industry-memory trajectory.",
        done_when="The trajectory replays without lookahead and remains traceable.",
        exclusive_write_prefixes=("src/banking", "tests/banking"),
        target_capability_ids=("CAP-0009",),
        dependencies=(),
        reservation_revision=1,
        assignment_epoch=assignment_epoch,
        lifecycle_state="active",
        cursor_path=CURSOR_PATH,
    )


def _cursor(
    *,
    checkpoint_sha: str = SHA_A,
    assignment_epoch: int = 1,
    unverified: bool = False,
    verification_head_sha: str | None = SHA_A,
    verification_refs: tuple[str, ...] = (VERIFICATION_REF,),
    receipt_refs: tuple[str, ...] = (),
) -> WorkstreamCursorV2:
    return WorkstreamCursorV2(
        schema_version="longcycle-workstream-cursor/v2",
        workstream_id=WORKSTREAM_ID,
        branch=BRANCH,
        reservation_revision=1,
        assignment_epoch=assignment_epoch,
        cursor_sequence=3,
        checkpoint_based_on_head_sha=checkpoint_sha,
        verification_head_sha=verification_head_sha,
        parent_refs=PARENT_REFS,
        last_completed_action="Declared the bounded worker objective.",
        current_task="Implement one bounded banking adapter slice.",
        why_now="It is the next reserved proof in the parallel pilot.",
        task_done_when="The focused adapter contract and tests pass.",
        next_atomic_action="Inspect the adapter fixture and implement its smallest missing case.",
        required_capability="bounded_execution",
        insufficient_capability_action="stop_and_escalate",
        progress_state="partial" if unverified else "in_progress",
        partial_summary="No sufficient exact-head verification was observed." if unverified else None,
        unverified=unverified,
        verification_refs=verification_refs,
        artifact_refs=(),
        integration_request_refs=(),
        receipt_refs=receipt_refs,
    )


def _valid_reference_facts(cursor: WorkstreamCursorV2) -> tuple[RemoteReferenceFact, ...]:
    groups = (
        ("verification", cursor.verification_refs),
        ("artifact", cursor.artifact_refs),
        ("integration_request", cursor.integration_request_refs),
        ("receipt", cursor.receipt_refs),
    )
    return tuple(
        RemoteReferenceFact(
            ref=ref,
            kind=kind,
            state="valid",
            git_blob_oid=OID,
            detail="resolved at exact remote worker head",
        )
        for kind, refs in groups
        for ref in refs
    )


def _remote(
    cursor: WorkstreamCursorV2,
    *,
    head_sha: str | None = None,
    edges: tuple[RemoteAncestryEdge, ...] = (),
    checkpoint_is_ancestor: bool = True,
    ancestry_complete: bool = True,
    reference_facts: tuple[RemoteReferenceFact, ...] | None = None,
    handoff_only_paths: tuple[str, ...] = (CURSOR_PATH,),
    verification_head_exists: bool | None = None,
    verification_head_is_ancestor: bool | None = None,
) -> RemoteWorkstreamFacts:
    if head_sha is None:
        head_sha = cursor.checkpoint_based_on_head_sha
    if cursor.verification_head_sha is not None:
        if verification_head_exists is None:
            verification_head_exists = True
        if verification_head_is_ancestor is None:
            verification_head_is_ancestor = True
    return RemoteWorkstreamFacts(
        authoritative_remote="origin",
        main_ref="refs/heads/main",
        main_head_sha=SHA_D,
        worker_ref=f"refs/heads/{BRANCH}",
        remote_worker_head_sha=head_sha,
        refreshed_from_remote=True,
        checkpoint_is_ancestor=checkpoint_is_ancestor,
        ancestry_complete=ancestry_complete,
        verification_head_exists=verification_head_exists,
        verification_head_is_ancestor_of_checkpoint=verification_head_is_ancestor,
        ancestry_edges=edges,
        handoff_only_paths=handoff_only_paths,
        reference_facts=(_valid_reference_facts(cursor) if reference_facts is None else reference_facts),
    )


def _evaluate(
    cursor: WorkstreamCursorV2,
    *,
    reservation: WorkstreamReservationIdentity | None = None,
    remote: RemoteWorkstreamFacts | None = None,
) -> WorkstreamContinuityResult:
    return evaluate_workstream_continuity(
        reservation=reservation or _reservation(),
        cursor=cursor,
        remote=remote or _remote(cursor),
    )


def test_exact_verified_checkpoint_is_clean() -> None:
    cursor = _cursor()

    result = _evaluate(cursor)

    assert result.status == "CLEAN"
    assert result.can_execute_cursor
    assert not result.requires_handoff_repair
    assert result.verification_head_sha == SHA_A


def test_remote_preflight_requires_complete_main_reservation_authority() -> None:
    projection = WorkstreamReservationIdentity(
        schema_version="longcycle-workstream-reservation/v2",
        workstream_id=WORKSTREAM_ID,
        branch=BRANCH,
        reservation_revision=1,
        assignment_epoch=1,
        lifecycle_state="active",
        cursor_path=CURSOR_PATH,
    ).model_dump(mode="json")

    with pytest.raises(ValidationError):
        WorkstreamReservationV2.model_validate(projection)


def test_cursor_only_acknowledgement_delta_remains_clean() -> None:
    cursor = _cursor()
    edge = RemoteAncestryEdge(
        parent_sha=SHA_A,
        commit_sha=SHA_B,
        touched_paths=(CURSOR_PATH,),
    )

    result = _evaluate(cursor, remote=_remote(cursor, head_sha=SHA_B, edges=(edge,)))

    assert result.status == "CLEAN"
    assert result.cursor_only_paths == (CURSOR_PATH,)
    assert result.substantive_paths == ()


def test_pushed_substantive_delta_requires_handoff_recovery() -> None:
    cursor = _cursor()
    edge = RemoteAncestryEdge(
        parent_sha=SHA_A,
        commit_sha=SHA_B,
        touched_paths=(CURSOR_PATH, "src/longcycle/adapters/banking.py"),
    )

    result = _evaluate(cursor, remote=_remote(cursor, head_sha=SHA_B, edges=(edge,)))

    assert result.status == "RECOVERY_REQUIRED"
    assert result.requires_handoff_repair
    assert not result.requires_coordinator
    assert result.substantive_paths == ("src/longcycle/adapters/banking.py",)


def test_remote_preflight_never_claims_to_observe_unpushed_work() -> None:
    cursor = _cursor()

    result = _evaluate(cursor)

    assert result.unpushed_work_observable is False
    assert result.unpushed_work_policy == "retry_current_atomic_action"
    assert result.retry_atomic_action == cursor.next_atomic_action


def test_non_ancestor_checkpoint_is_blocked() -> None:
    cursor = _cursor()
    remote = _remote(
        cursor,
        head_sha=SHA_B,
        checkpoint_is_ancestor=False,
    )

    result = _evaluate(cursor, remote=remote)

    assert result.status == "BLOCKED"
    assert result.requires_coordinator
    assert "checkpoint_not_ancestor" in result.reason_codes


def test_assignment_epoch_mismatch_is_blocked() -> None:
    cursor = _cursor(assignment_epoch=1)

    result = _evaluate(cursor, reservation=_reservation(assignment_epoch=2))

    assert result.status == "BLOCKED"
    assert "assignment_epoch_mismatch" in result.reason_codes


def test_missing_required_receipt_is_blocked() -> None:
    cursor = _cursor(receipt_refs=(RECEIPT_REF,))
    facts = (
        *_valid_reference_facts(_cursor()),
        RemoteReferenceFact(
            ref=RECEIPT_REF,
            kind="receipt",
            state="missing",
            detail="not present at exact worker head",
        ),
    )

    result = _evaluate(cursor, remote=_remote(cursor, reference_facts=facts))

    assert result.status == "BLOCKED"
    assert f"required_receipt_missing:{RECEIPT_REF}" in result.reason_codes


def test_verification_head_must_match_checkpoint_even_when_unverified() -> None:
    with pytest.raises(ValidationError):
        _cursor(
            checkpoint_sha=SHA_B,
            unverified=True,
            verification_head_sha=SHA_A,
        )


def test_missing_exact_verification_commit_is_blocked() -> None:
    cursor = _cursor()
    remote = _remote(
        cursor,
        verification_head_exists=False,
        verification_head_is_ancestor=False,
    )

    result = _evaluate(cursor, remote=remote)

    assert result.status == "BLOCKED"
    assert "verification_head_missing" in result.reason_codes


def test_unverified_checkpoint_may_have_no_verification_refs() -> None:
    cursor = _cursor(
        unverified=True,
        verification_head_sha=None,
        verification_refs=(),
    )

    result = _evaluate(cursor)

    assert result.status == "CLEAN"
    assert result.verification_head_sha is None


def test_unverified_cursor_cannot_enter_the_integration_queue() -> None:
    payload = _cursor(
        unverified=True,
        verification_head_sha=None,
        verification_refs=(),
    ).model_dump(mode="json")
    payload["progress_state"] = "ready_for_integration"

    with pytest.raises(ValidationError):
        WorkstreamCursorV2.model_validate(payload)


@pytest.mark.parametrize(
    ("level", "fake_target"),
    [
        ("terminal_mission", "STRATEGIC_COMPASS.md.evil#mission"),
        ("medium_term_goal", ".longcycle/handoff/current.json.backup#goal"),
        ("workstream_goal", f"{WORKSTREAM_ROOT}/reservation.json.evil#goal"),
    ],
)
def test_parent_refs_cannot_route_to_lookalike_authority_files(
    level: str,
    fake_target: str,
) -> None:
    payload = _cursor().model_dump(mode="json")
    payload["parent_refs"] = [
        f"{level}={fake_target}" if item.startswith(f"{level}=") else item
        for item in payload["parent_refs"]
    ]

    with pytest.raises(ValidationError):
        WorkstreamCursorV2.model_validate(payload)


def test_incomplete_or_uncovered_delta_is_blocked() -> None:
    cursor = _cursor()
    disconnected = RemoteAncestryEdge(
        parent_sha=SHA_C,
        commit_sha=SHA_B,
        touched_paths=(CURSOR_PATH,),
    )

    incomplete = _evaluate(
        cursor,
        remote=_remote(cursor, head_sha=SHA_B, ancestry_complete=False),
    )
    uncovered = _evaluate(
        cursor,
        remote=_remote(cursor, head_sha=SHA_B, edges=(disconnected,)),
    )

    assert incomplete.status == "BLOCKED"
    assert "ancestry_audit_incomplete" in incomplete.reason_codes
    assert uncovered.status == "BLOCKED"
    assert "ancestry_edges_do_not_cover_checkpoint_to_head" in uncovered.reason_codes


def test_handoff_only_policy_cannot_be_broadened_by_caller() -> None:
    cursor = _cursor()
    remote = _remote(
        cursor,
        handoff_only_paths=(CURSOR_PATH, RECEIPT_REF),
    )

    result = _evaluate(cursor, remote=remote)

    assert result.status == "BLOCKED"
    assert "handoff_only_policy_mismatch" in result.reason_codes


@pytest.mark.parametrize(
    ("result", "expected_exit"),
    [
        (_evaluate(_cursor()), 0),
        (
            _evaluate(
                _cursor(),
                remote=_remote(
                    _cursor(),
                    head_sha=SHA_B,
                    edges=(
                        RemoteAncestryEdge(
                            parent_sha=SHA_A,
                            commit_sha=SHA_B,
                            touched_paths=("src/longcycle/adapters/banking.py",),
                        ),
                    ),
                ),
            ),
            1,
        ),
        (
            _evaluate(
                _cursor(),
                remote=_remote(
                    _cursor(),
                    head_sha=SHA_B,
                    checkpoint_is_ancestor=False,
                ),
            ),
            2,
        ),
    ],
)
def test_cli_exit_code_matches_derived_status(
    result: WorkstreamContinuityResult,
    expected_exit: int,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit_script, "audit_remote_workstream", lambda **_kwargs: result)

    exit_code = audit_script.main([WORKSTREAM_ID, "--root", str(tmp_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == expected_exit
    assert payload["status"] == result.status


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def test_cli_refreshes_remote_and_detects_interruption_after_push(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    repo = tmp_path / "producer"
    remote.mkdir()
    repo.mkdir()
    _git(remote, "init", "--bare")
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.name", "Continuity Test")
    _git(repo, "config", "user.email", "continuity@example.invalid")

    reservation_payload = _reservation().model_dump(mode="json")
    _write_json(repo / WORKSTREAM_ROOT / "reservation.json", reservation_payload)
    _write_json(
        repo / ".longcycle/baseline/current.json",
        {
            "schema_version": "longcycle-architecture-baseline-pointer/v1",
            "current_baseline": "architecture-v1",
        },
    )
    _write_json(
        repo / ".longcycle/capabilities/active-index.json",
        {"schema_version": "longcycle-capability-index/v1", "active": [{"id": "CAP-0009"}]},
    )
    _write_json(
        repo / WORKSTREAM_ROOT / "change-contract.json",
        {
            "schema_version": "longcycle-change-contract/v1",
            "intent_id": reservation_payload["intent_id"],
            "baseline": reservation_payload["baseline"],
            "change_level": "L2",
        },
    )
    _write_json(
        repo / WORKSTREAM_ROOT / "capability-admission.json",
        {
            "schema_version": "longcycle-capability-admission/v2",
            "intent_id": reservation_payload["intent_id"],
            "disposition": "extend",
            "target_capability_ids": reservation_payload["target_capability_ids"],
        },
    )
    _write_json(repo / VERIFICATION_REF, {"schema_version": "test-verification/v1", "ok": True})
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "seed worker reservation and verification receipt")
    substantive_sha = _git(repo, "rev-parse", "HEAD")

    cursor = _cursor(
        checkpoint_sha=substantive_sha,
        verification_head_sha=substantive_sha,
    )
    _write_json(repo / CURSOR_PATH, cursor.model_dump(mode="json"))
    _git(repo, "add", CURSOR_PATH)
    _git(repo, "commit", "-m", "acknowledge worker checkpoint")
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "origin", "HEAD:refs/heads/main", f"HEAD:refs/heads/{BRANCH}")

    clean = audit_script.audit_remote_workstream(root=repo, workstream_id=WORKSTREAM_ID)
    assert clean.status == "CLEAN"

    (repo / "local-only.txt").write_text("not durable\n", encoding="utf-8")
    still_clean = audit_script.audit_remote_workstream(root=repo, workstream_id=WORKSTREAM_ID)
    assert still_clean.status == "CLEAN"
    assert still_clean.unpushed_work_observable is False

    implementation = repo / "src" / "banking.py"
    implementation.parent.mkdir(parents=True)
    implementation.write_text("IMPLEMENTED = True\n", encoding="utf-8")
    _git(repo, "add", implementation.relative_to(repo).as_posix())
    _git(repo, "commit", "-m", "partial banking implementation before interruption")
    _git(repo, "push", "origin", f"HEAD:refs/heads/{BRANCH}")

    interrupted = audit_script.audit_remote_workstream(root=repo, workstream_id=WORKSTREAM_ID)
    assert interrupted.status == "RECOVERY_REQUIRED"
    assert interrupted.substantive_paths == ("src/banking.py",)
