import asyncio
import json
from typing import Any, Dict, List

from app.config import settings
from app.query_parser import OpenAIQueryParser

EVAL_DATASET: List[Dict[str, Any]] = [
    {
        "query": "Show me all the bookings you have in USD",
        "expected": {
            "expect_error": True,
            "currency": "USD",
        },
    },
    {
        "query": "Show me bookings in November 2024 in USD",
        "expected": {
            "start_date": "2024-11-01",
            "end_date": "2024-11-30",
            "currency": "USD",
        },
    },
    {
        "query": "Prikaži rezervacije za ožujak 2023 u eurima",
        "expected": {
            "start_date": "2023-03-01",
            "end_date": "2023-03-31",
            "currency": "EUR",
        },
    },
    {
        "query": "bookings 2024-11-10 to 2024-11-20",
        "expected": {
            "start_date": "2024-11-10",
            "end_date": "2024-11-20",
            "currency": "EUR",
        },
    },
]


async def evaluate():
    parser = OpenAIQueryParser(api_key=settings.openai_api_key)

    total = len(EVAL_DATASET)
    passed = 0
    results = []

    for item in EVAL_DATASET:
        query = item["query"]
        expected = item["expected"]
        expect_error = expected.get("expect_error", False)

        try:
            parsed = parser.parse_booking_query(query)

            if expect_error:
                results.append(
                    {
                        "query": query,
                        "parsed": parsed,
                        "expected": expected,
                        "status": "MISMATCH_EXPECTED_ERROR",
                    }
                )
                continue

            success = (
                    parsed["start_date"] == expected["start_date"]
                    and parsed["end_date"] == expected["end_date"]
                    and parsed["currency"].upper() == expected["currency"].upper()
            )

            if success:
                passed += 1

            results.append(
                {
                    "query": query,
                    "parsed": parsed,
                    "expected": expected,
                    "status": "OK" if success else "MISMATCH",
                }
            )

        except Exception as e:
            if expect_error:
                # Očekivana greška → treat as pass
                passed += 1
                results.append(
                    {
                        "query": query,
                        "status": "OK_ERROR",
                        "error": str(e),
                    }
                )
            else:
                results.append(
                    {
                        "query": query,
                        "status": "ERROR",
                        "error": str(e),
                    }
                )

    # ==== Summary ====
    for res in results:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        print()

    print("\n=== OpenAI Parser Evaluation ===")
    print(f"Total queries:    {total}")
    print(f"Correct outputs:  {passed}")
    print(f"Accuracy:         {passed / total * 100:.1f}%")
    print("--------------------------------------\n")


if __name__ == "__main__":
    asyncio.run(evaluate())
