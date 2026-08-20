from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from .models import DomainModel


class ClaimScope(StrEnum):
    LEGAL_DISCLOSURE = "legal_disclosure"
    OFFICIAL_STATISTIC = "official_statistic"
    SELF_STATEMENT = "self_statement"
    MANAGEMENT_GUIDANCE = "management_guidance"
    MARKET_MEASUREMENT = "market_measurement"
    PROJECT_STATUS = "project_status"
    POLICY_TEXT = "policy_text"
    THIRD_PARTY_FACT = "third_party_fact"
    INDUSTRY_EXPECTATION = "industry_expectation"
    TECHNICAL_SPECIFICATION = "technical_specification"
    OTHER = "other"


class AuthorityClass(StrEnum):
    AUTHORITATIVE_PRIMARY = "authoritative_primary"
    PRIMARY_SELF_STATEMENT = "primary_self_statement"
    METHODOLOGICAL_PRIMARY = "methodological_primary"
    REPUTABLE_SECONDARY = "reputable_secondary"
    SECONDARY = "secondary"
    DISCOVERY_ONLY = "discovery_only"


class MemoryLeadKind(StrEnum):
    LANDMARK = "landmark"
    MISSING_EVENT = "missing_event"
    ACTOR = "actor"
    TERMINOLOGY = "terminology"
    METRIC = "metric"
    MECHANISM = "mechanism"
    PRICING_RULE = "pricing_rule"
    CONTRACT_CHANGE = "contract_change"
    PROCESS_BOTTLENECK = "process_bottleneck"
    PROJECT_PATTERN = "project_pattern"
    INVENTORY_PATTERN = "inventory_pattern"
    CAPITAL_CYCLE = "capital_cycle"
    POLICY_SHIFT = "policy_shift"
    TECHNOLOGY_SHIFT = "technology_shift"
    CROSS_INDUSTRY_DEPENDENCY = "cross_industry_dependency"
    NARRATIVE = "narrative"
    CAUSAL_HYPOTHESIS = "causal_hypothesis"
    ANOMALY = "anomaly"


class EvidenceStance(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXT = "context"
    WEAK_MATCH = "weak_match"
    UNRELATED = "unrelated"


class MemoryAuditDisposition(StrEnum):
    UNRESOLVED = "unresolved"
    SEEK_PRIMARY = "seek_primary"
    PRIMARY_SUPPORTS_LEAD = "primary_supports_lead"
    PRIMARY_CONTRADICTS_LEAD = "primary_contradicts_lead"
    AUTHORITATIVE_CONFLICT = "authoritative_conflict"
    SECONDARY_ONLY_SUPPORT = "secondary_only_support"
    SECONDARY_ONLY_CONTRADICTION = "secondary_only_contradiction"
    SCOPE_MISMATCH = "scope_mismatch"


class MemoryLead(DomainModel):
    id: UUID
    kind: MemoryLeadKind
    summary: str = Field(min_length=1)
    claim_scope: ClaimScope
    memory_confidence: float = Field(ge=0, le=1)
    importance_score: float = Field(ge=0, le=1)
    novelty_score: float = Field(ge=0, le=1)
    searchability_score: float = Field(ge=0, le=1)
    suggested_queries: tuple[str, ...] = ()
    suggested_source_types: tuple[str, ...] = ()

    @property
    def search_priority(self) -> float:
        """Priority for investigation, never a probability that the lead is true."""
        return (
            0.35 * self.importance_score
            + 0.25 * self.novelty_score
            + 0.20 * self.searchability_score
            + 0.20 * self.memory_confidence
        )


class EvidenceAssessment(DomainModel):
    evidence_fragment_id: UUID
    stance: EvidenceStance
    authority_class: AuthorityClass
    claim_scope: ClaimScope
    scope_match: bool
    independent_cluster: str | None = None


class MemoryAuditResult(DomainModel):
    disposition: MemoryAuditDisposition
    reason_codes: tuple[str, ...]
    supporting_evidence_ids: tuple[UUID, ...] = ()
    contradicting_evidence_ids: tuple[UUID, ...] = ()

    @property
    def lead_may_publish_as_fact(self) -> bool:
        """A memory lead itself is never publishable, regardless of audit outcome."""
        return False
