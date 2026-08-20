from __future__ import annotations

from enum import StrEnum


class EntityType(StrEnum):
    INDUSTRY = "industry"
    PRODUCT = "product"
    ORGANIZATION = "organization"
    SECURITY = "security"
    FACILITY = "facility"
    PRODUCTION_LINE = "production_line"
    CAPACITY_PROJECT = "capacity_project"
    EVENT = "event"


class SourceKind(StrEnum):
    REGULATOR = "regulator"
    EXCHANGE = "exchange"
    COMPANY = "company"
    ASSOCIATION = "association"
    GOVERNMENT = "government"
    DATA_VENDOR = "data_vendor"
    NEWS = "news"
    RESEARCH = "research"
    MANUAL = "manual"


class QualityGrade(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class FactStatus(StrEnum):
    CANDIDATE = "candidate"
    TRUSTED = "trusted"
    REVIEW = "review"
    CONFLICT = "conflict"
    QUARANTINED = "quarantined"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class FactValueKind(StrEnum):
    NUMERIC = "numeric"
    TEXT = "text"
    BOOLEAN = "boolean"
    DATE = "date"
    ENTITY = "entity"
    JSON = "json"


class JobStage(StrEnum):
    DISCOVER = "discover"
    FETCH = "fetch"
    ARCHIVE = "archive"
    PARSE = "parse"
    EXTRACT = "extract"
    NORMALIZE = "normalize"
    VALIDATE = "validate"
    RECONCILE = "reconcile"
    PUBLISH = "publish"
    DERIVE = "derive"


class JobStatus(StrEnum):
    QUEUED = "queued"
    LEASED = "leased"
    SUCCEEDED = "succeeded"
    RETRY = "retry"
    DEAD = "dead"
    CANCELLED = "cancelled"


class Cadence(StrEnum):
    DAILY = "daily"
    EVERY_THREE_DAYS = "every_three_days"
    WEEKLY = "weekly"
    SOURCE_NATIVE = "source_native"
    EVENT_DRIVEN = "event_driven"


class MetricKind(StrEnum):
    PRICE = "price"
    CAPACITY = "capacity"
    EFFECTIVE_CAPACITY = "effective_capacity"
    PRODUCTION = "production"
    UTILIZATION = "utilization"
    INVENTORY = "inventory"
    MARGIN = "margin"
    CAPEX = "capex"
    ORDERBOOK = "orderbook"
    DEMAND = "demand"
    FREIGHT = "freight"
    CUSTOM = "custom"


class MarketBasis(StrEnum):
    SPOT = "spot"
    CONTRACT = "contract"
    LIST = "list"
    AUCTION = "auction"
    INDEX = "index"
    ASSESSMENT = "assessment"


class TaxBasis(StrEnum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class FreightBasis(StrEnum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    EX_WORKS = "ex_works"
    DELIVERED = "delivered"
    UNKNOWN = "unknown"


class PriceComponent(StrEnum):
    LOW = "low"
    HIGH = "high"
    MID = "mid"
    AVERAGE = "average"
    SETTLEMENT = "settlement"
    CLOSE = "close"


class ObservationFrequency(StrEnum):
    INSTANT = "instant"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class ValidTimeKind(StrEnum):
    PERIOD = "period"
    TIMELESS = "timeless"
    UNKNOWN = "unknown"


class ReviewSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Decision(StrEnum):
    ACCEPT = "accept"
    REVIEW = "review"
    CONFLICT = "conflict"
    QUARANTINE = "quarantine"
