# Fresh-chat handoff audit protocol

This protocol is for a genuinely new chat/session that has no access to the previous conversation.

The purpose is to measure whether Longcycle's repository-backed handoff is sufficient for a fresh agent to reconstruct the project's intent, constraints, live execution state, future phase commitments and next action without the user restating any of them.

## Input boundary

The fresh agent should receive only a minimal user instruction identifying the repository and asking it to run the handoff flow. The prompt must not reveal the active branch, PR number, campaign count, current phase, CI result, or next action.

The agent may read GitHub repository state, issues, pull requests, commits, workflow runs, and files as directed by the repository's own bootstrap/handoff mechanism. It must not use public web research to fill project-state gaps.

## Allowed mutation

The audit is read-only except for exactly one final report file requested by the user.

The agent must not:

- change source code, tests, migrations, research data, coverage, checkpoint, PR metadata, issues, labels, branches, or CI configuration;
- continue the Memory Atlas or run fresh historical research;
- repair any inconsistency it discovers;
- merge, close, or otherwise mutate the active PR;
- create any file other than the requested audit report.

If it finds a defect, stale checkpoint, failed CI, or ambiguous state, it records that in the report and stops.

## Required reconstruction

The report should reconstruct, from repository evidence rather than user hints:

1. repository, active branch, active PR, live HEAD and checkpoint base SHA;
2. any live-HEAD delta that must be reconciled after the checkpoint;
3. latest relevant CI run and whether its hard correctness gate is currently trustworthy;
4. project north star and the distinction between Reality, Expectation/Judgment, Outcome, and Model Prior / Memory Atlas;
5. non-negotiable epistemic invariants and forbidden shortcuts;
6. current lithium-battery Memory Campaign phase, raw-lead count, shard count, sealed-shard state, and search visibility;
7. latest coherent milestone already completed;
8. ordered next actions the prior session intended to execute;
9. future phase commitments that are not immediate next actions but must survive until their phase is reached;
10. inconsistencies, stale fields, missing context, or places where the agent had to infer rather than recover;
11. a concise assessment of whether it could safely continue development without asking the user to restate project context.

## State authority classification

For every important recovered conclusion, distinguish which authority class supports it:

- **canonical / immutable** — Git commit graph, raw blind JSONL, archived original evidence, explicit user directives;
- **deterministic-derived** — raw counts, typed validation/index output, machine-reconstructed coverage, live CI outcome;
- **curated research assessment** — novelty labels, gap severity, semantic importance, bridge/satellite promotion and similar research judgments;
- **narrative** — PR body, README and devlog prose.

Do not describe a curated research assessment as mechanically verified merely because it appears in JSON or because a CI test confirms the file is internally consistent. Do not let narrative state override canonical or deterministic-derived state.

## Evidence trail

The report must name the repository resources it actually used, in the order used, and distinguish:

- checkpoint snapshot state;
- live GitHub state;
- state derived directly from canonical/immutable artifacts;
- deterministic-derived state;
- curated research assessment;
- narrative state;
- inference made by the fresh agent.

Do not silently reconcile contradictions. Record both sides and explain which source the handoff protocol says is authoritative.

## Audit verdict

End with six explicit fields:

- `deterministic_state_fidelity`: high / medium / low
- `semantic_plan_recovery_confidence`: high / medium / low
- `reconstruction_confidence`: high / medium / low
- `safe_to_resume_without_user_restatement`: yes / no
- `handoff_defects_found`: count plus short names
- `operations_performed`: must state that the report file was the only mutation

A high-quality report is not one that says everything is healthy. It is one that accurately reconstructs the state, distinguishes machine facts from research judgment, recovers future phase commitments, and surfaces real drift when present.
