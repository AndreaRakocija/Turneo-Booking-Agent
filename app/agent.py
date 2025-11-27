from .models import AgentResult
from .query_parser import BookingQueryInterpreter
from .services import BookingService, BookingSummary


class BookingQueryAgent:
    def __init__(self, interpreter: BookingQueryInterpreter, booking_service: BookingService):
        self.interpreter = interpreter
        self.booking_service = booking_service

    async def run(self, query: str) -> AgentResult:
        filters = self.interpreter.interpret(query)
        summary: BookingSummary = await self.booking_service.summarize_bookings(filters)

        msg = (
            f"The total value of bookings between "
            f"{filters.start_date.isoformat()} and {filters.end_date.isoformat()} "
            f"was {summary.total_value:,.2f} {summary.currency}."
        )

        return AgentResult(
            message=msg,
            filters=filters,
            total_value=summary.total_value,
            currency=summary.currency,
        )
