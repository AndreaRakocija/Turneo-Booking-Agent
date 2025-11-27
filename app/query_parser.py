from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from calendar import monthrange
from datetime import date
from typing import NotRequired, TypedDict

from openai import OpenAI

from .models import QueryFilters

logger = logging.getLogger(__name__)


class ParsedQuery(TypedDict):
    start_date: str
    end_date: str
    currency: NotRequired[str]


class BookingQueryParser(ABC):
    @abstractmethod
    def parse_booking_query(self, query: str) -> ParsedQuery:
        ...


MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

SUPPORTED_CURRENCIES = [
    "EUR",
    "USD",
    "GBP",
    "JPY",
    "CHF",
    "AUD",
    "CAD",
]


class RuleBasedQueryParser(BookingQueryParser):

    def parse_booking_query(self, query: str) -> ParsedQuery:
        q_lower = query.lower()

        # month + year - "november 2024"
        month_year = re.search(
            r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})",
            q_lower,
        )
        if not month_year:
            raise ValueError("Could not parse query")

        month_name = month_year.group(1)
        year = int(month_year.group(2))
        month = MONTHS[month_name]

        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])

        q_upper = query.upper()

        currency = "EUR"  # default
        found = False
        for code in SUPPORTED_CURRENCIES:
            if code in q_upper:
                currency = code
                found = True
                break

        if not found:
            logger.info(
                "No explicit currency found in query %r, defaulting to EUR.",
                query,
            )

        return {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "currency": currency,
        }


class OpenAIQueryParser(BookingQueryParser):

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def parse_booking_query(self, query: str) -> ParsedQuery:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "extract_booking_filters",
                    "description": (
                        "Extract a concrete date range and optional target "
                        "currency from a natural language query about bookings."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": (
                                    "Start of date range, ISO format YYYY-MM-DD. "
                                    "If the query mentions only a month/year "
                                    "like 'November 2024', use the first day "
                                    "of that month."
                                ),
                            },
                            "end_date": {
                                "type": "string",
                                "description": (
                                    "End of date range, ISO format YYYY-MM-DD. "
                                    "If the query mentions only a month/year "
                                    "like 'November 2024', use the last day "
                                    "of that month."
                                ),
                            },
                            "currency": {
                                "type": "string",
                                "description": (
                                    "Optional 3-letter ISO currency code "
                                    "(e.g. EUR, USD, GBP). "
                                    "If not specified in the query, you may omit it."
                                ),
                            },
                        },
                        "required": ["start_date", "end_date"],
                    },
                },
            }
        ]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a booking analytics parser. "
                    "Given a user query, you MUST call the provided function. "
                    "If the user query does NOT contain any date information "
                    "(no month, no year, no specific date), "
                    "you MUST call the function with start_date='UNSUPPORTED' "
                    "and end_date='UNSUPPORTED'. "
                    "NEVER invent or guess dates that are not explicitly present "
                    "or clearly implied."
                    f"Today is {date.today().isoformat()}."
                ),
            },
            {"role": "user", "content": query},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice={
                    "type": "function",
                    "function": {"name": "extract_booking_filters"},
                },
                temperature=0,
            )
        except Exception as e:
            raise ValueError(f"OpenAI call failed: {e}") from e

        msg = response.choices[0].message

        if not msg.tool_calls:
            raise ValueError("LLM did not call the extract_booking_filters function")

        tool_call = msg.tool_calls[0]
        raw_args = tool_call.function.arguments

        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            raise ValueError(f"LLM returned invalid tool arguments: {raw_args}")

        if args.get("start_date") == "UNSUPPORTED" or args.get("end_date") == "UNSUPPORTED":
            raise ValueError("Query does not contain any valid date range.")

        for field in ("start_date", "end_date"):
            if field not in args or not args[field]:
                raise ValueError(f"LLM did not provide required field: {field}")

        raw_currency = args.get("currency")
        currency = (
            raw_currency.upper()
            if isinstance(raw_currency, str) and raw_currency
            else "EUR"
        )

        return {
            "start_date": args["start_date"],
            "end_date": args["end_date"],
            "currency": currency,
        }


class BookingQueryInterpreter:

    def __init__(self, primary: BookingQueryParser, fallback: BookingQueryParser | None = None):
        if isinstance(primary, RuleBasedQueryParser):
            self.primary = primary
            self.fallback = None
        else:
            self.primary = primary
            self.fallback = fallback or RuleBasedQueryParser()

    def interpret(self, query: str) -> QueryFilters:
        try:
            parsed = self.primary.parse_booking_query(query)
        except Exception:
            if self.fallback:
                parsed = self.fallback.parse_booking_query(query)
            else:
                raise

        try:
            start = date.fromisoformat(parsed["start_date"])
            end = date.fromisoformat(parsed["end_date"])
        except Exception as e:
            raise ValueError(f"Invalid dates from parser: {parsed}") from e

        currency = parsed.get("currency", "EUR").upper()

        logger.debug(
            "Interpreted query %r -> start=%s, end=%s, currency=%s",
            query,
            start,
            end,
            currency,
        )

        return QueryFilters(
            start_date=start,
            end_date=end,
            target_currency=currency,
        )
