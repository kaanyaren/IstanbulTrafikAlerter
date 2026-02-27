"""
BaseAPIService — Dış API adaptörleri için soyut temel sınıf (Görev 2.1)

Özellikler:
- httpx.AsyncClient ile async HTTP
- tenacity ile 3 deneme, exponential backoff retry
- Rate limit takibi (X-RateLimit-Remaining header'dan)
- Circuit breaker: 5 ardışık hata → 60 sn devre dışı
- Cache hook (CacheService ile entegrasyon)
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.services.cache import cache_service

logger = logging.getLogger(__name__)

# Circuit breaker ayarları
_CIRCUIT_FAILURE_THRESHOLD = 5
_CIRCUIT_OPEN_SECONDS = 60


class CircuitOpenError(Exception):
    """Devre açık olduğunda fırlatılır."""


class BaseAPIService(ABC):
    """Tüm dış API servisleri için soyut temel sınıf."""

    def __init__(
        self,
        base_url: str = "",
        timeout: float = 10.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url
        self._timeout = timeout
        self._headers = headers or {}

        # Rate limit tracking
        self._rate_limit_remaining: int | None = None

        # Circuit breaker durumu
        self._failure_count: int = 0
        self._circuit_open_until: float = 0.0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def fetch(self, url: str, **kwargs: Any) -> Any:
        """Alt sınıflar bu metodu implement eder."""

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        HTTP isteği gönder.
        - Circuit breaker kontrolü
        - Retry (3 deneme, exponential backoff 1→2→4 sn)
        - Rate limit header takibi
        """
        self._check_circuit()

        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(
                    (httpx.TransportError, httpx.TimeoutException)
                ),
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=4),
                reraise=True,
            ):
                with attempt:
                    response = await self._do_request(method, url, **kwargs)
                    self._update_rate_limit(response)
                    self._on_success()
                    return response
        except RetryError as exc:
            self._on_failure()
            raise exc
        except Exception as exc:
            self._on_failure()
            raise exc

    async def cache_hook(
        self,
        cache_key: str,
        callback: Any,
        ttl: int | None = None,
    ) -> Any:
        """Cache'te varsa döndür, yoksa callback çalıştır ve cache'e yaz."""
        return await cache_service.get_or_set(cache_key, callback, ttl)

    # ------------------------------------------------------------------
    # Yardımcı metodlar
    # ------------------------------------------------------------------

    async def _do_request(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self._timeout,
        ) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response

    def _check_circuit(self) -> None:
        """Devre açıksa ve süre dolmadıysa hata fırlat."""
        if self._circuit_open_until and time.monotonic() < self._circuit_open_until:
            remaining = self._circuit_open_until - time.monotonic()
            raise CircuitOpenError(
                f"Devre açık — {remaining:.0f} sn sonra tekrar dene"
            )
        if self._circuit_open_until and time.monotonic() >= self._circuit_open_until:
            # Süre doldu, sıfırla (half-open)
            logger.info("%s: Devre kapatıldı (half-open).", self.__class__.__name__)
            self._failure_count = 0
            self._circuit_open_until = 0.0

    def _on_success(self) -> None:
        self._failure_count = 0

    def _on_failure(self) -> None:
        self._failure_count += 1
        logger.warning(
            "%s: Ardışık hata sayısı %d/%d",
            self.__class__.__name__,
            self._failure_count,
            _CIRCUIT_FAILURE_THRESHOLD,
        )
        if self._failure_count >= _CIRCUIT_FAILURE_THRESHOLD:
            self._circuit_open_until = time.monotonic() + _CIRCUIT_OPEN_SECONDS
            logger.error(
                "%s: Devre açıldı — %d sn boyunca devre dışı.",
                self.__class__.__name__,
                _CIRCUIT_OPEN_SECONDS,
            )

    def _update_rate_limit(self, response: httpx.Response) -> None:
        header = response.headers.get("X-RateLimit-Remaining")
        if header is not None:
            try:
                self._rate_limit_remaining = int(header)
                logger.debug(
                    "%s: Kalan istek limiti: %d",
                    self.__class__.__name__,
                    self._rate_limit_remaining,
                )
            except ValueError:
                pass

    @property
    def is_circuit_open(self) -> bool:
        return bool(
            self._circuit_open_until
            and time.monotonic() < self._circuit_open_until
        )
