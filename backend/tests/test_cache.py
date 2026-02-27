"""
Redis Cache Servisi Testleri (Görev 2.5 doğrulama)

Mock redis.asyncio kullanılır — gerçek Redis gerekmez.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cache import CacheService


@pytest.fixture
def mock_redis():
    """Sahte redis client döndürür."""
    client = AsyncMock()
    return client


@pytest.fixture
def cache(mock_redis):
    svc = CacheService.__new__(CacheService)
    svc._client = mock_redis
    svc._pool = MagicMock()
    return svc


class TestCacheGet:
    async def test_get_returns_none_when_missing(self, cache, mock_redis):
        mock_redis.get.return_value = None
        result = await cache.get("missing_key")
        assert result is None

    async def test_get_deserializes_json(self, cache, mock_redis):
        payload = {"name": "istanbul", "count": 42}
        mock_redis.get.return_value = json.dumps(payload)
        result = await cache.get("my_key")
        assert result == payload

    async def test_get_returns_none_on_exception(self, cache, mock_redis):
        mock_redis.get.side_effect = Exception("redis error")
        result = await cache.get("bad_key")
        assert result is None


class TestCacheSet:
    async def test_set_with_ttl(self, cache, mock_redis):
        mock_redis.setex = AsyncMock(return_value=True)
        result = await cache.set("k", {"v": 1}, ttl=300)
        assert result is True
        mock_redis.setex.assert_called_once_with("k", 300, json.dumps({"v": 1}))

    async def test_set_without_ttl(self, cache, mock_redis):
        mock_redis.set = AsyncMock(return_value=True)
        result = await cache.set("k", "hello")
        assert result is True
        mock_redis.set.assert_called_once_with("k", json.dumps("hello"))

    async def test_set_returns_false_on_exception(self, cache, mock_redis):
        mock_redis.set.side_effect = Exception("fail")
        result = await cache.set("k", "v")
        assert result is False


class TestCacheDelete:
    async def test_delete_calls_redis(self, cache, mock_redis):
        mock_redis.delete = AsyncMock(return_value=1)
        result = await cache.delete("k")
        assert result is True
        mock_redis.delete.assert_called_once_with("k")


class TestCacheGetOrSet:
    async def test_returns_cached_value(self, cache, mock_redis):
        mock_redis.get.return_value = json.dumps("cached")
        callback = AsyncMock(return_value="fresh")
        result = await cache.get_or_set("k", callback, ttl=60)
        assert result == "cached"
        callback.assert_not_called()

    async def test_calls_callback_when_miss(self, cache, mock_redis):
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock(return_value=True)
        callback = AsyncMock(return_value={"data": "new"})
        result = await cache.get_or_set("k", callback, ttl=60)
        assert result == {"data": "new"}
        callback.assert_called_once()

    async def test_ttl_expiry_returns_none(self, cache, mock_redis):
        """TTL dolmuşken get→None, callback çağrılmış olmalı."""
        # İlk get → None (TTL dolmuş gibi davranır)
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock(return_value=True)
        callback = AsyncMock(return_value=None)
        result = await cache.get_or_set("expired_key", callback, ttl=1)
        assert result is None
        callback.assert_called_once()
