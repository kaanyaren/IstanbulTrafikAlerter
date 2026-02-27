"""
Geocoding Servisi Testleri (Görev 2.4 doğrulama)

Mock Nominatim yanıtı ile Vodafone Park koordinat doğrulaması.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.geocoding import Coordinates, GeocodingService


class TestNominatimGeocoding:
    async def test_vodafone_park_coordinates(self):
        """
        'Vodafone Park, İstanbul' → yaklaşık (41.0425, 29.0068) olmalı.
        """
        svc = GeocodingService()

        nominatim_response = [{"lat": "41.0425", "lon": "29.0068"}]

        mock_response = MagicMock()
        mock_response.json.return_value = nominatim_response
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        async def dummy_cache(key, cb, ttl=None):
            return await cb()

        with patch.object(svc, "_do_request", return_value=mock_response):
            # Cache'i geç (cache_hook'u bypass et)
            with patch.object(svc, "cache_hook", new=dummy_cache):
                result = await svc.geocode("Vodafone Park, İstanbul")

        assert result is not None
        assert isinstance(result, Coordinates)
        assert abs(result.lat - 41.0425) < 0.01
        assert abs(result.lon - 29.0068) < 0.01

    async def test_unknown_address_returns_none(self):
        """Nominatim boş dönünce ve Google key yoksa None döner."""
        svc = GeocodingService()

        mock_response = MagicMock()
        mock_response.json.return_value = []  # boş sonuç
        mock_response.headers = {}
        mock_response.raise_for_status = MagicMock()

        async def dummy_cache(key, cb, ttl=None):
            return await cb()

        with patch.object(svc, "_do_request", return_value=mock_response):
            with patch.object(svc, "cache_hook", new=dummy_cache):
                result = await svc.geocode("xyzxyzxyz bilinmeyen yer")

        assert result is None

    async def test_google_fallback_used_when_nominatim_fails(self):
        """Nominatim hata verince Google'a düşmeli."""
        svc = GeocodingService()

        call_count = {"n": 0}

        async def mock_fetch(method, url, **kwargs):
            call_count["n"] += 1
            if "nominatim" in url:
                raise Exception("nominatim down")
            # Google yanıtı
            mock = MagicMock()
            mock.json.return_value = {
                "status": "OK",
                "results": [{"geometry": {"location": {"lat": 41.04, "lng": 29.00}}}],
            }
            mock.headers = {}
            mock.raise_for_status = MagicMock()
            return mock

        async def dummy_cache(key, cb, ttl=None):
            return await cb()

        with patch("app.services.geocoding.settings") as mock_settings:
            mock_settings.GOOGLE_MAPS_API_KEY = "fake_key"
            mock_settings.REDIS_URL = "redis://localhost:6379"
            with patch.object(svc, "_do_request", side_effect=mock_fetch):
                with patch.object(svc, "cache_hook", new=dummy_cache):
                    result = await svc.geocode("Test Mekan")

        assert result is not None
        assert abs(result.lat - 41.04) < 0.01
