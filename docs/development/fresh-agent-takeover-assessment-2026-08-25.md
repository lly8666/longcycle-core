# Fresh-Agent takeover assessment — 2026-08-25

Status: external ad-hoc takeover assessment completed; remediation required and applied before seq96 handoff freeze.

## Test setup

A genuinely new Agent was started by the user from the original repository/bootstrap prompt. The Agent reported that it:

- did not read the prior chat;
- did not read an existing Fresh-Agent rehearsal/report;
- performed a read-only takeover;
- did not modify the repository, comment on the PR, rerun CI, merge, or download GitHub Actions artifacts.

This is stronger evidence of continuity than a same-Agent artificial-ignorance rehearsal. It is an ad-hoc external assessment; the scheduled every-10-sequence Fresh-Agent drill remains due at sequence 100.

Assessment question used to judge the handoff outcome:

> 如果你是一个完全没看过这段聊天的新 Agent，只读仓库当前 handoff，你能否准确说出 Longcycle 现在在做什么、哪些规则绝不能改、刚刚改了什么、下一步唯一正确的工作顺序是什么？

The external Agent actually followed the repository bootstrap path rather than literally reading only one handoff file, which is the intended production takeover behavior.

## Pre-remediation result

Score: **91 / 100**

- Continuity recovery: **PASS**
- Semantic fidelity: **CONDITIONAL FAIL**
- Overall takeover gate: **not yet sealable before remediation**

### What it recovered correctly

The Agent independently recovered:

1. Longcycle is a point-in-time, evidence-traceable industrial memory rather than a crawler/RAG/report generator.
2. Reality, contemporaneous Judgment/Expectation and later Outcome are separate epistemic layers.
3. Historical recovery is Memory-first, Evidence-final; blind recall must seal before fresh search.
4. Model memory/search/reasoning are research discovery, never publishable Evidence.
5. `not_found != false`, claim-scoped source authority and source-independence rules.
6. no-lookahead and valid/known/target-time separation.
7. bounded/lower-capability Agents are evidence-engineering executors; independent synthesis beyond capability must stop-and-escalate.
8. capability work should reuse/extend existing owners rather than creating parallel semantic owners.
9. source-backed REVIEW/QUARANTINE Reality candidates are researcher-only projection and must not lower canonical Reality thresholds.
10. live Git/CI outrank a stale handoff snapshot. It correctly found that the live branch was ahead of the recorded checkpoint and therefore inspected current CI before starting new storage research.
11. unknowns were left unknown rather than guessed.

That is strong evidence that CAP-0009 continuity preserves mission, authority boundaries, execution ordering and live-state recovery rather than merely replaying a stale TODO list.

## Semantic fidelity defect exposed by the test

The Agent interpreted historical minimum search depth as a fixed requirement even after claim-scoped authoritative original content had directly answered a claim. It stated, in substance, that finding one strong authoritative source could never justify stopping before the configured generic minimum query/source depth.

That interpretation was too strict.

The correct durable rule is:

> **Minimum search depth is an `unresolved-exhaustion` anti-premature-stop gate, not a corroboration/search-count quota for a claim already directly resolved by claim-scoped authoritative original content.**

Therefore:

- an unresolved search must complete the configured minimum query-family/source-type/primary-domain/reverse/citation depth before it may declare `unresolved-exhaustion`;
- `unresolved-exhaustion` remains unresolved, not false and not proof of completeness;
- if the Agent has actually read claim-scoped authoritative original content that directly answers the claim, verified source identity and scope, the task may resolve without mechanically reaching fixed query/source counts;
- high-impact resolved claims retain the configured reverse-query guard;
- citation chains, scope ambiguity, source conflict, or content that does not directly answer the claim still require further investigation;
- source count never substitutes for claim-scoped authority.

Plain-language compression:

> **对“没找到/仍 unresolved”要求搜得够深；对“找到了”要求证据够直接、scope 对得上。多搜不是目标；有足够理由得出你声称的结论才是目标。**

## Why this was a repository defect, not merely an Agent mistake

The Agent's over-strict interpretation was plausible from the then-live repository because execution logic, capability summary language and SOP wording had recently moved through conflicting revisions. The test therefore exposed a real continuity defect: a competent new Agent could recover the high-level rule yet still infer the wrong stop semantics.

This is exactly what the Fresh-Agent mechanism is intended to catch.

## Remediation applied before true handoff

The closeout aligns these layers:

- `src/longcycle/application/memory_campaign.py`
  - `verification_stop_decision(...)` distinguishes authoritative resolution from unresolved exhaustion;
  - full configured depth remains mandatory for unresolved-exhaustion;
  - high-impact resolved claims retain reverse-query protection.
- `tests/test_memory_campaign.py`
  - shallow unresolved exhaustion is rejected;
  - authoritative direct resolution is allowed without fixed search quotas;
  - high-impact reverse-query protection is tested.
- `docs/research/research-agent-sop.md`
  - explicitly separates resolved authoritative content from unresolved-exhaustion;
  - preserves strict anti-premature-stop behavior without creating a search-count KPI.
- `METHODOLOGY_CORE.md`
  - promotes the calibrated rule into the bounded cross-industry method core.
- `docs/development/project-constitution.md`
  - records the same invariant for future sessions.
- `.longcycle/capabilities/cards/CAP-0006.json`
  - guards/non-goals encode the distinction without creating a new semantic owner.
- `.longcycle/capabilities/current-admission.json`
  - records this as an extension/closeout of existing CAP-0005/CAP-0006/CAP-0009/CAP-0010 ownership.

The strict Agent-capability rule is unchanged by this remediation: bounded/lower-capability Agents remain evidence-engineering executors and must stop-and-escalate when a task requires independent synthesis beyond their declared capability.

The REVIEW/QUARANTINE Reality candidate lane is also unchanged: it is research-only visibility over CAP-0003 state via CAP-0005, never a second truth system and never canonical promotion.

## Scoring rubric and result

| Dimension | Score | Assessment |
| --- | ---: | --- |
| Isolation discipline | 10/10 | No old chat/report dependency reported. |
| Live-state recovery | 20/20 | Correct branch/PR/HEAD delta/CI priority. |
| Product mission | 20/20 | Correct point-in-time industrial-memory mission. |
| Capability/owner discipline | 18/20 | Existing-owner model recovered correctly. |
| Next-action ordering | 15/15 | Correctly stopped domain work behind live red CI. |
| Invariant precision | 8/15 | One material over-strict search-stop interpretation. |
| Unknown management | 10/10 | Did not invent unavailable CI root cause or evidence. |
| **Total** | **91/100** | Strong takeover with one semantic-fidelity gate failure. |

## Closure criterion

The external test becomes a successful continuity finding only after:

1. the remediation above is committed;
2. capability generated artifacts/admission are consistent;
3. the exact implementation/governance HEAD passes CI;
4. seq96 handoff is frozen from that verified state and reread for contradictions/stale instructions;
5. the final handoff HEAD is revalidated as live state.

A future Agent must recover both halves of the search rule. If it says either “a shallow not-found is enough to stop” or “every directly resolved claim must mechanically hit 6 query families / 3 source classes”, continuity fidelity has regressed.
