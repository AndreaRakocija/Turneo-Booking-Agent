from dataclasses import dataclass
from datetime import date


@dataclass
class Booking:
    id: str
    check_in: date
    currency: str
    amount: float


@dataclass
class BookingSummary:
    total_value: float
    currency: str


@dataclass
class QueryFilters:
    start_date: date
    end_date: date
    target_currency: str


@dataclass
class AgentResult:
    message: str
    filters: QueryFilters | None = None
    total_value: float | None = None
    currency: str | None = None
