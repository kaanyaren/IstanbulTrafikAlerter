"""
İBB Açık Veri Trafik Servisi (Görev 2.2)

Endpoint: https://data.ibb.gov.tr/api/3/action/datastore_search
Cache: Redis 5 dakika
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from app.services.base_api import BaseAPIService

logger = logging.getLogger(__name__)

IBB_TRAFFIC_URL = "https://data.ibb.gov.tr/api/3/action/datastore_search"
# İBB trafik yoğunluk verisi için resource_id (örnek — gerçek ID IBB portalından alınır)
IBB_TRAFFIC_RESOURCE_ID = "traffic_density"

CACHE_TTL = 5 * 60  # 5 dakika


# ------------------------------------------------------------------
# Pydantic schema
# ------------------------------------------------------------------

class TrafficZone(BaseModel):
    """Normalize edilmiş trafik bölgesi."""

    zone_id: str = Field(alias="GEOHASH", default="")
    road_name: str = Field(alias="ROAD_NAME", default="")
    direction: str = Field(alias="YOLYON", default="")
    speed_kmh: float = Field(alias="MINIMUM_SPEED", default=0.0)
    density: int = Field(alias="NUMBER_OF_VEHICLES", default=0)
    lat: float | None = Field(alias="LATITUDE", default=None)
    lon: float | None = Field(alias="LONGITUDE", default=None)
    timestamp: str = Field(alias="DATE_TIME", default="")

    class Config:
        populate_by_name = True


# ------------------------------------------------------------------
# Servis
# ------------------------------------------------------------------

class IBBTrafficService(BaseAPIService):
    """İBB açık veri portalından trafik yoğunluk verisi çeker."""

    def __init__(self) -> None:
        super().__init__(base_url="", timeout=15.0)

    async def fetch(self, url: str, **kwargs: Any) -> dict[str, Any]:
        response = await self.request("GET", url, **kwargs)
        return response.json()

    async def get_traffic_zones(
        self,
        resource_id: str = IBB_TRAFFIC_RESOURCE_ID,
        limit: int = 100,
    ) -> list[TrafficZone]:
        """
        İBB trafik yoğunluk verisi döndürür.
        Veriler 5 dakika Redis'te önbelleğe alınır.
        """
        cache_key = f"ibb:traffic:{resource_id}:{limit}"

        async def _fetch() -> list[dict]:
            data = await self.fetch(
                IBB_TRAFFIC_URL,
                params={"resource_id": resource_id, "limit": limit},
            )
            result = data.get("result", {})
            records = result.get("records", [])
            logger.info(
                "IBB trafik verisi: %d kayıt alındı.",
                len(records),
            )
            return records

        records = await self.cache_hook(cache_key, _fetch, CACHE_TTL)

        zones: list[TrafficZone] = []
        for rec in (records or []):
            try:
                zones.append(TrafficZone.model_validate(rec))
            except Exception:
                logger.debug("Kayıt parse hatası: %s", rec)
        return zones
