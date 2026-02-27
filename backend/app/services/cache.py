"""
Redis Cache Yardımcı Modülü (Görev 2.5)

Özellikler:
- Async redis ile connection pool
- JSON otomatik serialize / deserialize
- get, set, delete, get_or_set metodları
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Awaitable

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis tabanlı async cache servisi."""

    def __init__(self, redis_url: str | None = None) -> None:
        url = redis_url or settings.REDIS_URL
        self._pool = aioredis.ConnectionPool.from_url(
            url,
            max_connections=20,
            decode_responses=True,
        )
        self._client: aioredis.Redis = aioredis.Redis(connection_pool=self._pool)

    # ------------------------------------------------------------------
    # Temel metodlar
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Any | None:
        """Cache'ten değer al. Yoksa None döner."""
        try:
            raw = await self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            logger.exception("Cache get hatası: key=%s", key)
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Cache'e değer yaz. ttl saniye cinsinden."""
        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
            return True
        except Exception:
            logger.exception("Cache set hatası: key=%s", key)
            return False

    async def delete(self, key: str) -> bool:
        """Cache'ten değer sil."""
        try:
            await self._client.delete(key)
            return True
        except Exception:
            logger.exception("Cache delete hatası: key=%s", key)
            return False

    async def get_or_set(
        self,
        key: str,
        callback: Callable[[], Awaitable[Any]],
        ttl: int | None = None,
    ) -> Any:
        """
        Cache'te varsa döndür, yoksa callback çalıştır, sonucu cache'e yaz ve döndür.
        """
        cached = await self.get(key)
        if cached is not None:
            return cached

        value = await callback()
        if value is not None:
            await self.set(key, value, ttl)
        return value

    async def close(self) -> None:
        """Connection pool'ı kapat."""
        await self._client.aclose()


# Singleton instance (uygulama başında oluşturulur)
cache_service = CacheService()
