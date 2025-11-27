import logging
from typing import Dict, Iterable, Tuple

from .fx_client import FXRateProvider
from .models import Booking, BookingSummary, QueryFilters
from .repositories import BookingRepository

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self, repo: BookingRepository, fx_client: FXRateProvider):
        self.repo = repo
        self.fx_client = fx_client

    async def summarize_bookings(self, filters: QueryFilters) -> BookingSummary:
        bookings: Iterable[Booking] = await self.repo.get_bookings_between(
            filters.start_date, filters.end_date
        )

        booking_list = list(bookings)
        logger.info(
            "Total bookings retrieved between %s and %s: %d",
            filters.start_date,
            filters.end_date,
            len(booking_list),
        )

        target = filters.target_currency.upper()
        total = 0.0

        rate_cache: Dict[Tuple[str, str], float] = {}

        for b in booking_list:
            src = b.currency.upper()

            if src == target:
                total += b.amount
                continue

            key = (src, target)
            rate = rate_cache.get(key)

            if rate is None:
                try:
                    rate = await self.fx_client.get_rate(src, target)
                except ValueError as e:
                    logger.error(
                        "Could not convert from %s to %s: %s",
                        src,
                        target,
                        e,
                    )
                    raise ValueError(f"Could not convert from {src} to {target}: {e}") from e

                rate_cache[key] = rate
                logger.debug(f"Fetched FX rate {src}->{target} = {rate}")

            converted = b.amount * rate
            total += converted

        return BookingSummary(
            total_value=round(total, 2),
            currency=target,
        )
