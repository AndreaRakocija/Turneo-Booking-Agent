from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

import httpx

from .config import settings


class TurneoClient:
    def __init__(self):
        self.base_url = settings.turneo_api_root.rstrip("/")
        self.api_key = settings.turneo_api_key

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Accept": "application/json",
        }

    async def list_bookings(
            self,
            start_date: date | None = None,
            end_date: date | None = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}

        if start_date:
            params["startTime[gte]"] = start_date.isoformat()
        if end_date:
            params["startTime[lte]"] = end_date.isoformat()

        all_results: List[Dict[str, Any]] = []

        url = f"{self.base_url}/bookings"

        async with httpx.AsyncClient(timeout=10.0) as client:
            first_request = True

            while url:
                try:
                    resp = await client.get(
                        url,
                        headers=self._headers(),
                        params=params if first_request else None,
                    )
                    resp.raise_for_status()
                except httpx.RequestError as e:
                    raise RuntimeError(f"Failed to contact Turneo API: {e}") from e
                except httpx.HTTPStatusError as e:
                    raise RuntimeError(
                        f"Turneo API returned error status "
                        f"{e.response.status_code}: {e.response.text}"
                    ) from e

                data = resp.json()

                results = data.get("results", [])
                if isinstance(results, list):
                    all_results.extend(results)

                url = data.get("next") or None
                first_request = False

        return all_results
