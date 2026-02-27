"""
BaseAPIService Testleri (Görev 2.1 doğrulama)

Mock httpx ile retry ve circuit breaker davranışları test edilir.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.base_api import BaseAPIService, CircuitOpenError


# ------------------------------------------------------------------
# Concrete test sınıfı
# ------------------------------------------------------------------

class SimpleAPIService(BaseAPIService):
    """Test için somut implementasyon."""

    async def fetch(self, url: str, **kwargs):
        return await self.request("GET", url, **kwargs)


# ------------------------------------------------------------------
# Retry testleri
# ------------------------------------------------------------------

class TestRetry:
    async def test_retry_3_times_then_raise(self):
        """İstek sürekli hata verirse 3 denemeden sonra exception fırlatılmalı."""
        svc = SimpleAPIService()

        call_count = 0

        async def failing_request(method, url, **kwargs):
            nonlocal call_count
            call_count += 1
            raise httpx.TransportError("bağlantı hatası")

        with patch.object(svc, "_do_request", side_effect=failing_request):
            with pytest.raises((httpx.TransportError, Exception)):
                await svc.request("GET", "http://example.com/test")

        assert call_count == 3

    async def test_retry_succeeds_on_second_attempt(self):
        """İlk istek başarısız, ikinci başarılı olmalı."""
        svc = SimpleAPIService()

        calls = []
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        async def flaky_request(method, url, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                raise httpx.TransportError("ilk deneme başarısız")
            return mock_response

        with patch.object(svc, "_do_request", side_effect=flaky_request):
            response = await svc.request("GET", "http://example.com/test")

        assert len(calls) == 2
        assert response == mock_response


# ------------------------------------------------------------------
# Circuit breaker testleri
# ------------------------------------------------------------------

class TestCircuitBreaker:
    async def test_circuit_opens_after_5_failures(self):
        """5 ardışık hata sonrası devre açılmalı."""
        svc = SimpleAPIService()

        async def always_fail(method, url, **kwargs):
            raise httpx.TransportError("hata")

        with patch.object(svc, "_do_request", side_effect=always_fail):
            for _ in range(5):
                with pytest.raises(Exception):
                    await svc.request("GET", "http://example.com")

        assert svc.is_circuit_open

    async def test_circuit_raises_immediately_when_open(self):
        """Devre açıkken yeni istek direkt CircuitOpenError fırlatmalı."""
        svc = SimpleAPIService()
        # Devreyi manuel aç
        svc._failure_count = 5
        svc._circuit_open_until = time.monotonic() + 60

        with pytest.raises(CircuitOpenError):
            await svc.request("GET", "http://example.com/test")

    async def test_circuit_closes_after_timeout(self):
        """60 saniye sonra devre half-open konumuna geçmeli."""
        svc = SimpleAPIService()
        # Devreyi geçmişe koy (sanki 60sn geçmiş)
        svc._failure_count = 5
        svc._circuit_open_until = time.monotonic() - 1  # geçmiş

        # _check_circuit çağrısı sıfırlamalı
        svc._check_circuit()
        assert svc._failure_count == 0
        assert svc._circuit_open_until == 0.0
