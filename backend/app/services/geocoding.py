"""
Geocoding Servisi (Görev 2.4)

- Birincil: Nominatim (OpenStreetMap) — ücretsiz, max 1 req/sn
- Yedek: Google Geocoding API (GOOGLE_MAPS_API_KEY ayarlıysa)
- Redis cache TTL 30 gün
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, NamedTuple

from app.config import settings
from app.services.base_api import BaseAPIService

logger = logging.getLogger(__name__)

CACHE_TTL_30_DAYS = 30 * 24 * 60 * 60  # saniye
_NOMINATIM_RATE_LIMIT = 1.0  # saniye (max 1 req/sn)


class Coordinates(NamedTuple):
    lat: float
    lon: float


class GeocodingService(BaseAPIService):
    """Mekan adından koordinat çözümler."""

    _NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
    _GOOGLE_BASE = "https://maps.googleapis.com"

    def __init__(self) -> None:
        super().__init__(
            base_url="",
            timeout=10.0,
            headers={"User-Agent": "IstanbulTrafikAlerter/1.0"},
        )
        self._last_nominatim_call: float = 0.0

    async def fetch(self, url: str, **kwargs: Any) -> Any:
        response = await self.request("GET", url, **kwargs)
        return response.json()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def geocode(self, address: str) -> Coordinates | None:
        """
        Adres → Koordinat.
        Önce Nominatim dener, başarısız olursa Google'a düşer.
        Sonuç 30 gün Redis'te önbelleğe alınır.
        """
        cache_key = f"geocode:{address.lower().strip()}"

        async def _resolve() -> dict | None:
            result = await self._nominatim(address)
            if result:
                return {"lat": result.lat, "lon": result.lon}
            result = await self._google(address)
            if result:
                return {"lat": result.lat, "lon": result.lon}
            return None

        cached = await self.cache_hook(cache_key, _resolve, CACHE_TTL_30_DAYS)
        if cached:
            return Coordinates(lat=cached["lat"], lon=cached["lon"])
        return None

    # ------------------------------------------------------------------
    # Nominatim
    # ------------------------------------------------------------------

    async def _nominatim(self, address: str) -> Coordinates | None:
        await self._nominatim_rate_limit()
        try:
            data = await self.fetch(
                f"{self._NOMINATIM_BASE}/search",
                params={
                    "q": address,
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "tr",
                },
            )
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                logger.info(
                    "Nominatim geocode: '%s' → (%.4f, %.4f)", address, lat, lon
                )
                return Coordinates(lat=lat, lon=lon)
        except Exception:
            logger.warning("Nominatim başarısız: %s", address)
        return None

    async def _nominatim_rate_limit(self) -> None:
        """Nominatim max 1 req/sn rate limit."""
        import time

        now = time.monotonic()
        elapsed = now - self._last_nominatim_call
        if elapsed < _NOMINATIM_RATE_LIMIT:
            await asyncio.sleep(_NOMINATIM_RATE_LIMIT - elapsed)
        self._last_nominatim_call = time.monotonic()

    # ------------------------------------------------------------------
    # Google Geocoding (yedek)
    # ------------------------------------------------------------------

    async def _google(self, address: str) -> Coordinates | None:
        api_key = settings.GOOGLE_MAPS_API_KEY
        if not api_key:
            logger.debug("Google Geocoding API key tanımlı değil, atlanıyor.")
            return None
        try:
            data = await self.fetch(
                f"{self._GOOGLE_BASE}/maps/api/geocode/json",
                params={"address": address, "key": api_key, "region": "tr"},
            )
            if data.get("status") == "OK":
                loc = data["results"][0]["geometry"]["location"]
                lat, lon = loc["lat"], loc["lng"]
                logger.info(
                    "Google geocode: '%s' → (%.4f, %.4f)", address, lat, lon
                )
                return Coordinates(lat=lat, lon=lon)
        except Exception:
            logger.warning("Google Geocoding başarısız: %s", address)
        return None
