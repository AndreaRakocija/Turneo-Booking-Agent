from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import Iterable, List

from .models import Booking
from .turneo_client import TurneoClient

logger = logging.getLogger(__name__)


class BookingRepository(ABC):
    @abstractmethod
    async def get_bookings_between(self, start_date: date, end_date: date) -> Iterable[Booking]:
        ...


class TurneoBookingRepository(BookingRepository):
    def __init__(self, client: TurneoClient):
        self.client = client

    async def get_bookings_between(self, start_date: date, end_date: date) -> Iterable[Booking]:
        raw_list: List[dict] = await self.client.list_bookings(
            start_date=start_date,
            end_date=end_date,
        )

        bookings: List[Booking] = []

        for item in raw_list:
            try:
                local_time_str = item.get("localTime") or item.get("time")
                if not local_time_str:
                    continue

                date_str = local_time_str.split("T", 1)[0]
                check_in = date.fromisoformat(date_str)

                price = item.get("price", {}).get("finalRetailPrice", {})
                amount = float(price.get("amount", 0.0))
                currency = price.get("currency", "EUR")

                bookings.append(
                    Booking(
                        id=str(item["id"]),
                        check_in=check_in,
                        currency=currency,
                        amount=amount,
                    )
                )
            except Exception as e:
                logger.warning("Skipping malformed booking item %r: %s", item, e)
                continue

        logger.info(
            "Mapped %d bookings from Turneo API between %s and %s",
            len(bookings),
            start_date,
            end_date,
        )
        return bookings
