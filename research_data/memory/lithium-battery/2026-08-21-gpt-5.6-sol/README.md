# Lithium Battery Memory Campaign — 2026-08-21 / GPT-5.6 Sol

## Status

`blind_stage: running`

This directory contains unsourced model-memory research artifacts. Nothing here is Fact, Judgment, or Evidence.

## Instrument

- provider: OpenAI / ChatGPT runtime
- model: GPT-5.6 Sol
- model_version: not exposed beyond product model name
- declared_knowledge_cutoff: unknown / not asserted
- campaign_started_at: 2026-08-21T00:53:00+08:00
- source_visibility for blind shards: none
- fresh web search: forbidden until the relevant blind shard/pass is sealed
- protocol: `docs/research/model-memory-exhaustion-protocol.md`
- sharding design: `docs/research/lithium-battery-memory-sharding.md`

## Important epistemic status

Every record under `blind/` is one of:

- a recalled historical lead;
- a recalled actor/project/term;
- an inferred mechanism explicitly marked as inference;
- a search key;
- an uncertain fragment.

It is **not publishable evidence**.

## Directory convention

```text
blind/
  <shard_id>/
    <pass_id>.jsonl
    <pass_id>.meta.json
    shard-index.json
prompts/
  recall-v1.md
  recall-v2.md
analysis/
  prompt-observations.md
  coverage-index.json
self-verification/
  ... only after shard seal
```

## First experiment

Two neighboring shards are intentionally recalled independently:

- `UP-HARDROCK`
- `UP-CHEMICALS`

Neither blind shard may read the other shard's output. After both are sealed, a separate stitch pass may compare only their compressed indexes.

## Checkpoint rule

A pass is committed immediately after generation. A later run resumes from the next incomplete `shard_id/pass_id`; no conversation continuity is required.