from __future__ import annotations

from typing import Any, Dict, Protocol

import httpx

from .config import settings


class FXRateProvider(Protocol):
    async def get_rate(self, from_currency: str, to_currency: str) -> float:
        ...


class FXClient(FXRateProvider):

    def __init__(self) -> None:
        self.base_url = (settings.fx_api_root or "").rstrip("/")
        self.api_key = settings.fx_api_key or None

    async def get_rate(self, from_currency: str, to_currency: str) -> float:
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return 1.0

        if not self.base_url or not self.api_key:
            raise RuntimeError(
                "FX client is not configured but a conversion from "
                f"{from_currency} to {to_currency} was requested."
            )

        params: Dict[str, Any] = {
            "base": from_currency,
            "currencies": to_currency,
            "format": "json",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/latest", params=params)
                resp.raise_for_status()
            except httpx.RequestError as e:
                raise RuntimeError(f"Failed to contact FX API: {e}") from e
            except httpx.HTTPStatusError as e:
                raise RuntimeError(
                    f"FX API returned error status {e.response.status_code}: {e.response.text}"
                ) from e

            data: Dict[str, Any] = resp.json()

        if not data.get("success", False):
            raise ValueError(f"FX API error: {data}")

        rates = data.get("rates", {})
        rate = rates.get(to_currency)
        if rate is None:
            raise ValueError(f"No FX rate for {from_currency}->{to_currency} in response")

        return float(rate)
