# Fresh-Agent Continuity Drill — operator note

Use GitHub issue **#129** as the stable rendezvous for an external fresh-Agent black-box test.

The testing Agent should receive only the issue number/repository and no prior Longcycle chat. It must follow `docs/development/fresh-agent-continuity-drill.md`, test the live active branch resolved through issue #2, and make exactly one repository mutation: its JSON report under `.longcycle/handoff/rehearsals/`.

After the report commit exists, a maintainer should inspect the report against the live subject HEAD and the three large-logic criteria. Do not accept the report's own `PASS` value without reading its `answer_summary`, `reads`, `authority_refs`, and any `unexpected_reads`.
