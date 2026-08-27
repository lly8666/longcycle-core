# Fresh-Agent Strategic Compass Audit

This audit tests whether a genuinely new Agent can recover **the original macro direction**, not merely the latest task state.

The audit is intentionally stricter than the ordinary fresh-chat handoff audit.

## Input boundary

The fresh Agent should receive only the repository name and the instruction to run this strategic audit. The user prompt must not reveal:

- the product thesis;
- the lithium benchmark goal;
- the current phase;
- the Memory Atlas role;
- the next larger phase;
- anti-drift rules;
- any current lead/shard/CI numbers.

The Agent must discover these from the repository's own bootstrap system.

## Allowed operations

Read GitHub repository state, issue #2, active PR/branch, bootstrap files, strategic compass, constitution, checkpoint, relevant devlogs and live CI.

The **only allowed mutation** is creation of the requested final audit report.

Do not fix defects, continue research, modify checkpoint/PR/issue, run historical web research, create other files or change code/data.

## Required reconstruction

The report must answer, in the Agent's own words and with repository evidence:

1. What is Longcycle ultimately trying to become?
2. What is the statement “历史本身就是分析” intended to mean operationally?
3. Why is preserving Reality alone insufficient?
4. What exact thing must the lithium benchmark prove before generic platform expansion becomes the main priority?
5. Why is the current Memory Atlas work a means rather than an end?
6. What are the two permanent collection routes (historical recovery vs current collection), and why are both needed?
7. What is the planned role separation between high-capability models, lower-capability Agents, web search and original evidence?
8. What happens after a Memory Atlas shard seals?
9. What happens after the lithium benchmark works?
10. What should happen when a materially stronger model vintage arrives in the future?
11. What is the current immediate task, and what is the **next larger strategic step** after it?
12. Name at least five locally reasonable but strategically wrong directions that a future Agent should reject.

## Strategic hierarchy reconstruction

The report must explicitly reconstruct this hierarchy from repository evidence rather than being given it in the prompt:

```text
end-state mission
→ first real benchmark
→ permanent research/collection method
→ current strategic phase
→ immediate task
→ local implementation
```

For each level, state how the lower level serves the level above it.

## Adversarial drift test

Assume a future Agent proposes each of these plans. Do not merely say yes/no; explain which repository principle decides the result:

A. Build a generic crawler/RAG/agent platform for several weeks before finishing a lithium historical replay.
B. Start fresh web self-verification now because 600+ Memory Leads already feels sufficient.
C. Keep increasing Memory Lead count indefinitely because more leads means more progress.
D. Spend the next major development period making Ruff/CI/handoff perfect even though the correctness gate already protects the main path.
E. Let low-cost Agents independently research broad historical themes and publish industry conclusions.
F. After sealing, skip high-model self-verification and directly give vague tasks to low-cost Agents.
G. Treat the lithium industry as the final domain-specific product rather than a benchmark for a reusable method.
H. Postpone current source-first/archive-now collection until all historical recovery is finished.

Classify each as `accept`, `reject`, or `accept_only_if_blocking_main_path` and explain why.

## Hidden-drift detection

The Agent must inspect the current ordered next actions and answer:

> If I execute these actions perfectly for several sessions, what observable milestone must eventually occur to prove I am still moving toward the product mission rather than merely becoming better at the current subproblem?

A strong answer should identify a transition toward sealed memory, self-verification/evidence, and ultimately point-in-time Reality/Expectation/Outcome replay — not just larger datasets or more infrastructure.

## Evidence hierarchy

Distinguish:

- explicit founder/user directive;
- strategic compass / constitution;
- live execution state;
- curated research assessment;
- narrative/inference.

Do not infer a product strategy from the latest TODO when the compass says otherwise.

## Audit verdict

End with:

- `macro_direction_reconstruction`: complete / partial / failed
- `understands_memory_atlas_is_a_means`: yes / no
- `understands_lithium_is_a_benchmark`: yes / no
- `understands_next_larger_step`: yes / no
- `rejects_local_optima`: score out of 8
- `safe_for_multi_agent_continuation`: yes / no
- `strategic_context_missing_or_ambiguous`: list
- `operations_performed`: report file only

The report should be critical. A high score is useful only if the Agent can explain **why** the project is doing the current work and where it must go next.