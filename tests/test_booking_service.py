from dataclasses import dataclass
from datetime import date
from typing import Iterable, List

import pytest

from app.models import Booking, QueryFilters
from app.repositories import BookingRepository
from app.services import BookingService


@dataclass
class FakeFXClient:
    rate: float

    async def get_rate(self, from_currency: str, to_currency: str) -> float:
        return self.rate


class FakeBookingRepository(BookingRepository):
    def __init__(self, bookings: List[Booking]):
        self._bookings = bookings

    async def get_bookings_between(self, start_date: date, end_date: date) -> Iterable[Booking]:
        return self._bookings

@pytest.mark.asyncio
async def test_booking_service_summarize_with_conversion():
    bookings = [
        Booking(id="1", check_in=date(2024, 11, 1), currency="EUR", amount=100.0),
        Booking(id="2", check_in=date(2024, 11, 2), currency="USD", amount=100.0),
    ]

    repo = FakeBookingRepository(bookings)
    fx_client = FakeFXClient(rate=2.0)

    service = BookingService(repo=repo, fx_client=fx_client)

    filters = QueryFilters(
        start_date=date(2024, 11, 1),
        end_date=date(2024, 11, 30),
        target_currency="EUR",
    )

    summary = await service.summarize_bookings(filters)

    # 100 (EUR) + 100 * 2.0 (USD->EUR) = 300
    assert summary.currency == "EUR"
    assert summary.total_value == 300.0


@pytest.mark.asyncio
async def test_booking_service_returns_zero_when_no_bookings():
    repo = FakeBookingRepository(bookings=[])
    fx_client = FakeFXClient(rate=1.0)
    service = BookingService(repo=repo, fx_client=fx_client)

    filters = QueryFilters(
        start_date=date(2024, 11, 1),
        end_date=date(2024, 11, 30),
        target_currency="EUR",
    )

    summary = await service.summarize_bookings(filters)

    assert summary.currency == "EUR"
    assert summary.total_value == 0.0
