# Membership equivalent-source corroboration

## Why this is a tightening correction

The first relaxation removed the old structural rule that an industry-membership resolution had to contain exactly one selected assertion. CAP-0005 could then use an auditable semantic judgment to choose a catalog representation when CAP-0003 had selected several source assertions.

That still left one information-loss bug: the final catalog projection inherited `known_at` and supporting Evidence only from the one representative assertion chosen by the semantic judgment. If an earlier source and a later source expressed exactly the same membership semantics, choosing the later row could incorrectly delay historical discoverability and discard valid corroborating Evidence.

In plain language: the system had stopped saying “there may only be one source”, but it was still behaving as though only one source mattered after the choice.

## Correct boundary

Strictness belongs on semantic identity, not on physical row count.

Two selected `industry.membership` assertions are deterministically equivalent only when all of these match exactly:

- subject entity type and entity ID;
- industry node ID;
- membership role;
- exposure type;
- valid-time kind;
- valid-time start and end.

Equivalent assertions form one source-support cluster. The cluster is not a model inference. The application can mechanically determine it from already-selected source assertions.

For the chosen semantic cluster:

- preserve supporting Evidence from every equivalent assertion;
- preserve the earliest source `known_at` as the membership's historical visibility time;
- keep the semantic-decision time separate as `system_from`;
- retain one representative assertion ID for audit/navigation;
- persist the full equivalent `supporting_assertion_ids` set so PostgreSQL readback reconstructs the same provenance.

If candidate assertions differ on any semantic-definition field, they do **not** get merged. They stay on the existing auditable standard-to-deep model judgment path, and unresolved material conflict still fails before catalog write.

## What did not change

This does not relax CAP-0003 reconciliation, Grounded Evidence, valid-time precision, source authority, or no-lookahead. It also does not allow the model to invent a role, entity, industry, timing, Evidence identity, or equivalence relation.

The correction only prevents a later duplicate source from erasing an earlier knowable source or making a historically known membership appear later than it actually became knowable.

The governing rule is therefore:

> multiple source rows are acceptable when they have one deterministic semantic answer; preserve all equivalent source support, and use model judgment only for genuine semantic ambiguity.
