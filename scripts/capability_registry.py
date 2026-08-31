from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_ROOT = ROOT / ".longcycle" / "capabilities"
CARDS_ROOT = CAPABILITY_ROOT / "cards"
INDEX_PATH = CAPABILITY_ROOT / "active-index.json"
ADMISSION_PATH = CAPABILITY_ROOT / "current-admission.json"
HANDOFF_PATH = ROOT / ".longcycle" / "handoff" / "current.json"

CARD_SCHEMA = "longcycle-capability/v1"
INDEX_SCHEMA = "longcycle-capability-index/v1"
ADMISSION_SCHEMA = "longcycle-capability-admission/v2"
MAX_INDEX_BYTES = 64 * 1024
ID_PATTERN = re.compile(r"^CAP-[0-9]{4}$")
SEMANTIC_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
STATUS_VALUES = {"active", "superseded", "retired"}
MATURITY_VALUES = {"experimental", "stable", "core_locked"}
DISPOSITIONS = {"reuse", "extend", "replace", "new"}
ENTRYPOINT_KINDS = {"application", "port", "adapter", "cli", "workflow", "schema", "script"}
GUARD_KINDS = {"test", "type", "runtime", "schema", "protocol"}

GOVERNANCE_MODE = "converging"
GOVERNANCE_HORIZON = {
    "short_term": (
        "Every material capability change discovers existing owners first, records a "
        "reuse/extend/replace/new disposition, and keeps the compact registry in the "
        "default handoff read set."
    ),
    "medium_term": (
        "Keep one semantic owner per stable capability, grow cards only when stable responsibilities change, "
        "and use CI ownership/audit guards to make duplicate parallel implementations increasingly difficult."
    ),
    "long_term": (
        "Promote mature semantic owners to core_locked; overlapping new capabilities require a demonstrated "
        "truthful unmet requirement or an explicit supersession path rather than architectural preference."
    ),
}

CARD_KEYS = {
    "schema_version",
    "id",
    "status",
    "maturity",
    "title",
    "purpose",
    "scope",
    "aliases",
    "tags",
    "owned_semantics",
    "entrypoints",
    "extension_seams",
    "non_goals",
    "guards",
    "revisit_when",
    "supersedes",
    "superseded_by",
}
REQUIRED_CARD_KEYS = CARD_KEYS - {"superseded_by"}
MARKER_KEYS = {"kind", "path", "contains", "description"}
ADMISSION_KEYS = {
    "schema_version",
    "intent_id",
    "intent",
    "governance_mode",
    "disposition",
    "target_capability_ids",
    "closest_existing_capability_ids",
    "rationale_summary",
    "rationale_details_ref",
    "unmet_requirement",
    "evidence_refs",
    "planned_paths",
    "proposed_capability_id",
}


class CapabilityRegistryError(ValueError):
    pass


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityRegistryError(f"{_relative(path)} is not valid readable JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise CapabilityRegistryError(f"{_relative(path)} must contain a JSON object")
    return payload


def _text(payload: dict[str, Any], key: str, *, max_length: int = 800) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CapabilityRegistryError(
            f"{payload.get('id', payload.get('intent_id', '<unknown>'))}: {key} must be nonblank text"
        )
    if len(value) > max_length:
        raise CapabilityRegistryError(f"{key} exceeds {max_length} characters; distill it")
    return value


def _text_list(
    payload: dict[str, Any],
    key: str,
    *,
    allow_empty: bool = False,
    max_items: int = 16,
    max_item_length: int = 320,
) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "a list" if allow_empty else "a non-empty list"
        raise CapabilityRegistryError(
            f"{payload.get('id', payload.get('intent_id', '<unknown>'))}: {key} must be {qualifier}"
        )
    if len(value) > max_items:
        raise CapabilityRegistryError(f"{key} has more than {max_items} items; consolidate it")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise CapabilityRegistryError(f"{key} contains blank/non-text data")
        if len(item) > max_item_length:
            raise CapabilityRegistryError(f"{key} item exceeds {max_item_length} characters")
        result.append(item)
    if len(result) != len(set(result)):
        raise CapabilityRegistryError(f"{key} contains duplicates")
    return result


def _validate_repo_path(raw: str, *, label: str) -> Path:
    if raw.startswith("/") or raw.startswith("../"):
        raise CapabilityRegistryError(f"{label} must be repository-relative: {raw}")
    path = (ROOT / raw).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise CapabilityRegistryError(f"{label} escapes repository: {raw}") from exc
    return path


def _validate_marker(card_id: str, raw: Any, *, entrypoint: bool) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise CapabilityRegistryError(f"{card_id}: marker must be an object")
    if set(raw) != MARKER_KEYS:
        raise CapabilityRegistryError(
            f"{card_id}: marker keys invalid; expected={sorted(MARKER_KEYS)} got={sorted(raw)}"
        )
    allowed = ENTRYPOINT_KINDS if entrypoint else GUARD_KINDS
    kind = raw.get("kind")
    if kind not in allowed:
        raise CapabilityRegistryError(
            f"{card_id}: unsupported {'entrypoint' if entrypoint else 'guard'} kind {kind!r}"
        )
    path_text = raw.get("path")
    contains = raw.get("contains")
    description = raw.get("description")
    if not all(isinstance(value, str) and value.strip() for value in (path_text, contains, description)):
        raise CapabilityRegistryError(
            f"{card_id}: marker path/contains/description must be nonblank text"
        )
    path = _validate_repo_path(path_text, label=f"{card_id} marker path")
    if not path.is_file():
        raise CapabilityRegistryError(f"{card_id}: marker path does not exist: {path_text}")
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise CapabilityRegistryError(
            f"{card_id}: marker path must be UTF-8 text: {path_text}"
        ) from exc
    if contains not in content:
        raise CapabilityRegistryError(
            f"{card_id}: marker missing from {path_text}: {contains!r}"
        )
    return {
        "kind": kind,
        "path": path_text,
        "contains": contains,
        "description": description,
    }


def _validate_card(path: Path, card: dict[str, Any]) -> dict[str, Any]:
    unknown = set(card) - CARD_KEYS
    missing = REQUIRED_CARD_KEYS - set(card)
    if unknown or missing:
        raise CapabilityRegistryError(
            f"{_relative(path)} card keys invalid; missing={sorted(missing)} unknown={sorted(unknown)}"
        )
    if card.get("schema_version") != CARD_SCHEMA:
        raise CapabilityRegistryError(f"{_relative(path)} has unsupported schema_version")
    card_id = _text(card, "id", max_length=8)
    if not ID_PATTERN.fullmatch(card_id):
        raise CapabilityRegistryError(f"{_relative(path)} has invalid capability id {card_id!r}")
    if card.get("status") not in STATUS_VALUES:
        raise CapabilityRegistryError(f"{card_id}: unsupported status {card.get('status')!r}")
    if card.get("maturity") not in MATURITY_VALUES:
        raise CapabilityRegistryError(f"{card_id}: unsupported maturity {card.get('maturity')!r}")
    _text(card, "title", max_length=160)
    _text(card, "purpose")
    scopes = _text_list(card, "scope", max_items=16)
    aliases = _text_list(card, "aliases", max_items=16)
    tags = _text_list(card, "tags", max_items=16)
    semantics = _text_list(card, "owned_semantics", max_items=16)
    extension_seams = _text_list(card, "extension_seams", allow_empty=True, max_items=12)
    non_goals = _text_list(card, "non_goals", allow_empty=True, max_items=12)
    _text(card, "revisit_when")
    supersedes = _text_list(card, "supersedes", allow_empty=True, max_items=12)

    for scope in scopes:
        _validate_repo_path(
            scope.replace("**", "placeholder").replace("*", "placeholder"),
            label=f"{card_id} scope",
        )
    for semantic in semantics:
        if not SEMANTIC_PATTERN.fullmatch(semantic):
            raise CapabilityRegistryError(f"{card_id}: invalid owned semantic key {semantic!r}")
    if card_id in supersedes:
        raise CapabilityRegistryError(f"{card_id}: capability cannot supersede itself")

    entrypoints_raw = card.get("entrypoints")
    if not isinstance(entrypoints_raw, list) or not entrypoints_raw:
        raise CapabilityRegistryError(f"{card_id}: active capability needs at least one entrypoint")
    guards_raw = card.get("guards")
    if not isinstance(guards_raw, list) or not guards_raw:
        raise CapabilityRegistryError(f"{card_id}: active capability needs at least one guard")
    entrypoints = [_validate_marker(card_id, item, entrypoint=True) for item in entrypoints_raw]
    guards = [_validate_marker(card_id, item, entrypoint=False) for item in guards_raw]

    if card.get("status") == "superseded":
        superseded_by = card.get("superseded_by")
        if not isinstance(superseded_by, str) or not ID_PATTERN.fullmatch(superseded_by):
            raise CapabilityRegistryError(f"{card_id}: superseded capability requires superseded_by")
    elif card.get("superseded_by") is not None:
        raise CapabilityRegistryError(
            f"{card_id}: superseded_by is only valid for superseded capability"
        )

    normalized = dict(card)
    normalized["scope"] = scopes
    normalized["aliases"] = aliases
    normalized["tags"] = tags
    normalized["owned_semantics"] = semantics
    normalized["extension_seams"] = extension_seams
    normalized["non_goals"] = non_goals
    normalized["supersedes"] = supersedes
    normalized["entrypoints"] = entrypoints
    normalized["guards"] = guards
    return normalized


def load_cards() -> list[tuple[Path, dict[str, Any]]]:
    if not CARDS_ROOT.is_dir():
        raise CapabilityRegistryError(
            f"missing capability cards directory: {_relative(CARDS_ROOT)}"
        )
    cards: list[tuple[Path, dict[str, Any]]] = []
    ids: set[str] = set()
    for path in sorted(CARDS_ROOT.glob("*.json")):
        card = _validate_card(path, _load_json(path))
        card_id = card["id"]
        if card_id in ids:
            raise CapabilityRegistryError(f"duplicate capability id: {card_id}")
        ids.add(card_id)
        cards.append((path, card))
    if not cards:
        raise CapabilityRegistryError("capability registry must contain at least one card")

    known_ids = {card["id"] for _, card in cards}
    semantic_owner: dict[str, str] = {}
    for _, card in cards:
        missing = set(card["supersedes"]) - known_ids
        if missing:
            raise CapabilityRegistryError(
                f"{card['id']}: supersedes unknown ids {sorted(missing)}"
            )
        if card.get("superseded_by") and card["superseded_by"] not in known_ids:
            raise CapabilityRegistryError(f"{card['id']}: superseded_by references unknown id")
        if card["status"] != "active":
            continue
        for semantic in card["owned_semantics"]:
            previous = semantic_owner.get(semantic)
            if previous is not None:
                raise CapabilityRegistryError(
                    f"duplicate active semantic ownership for {semantic!r}: {previous} and {card['id']}"
                )
            semantic_owner[semantic] = card["id"]
    return cards


def build_index(cards: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    """Build a hot routing index; full capability contracts stay in exact cards."""

    active: list[dict[str, Any]] = []
    for path, card in cards:
        if card["status"] != "active":
            continue
        active.append(
            {
                "id": card["id"],
                "title": card["title"],
                "maturity": card["maturity"],
                "owned_semantics": card["owned_semantics"],
                "card_path": _relative(path),
            }
        )
    active.sort(key=lambda item: item["id"])
    index = {
        "schema_version": INDEX_SCHEMA,
        "governance_mode": GOVERNANCE_MODE,
        "policy": (
            "Discover existing owners before material capability work. Prefer reuse/extend; "
            "new semantic ownership needs a demonstrated unmet requirement. Exact semantic "
            "ownership is unique."
        ),
        "governance_horizon": GOVERNANCE_HORIZON,
        "active": active,
    }
    size = len(_canonical_json(index).encode("utf-8"))
    if size > MAX_INDEX_BYTES:
        raise CapabilityRegistryError(
            f"capability active-index is {size} bytes; hot router limit is {MAX_INDEX_BYTES}; "
            "keep detail in exact capability cards"
        )
    return index


def rebuild_index() -> None:
    """Developer generator: cards are canonical; active-index is derived."""

    cards = load_cards()
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(_canonical_json(build_index(cards)), encoding="utf-8")
    print(
        f"CAPABILITY_INDEX_WRITTEN active={sum(card['status'] == 'active' for _, card in cards)}"
    )


def _index_diff(actual: dict[str, Any], expected: dict[str, Any]) -> str:
    actual_lines = _canonical_json(actual).splitlines(keepends=True)
    expected_lines = _canonical_json(expected).splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            actual_lines,
            expected_lines,
            fromfile="repository active-index.json",
            tofile="generated from capability cards",
        )
    )


def _validate_reference(value: str, *, label: str) -> None:
    if value.startswith(("issue:", "commit:", "ci:", "receipt:")):
        return
    path = _validate_repo_path(value, label=label)
    if not path.exists():
        raise CapabilityRegistryError(f"{label} does not exist: {value}")


def validate_admission(active_cards: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not ADMISSION_PATH.is_file():
        raise CapabilityRegistryError(
            f"missing current capability admission: {_relative(ADMISSION_PATH)}"
        )
    payload = _load_json(ADMISSION_PATH)
    if set(payload) != ADMISSION_KEYS:
        raise CapabilityRegistryError(
            f"current admission keys invalid; expected={sorted(ADMISSION_KEYS)} got={sorted(payload)}"
        )
    if payload.get("schema_version") != ADMISSION_SCHEMA:
        raise CapabilityRegistryError("current admission has unsupported schema_version")
    _text(payload, "intent_id", max_length=120)
    _text(payload, "intent")
    _text(payload, "rationale_summary", max_length=800)
    rationale_details_ref = _text(payload, "rationale_details_ref", max_length=320)
    _validate_reference(rationale_details_ref, label="rationale details ref")
    if payload.get("governance_mode") != GOVERNANCE_MODE:
        raise CapabilityRegistryError("current admission governance_mode is stale")
    disposition = payload.get("disposition")
    if disposition not in DISPOSITIONS:
        raise CapabilityRegistryError(f"unsupported capability disposition {disposition!r}")

    targets = _text_list(payload, "target_capability_ids", allow_empty=True, max_items=8)
    closest = _text_list(
        payload, "closest_existing_capability_ids", allow_empty=True, max_items=8
    )
    evidence = _text_list(payload, "evidence_refs", allow_empty=True, max_items=12)
    planned = _text_list(payload, "planned_paths", allow_empty=True, max_items=16)
    for capability_id in [*targets, *closest]:
        if capability_id not in active_cards:
            raise CapabilityRegistryError(
                f"admission references inactive/unknown capability {capability_id}"
            )
    for path in planned:
        _validate_repo_path(
            path.replace("**", "placeholder").replace("*", "placeholder"),
            label="planned path",
        )
    for ref in evidence:
        _validate_reference(ref, label="evidence ref")

    unmet = payload.get("unmet_requirement")
    proposed = payload.get("proposed_capability_id")
    if unmet is not None and (not isinstance(unmet, str) or not unmet.strip()):
        raise CapabilityRegistryError("unmet_requirement must be null or nonblank text")
    if proposed is not None and (
        not isinstance(proposed, str) or not ID_PATTERN.fullmatch(proposed)
    ):
        raise CapabilityRegistryError("proposed_capability_id must be null or CAP-NNNN")

    if disposition in {"reuse", "extend"}:
        if not targets:
            raise CapabilityRegistryError(
                f"{disposition} admission requires target_capability_ids"
            )
        if proposed is not None:
            raise CapabilityRegistryError(
                f"{disposition} admission cannot propose a new capability id"
            )
        if unmet is not None:
            raise CapabilityRegistryError(
                f"{disposition} admission must not claim an unmet requirement"
            )
        if disposition == "extend" and not planned:
            raise CapabilityRegistryError("extend admission requires planned_paths")
    elif disposition == "replace":
        if not targets or proposed is None or not evidence:
            raise CapabilityRegistryError(
                "replace admission requires targets, proposed id and evidence_refs"
            )
    else:
        if proposed is None:
            raise CapabilityRegistryError("new admission requires proposed_capability_id")
        if proposed in active_cards:
            raise CapabilityRegistryError("new admission proposed id already exists")
        if not closest:
            raise CapabilityRegistryError(
                "new admission must identify closest existing capabilities"
            )
        if unmet is None:
            raise CapabilityRegistryError(
                "new admission requires a demonstrated unmet_requirement"
            )
        if not evidence:
            raise CapabilityRegistryError("new admission requires evidence_refs")
        if not planned:
            raise CapabilityRegistryError("new admission requires planned_paths")

    return payload


def validate_handoff() -> None:
    handoff = _load_json(HANDOFF_PATH)
    read_set = handoff.get("resume_read_set")
    if not isinstance(read_set, list):
        raise CapabilityRegistryError("handoff resume_read_set must be a list")
    required = ".longcycle/capabilities/active-index.json"
    if required not in read_set:
        raise CapabilityRegistryError(
            "handoff must keep the compact capability index in resume_read_set so fresh "
            "Agents recover ownership"
        )


def audit() -> None:
    """CI/read-only audit: regenerate in memory and compare; never rewrite repository state."""

    cards = load_cards()
    expected = build_index(cards)
    if not INDEX_PATH.is_file():
        raise CapabilityRegistryError(
            f"missing generated capability index: {_relative(INDEX_PATH)}; "
            "run `python scripts/capability_registry.py rebuild-index`"
        )
    actual = _load_json(INDEX_PATH)
    if actual != expected:
        diff = _index_diff(actual, expected)
        raise CapabilityRegistryError(
            "capability index is a stale generated artifact; capability cards are canonical. "
            "Run `python scripts/capability_registry.py rebuild-index` and commit the result.\n"
            f"{diff}"
        )
    active_cards = {card["id"]: card for _, card in cards if card["status"] == "active"}
    admission = validate_admission(active_cards)
    validate_handoff()
    print(
        "CAPABILITY_REGISTRY_AUDIT_PASS "
        f"active={len(active_cards)} mode={GOVERNANCE_MODE} "
        f"admission={admission['disposition']}:"
        f"{','.join(admission['target_capability_ids']) or admission['proposed_capability_id']}"
    )


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(
            r"[a-z0-9]+",
            text.casefold().replace("_", " ").replace("-", " ").replace(".", " "),
        )
        if len(token) >= 2
    }


def relevant(query_text: str) -> None:
    query = query_text.strip()
    if not query:
        raise CapabilityRegistryError("relevant requires a nonblank intent/query")
    query_tokens = _tokens(query)
    matches: list[tuple[int, dict[str, Any]]] = []
    for _, card in load_cards():
        if card["status"] != "active":
            continue
        searchable_parts = [
            card["id"],
            card["title"],
            card["purpose"],
            *card["aliases"],
            *card["tags"],
            *card["owned_semantics"],
            *card["extension_seams"],
            *card["non_goals"],
        ]
        searchable = " ".join(searchable_parts)
        tokens = _tokens(searchable)
        score = len(query_tokens & tokens)
        folded_query = query.casefold()
        if any(
            folded_query in part.casefold() or part.casefold() in folded_query
            for part in searchable_parts
            if len(part) > 5
        ):
            score += 4
        if score:
            matches.append((score, card))
    matches.sort(key=lambda item: (-item[0], item[1]["id"]))
    if not matches:
        print("CAPABILITY_RELEVANT none")
        return
    print(f"CAPABILITY_RELEVANT count={min(5, len(matches))}")
    for score, card in matches[:5]:
        print(f"\n[{card['id']}] {card['title']} maturity={card['maturity']} score={score}")
        print(f"purpose: {card['purpose']}")
        print("owned_semantics:")
        for semantic in card["owned_semantics"]:
            print(f"  - {semantic}")
        print("extension_seams:")
        for seam in card["extension_seams"]:
            print(f"  - {seam}")
        print(f"card: .longcycle/capabilities/cards/{card['id']}.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Longcycle stable capability ownership registry"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit")
    subparsers.add_parser("rebuild-index")
    relevant_parser = subparsers.add_parser("relevant")
    relevant_parser.add_argument("query", nargs="+")
    args = parser.parse_args(argv)
    try:
        if args.command == "audit":
            audit()
        elif args.command == "rebuild-index":
            rebuild_index()
        else:
            relevant(" ".join(args.query))
    except CapabilityRegistryError as exc:
        print(f"CAPABILITY_REGISTRY_ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
