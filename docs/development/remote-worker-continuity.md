# Remote-only Worker Continuity Protocol v1

> Normative extension of `docs/development/session-handoff-protocol.md` for disposable worker Agents. This file is the stable detailed pointer; bootstrap files and prompts should link here instead of copying it.

## 1. Contract

Longcycle roles and workstreams may live for months or years. An individual Agent instance is a short-lived executor and may disappear at any turn boundary.

The continuity contract is therefore:

```text
durable role + main-owned reservation + remote worker ref + branch-local cursor
    > Agent identity, chat history, local checkout or process memory
```

All continuity-bearing work is complete only after it is pushed and re-read from the remote ref. A local checkout is a staging surface, never handoff authority. A returning Agent and a zero-context replacement run the same startup preflight; the protocol does not depend on recognizing which one arrived.

This extends the existing CAP-0009/CAP-0010 control plane. It does not create another history store, semantic-owner registry, scheduler or distributed lock.

## 2. Goal hierarchy without duplication

Every worker must reconstruct the complete causal chain before substantive work:

| Planning level | Stable owner | Worker question |
| --- | --- | --- |
| terminal mission | `STRATEGIC_COMPASS.md` | What lasting researcher capability must Longcycle provide? |
| long-term product direction | `STRATEGIC_COMPASS.md` | What enduring cross-industry system makes that mission scalable? |
| global medium-term proof | `.longcycle/handoff/current.json -> strategic_horizon.medium_term_goal` | What capability is the project proving now? |
| global short-term goal | `.longcycle/handoff/current.json -> strategic_horizon.short_term_goal` | What project milestone currently advances that proof? |
| reserved workstream milestone | main-side `reservation.json -> goal / done_when` | What bounded contribution was this workstream reserved to deliver? |
| current task and immediate next action | remote worker `cursor.json` | What is being done now, why now, what ends it, and what follows? |

Longcycle's project-level hierarchy remains terminal mission -> long-term direction -> global medium-term goal -> global short-term goal -> atomic task. The reservation inserts a durable execution-ownership link between the global short-term goal and the atomic task; it does not replace or shadow the global short-term owner.

The worker does not copy these six links into prose in every cursor. It reads the owning layer and records exact `parent_refs` plus the current task. Stable bootstrap documents carry one pointer to this protocol rather than embedding another copy of its prose.

Before execution, state a concise causal alignment in the session: current task -> reserved workstream milestone -> global short-term goal -> global medium-term proof -> long-term direction -> terminal mission. Persist that statement only when it changes a durable decision; private reasoning and routine alignment checks do not become a diary.

## 3. Remote workstream authority

A v2 workstream has this shape:

```text
.longcycle/workstreams/<workstream-id>/
    reservation.json
    cursor.json
    change-contract.json
    capability-admission.json
    requests/
    receipts/
    escalations/
```

The copy of `reservation.json` on refreshed `main` is the authority for identity, intent, goal, acceptance, scope, owner routing, dependencies, reservation revision, assignment fence and `lifecycle_state`. `lifecycle_state` is exactly `active`, `integrated` or `closed`; only the coordinator/integration lane changes it. A worker may not redefine those facts from its branch.

The copy of `cursor.json` on the refreshed remote worker ref is the authority for execution progress. Its minimum continuation content is:

- workstream identity plus the reservation revision and assignment epoch it accepted;
- monotonically increasing `cursor_sequence`;
- `checkpoint_based_on_head_sha`, which pins the last remote substantive or WIP commit the cursor has accounted for;
- `last_completed_action`, `current_task`, `why_now`, `task_done_when` and `next_atomic_action`;
- truthful `progress_state`: `planned`, `in_progress`, `partial`, `verifying`, `ready_for_integration`, `blocked`, `paused` or `superseded`;
- a bounded `partial_summary` plus the verification triple: explicit `unverified`, nullable exact `verification_head_sha`, and bounded `verification_refs`;
- required capability and the stop/escalate behavior when that capability is unavailable;
- bounded `verification_refs`, `artifact_refs`, `integration_request_refs` and `receipt_refs`.

`checkpoint_based_on_head_sha` and `verification_head_sha` have different meanings. The checkpoint is the substantive/WIP commit whose state the cursor acknowledges. The verification SHA, when present, is the exact commit on which the referenced checks were observed and must equal the checkpoint. Non-empty `verification_refs` require that SHA; an empty verification-ref list requires it to be `null`. `unverified: false` requires the matching SHA and non-empty resolvable refs. `unverified: true` means the checkpoint lacks sufficient observed verification; it may carry no verification (`verification_head_sha: null`, empty refs) or incomplete checks pinned to that same checkpoint, but never an older-head implication. Partial or unverified work requires a truthful bounded `partial_summary`.

`progress_state` describes the work. It is exactly one of `planned`, `in_progress`, `partial`, `verifying`, `ready_for_integration`, `blocked`, `paused` or `superseded`. It is not the handoff-freshness state. `CLEAN`, `RECOVERY_REQUIRED` and `BLOCKED` are always derived from refreshed remote facts and must not be stored as a mutable authoritative flag. In particular, a `blocked` cursor may still be continuity-`CLEAN`, while `ready_for_integration` may still need recovery.

Routine replacement of one Agent instance by another does not create a new permanent role or append an Agent genealogy. `assignment_epoch` changes only when the coordinator deliberately revokes/reassigns the writer fence or changes the reservation, not merely because a normal fresh instance continues the same serialized worker role.

## 4. Mandatory remote startup preflight

Target budget: about two minutes on the normal clean path.

Run the remote audit through the stable entrypoint (options shown explicitly; `origin` and `main` are defaults):

```bash
python scripts/audit_workstream_continuity.py <workstream-id> --remote origin --main-branch main
```

Exit `0` is `CLEAN`, exit `1` is `RECOVERY_REQUIRED`, and exit `2` is `BLOCKED` (including invalid/unavailable remote facts). The command fetches explicit remote refs into audit-only refs and does not treat the local checkout or cached tracking refs as authority.

Before accepting a new task, every worker Agent must:

1. refresh remote `main` and the exact remote worker ref; do not trust a cached tracking ref;
2. load the bounded Strategy/Method/Baseline/global horizon set, the main-side reservation and the branch-local cursor;
3. verify workstream id, branch, Baseline, intent, reservation revision, assignment epoch, owner routing, dependencies and allowed write prefixes;
4. verify that `checkpoint_based_on_head_sha` exists and is an ancestor of the remote worker head;
5. inspect the bounded commit/path delta from that checkpoint to the remote head;
6. verify every hot request/receipt/verification pointer needed by the cursor, and ensure the verification triple is internally consistent;
7. derive exactly one continuity decision below;
8. run the five-level alignment and only then begin or resume substantive work.

Normal worker pushes are fast-forward only. Never force-push a producer branch. If a push is rejected, refresh the remote ref and rerun preflight; do not blindly rebase over an unknown writer.

The automated delta audit is intentionally bounded at 64 ancestry edges, 256 touched paths per edge and 1,024 touched paths total. Exceeding a bound makes ancestry facts incomplete and therefore `BLOCKED`; it does not silently truncate a large unknown delta into `CLEAN`.

### 4.1 Derived decisions

| Decision | Remote facts | Required action |
| --- | --- | --- |
| `CLEAN` | reservation/fence match; checkpoint is reachable; every commit after it is a valid cursor-only acknowledgement represented by the live cursor; required hot pointers are valid | continue the cursor, even when `progress_state` is `partial`, `verifying` or `blocked` |
| `RECOVERY_REQUIRED` | checkpoint is an ancestor, but later remote commits or receipts contain bounded, attributable work the cursor has not yet acknowledged | do no new feature work; run the recovery transaction first |
| `BLOCKED` | checkpoint is missing/non-ancestor; branch or reservation/fence conflicts; delta has an unknown writer or cannot be bounded/classified; required receipt/digest is contradictory; or the only claimed work was never pushed and is unavailable | stop, preserve exact evidence and route the blocker to the coordinator |

A cursor acknowledgement is normally one cursor-only commit after the pinned substantive/WIP commit. The cursor's referenced request/receipt/escalation artifacts are themselves pushed in the preceding S/control-plane increment, then H points to them. This keeps the machine classification unambiguous: H changes exactly the reserved `cursor.json`; merely touching the workstream directory does not make an arbitrary change handoff-only.

`CLEAN` means the remote continuation story is internally complete; it does not mean the product task is finished or fully verified.

## 5. Interrupted-work recovery

The startup gate runs before task classification, including when the user has just supplied a different task.

For `RECOVERY_REQUIRED`:

```text
refresh exact remote refs
-> inspect checkpoint..remote-worker-head commits and paths
-> classify the bounded delta as completed / partial / unrelated / unsafe
-> load only exact owner, Repair Memory and receipt refs needed by that delta
-> run focused validation when possible; otherwise set unverified truthfully, using a null verification_head_sha when no check ran or the current checkpoint SHA when incomplete check refs exist
-> if recovery creates a request/receipt, push it as one bounded S/control-plane increment
-> push one cursor-only H to acknowledge the real remote state and any new refs
-> refresh and re-read the remote worker ref
-> rerun preflight
-> begin new work only after CLEAN
```

The recovery Agent does not need the interrupted Agent's private reasoning. It needs `current_task`, `task_done_when`, the remote diff, tests and durable receipts. When intent is still ambiguous after those facts, choose `partial` with a truthful `partial_summary`, set `unverified: true` and name a concrete inspection next action; do not invent completion.

This transaction is identical for the same Agent returning after interruption and for a zero-context replacement. The returning Agent may remember useful context, but that memory cannot override remote state.

If a new user request supersedes unfinished work, first make the existing remote state handoff-safe. Mark it paused, superseded, partial or blocked rather than pretending it completed, then route the new request through the coordinator/reservation boundary.

### 5.1 The unrecoverable boundary

Work that was never pushed is not recoverable under a remote-only contract. If a still-running environment happens to retain local edits, it may turn them into a coherent WIP commit and push them before proceeding, but no successor may depend on that possibility.

If the environment is gone, restart from the last remote `next_atomic_action`. At most one deliberately small atomic unit should need to be repeated. Never claim that unpushed code, research, decisions or validation were recovered.

## 6. Turn-boundary development slice

There is no mandatory minute count, dialogue count or fixed push cadence. Each invocation still chooses a bounded atomic unit, keeps unpushed work small enough to repeat, validates proportionately and attempts a cursor acknowledgement at a safe closing boundary. A timer never decides correctness or continuity status.

The invariant is startup recovery, not scheduled closure: if an invocation disappears before it writes H, the next invocation detects the pushed delta and repairs that handoff before it interprets or starts any newly supplied task.

### 6.1 Remote micro-push and task H

Use two kinds of remote checkpoint:

- **S -- substantive/WIP push:** a coherent code, research or control-plane increment. WIP is acceptable when its scope and incompleteness are explicit. It bounds potential loss but does not by itself update the continuation story.
- **H -- cursor acknowledgement:** a small follow-up commit that points at the accounted S commit, records truthful progress/validation and names the next atomic action.

Every completed atomic task gets an H. Each invocation attempts H when it reaches a safe closing boundary, even if the task remains partial. Several S pushes may occur inside one atomic task; they need not each trigger a long narrative rewrite. If interruption lands between S and H, the next startup derives `RECOVERY_REQUIRED` and supplies the missing H before new work or a newly supplied task.

The previous H should already name the next atomic action, so normal startup does not require another ceremonial handoff commit. This keeps continuity bounded without making it a second development project.

Worker micro-pushes run focused boundary/schema tests. Full CI belongs at `ready_for_integration` and on the exact serial-integration head unless the change risk requires it earlier.

## 7. External side effects

Git commits are replayable; uploads, deployments, payments and third-party mutations may not be. Before any non-trivially idempotent external side effect:

1. create a typed intent receipt containing operation kind, exact target, request digest, idempotency key, expected result and verification method;
2. push that receipt as S, then push a cursor-only H that references it and re-read the remote ref;
3. execute the side effect with that idempotency key where supported;
4. verify external state and push an outcome receipt as S;
5. acknowledge the result in a cursor-only H.

After interruption between intent and outcome, the successor checks the external system using the recorded key before retrying. It must never infer "not done" merely because the outcome receipt is absent.

### 7.1 Drive database candidates

A Drive-hosted database is never a concurrently writable handoff object. The worker first pins the
main-promoted generation's exact file/revision identity, digest, size and schema revision, verifies
it into private storage and treats the base as read-only. It uploads a new immutable candidate only
after the intent receipt is remote; the outcome is complete only after the new identity and
round-trip digest are observed.

If interruption leaves intent without outcome, startup recovery inspects Drive using recorded
identity or operation metadata/digest before retry. Ambiguity is `BLOCKED`, not permission to upload
again. Candidate upload never advances current state: only the serial integration lane may compare
the base against refreshed main, replay/resolve changes and promote a new generation head. See
`docs/development/parallel-data-plane.md`.

## 8. Vertical Alignment Loop: anti-tunnel control

Run the loop after startup, before a substantive subproblem, after a coherent subtask, before scope expansion and whenever new evidence changes an assumption:

```text
current task / task_done_when
up to main-reserved workstream goal / done_when
up to global short and medium horizons
up to long-term product direction
up to terminal mission
```

Ask:

1. Is `task_done_when` or the workstream `done_when` already met?
2. Will more work materially improve the parent result, or only a local metric/code shape?
3. Has new evidence changed the priority or invalidated the plan?
4. Is the work deepening only because it is interesting or easy to measure?
5. Would stopping now materially harm the researcher-facing result or safe continuity?

When parent-level marginal value collapses, stop, close H and let the coordinator re-rank. A valid local defect does not automatically deserve the remainder of the roadmap. Scope, semantic-owner or dependency changes go through the main reservation; the worker cannot turn curiosity into self-issued authority.

## 9. Independent multi-Agent communication

Chat may help humans observe work, but no worker dependency may require another Agent's chat history.

The consumer writes a typed request under its own `requests/` directory and exposes only that path through the cursor. At minimum the request names:

- stable request id and requesting workstream;
- requested capability/result and why it advances the parent goal;
- inputs/constraints plus semantic-owner and Baseline boundaries;
- machine- or human-checkable acceptance;
- dependency/integration consequence and current status.

The coordinator may satisfy it in the serial lane, expand a reservation, or register a separate product/platform workstream. The provider does not edit the consumer's cursor.

A result becomes consumable only through a typed completion receipt merged by the serial integration lane. That receipt pins the request id, producer workstream/head, integrated main SHA, contract/result refs, `verification_head_sha` plus observed verification refs, limitations and the smallest supported consumption entrypoint. A worker-branch message saying "done" is not a delivery contract.

Consumer startup reads the exact completion receipt referenced by its refreshed reservation/cursor, not all provider history. This permits an industry Agent, a shared-function Agent and their replacement instances to remain mutually independent.

In v1, the machine gate proves that request/receipt pointers are bounded durable blobs on the exact remote head; it does not infer that an arbitrary blob semantically satisfies a request. Until schemas are hardened from the first real Banking/Shipping pilot, the serial integration lane must inspect the required fields above before issuing a completion receipt. Blob existence alone is never completion evidence.

## 10. Bounded growth over years

Hot recovery cost must depend on current active work, never the number of sessions or project age.

| Hot object | Hard operating bound |
| --- | ---: |
| global `current.json` | 64 KiB; at most 5 project/integration lanes |
| global `resume_read_set` | at most 8 files |
| global ordered actions | at most 8 items |
| capability and active-workstream router | 64 KiB each; routing metadata only; at most 64 active workstreams |
| one active `reservation.json` | 16 KiB |
| one active `cursor.json` | 16 KiB |
| reservation routing lists | at most 16 dependencies, 32 write prefixes and 16 capability owners |
| cursor parent refs | at most 8 |
| verification / artifact / integration-request / receipt refs in one cursor | at most 8 of each; at most 24 total |
| one typed request or receipt | 16 KiB; larger evidence lives behind exact refs |

Use three temperatures:

- **Hot:** stable bootstrap pointers, global project horizon, active router, one main reservation, one branch cursor and its unresolved/recent refs.
- **Warm:** exact Capability/Repair Memory cards, active typed requests, completion/validation receipts and current Domain Pack context loaded only when referenced.
- **Cold:** old cursors, completed requests, closed workstreams, devlogs, rehearsal reports, old industry detail, full Git history and external assets.

Rules:

- overwrite current cursor fields; do not append session summaries or Agent genealogies;
- replace completed request/receipt lists with one current delivery/closure pointer;
- remove integrated/closed workstreams from the active router after unresolved dependencies are discharged; preserve a compact closure receipt and let Git retain detail;
- keep large source/research/export payloads outside Git; Git stores bounded identity, schema, locator and digest metadata;
- audit history incrementally from a prior receipt rather than scanning all history on every micro-push;
- schedule workstream cohorts when the active router reaches its byte bound instead of enlarging the default bootstrap;
- retrieve cold history through owner -> Repair Memory -> exact origin refs, then return to live authority.

Linear cold Git history is acceptable. Linear default context, cursor narrative or routine-CI scan cost is not.

## 11. Closure and acceptance

A slice is handoff-complete only when:

1. remote substantive/WIP state is pushed or explicitly absent;
2. verification is truthfully represented by `unverified`, `verification_head_sha` and `verification_refs`;
3. active request/receipt pointers resolve and fit their bounds;
4. H is pushed with the correct checkpoint, progress and next action;
5. the Agent refreshes the remote ref, re-reads the final cursor and derives `CLEAN`;
6. the Vertical Alignment Loop still connects the next action to every parent level.

The proportional test catalogue includes: normal S+H closure; interruption after S but before H; returning-Agent and Fresh-Agent recovery equivalence; unpushed-work loss; non-ancestor checkpoint; reservation/assignment mismatch; concurrent-writer push rejection; missing or contradictory receipt; intent-without-outcome side effect; unsatisfied product dependency; and bounded hot context after many handoffs/closed workstreams. Remote authority, writer fencing, PIT/Baseline preservation and unnoticed pushed work are hard gates. A routine low-risk worker increment need not rerun every catalogue scenario or assert wording, timing and harmless extensible metadata exactly.

The governing rule is:

> Keep the role and repository state durable, keep the Agent disposable, make one atomic unit cheap to repeat, and make every pushed unit impossible to overlook.
