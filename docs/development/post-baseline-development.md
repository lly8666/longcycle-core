# Post-Baseline Development

Architecture Baseline v1 changes Longcycle's default engineering posture from architecture exploration to product/domain construction on a stable semantic foundation.

## Before material work

1. Read `.longcycle/baseline/current.json` and the referenced manifest/document.
2. Write/update `.longcycle/change-contract/current.json` with the goal, `L1/L2/L3/L4`, affected Baseline invariants and acceptance criteria.
3. Run existing Capability Registry admission separately and classify semantic ownership as `reuse / extend / replace / new`.
4. Prefer existing owner extension seams. A new industry normally changes Domain Pack/catalog/source/research content, not Evidence/PIT/Reality/Judgment architecture.
5. Query path-scoped Repair Memory before editing known paths.

Change level and capability disposition answer different questions:

```text
change_level         = how close this change is to the frozen Baseline
capability disposition = which existing semantic owner handles the capability
```

Examples:

```text
L1 + reuse    parser bug or implementation refactor
L2 + extend   new industry predicate, unit, API or Domain Pack
L3 + replace  proposed Baseline semantic-owner change after a real counterexample
L4            mission change; explicit user decision required
```

## L1 / L2 normal path

Agents may implement autonomously. They must keep Baseline-critical semantic regressions green and must not change those tests' expected meaning merely to accommodate new code.

A short Change Contract should answer:

```text
Goal:
Baseline/version:
Change level:
Existing capability admission / owners:
Baseline impact:
Affected invariant ids:
Schema impact:
Acceptance:
```

Implementation freedom remains broad: adapters, parsers, UI/CLI/API, domain catalogs, research packets, performance, caches and internal composition may change when the locked semantics remain true.

## L3 architecture pressure

If a real requirement appears to require changing Evidence, Reality/Judgment/Outcome separation, known/valid/system time, no-lookahead, provenance/revision semantics, source authority, source representation states or semantic-owner boundaries:

1. stop ordinary implementation;
2. preserve the concrete source-grounded counterexample or demonstrate the security/consistency defect;
3. identify the Baseline invariant under pressure;
4. show why current extension seams cannot truthfully represent the case;
5. write an Architecture Change Proposal/ADR covering old-data compatibility, migration, PIT/no-lookahead and provenance consequences;
6. obtain explicit architecture review before changing the Baseline and its semantic regressions;
7. release a new Baseline version if approved.

`Cleaner`, `more generic`, `future-proof`, framework preference, fewer classes or one industry convenience are not architecture evidence.

## L4 mission pressure

If the proposal changes why Longcycle exists—for example replacing point-in-time industrial memory with a generic RAG/report platform—stop and obtain an explicit user decision before architecture work.

## Tests

Baseline-critical tests are part of the contract at the level of **semantic expectation**, not frozen file bytes. Mechanical fixture/import updates are permitted under L1/L2. Changing what a protected regression says is correct requires L3/L4.

The focused `.github/workflows/architecture-baseline.yml` gate validates the manifest/change contract and a compact Baseline-critical regression set. `longcycle/full-ci` remains the complete correctness gate.

## Documentation ownership after the freeze

- `STRATEGIC_COMPASS.md`: terminal mission and success criteria.
- `METHODOLOGY_CORE.md`: adopted cross-industry research method.
- `ARCHITECTURE_BASELINE_V1.md` + `.longcycle/baseline/*`: frozen semantic contract and change policy.
- Capability Registry: semantic owners and extension seams.
- `.longcycle/change-contract/current.json`: current change risk classification only.
- `.longcycle/handoff/current.json`: live horizon/cursor.
- code/migrations/tests/live CI: actual implementation state.
- old devlogs, research reports, rehearsal reports and PR discussions: historical provenance; do not rewrite them to match current doctrine.

## Database evolution

Migration `0039` is the schema ceiling at the v1 freeze, not the last migration forever. Post-Baseline migrations are allowed under L1/L2 when they extend implementation/domain capability without changing a locked semantic. Over time, industry knowledge releases should be separated from global schema capability where useful; that cleanup is normal post-Baseline engineering and is not a freeze prerequisite.
