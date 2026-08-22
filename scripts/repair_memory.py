from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MEMORY_ROOT = ROOT / ".longcycle" / "repair-memory"
CARDS_ROOT = MEMORY_ROOT / "invariants"
INDEX_PATH = MEMORY_ROOT / "active-index.json"

CARD_SCHEMA = "longcycle-repair-invariant/v1"
INDEX_SCHEMA = "longcycle-repair-memory-index/v1"
ID_PATTERN = re.compile(r"^RI-[0-9]{4}$")
MAX_CARD_BYTES = 6144
MAX_TEXT = 700
MAX_LIST_ITEM = 320

CARD_KEYS = {
    "schema_version",
    "id",
    "status",
    "kind",
    "severity",
    "title",
    "scope",
    "tags",
    "failure_signature",
    "root_cause",
    "invariant",
    "anti_regression",
    "guards",
    "revisit_when",
    "origin_refs",
    "supersedes",
    "superseded_by",
}
REQUIRED_CARD_KEYS = {
    "schema_version",
    "id",
    "status",
    "kind",
    "severity",
    "title",
    "scope",
    "tags",
    "failure_signature",
    "root_cause",
    "invariant",
    "anti_regression",
    "guards",
    "revisit_when",
    "origin_refs",
    "supersedes",
}
GUARD_KEYS = {"kind", "path", "contains", "description"}
STATUS_VALUES = {"active", "superseded", "retired"}
KIND_VALUES = {"code", "data", "architecture", "process"}
SEVERITY_VALUES = {"low", "medium", "high", "critical"}
GUARD_KINDS = {"test", "schema", "type", "runtime", "protocol"}
EXECUTABLE_OR_STRUCTURAL_GUARDS = {"test", "schema", "type", "runtime"}


class RepairMemoryError(ValueError):
    pass


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RepairMemoryError(f"{_relative(path)} is not valid readable JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RepairMemoryError(f"{_relative(path)} must contain a JSON object")
    return payload


def _require_text(card: dict[str, Any], key: str, *, max_length: int = MAX_TEXT) -> str:
    value = card.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RepairMemoryError(f"{card.get('id', '<unknown>')}: {key} must be nonblank text")
    if len(value) > max_length:
        raise RepairMemoryError(
            f"{card.get('id', '<unknown>')}: {key} exceeds {max_length} characters; distill it"
        )
    return value


def _require_text_list(
    card: dict[str, Any],
    key: str,
    *,
    allow_empty: bool = False,
    max_items: int = 12,
) -> list[str]:
    value = card.get(key)
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "a list" if allow_empty else "a non-empty list"
        raise RepairMemoryError(f"{card.get('id', '<unknown>')}: {key} must be {qualifier}")
    if len(value) > max_items:
        raise RepairMemoryError(
            f"{card.get('id', '<unknown>')}: {key} has more than {max_items} items; consolidate it"
        )
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise RepairMemoryError(f"{card.get('id', '<unknown>')}: {key} contains blank/non-text data")
        if len(item) > MAX_LIST_ITEM:
            raise RepairMemoryError(
                f"{card.get('id', '<unknown>')}: {key} item exceeds {MAX_LIST_ITEM} characters"
            )
        result.append(item)
    if len(set(result)) != len(result):
        raise RepairMemoryError(f"{card.get('id', '<unknown>')}: {key} contains duplicates")
    return result


def _validate_guard(card_id: str, raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise RepairMemoryError(f"{card_id}: every guard must be an object")
    unknown = set(raw) - GUARD_KEYS
    missing = GUARD_KEYS - set(raw)
    if unknown or missing:
        raise RepairMemoryError(
            f"{card_id}: guard keys invalid; missing={sorted(missing)} unknown={sorted(unknown)}"
        )
    kind = raw["kind"]
    if kind not in GUARD_KINDS:
        raise RepairMemoryError(f"{card_id}: unsupported guard kind {kind!r}")
    for key in ("path", "contains", "description"):
        if not isinstance(raw[key], str) or not raw[key].strip():
            raise RepairMemoryError(f"{card_id}: guard {key} must be nonblank text")
        if len(raw[key]) > MAX_LIST_ITEM:
            raise RepairMemoryError(f"{card_id}: guard {key} is too long")
    path = ROOT / raw["path"]
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise RepairMemoryError(f"{card_id}: guard path must stay inside the repository") from exc
    if not path.is_file():
        raise RepairMemoryError(f"{card_id}: guard path does not exist: {raw['path']}")
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise RepairMemoryError(f"{card_id}: guard path must be UTF-8 text: {raw['path']}") from exc
    if raw["contains"] not in content:
        raise RepairMemoryError(
            f"{card_id}: guard marker missing from {raw['path']}: {raw['contains']!r}"
        )
    return {key: str(raw[key]) for key in GUARD_KEYS}


def _validate_card(path: Path, card: dict[str, Any]) -> dict[str, Any]:
    if path.stat().st_size > MAX_CARD_BYTES:
        raise RepairMemoryError(
            f"{_relative(path)} exceeds {MAX_CARD_BYTES} bytes; Repair Memory cards must stay distilled"
        )
    unknown = set(card) - CARD_KEYS
    missing = REQUIRED_CARD_KEYS - set(card)
    if unknown or missing:
        raise RepairMemoryError(
            f"{_relative(path)} card keys invalid; missing={sorted(missing)} unknown={sorted(unknown)}"
        )
    if card["schema_version"] != CARD_SCHEMA:
        raise RepairMemoryError(f"{_relative(path)} has unsupported schema_version")
    card_id = _require_text(card, "id", max_length=7)
    if not ID_PATTERN.fullmatch(card_id):
        raise RepairMemoryError(f"{_relative(path)} has invalid invariant id {card_id!r}")
    if card["status"] not in STATUS_VALUES:
        raise RepairMemoryError(f"{card_id}: unsupported status {card['status']!r}")
    if card["kind"] not in KIND_VALUES:
        raise RepairMemoryError(f"{card_id}: unsupported kind {card['kind']!r}")
    if card["severity"] not in SEVERITY_VALUES:
        raise RepairMemoryError(f"{card_id}: unsupported severity {card['severity']!r}")
    _require_text(card, "title", max_length=160)
    _require_text(card, "failure_signature")
    _require_text(card, "root_cause")
    _require_text(card, "invariant")
    _require_text(card, "revisit_when")
    scopes = _require_text_list(card, "scope", max_items=12)
    _require_text_list(card, "tags", max_items=12)
    _require_text_list(card, "anti_regression", max_items=8)
    _require_text_list(card, "origin_refs", max_items=8)
    _require_text_list(card, "supersedes", allow_empty=True, max_items=8)
    if any(scope.startswith("/") or scope.startswith("../") for scope in scopes):
        raise RepairMemoryError(f"{card_id}: scope patterns must be repository-relative")

    guards = card.get("guards")
    if not isinstance(guards, list) or not guards:
        raise RepairMemoryError(f"{card_id}: active reasoning requires at least one concrete guard")
    if len(guards) > 8:
        raise RepairMemoryError(f"{card_id}: too many guards; consolidate the invariant")
    normalized_guards = [_validate_guard(card_id, guard) for guard in guards]
    if card["status"] == "active" and card["kind"] != "process":
        if not any(guard["kind"] in EXECUTABLE_OR_STRUCTURAL_GUARDS for guard in normalized_guards):
            raise RepairMemoryError(
                f"{card_id}: active non-process invariant needs an executable/structural guard"
            )
    if card["status"] == "superseded":
        superseded_by = card.get("superseded_by")
        if not isinstance(superseded_by, str) or not ID_PATTERN.fullmatch(superseded_by):
            raise RepairMemoryError(f"{card_id}: superseded card requires superseded_by")
    elif card.get("superseded_by") is not None:
        raise RepairMemoryError(f"{card_id}: superseded_by is only valid for superseded cards")

    result = dict(card)
    result["guards"] = normalized_guards
    return result


def load_cards() -> list[tuple[Path, dict[str, Any]]]:
    if not CARDS_ROOT.is_dir():
        raise RepairMemoryError(f"missing Repair Memory directory: {_relative(CARDS_ROOT)}")
    cards: list[tuple[Path, dict[str, Any]]] = []
    ids: set[str] = set()
    for path in sorted(CARDS_ROOT.glob("*.json")):
        card = _validate_card(path, _load_json(path))
        card_id = card["id"]
        if card_id in ids:
            raise RepairMemoryError(f"duplicate Repair Memory invariant id: {card_id}")
        ids.add(card_id)
        cards.append((path, card))
    if not cards:
        raise RepairMemoryError("Repair Memory must contain at least one invariant card")
    known_ids = {card["id"] for _, card in cards}
    for _, card in cards:
        missing = set(card["supersedes"]) - known_ids
        if missing:
            raise RepairMemoryError(f"{card['id']}: supersedes unknown ids {sorted(missing)}")
        if card.get("superseded_by") and card["superseded_by"] not in known_ids:
            raise RepairMemoryError(
                f"{card['id']}: superseded_by references unknown id {card['superseded_by']}"
            )
    return cards


def build_index(cards: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    active = []
    for path, card in cards:
        if card["status"] != "active":
            continue
        active.append(
            {
                "id": card["id"],
                "title": card["title"],
                "kind": card["kind"],
                "severity": card["severity"],
                "scope": card["scope"],
                "tags": card["tags"],
                "card_path": _relative(path),
            }
        )
    active.sort(key=lambda item: item["id"])
    return {
        "schema_version": INDEX_SCHEMA,
        "policy": "Route by path/tag, then load only matching active cards. Git is chronological cold history.",
        "active": active,
    }


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def rebuild_index() -> None:
    cards = load_cards()
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(_canonical_json(build_index(cards)), encoding="utf-8")
    print(f"REPAIR_MEMORY_INDEX_WRITTEN active={sum(card['status'] == 'active' for _, card in cards)}")


def audit() -> None:
    cards = load_cards()
    expected = build_index(cards)
    if not INDEX_PATH.is_file():
        raise RepairMemoryError(f"missing generated Repair Memory index: {_relative(INDEX_PATH)}")
    actual = _load_json(INDEX_PATH)
    if actual != expected:
        raise RepairMemoryError(
            "Repair Memory index is stale; run `python scripts/repair_memory.py rebuild-index`"
        )
    active_count = sum(card["status"] == "active" for _, card in cards)
    print(f"REPAIR_MEMORY_AUDIT_PASS cards={len(cards)} active={active_count}")


def _normalize_repo_path(raw: str) -> str:
    candidate = raw.replace("\\", "/")
    if candidate.startswith("./"):
        candidate = candidate[2:]
    absolute = Path(raw)
    if absolute.is_absolute():
        try:
            candidate = absolute.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            pass
    return candidate


def _matches_scope(path: str, scopes: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in scopes)


def relevant(paths: list[str]) -> None:
    cards = [(path, card) for path, card in load_cards() if card["status"] == "active"]
    normalized = [_normalize_repo_path(path) for path in paths]
    matched: list[tuple[Path, dict[str, Any], list[str]]] = []
    for card_path, card in cards:
        hits = [path for path in normalized if _matches_scope(path, card["scope"])]
        if hits:
            matched.append((card_path, card, hits))
    if not matched:
        print("REPAIR_MEMORY_RELEVANT none")
        return
    print(f"REPAIR_MEMORY_RELEVANT count={len(matched)}")
    for card_path, card, hits in matched:
        print(f"\n[{card['id']}] {card['title']} ({card['severity']}/{card['kind']})")
        print(f"card: {_relative(card_path)}")
        print(f"matched_paths: {', '.join(hits)}")
        print(f"failure: {card['failure_signature']}")
        print(f"root_cause: {card['root_cause']}")
        print(f"invariant: {card['invariant']}")
        print("avoid:")
        for item in card["anti_regression"]:
            print(f"  - {item}")
        print(f"revisit_when: {card['revisit_when']}")
        print("guards:")
        for guard in card["guards"]:
            print(f"  - {guard['kind']}: {guard['path']} — {guard['description']}")


def query(terms: list[str]) -> None:
    needles = [term.casefold() for term in terms if term.strip()]
    if not needles:
        raise RepairMemoryError("query requires at least one nonblank term")
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path, card in load_cards():
        if card["status"] != "active":
            continue
        searchable = "\n".join(
            [
                card["id"],
                card["title"],
                card["failure_signature"],
                card["root_cause"],
                card["invariant"],
                *card["tags"],
                *card["anti_regression"],
            ]
        ).casefold()
        if all(needle in searchable for needle in needles):
            matches.append((path, card))
    if not matches:
        print("REPAIR_MEMORY_QUERY none")
        return
    print(f"REPAIR_MEMORY_QUERY count={len(matches)}")
    for path, card in matches:
        print(f"[{card['id']}] {card['title']} — {_relative(path)}")
        print(f"  invariant: {card['invariant']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit and query bounded Longcycle Repair Memory")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit", help="validate cards, guards and generated active index")
    subparsers.add_parser("rebuild-index", help="regenerate the compact active index")
    relevant_parser = subparsers.add_parser("relevant", help="show active invariants matching repo paths")
    relevant_parser.add_argument("paths", nargs="+", help="repository-relative paths intended for editing")
    query_parser = subparsers.add_parser("query", help="search active invariant rationale by terms")
    query_parser.add_argument("terms", nargs="+", help="terms that must all appear in the card")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.command == "audit":
            audit()
        elif args.command == "rebuild-index":
            rebuild_index()
        elif args.command == "relevant":
            relevant(args.paths)
        elif args.command == "query":
            query(args.terms)
        else:  # pragma: no cover - argparse owns this branch
            raise RepairMemoryError(f"unknown command: {args.command}")
    except RepairMemoryError as exc:
        print(f"REPAIR_MEMORY_ERROR {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
