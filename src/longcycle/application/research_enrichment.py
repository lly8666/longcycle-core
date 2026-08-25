from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ResearchEnrichmentStatus = Literal["AVAILABLE", "UNAVAILABLE_EXPECTED"]
DETERMINISTIC_INDUSTRY_SUBJECTS = "deterministic_industry_subjects"


class ExpectedResearchEnrichmentUnavailable(RuntimeError):
    """An optional research service could not run for an expected operational reason.

    These failures may degrade a researcher view without changing or hiding already-valid
    historical truth. Adapters should translate only known operational conditions into this
    family; arbitrary programming/database/schema errors must not be converted into it.
    """

    reason_code = "expected_unavailable"

    def __init__(self, message: str = "optional research enrichment is unavailable") -> None:
        super().__init__(message)


class ProviderTimeout(ExpectedResearchEnrichmentUnavailable):
    reason_code = "provider_timeout"


class RateLimitExceeded(ExpectedResearchEnrichmentUnavailable):
    reason_code = "rate_limit"


class ProviderUnavailable(ExpectedResearchEnrichmentUnavailable):
    reason_code = "provider_unavailable"


class NetworkUnavailable(ExpectedResearchEnrichmentUnavailable):
    reason_code = "network_error"


class OptionalCredentialsMissing(ExpectedResearchEnrichmentUnavailable):
    reason_code = "optional_credentials_missing"


class UpstreamServerUnavailable(ExpectedResearchEnrichmentUnavailable):
    reason_code = "upstream_5xx"


class ResearchBudgetExhausted(ExpectedResearchEnrichmentUnavailable):
    reason_code = "budget_exhausted"


class CapabilityNotSupported(ExpectedResearchEnrichmentUnavailable):
    reason_code = "capability_not_supported"


class ResearchEnrichmentDefect(RuntimeError):
    """Unexpected implementation/contract failure in an optional research lane.

    Core application code does not silently downgrade this class. Development/CI/staging
    therefore fail loudly instead of misreporting a programming defect as provider downtime.
    """


class ResearchEnrichmentContractViolation(ResearchEnrichmentDefect):
    pass


@dataclass(frozen=True)
class EnrichmentComponentResult:
    component: str
    status: ResearchEnrichmentStatus
    result_count: int | None = None
    reason: str | None = None
    message: str | None = None

    def as_payload(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status,
            "result_count": self.result_count,
            "reason": self.reason,
            "message": self.message,
        }


def available_component(component: str, *, result_count: int) -> EnrichmentComponentResult:
    return EnrichmentComponentResult(
        component=component,
        status="AVAILABLE",
        result_count=result_count,
    )


def unavailable_component(
    component: str,
    exc: ExpectedResearchEnrichmentUnavailable,
) -> EnrichmentComponentResult:
    return EnrichmentComponentResult(
        component=component,
        status="UNAVAILABLE_EXPECTED",
        reason=exc.reason_code,
        message=str(exc),
    )


def unsupported_component(component: str) -> EnrichmentComponentResult:
    return unavailable_component(
        component,
        CapabilityNotSupported(f"optional capability {component!r} is not supported by this reader"),
    )


def defect(component: str, exc: Exception) -> ResearchEnrichmentDefect:
    if isinstance(exc, ResearchEnrichmentDefect):
        return exc
    return ResearchEnrichmentDefect(
        f"optional research enrichment {component!r} failed with an unexpected defect: "
        f"{type(exc).__name__}: {exc}"
    )


def overall_status(
    components: tuple[EnrichmentComponentResult, ...] | list[EnrichmentComponentResult],
) -> ResearchEnrichmentStatus:
    if any(item.status == "UNAVAILABLE_EXPECTED" for item in components):
        return "UNAVAILABLE_EXPECTED"
    return "AVAILABLE"
