"""
Etkinlik Veri Servisi (Görev 2.3)

İki kaynak adaptörü:
1. IBBKulturAdapter   — İBB Kültür açık veri API
2. SeatGeekAdapter    — SeatGeek açık API (API key gereksiz, İstanbul sorgusu)

Event modeli normalize edilir; duplikasyon (source + source_id) ile kontrol edilir.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.services.base_api import BaseAPIService

logger = logging.getLogger(__name__)

CACHE_TTL = 30 * 60  # 30 dakika


# ------------------------------------------------------------------
# Pydantic schema
# ------------------------------------------------------------------

class Event(BaseModel):
    """Normalize edilmiş etkinlik modeli."""

    source: str
    source_id: str
    title: str
    description: str = ""
    venue: str = ""
    city: str = "İstanbul"
    lat: float | None = None
    lon: float | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    url: str = ""
    category: str = ""

    @property
    def dedup_key(self) -> str:
        return f"{self.source}:{self.source_id}"


# ------------------------------------------------------------------
# Soyut adaptör
# ------------------------------------------------------------------

class BaseEventAdapter(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    async def fetch_events(self) -> list[Event]: ...


# ------------------------------------------------------------------
# Adaptör 1: İBB Kültür API
# ------------------------------------------------------------------

class IBBKulturAdapter(BaseAPIService, BaseEventAdapter):
    """İBB Kültür portalından etkinlik çeker."""

    _BASE = "https://kultursanat.ibb.istanbul"
    _ENDPOINT = "/api/event/geteventlist"

    @property
    def source_name(self) -> str:
        return "ibb_kultur"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=15.0)

    async def fetch(self, url: str, **kwargs: Any) -> Any:
        response = await self.request("GET", url, **kwargs)
        return response.json()

    async def fetch_events(self) -> list[Event]:
        cache_key = "events:ibb_kultur"

        async def _fetch() -> list[dict]:
            try:
                data = await self.fetch(
                    self._ENDPOINT,
                    params={"pageSize": 50, "pageIndex": 0},
                )
                return data if isinstance(data, list) else data.get("data", [])
            except Exception:
                logger.exception("IBBKultur fetch hatası")
                return []

        raw = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        events: list[Event] = []
        for item in (raw or []):
            try:
                events.append(
                    Event(
                        source=self.source_name,
                        source_id=str(item.get("id", item.get("Id", ""))),
                        title=item.get("name", item.get("Name", "")),
                        description=item.get("description", item.get("Description", "")),
                        venue=item.get("place", item.get("Place", "")),
                        start_at=self._parse_dt(item.get("startDate", item.get("StartDate"))),
                        end_at=self._parse_dt(item.get("endDate", item.get("EndDate"))),
                        url=item.get("url", item.get("Url", "")),
                        category=item.get("category", item.get("Category", "")),
                    )
                )
            except Exception:
                logger.debug("IBBKultur parse hatası: %s", item)
        return events

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None


# ------------------------------------------------------------------
# Adaptör 2: SeatGeek API (ücretsiz, İstanbul filtreleme)
# ------------------------------------------------------------------

class SeatGeekAdapter(BaseAPIService, BaseEventAdapter):
    """SeatGeek açık API — İstanbul etkinlikleri."""

    _BASE = "https://api.seatgeek.com"
    _ENDPOINT = "/2/events"

    @property
    def source_name(self) -> str:
        return "seatgeek"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=15.0)

    async def fetch(self, url: str, **kwargs: Any) -> Any:
        response = await self.request("GET", url, **kwargs)
        return response.json()

    async def fetch_events(self) -> list[Event]:
        cache_key = "events:seatgeek:istanbul"

        async def _fetch() -> list[dict]:
            try:
                data = await self.fetch(
                    self._ENDPOINT,
                    params={
                        "venue.city": "Istanbul",
                        "per_page": 50,
                        "sort": "datetime_local.asc",
                    },
                )
                return data.get("events", [])
            except Exception:
                logger.exception("SeatGeek fetch hatası")
                return []

        raw = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        events: list[Event] = []
        for item in (raw or []):
            try:
                venue = item.get("venue", {})
                events.append(
                    Event(
                        source=self.source_name,
                        source_id=str(item.get("id", "")),
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        venue=venue.get("name", ""),
                        city=venue.get("city", "İstanbul"),
                        lat=venue.get("location", {}).get("lat"),
                        lon=venue.get("location", {}).get("lon"),
                        start_at=self._parse_dt(item.get("datetime_local")),
                        url=item.get("url", ""),
                        category=item.get("type", ""),
                    )
                )
            except Exception:
                logger.debug("SeatGeek parse hatası: %s", item)
        return events

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except Exception:
            return None


# ------------------------------------------------------------------
# Ana servis
# ------------------------------------------------------------------

class EventService:
    """Tüm kaynaklardan etkinlik çekip duplikasyon kontrolü yapar."""

    def __init__(self, adapters: list[BaseEventAdapter] | None = None) -> None:
        self.adapters: list[BaseEventAdapter] = adapters or [
            IBBKulturAdapter(),
            SeatGeekAdapter(),
        ]

    async def get_events(self) -> list[Event]:
        """
        Tüm adaptörlerden etkinlik çekip birleştirir.
        Duplikasyonlar (source + source_id) çıkarılır.
        """
        seen: set[str] = set()
        events: list[Event] = []

        for adapter in self.adapters:
            try:
                batch = await adapter.fetch_events()
                for event in batch:
                    if event.dedup_key not in seen:
                        seen.add(event.dedup_key)
                        events.append(event)
                logger.info(
                    "%s: %d etkinlik alındı.", adapter.source_name, len(batch)
                )
            except Exception:
                logger.exception(
                    "%s adaptörü hata verdi.", adapter.source_name
                )

        logger.info("Toplam %d eşsiz etkinlik.", len(events))
        return events
