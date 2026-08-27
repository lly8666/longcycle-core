from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class MemoryAuditLens:
    code: str
    instruction: str


MEMORY_AUDIT_LENSES: tuple[MemoryAuditLens, ...] = (
    MemoryAuditLens(
        "historical_landmarks",
        "Recall indispensable events, projects, price regimes, policy changes, and company actions.",
    ),
    MemoryAuditLens(
        "historical_vocabulary",
        "Recall old names, abbreviations, project aliases, metric names, and period-specific search terms.",
    ),
    MemoryAuditLens(
        "pricing_and_contracts",
        "Recall auctions, formula pricing, long-term contracts, premiums, discounts, prepayments, and offtakes.",
    ),
    MemoryAuditLens(
        "effective_supply_bottlenecks",
        "Recall permitting, equipment lead times, commissioning, yield, recovery, qualification, utilities, and logistics.",
    ),
    MemoryAuditLens(
        "inventory_location",
        "Recall where inventory accumulated or was destocked along the physical value chain.",
    ),
    MemoryAuditLens(
        "capital_cycle",
        "Recall financing, capex, fundraising, equipment orders, M&A, cancellations, impairments, and project delays.",
    ),
    MemoryAuditLens(
        "technology_and_unit_intensity",
        "Recall technology substitution, chemistry mix, process changes, yield changes, and unit-material-intensity shifts.",
    ),
    MemoryAuditLens(
        "cross_industry_dependencies",
        "Recall external drivers from energy, chemicals, mining equipment, shipping, grids, finance, trade, and regulation.",
    ),
    MemoryAuditLens(
        "contemporaneous_narratives",
        "Recall what people at the time believed would happen and the reasons they used; do not rewrite this as fact.",
    ),
    MemoryAuditLens(
        "negative_space",
        "Identify missing links that would make the known historical sequence implausibly incomplete.",
    ),
)


def _lens_text() -> str:
    return "\n".join(f"- {lens.code}: {lens.instruction}" for lens in MEMORY_AUDIT_LENSES)


def build_blind_recall_prompt(
    *,
    industry: str,
    period_start: date,
    period_end: date,
) -> str:
    """Build a prior-only prompt that intentionally contains no archive or web material."""

    return f"""You are generating UNSOURCED MODEL-MEMORY LEADS for Longcycle.
Industry: {industry}
Historical period: {period_start.isoformat()} to {period_end.isoformat()}

Critical rules:
1. You have NOT been given current web search results or the Longcycle archive in this run.
2. Do not present recalled material as verified fact.
3. Do not invent citations, URLs, report titles, page numbers, or exact numbers when uncertain.
4. Separate recollection from inference. Mark approximate dates and uncertainty explicitly.
5. The goal is to produce high-value SEARCH LEADS that ordinary keyword collection may miss.
6. Prefer obscure mechanisms, old terminology, cross-chain links, and missing intermediate steps over famous headlines.
7. A strong memory is still not evidence.

Run every audit lens independently:
{_lens_text()}

For each useful lead return:
- lead_kind
- claim_scope
- summary
- approximate period
- recalled details
- possible actors
- possible mechanism
- memory_confidence (self-reported recall strength only, not truth probability)
- importance_score
- novelty_score
- searchability_score
- suggested_queries
- suggested_source_types
- relations to other leads when useful

If you only vaguely remember something, keep it vague and generate search terms instead of fabricating precision.
"""


def build_gap_audit_prompt(
    *,
    industry: str,
    period_start: date,
    period_end: date,
    archive_coverage_summary: str,
) -> str:
    """Build a second-pass prompt that sees archive coverage but not fresh search rankings."""

    if not archive_coverage_summary.strip():
        raise ValueError("archive_coverage_summary must not be blank")

    return f"""You are auditing the COMPLETENESS of an existing Longcycle industry archive.
Industry: {industry}
Historical period: {period_start.isoformat()} to {period_end.isoformat()}

The text below is an ARCHIVE COVERAGE SUMMARY, not fresh web search results:
---
{archive_coverage_summary}
---

Rules:
1. Do not assume the archive is correct merely because a record exists.
2. Do not use hindsight to rewrite what historical actors knew at the time.
3. Do not convert your own memory into a fact or judgment assertion.
4. Look for negative space: missing events, missing mechanisms, missing revisions, missing terminology, and scope mismatches.
5. When your memory conflicts with archive material, output a conflict lead and specify what claim-scoped primary source should arbitrate it.
6. Do not resolve conflicts by source count or web popularity.

Audit through every lens:
{_lens_text()}

Return only actionable memory leads, anomaly leads, search terms, and proposed evidence types. Explicitly say when a recollection is weak.
"""
