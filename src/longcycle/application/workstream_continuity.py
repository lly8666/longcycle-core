from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WORKSTREAM_CURSOR_SCHEMA = "longcycle-workstream-cursor/v2"
WORKSTREAM_RESERVATION_SCHEMA = "longcycle-workstream-reservation/v2"
WORKSTREAM_CONTINUITY_RESULT_SCHEMA = "longcycle-workstream-continuity-result/v1"

MAX_CURSOR_BYTES = 16 * 1024
MAX_RESERVATION_BYTES = 16 * 1024
MAX_PARENT_REFS = 8
MAX_POINTER_REFS_PER_KIND = 8
MAX_TOTAL_POINTER_REFS = 24
MAX_ANCESTRY_EDGES = 64
MAX_TOUCHED_PATHS_PER_EDGE = 256
MAX_TOTAL_TOUCHED_PATHS = 1024
MAX_TEXT_LENGTH = 2_000
MAX_REF_LENGTH = 512

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
WORKSTREAM_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
CAPABILITY_ID_PATTERN = re.compile(r"^CAP-[0-9]{4}$")

REQUIRED_PARENT_REF_KEYS = (
    "terminal_mission",
    "long_term_direction",
    "medium_term_goal",
    "short_term_goal",
    "workstream_goal",
)
OPTIONAL_PARENT_REF_KEYS = (
    "methodology",
    "baseline",
    "capability_admission",
)

AgentCapabilityClass = Literal["high_capability_reasoning", "bounded_execution"]
CursorProgressState = Literal[
    "planned",
    "in_progress",
    "partial",
    "verifying",
    "ready_for_integration",
    "blocked",
    "paused",
    "superseded",
]
ReservationLifecycleState = Literal["active", "integrated", "closed"]
ContinuityStatus = Literal["CLEAN", "RECOVERY_REQUIRED", "BLOCKED"]
ReferenceKind = Literal["verification", "artifact", "integration_request", "receipt"]
ReferenceState = Literal["valid", "missing", "invalid"]


def _validate_nonblank_text(value: str, *, label: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must be nonblank")
    if len(normalized) > max_length:
        raise ValueError(f"{label} exceeds {max_length} characters")
    return normalized


def _validate_repo_path(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > MAX_REF_LENGTH:
        raise ValueError(f"{label} must be a nonblank bounded repository-relative path")
    parts = normalized.split("/")
    if (
        "\\" in normalized
        or "\x00" in normalized
        or "*" in normalized
        or ":" in normalized
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError(f"{label} must be a literal POSIX repository path: {value!r}")
    path = PurePosixPath(normalized)
    if path.is_absolute():
        raise ValueError(f"{label} must not escape or ambiguously address the repository: {value!r}")
    return path.as_posix()


def _normalize_ref_tuple(values: Iterable[str], *, label: str) -> tuple[str, ...]:
    normalized = tuple(_validate_repo_path(value, label=label) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{label} contains duplicate paths")
    return normalized


def _parent_ref_map(parent_refs: Iterable[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    allowed = {*REQUIRED_PARENT_REF_KEYS, *OPTIONAL_PARENT_REF_KEYS}
    for raw in parent_refs:
        value = _validate_nonblank_text(raw, label="parent_refs item", max_length=MAX_REF_LENGTH)
        key, separator, target = value.partition("=")
        if not separator or key not in allowed or not target.strip():
            raise ValueError(
                "parent_refs entries must use '<strategic-level>=<authority-ref>' with a known level"
            )
        if key in parsed:
            raise ValueError(f"parent_refs contains duplicate strategic level {key!r}")
        parsed[key] = target.strip()
    missing = set(REQUIRED_PARENT_REF_KEYS) - set(parsed)
    if missing:
        raise ValueError(f"parent_refs is missing five-level authority refs: {sorted(missing)}")
    return parsed


def _targets_authority(ref: str, authority_path: str) -> bool:
    """Accept one authority file, optionally followed by an in-file fragment."""

    return ref == authority_path or ref.startswith(f"{authority_path}#")


class WorkstreamReservationIdentity(BaseModel):
    """Main-owned reservation facts needed to fence one disposable worker."""

    # This is a projection of the full registry-owned reservation. Extra reservation
    # fields remain owned and validated by the registry rather than being duplicated here.
    model_config = ConfigDict(extra="ignore", frozen=True)

    schema_version: Literal["longcycle-workstream-reservation/v2"]
    workstream_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,63}$")
    branch: str = Field(min_length=1, max_length=255)
    reservation_revision: int = Field(ge=1)
    assignment_epoch: int = Field(ge=1)
    lifecycle_state: ReservationLifecycleState
    cursor_path: str

    @field_validator("branch")
    @classmethod
    def branch_is_bounded(cls, value: str) -> str:
        return _validate_nonblank_text(value, label="branch", max_length=255)

    @field_validator("cursor_path")
    @classmethod
    def cursor_path_is_safe(cls, value: str) -> str:
        return _validate_repo_path(value, label="cursor_path")

    @model_validator(mode="after")
    def cursor_belongs_to_workstream(self) -> Self:
        expected = f".longcycle/workstreams/{self.workstream_id}/cursor.json"
        if self.cursor_path != expected:
            raise ValueError(f"cursor_path must be exactly {expected!r}")
        return self


class WorkstreamReservationV2(WorkstreamReservationIdentity):
    """Complete main-owned reservation authority used by remote startup preflight."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["industry", "product", "platform", "research", "governance"]
    base_main_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    baseline: str = Field(min_length=1, max_length=255)
    intent_id: str = Field(min_length=1, max_length=255)
    change_contract_path: str
    capability_admission_path: str
    integration_lane: Literal["parallel", "global_serial"]
    parent_goal_ref: str = Field(min_length=1, max_length=MAX_REF_LENGTH)
    goal: str = Field(min_length=1, max_length=4_096)
    done_when: str = Field(min_length=1, max_length=4_096)
    exclusive_write_prefixes: tuple[str, ...] = Field(max_length=32)
    target_capability_ids: tuple[str, ...] = Field(max_length=16)
    dependencies: tuple[str, ...] = Field(max_length=16)

    @field_validator("baseline", "intent_id", "goal", "done_when")
    @classmethod
    def authority_text_is_nonblank(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "reservation text")
        max_length = 4_096 if field_name in {"goal", "done_when"} else 255
        return _validate_nonblank_text(value, label=str(field_name), max_length=max_length)

    @field_validator("change_contract_path", "capability_admission_path")
    @classmethod
    def authority_paths_are_safe(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "reservation authority path")
        return _validate_repo_path(value, label=str(field_name))

    @field_validator("exclusive_write_prefixes")
    @classmethod
    def write_prefixes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _normalize_ref_tuple(value, label="exclusive_write_prefixes")

    @field_validator("target_capability_ids")
    @classmethod
    def capability_ids_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("target_capability_ids contains duplicates")
        if any(CAPABILITY_ID_PATTERN.fullmatch(item) is None for item in value):
            raise ValueError("target_capability_ids contains an invalid capability id")
        return value

    @field_validator("dependencies")
    @classmethod
    def dependencies_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("dependencies contains duplicates")
        if any(WORKSTREAM_ID_PATTERN.fullmatch(item) is None for item in value):
            raise ValueError("dependencies contains an invalid workstream id")
        return value

    @model_validator(mode="after")
    def complete_authority_is_consistent(self) -> Self:
        root = f".longcycle/workstreams/{self.workstream_id}"
        expected_paths = {
            "cursor_path": f"{root}/cursor.json",
            "change_contract_path": f"{root}/change-contract.json",
            "capability_admission_path": f"{root}/capability-admission.json",
        }
        for field, expected in expected_paths.items():
            if getattr(self, field) != expected:
                raise ValueError(f"{field} must be exactly {expected!r}")
        if not _targets_authority(self.parent_goal_ref, ".longcycle/handoff/current.json"):
            raise ValueError("parent_goal_ref must route to .longcycle/handoff/current.json")
        if self.integration_lane == "parallel":
            expected_branch = f"workstream/{self.workstream_id}"
            if self.branch != expected_branch:
                raise ValueError(f"parallel reservation branch must be exactly {expected_branch!r}")
        elif self.branch == "main":
            raise ValueError("active reservation may not assign a worker directly to main")
        if self.workstream_id in self.dependencies:
            raise ValueError("workstream cannot depend on itself")

        canonical = json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(canonical) > MAX_RESERVATION_BYTES:
            raise ValueError(
                f"workstream reservation exceeds the {MAX_RESERVATION_BYTES}-byte hot-state limit"
            )
        return self


class WorkstreamCursorV2(BaseModel):
    """Bounded branch-local handoff cursor; it is current state, never a session diary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["longcycle-workstream-cursor/v2"]
    workstream_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,63}$")
    branch: str = Field(min_length=1, max_length=255)
    reservation_revision: int = Field(ge=1)
    assignment_epoch: int = Field(ge=1)
    cursor_sequence: int = Field(ge=1)
    checkpoint_based_on_head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    verification_head_sha: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    parent_refs: tuple[str, ...] = Field(min_length=5, max_length=MAX_PARENT_REFS)
    last_completed_action: str | None
    current_task: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    why_now: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    task_done_when: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    next_atomic_action: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    required_capability: AgentCapabilityClass
    insufficient_capability_action: Literal["stop_and_escalate"]
    progress_state: CursorProgressState
    partial_summary: str | None
    unverified: bool
    verification_refs: tuple[str, ...] = Field(max_length=MAX_POINTER_REFS_PER_KIND)
    artifact_refs: tuple[str, ...] = Field(max_length=MAX_POINTER_REFS_PER_KIND)
    integration_request_refs: tuple[str, ...] = Field(max_length=MAX_POINTER_REFS_PER_KIND)
    receipt_refs: tuple[str, ...] = Field(max_length=MAX_POINTER_REFS_PER_KIND)

    @field_validator("branch")
    @classmethod
    def branch_is_bounded(cls, value: str) -> str:
        return _validate_nonblank_text(value, label="branch", max_length=255)

    @field_validator(
        "current_task",
        "why_now",
        "task_done_when",
        "next_atomic_action",
    )
    @classmethod
    def task_text_is_nonblank(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "cursor text")
        return _validate_nonblank_text(value, label=str(field_name))

    @field_validator("last_completed_action", "partial_summary")
    @classmethod
    def optional_text_is_bounded(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        field_name = getattr(info, "field_name", "optional cursor text")
        return _validate_nonblank_text(value, label=str(field_name))

    @field_validator(
        "verification_refs",
        "artifact_refs",
        "integration_request_refs",
        "receipt_refs",
    )
    @classmethod
    def pointer_refs_are_safe(cls, value: tuple[str, ...], info: object) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "pointer refs")
        return _normalize_ref_tuple(value, label=str(field_name))

    @model_validator(mode="after")
    def cursor_is_bounded_and_strategically_linked(self) -> Self:
        parent_refs = _parent_ref_map(self.parent_refs)
        if not _targets_authority(parent_refs["terminal_mission"], "STRATEGIC_COMPASS.md"):
            raise ValueError("terminal_mission must route to STRATEGIC_COMPASS.md")
        if not _targets_authority(parent_refs["long_term_direction"], "STRATEGIC_COMPASS.md"):
            raise ValueError("long_term_direction must route to STRATEGIC_COMPASS.md")
        for key in ("medium_term_goal", "short_term_goal"):
            if not _targets_authority(
                parent_refs[key],
                ".longcycle/handoff/current.json",
            ):
                raise ValueError(f"{key} must route to .longcycle/handoff/current.json")
        expected_reservation = f".longcycle/workstreams/{self.workstream_id}/reservation.json"
        if not _targets_authority(parent_refs["workstream_goal"], expected_reservation):
            raise ValueError(f"workstream_goal must route to {expected_reservation}")

        pointer_groups = (
            self.verification_refs,
            self.artifact_refs,
            self.integration_request_refs,
            self.receipt_refs,
        )
        all_pointers = tuple(path for group in pointer_groups for path in group)
        if len(all_pointers) > MAX_TOTAL_POINTER_REFS:
            raise ValueError(f"cursor pointer refs exceed the total limit of {MAX_TOTAL_POINTER_REFS}")
        if len(all_pointers) != len(set(all_pointers)):
            raise ValueError("one cursor path cannot claim multiple pointer kinds")

        if (self.progress_state == "partial" or self.unverified) and self.partial_summary is None:
            raise ValueError("partial or unverified work requires a bounded partial_summary")

        if self.verification_refs and self.verification_head_sha is None:
            raise ValueError("verification_refs require an exact verification_head_sha")
        if self.verification_head_sha is not None and not self.verification_refs:
            raise ValueError("verification_head_sha requires non-empty verification_refs")
        if (
            self.verification_head_sha is not None
            and self.verification_head_sha != self.checkpoint_based_on_head_sha
        ):
            raise ValueError(
                "verification_head_sha must equal checkpoint_based_on_head_sha; "
                "older-head checks cannot verify the acknowledged checkpoint"
            )
        if not self.unverified:
            if not self.verification_refs:
                raise ValueError("verified work requires non-empty verification_refs")
        if self.progress_state == "ready_for_integration" and self.unverified:
            raise ValueError("ready_for_integration requires exact-head verification")

        canonical = json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(canonical) > MAX_CURSOR_BYTES:
            raise ValueError(f"worker cursor exceeds the {MAX_CURSOR_BYTES}-byte hot-state limit")
        return self


class RemoteAncestryEdge(BaseModel):
    """Paths touched by one parent->commit edge after the cursor checkpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    parent_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    touched_paths: tuple[str, ...] = Field(max_length=MAX_TOUCHED_PATHS_PER_EDGE)

    @field_validator("touched_paths")
    @classmethod
    def touched_paths_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(_normalize_ref_tuple(value, label="touched_paths")))

    @model_validator(mode="after")
    def edge_is_not_a_loop(self) -> Self:
        if self.parent_sha == self.commit_sha:
            raise ValueError("ancestry edge cannot point a commit to itself")
        return self


class RemoteReferenceFact(BaseModel):
    """Exact-worker-head availability/integrity fact for one durable cursor pointer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ref: str
    kind: ReferenceKind
    state: ReferenceState
    git_blob_oid: str | None = Field(default=None, pattern=r"^[0-9a-f]{40,64}$")
    detail: str = Field(min_length=1, max_length=MAX_REF_LENGTH)

    @field_validator("ref")
    @classmethod
    def ref_is_safe(cls, value: str) -> str:
        return _validate_repo_path(value, label="reference fact ref")

    @field_validator("detail")
    @classmethod
    def detail_is_bounded(cls, value: str) -> str:
        return _validate_nonblank_text(value, label="reference fact detail", max_length=MAX_REF_LENGTH)

    @model_validator(mode="after")
    def oid_matches_state(self) -> Self:
        if self.state == "valid" and self.git_blob_oid is None:
            raise ValueError("valid remote reference fact requires its exact Git blob oid")
        if self.state == "missing" and self.git_blob_oid is not None:
            raise ValueError("missing remote reference fact cannot have a Git blob oid")
        return self


class RemoteWorkstreamFacts(BaseModel):
    """Facts refreshed directly from explicit remote refs for one read-only preflight."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authoritative_remote: str = Field(min_length=1, max_length=255)
    main_ref: str = Field(min_length=1, max_length=255)
    main_head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    worker_ref: str = Field(min_length=1, max_length=255)
    remote_worker_head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    refreshed_from_remote: Literal[True]
    checkpoint_is_ancestor: bool
    ancestry_complete: bool
    verification_head_exists: bool | None = None
    verification_head_is_ancestor_of_checkpoint: bool | None = None
    ancestry_edges: tuple[RemoteAncestryEdge, ...] = Field(max_length=MAX_ANCESTRY_EDGES)
    handoff_only_paths: tuple[str, ...] = Field(min_length=1, max_length=MAX_POINTER_REFS_PER_KIND)
    reference_facts: tuple[RemoteReferenceFact, ...] = Field(max_length=MAX_TOTAL_POINTER_REFS)

    @field_validator("authoritative_remote", "main_ref", "worker_ref")
    @classmethod
    def remote_identity_is_bounded(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "remote identity")
        return _validate_nonblank_text(value, label=str(field_name), max_length=255)

    @field_validator("handoff_only_paths")
    @classmethod
    def handoff_paths_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _normalize_ref_tuple(value, label="handoff_only_paths")

    @model_validator(mode="after")
    def remote_facts_are_bounded(self) -> Self:
        edges = tuple((edge.parent_sha, edge.commit_sha) for edge in self.ancestry_edges)
        if len(edges) != len(set(edges)):
            raise ValueError("remote ancestry facts contain duplicate edges")
        touched_count = sum(len(edge.touched_paths) for edge in self.ancestry_edges)
        if touched_count > MAX_TOTAL_TOUCHED_PATHS:
            raise ValueError(f"remote ancestry facts exceed the {MAX_TOTAL_TOUCHED_PATHS}-path audit limit")
        fact_keys = tuple((fact.kind, fact.ref) for fact in self.reference_facts)
        if len(fact_keys) != len(set(fact_keys)):
            raise ValueError("remote reference facts contain duplicate kind/ref pairs")
        return self


class WorkstreamContinuityResult(BaseModel):
    """Derived preflight decision. This result is never persisted as cursor authority."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["longcycle-workstream-continuity-result/v1"]
    audit_only: Literal[True]
    status: ContinuityStatus
    can_execute_cursor: bool
    requires_handoff_repair: bool
    requires_coordinator: bool
    checkpoint_based_on_head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    verification_head_sha: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    remote_worker_head_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    changed_paths: tuple[str, ...]
    cursor_only_paths: tuple[str, ...]
    substantive_paths: tuple[str, ...]
    reason_codes: tuple[str, ...] = Field(min_length=1)
    summary: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    unpushed_work_observable: Literal[False]
    unpushed_work_policy: Literal["retry_current_atomic_action"]
    retry_atomic_action: str = Field(min_length=1)


def _normalized_branch_ref(value: str) -> str:
    prefix = "refs/heads/"
    return value[len(prefix) :] if value.startswith(prefix) else value


def _pointer_expectations(cursor: WorkstreamCursorV2) -> dict[tuple[ReferenceKind, str], None]:
    groups: tuple[tuple[ReferenceKind, tuple[str, ...]], ...] = (
        ("verification", cursor.verification_refs),
        ("artifact", cursor.artifact_refs),
        ("integration_request", cursor.integration_request_refs),
        ("receipt", cursor.receipt_refs),
    )
    return {(kind, ref): None for kind, refs in groups for ref in refs}


def _graph_reaches_head(
    *,
    checkpoint_sha: str,
    remote_head_sha: str,
    edges: tuple[RemoteAncestryEdge, ...],
) -> bool:
    reachable = {checkpoint_sha}
    pending = list(edges)
    made_progress = True
    while pending and made_progress:
        made_progress = False
        next_pending: list[RemoteAncestryEdge] = []
        for edge in pending:
            if edge.parent_sha in reachable:
                reachable.add(edge.commit_sha)
                made_progress = True
            else:
                next_pending.append(edge)
        pending = next_pending
    return remote_head_sha in reachable


def evaluate_workstream_continuity(
    *,
    reservation: WorkstreamReservationIdentity,
    cursor: WorkstreamCursorV2,
    remote: RemoteWorkstreamFacts,
) -> WorkstreamContinuityResult:
    """Derive continuity solely from main reservation, remote Git and durable refs.

    No caller-provided or cursor-persisted status flag participates in this decision.
    The result deliberately cannot observe work that never reached the remote; every
    outcome therefore carries an explicit retry policy for the declared atomic action.
    """

    blocking: list[str] = []

    if reservation.lifecycle_state != "active":
        blocking.append("reservation_not_active")
    if cursor.workstream_id != reservation.workstream_id:
        blocking.append("workstream_identity_mismatch")
    if cursor.branch != reservation.branch:
        blocking.append("reservation_branch_mismatch")
    if _normalized_branch_ref(remote.worker_ref) != reservation.branch:
        blocking.append("remote_worker_ref_mismatch")
    if cursor.reservation_revision != reservation.reservation_revision:
        blocking.append("reservation_revision_mismatch")
    if cursor.assignment_epoch != reservation.assignment_epoch:
        blocking.append("assignment_epoch_mismatch")
    if set(remote.handoff_only_paths) != {reservation.cursor_path}:
        blocking.append("handoff_only_policy_mismatch")
    if not remote.checkpoint_is_ancestor:
        blocking.append("checkpoint_not_ancestor")
    if not remote.ancestry_complete:
        blocking.append("ancestry_audit_incomplete")

    if cursor.verification_head_sha is None:
        if (
            remote.verification_head_exists is not None
            or remote.verification_head_is_ancestor_of_checkpoint is not None
        ):
            blocking.append("unexpected_verification_head_facts")
    else:
        if remote.verification_head_exists is not True:
            blocking.append("verification_head_missing")
        elif remote.verification_head_is_ancestor_of_checkpoint is not True:
            blocking.append("verification_head_not_ancestor_of_checkpoint")

    if remote.checkpoint_is_ancestor and remote.ancestry_complete:
        if cursor.checkpoint_based_on_head_sha == remote.remote_worker_head_sha:
            if remote.ancestry_edges:
                blocking.append("unexpected_edges_at_exact_checkpoint")
        elif not remote.ancestry_edges or not _graph_reaches_head(
            checkpoint_sha=cursor.checkpoint_based_on_head_sha,
            remote_head_sha=remote.remote_worker_head_sha,
            edges=remote.ancestry_edges,
        ):
            blocking.append("ancestry_edges_do_not_cover_checkpoint_to_head")

    expected_facts = _pointer_expectations(cursor)
    observed_facts = {(fact.kind, fact.ref): fact for fact in remote.reference_facts}
    for key in expected_facts:
        fact = observed_facts.get(key)
        if fact is None:
            blocking.append(f"required_{key[0]}_fact_missing:{key[1]}")
        elif fact.state == "missing":
            blocking.append(f"required_{key[0]}_missing:{key[1]}")
        elif fact.state == "invalid":
            blocking.append(f"required_{key[0]}_invalid:{key[1]}")
    unexpected_facts = set(observed_facts) - set(expected_facts)
    if unexpected_facts:
        blocking.append("unexpected_remote_reference_facts")

    changed_paths = tuple(sorted({path for edge in remote.ancestry_edges for path in edge.touched_paths}))
    handoff_only = set(remote.handoff_only_paths)
    cursor_only_paths = tuple(path for path in changed_paths if path in handoff_only)
    substantive_paths = tuple(path for path in changed_paths if path not in handoff_only)

    common = {
        "schema_version": WORKSTREAM_CONTINUITY_RESULT_SCHEMA,
        "audit_only": True,
        "checkpoint_based_on_head_sha": cursor.checkpoint_based_on_head_sha,
        "verification_head_sha": cursor.verification_head_sha,
        "remote_worker_head_sha": remote.remote_worker_head_sha,
        "changed_paths": changed_paths,
        "cursor_only_paths": cursor_only_paths,
        "substantive_paths": substantive_paths,
        "unpushed_work_observable": False,
        "unpushed_work_policy": "retry_current_atomic_action",
        "retry_atomic_action": cursor.next_atomic_action,
    }

    if blocking:
        return WorkstreamContinuityResult(
            **common,
            status="BLOCKED",
            can_execute_cursor=False,
            requires_handoff_repair=False,
            requires_coordinator=True,
            reason_codes=tuple(dict.fromkeys(blocking)),
            summary=(
                "Remote continuity facts are contradictory, incomplete, or outside the active "
                "main reservation; do not continue worker implementation."
            ),
            next_action=(
                "Stop and ask the coordinator to repair the reservation/remote history/durable "
                "reference facts. Work that was never pushed is unknowable; after the remote "
                f"state is safe, retry the declared atomic action: {cursor.next_atomic_action}"
            ),
        )

    if substantive_paths:
        return WorkstreamContinuityResult(
            **common,
            status="RECOVERY_REQUIRED",
            can_execute_cursor=False,
            requires_handoff_repair=True,
            requires_coordinator=False,
            reason_codes=("pushed_substantive_delta_after_cursor_checkpoint",),
            summary=(
                "The remote worker contains pushed substantive work that the branch-local cursor "
                "does not yet acknowledge."
            ),
            next_action=(
                "Do not start new feature work. Inspect every reported ancestry edge, classify the "
                "pushed work as completed/partial/unverified, run bounded verification, then push a "
                "cursor-only handoff acknowledgment and rerun this audit. Any later work that was "
                f"never pushed remains unknowable and must retry: {cursor.next_atomic_action}"
            ),
        )

    return WorkstreamContinuityResult(
        **common,
        status="CLEAN",
        can_execute_cursor=True,
        requires_handoff_repair=False,
        requires_coordinator=False,
        reason_codes=("cursor_checkpoint_matches_remote_or_has_cursor_only_delta",),
        summary=(
            "The active main reservation, exact remote worker history, cursor checkpoint, and "
            "durable pointer facts agree."
        ),
        next_action=(
            "Continue the declared atomic action from the remote cursor. Because local-only work is "
            "not observable, retry this action if a previous attempt never pushed: "
            f"{cursor.next_atomic_action}"
        ),
    )


__all__ = [
    "MAX_ANCESTRY_EDGES",
    "MAX_CURSOR_BYTES",
    "MAX_POINTER_REFS_PER_KIND",
    "MAX_RESERVATION_BYTES",
    "MAX_TOTAL_POINTER_REFS",
    "MAX_TOTAL_TOUCHED_PATHS",
    "MAX_TOUCHED_PATHS_PER_EDGE",
    "WORKSTREAM_CONTINUITY_RESULT_SCHEMA",
    "WORKSTREAM_CURSOR_SCHEMA",
    "WORKSTREAM_ID_PATTERN",
    "WORKSTREAM_RESERVATION_SCHEMA",
    "RemoteAncestryEdge",
    "RemoteReferenceFact",
    "RemoteWorkstreamFacts",
    "WorkstreamContinuityResult",
    "WorkstreamCursorV2",
    "WorkstreamReservationIdentity",
    "WorkstreamReservationV2",
    "evaluate_workstream_continuity",
]
