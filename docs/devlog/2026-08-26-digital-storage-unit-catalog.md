# Digital storage unit catalog

## Why this is an extension, not a new subsystem

The enterprise-SSD Reality packet was the first production path to persist a numeric storage-volume assertion and correctly failed when `EB` was not registered. Migration `0036_digital_storage_unit.sql` admitted the one unit required by that source without weakening fail-closed persistence. The next step is to make the existing CAP-0003 catalog durable enough that future TB/PB/EB, TiB/PiB/EiB and bit-oriented source material does not require one migration per observation.

Longcycle already has the right owners: `core.units`, versioned `core.unit_conversion_versions`, the PostgreSQL semantic snapshot, and a fingerprinted normalizer/reconciler runtime. This change extends those seams rather than introducing a parallel units library.

## Scope boundary

This catalog covers **digital information quantity**: bit/byte capacity and volume. It intentionally does not encode throughput (`MB/s`, `GB/s`), IOPS, transfer rate, latency, endurance events or NAND transfer-rate conventions as storage-capacity units. Those are different physical/statistical dimensions and should receive separate predicates/dimensions when source-backed research requires them.

The first batch covers the established mainstream range through yotta/yobi:

- decimal bit quantities: `bit`, `kbit`, `Mbit`, `Gbit`, `Tbit`, `Pbit`, `Ebit`, `Zbit`, `Ybit`;
- decimal byte quantities: `B`, `kB`, `MB`, `GB`, `TB`, `PB`, `EB`, `ZB`, `YB`;
- IEC binary bit quantities: `Kibit`, `Mibit`, `Gibit`, `Tibit`, `Pibit`, `Eibit`, `Zibit`, `Yibit`;
- IEC binary byte quantities: `KiB`, `MiB`, `GiB`, `TiB`, `PiB`, `EiB`, `ZiB`, `YiB`.

Ronna/quetta decimal prefixes are standardized but are not yet needed by the bounded industry cases in this repository. They can be added as adjacent graph edges when a real source requires them, without changing the model.

## Canonical symbols and ambiguity

Canonical symbols are case-sensitive. `GB` is a gigabyte and the common exact spelling `Gb` is a gigabit. Non-standard all-lower-case `gb` is deliberately **not** guessed, because its case-fold family contains both byte and bit meanings. Likewise `KiB` and `Kib` must never become the same value through blanket lower-casing.

Resolution therefore follows this order:

1. exact canonical symbol;
2. exact explicit alias;
3. explicit case-fold alias for unambiguous words such as `gigabytes`;
4. legacy case-fold fallback only when the whole case-fold family has one semantic target;
5. otherwise preserve the raw unit for review and fail closed.

This deliberately makes ambiguous casing such as `KB`, `gb` and `gB` non-canonical: `kB` is the SI kilobyte, exact `kb` is a kilobit alias, `GB` is a gigabyte and exact `Gb` is a gigabit. A source that erases those meaningful case distinctions must not be silently interpreted as decimal bytes, decimal bits or IEC binary bytes.

## Conversion graph

`core.unit_conversion_versions` remains the only conversion owner. The database stores a sparse set of authoritative adjacent edges rather than every possible pair:

- adjacent SI prefixes use multiplier `1000`;
- adjacent IEC prefixes use multiplier `1024`;
- `bit -> B` uses multiplier `0.125`;
- no additive offsets are used for information quantities.

The runtime synthesizes inverse edges and composes transitive paths. With N units the persisted graph remains O(N) rather than O(N²), while TB↔TiB, Gbit↔GB and other same-dimension comparisons are still available.

Runtime graph closure is also a semantic integrity check. If two paths imply different affine transforms for the same unit pair, loading the semantic snapshot fails. The database separately rejects zero multipliers, overlapping active definitions for one directed pair, cross-dimension edges and overlapping aliases.

## Durable conflict policy

`core.unit_alias_versions` stores explicit aliases with valid-time ranges. Exact aliases can intentionally differ only by case. Case-fold aliases are allowed only when they have one semantic target and do not collide with a case-sensitive canonical/alias family. Alias rows join the semantic fingerprint, so changing unit-language resolution changes the normalizer/reconciler version recorded by subsequent assertions.

Unknown and ambiguous unit strings are never silently coerced. They remain source-facing text/metadata and keep the assertion out of automatic canonical publication until the semantic catalog has an explicit decision.

## Standards basis

The design follows NIST SI guidance and IEC binary-prefix conventions summarized by NIST: SI prefixes denote powers of ten and must not be repurposed for powers of two; IEC `Ki/Mi/Gi/Ti/Pi/Ei/Zi/Yi` prefixes denote powers of 1024; one byte is eight bits. SNIA storage benchmarking guidance likewise warns that decimal and binary storage quantities must not be mixed because TB/TiB-scale differences are already material.

## Continuation

After this bounded CAP-0003/CAP-0007 extension is green on a fresh PostgreSQL generation and exact-head CI, resume the seq107 research cursor: build and execute the four-source TrendForce Grounded Evidence packet before projecting its April/August forecasts as Judgment/Expectation and its later quarterly observations as source-scoped Reality.
