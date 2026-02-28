from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.services.event_service import (
  AKMEventsAdapter,
  BaseEventAdapter,
  BiletinialEventsAdapter,
  Event,
  EventService,
  IBBEventsPortalAdapter,
  IBBKulturAdapter,
  TFFFixtureAdapter,
)


async def _passthrough_cache(_cache_key, callback, _ttl):
    return await callback()


@pytest.mark.asyncio
async def test_ibb_kultur_schema_validation_filters_invalid_items():
    adapter = IBBKulturAdapter()
    adapter.cache_hook = AsyncMock(side_effect=_passthrough_cache)
    adapter.fetch = AsyncMock(
        return_value={
            "data": [
                {
                    "id": 1,
                    "name": "CRR Konseri",
                    "description": "Açıklama",
                    "startDate": "2026-03-01T20:00:00Z",
                    "category": "music",
                },
                {
                    "name": "Eksik ID",
                    "startDate": "2026-03-02T20:00:00Z",
                },
            ]
        }
    )

    events = await adapter.fetch_events()

    assert len(events) == 1
    assert events[0].source_id == "1"
    assert events[0].title == "CRR Konseri"
    assert events[0].start_at == datetime(2026, 3, 1, 20, 0, tzinfo=events[0].start_at.tzinfo)


@pytest.mark.asyncio
async def test_ibb_kultur_venue_prefers_specific_field_and_normalizes_generic_place():
    adapter = IBBKulturAdapter()
    adapter.cache_hook = AsyncMock(side_effect=_passthrough_cache)
    adapter.fetch = AsyncMock(
        return_value={
            "data": [
                {
                    "id": 1,
                    "name": "Genel Etkinlik",
                    "place": "İstanbul Şehir Tiyatroları",
                    "startDate": "2026-03-01T20:00:00Z",
                },
                {
                    "id": 2,
                    "name": "Salon Etkinliği",
                    "place": "İstanbul Şehir Tiyatroları",
                    "venueName": "Harbiye Cemil Topuzlu Açıkhava Tiyatrosu",
                    "startDate": "2026-03-02T20:00:00Z",
                },
            ]
        }
    )

    events = await adapter.fetch_events()

    assert len(events) == 2
    assert events[0].venue == "İstanbul"
    assert events[1].venue == "Harbiye Cemil Topuzlu Açıkhava Tiyatrosu"


@pytest.mark.asyncio
async def test_akm_adapter_parses_event_cards():
    adapter = AKMEventsAdapter()
    adapter.cache_hook = AsyncMock(side_effect=_passthrough_cache)
    adapter.fetch = AsyncMock(
        return_value="""
        <html>
          <body>
            <div class='card'>
              <a href='/tr/etkinlik/don-giovanni'>AKM Etkinlik - Don Giovanni</a>
              <span>Opera</span>
              <span>05 Mart</span>
            </div>
          </body>
        </html>
        """
    )

    events = await adapter.fetch_events()

    assert len(events) == 1
    assert events[0].source == "akm"
    assert events[0].source_id == "don-giovanni"
    assert events[0].title == "Don Giovanni"
    assert events[0].category == "opera"
    assert events[0].start_at is not None


@pytest.mark.asyncio
async def test_akm_adapter_falls_back_to_next_data_payload():
        adapter = AKMEventsAdapter()
        adapter.cache_hook = AsyncMock(side_effect=_passthrough_cache)
        adapter.fetch = AsyncMock(
                return_value="""
                <html>
                    <body>
                        <script id='__NEXT_DATA__' type='application/json'>
                            {"props":{"pageProps":{"events":[{"slug":"don-giovanni","title":"Don Giovanni Opera","date":"05 Mart"}]}}}
                        </script>
                    </body>
                </html>
                """
        )

        events = await adapter.fetch_events()

        assert len(events) == 1
        assert events[0].source_id == "don-giovanni"
        assert events[0].title == "Don Giovanni Opera"
        assert events[0].url.endswith("/tr/etkinlik/don-giovanni")


@pytest.mark.asyncio
async def test_tff_fixture_adapter_supports_branch_and_league_params():
    adapter = TFFFixtureAdapter(page_id=142, league="1-lig", branch="football")
    adapter.cache_hook = AsyncMock(side_effect=_passthrough_cache)
    adapter.fetch = AsyncMock(
        return_value="""
        <html>
          <body>
            <div class='match-row'>
              27.02.2026 20:00
              <a href='/Default.aspx?pageId=28&kulupID=10'>İSTANBULSPOR A.Ş.</a>
              <a href='/Default.aspx?pageId=29&macId=284135'>1 - 2</a>
              <a href='/Default.aspx?pageId=28&kulupID=11'>ALAGÖZ HOLDİNG IĞDIR FK</a>
            </div>
          </body>
        </html>
        """
    )

    events = await adapter.fetch_events()

    assert adapter.source_name == "tff_football_1-lig"
    assert len(events) == 1
    assert events[0].source_id == "284135"
    assert events[0].title == "İSTANBULSPOR A.Ş. vs ALAGÖZ HOLDİNG IĞDIR FK"
    assert events[0].start_at == datetime(2026, 2, 27, 20, 0)


@pytest.mark.asyncio
async def test_tff_fixture_adapter_uses_scoreline_regex_fallback_for_teams():
        adapter = TFFFixtureAdapter(page_id=198, league="super-lig", branch="football")
        adapter.cache_hook = AsyncMock(side_effect=_passthrough_cache)
        adapter.fetch = AsyncMock(
                return_value="""
                <html>
                    <body>
                        <div class='match-row'>
                            27.02.2026 20:00 FENERBAHÇE A.Ş. 1 - 2 GALATASARAY A.Ş.
                            <a href='/Default.aspx?pageId=29&macId=999'>1 - 2</a>
                        </div>
                    </body>
                </html>
                """
        )

        events = await adapter.fetch_events()

        assert len(events) == 1
        assert events[0].source_id == "999"
        assert events[0].title == "FENERBAHÇE A.Ş. vs GALATASARAY A.Ş."


@pytest.mark.asyncio
async def test_ibb_events_portal_adapter_parses_event_links():
    adapter = IBBEventsPortalAdapter()
    adapter.cache_hook = AsyncMock(side_effect=_passthrough_cache)
    adapter.fetch = AsyncMock(
        return_value="""
        <html>
          <body>
            <a href='/gundem/etkinlikler/crr-senfoni-orkestrasi-turnede'>CRR Senfoni Orkestrası Turnede</a>
          </body>
        </html>
        """
    )

    events = await adapter.fetch_events()

    assert len(events) == 1
    assert events[0].source == "ibb_events_portal"
    assert events[0].source_id == "crr-senfoni-orkestrasi-turnede"
    assert events[0].title == "CRR Senfoni Orkestrası Turnede"


@pytest.mark.asyncio
async def test_ibb_events_portal_adapter_falls_back_to_payload_paths():
    adapter = IBBEventsPortalAdapter()

    async def cache_side_effect(_key, callback, _ttl):
        return await callback()

    adapter.cache_hook = AsyncMock(side_effect=cache_side_effect)
    adapter.fetch = AsyncMock(
        side_effect=[
            """
            <html><body>
              <script src='/_nuxt/static/1700000000/gundem/etkinlikler/payload.js'></script>
            </body></html>
            """,
            "window.__NUXT__={links:['/gundem/etkinlikler/muze-gecesi-istanbul']}"
        ]
    )

    events = await adapter.fetch_events()

    assert len(events) == 1
    assert events[0].source_id == "muze-gecesi-istanbul"
    assert events[0].url.endswith("/gundem/etkinlikler/muze-gecesi-istanbul")


@pytest.mark.asyncio
async def test_biletinial_adapter_filters_to_istanbul_events():
    adapter = BiletinialEventsAdapter()

    async def cache_side_effect(_key, callback, _ttl):
        return await callback()

    adapter.cache_hook = AsyncMock(side_effect=cache_side_effect)
    adapter.fetch = AsyncMock(
        return_value="""
        <html>
          <body>
            <a href='/tr-tr/muzik/blue-'>Blue (İstanbul) Konseri İstanbul Avrupa / Volkswagen Arena 17 Nisan 2026</a>
            <a href='/tr-tr/muzik/ankara-etkinligi'>Ankara Konseri</a>
          </body>
        </html>
        """
    )

    events = await adapter.fetch_events()

    assert len(events) >= 1
    assert any(event.source_id == "blue-" for event in events)
    assert any(event.category == "music" for event in events)


@pytest.mark.asyncio
async def test_biletinial_adapter_accepts_istanbul_district_mentions():
        adapter = BiletinialEventsAdapter()

        async def cache_side_effect(_key, callback, _ttl):
                return await callback()

        adapter.cache_hook = AsyncMock(side_effect=cache_side_effect)
        adapter.fetch = AsyncMock(
                return_value="""
                <html>
                    <body>
                        <div><a href='/tr-tr/muzik/iksv-caz-aksamlari'>IKSV Caz Akşamları</a> Beşiktaş / Harbiye</div>
                        <a href='/tr-tr/muzik/ankara-etkinligi'>Ankara Konseri</a>
                    </body>
                </html>
                """
        )

        events = await adapter.fetch_events()

        assert any(event.source_id == "iksv-caz-aksamlari" for event in events)


@pytest.mark.asyncio
async def test_biletinial_adapter_falls_back_to_route_regex_extraction():
        adapter = BiletinialEventsAdapter()

        async def cache_side_effect(_key, callback, _ttl):
                return await callback()

        adapter.cache_hook = AsyncMock(side_effect=cache_side_effect)
        adapter.fetch = AsyncMock(
                return_value="""
                <html>
                    <body>
                        <script>
                            window.__DATA__={routes:["/tr-tr/muzik/mogollar-2026","/tr-tr/futbol/istanbul-derbisi"]}
                        </script>
                    </body>
                </html>
                """
        )

        events = await adapter.fetch_events()

        assert any(event.source_id == "mogollar-2026" for event in events)


@pytest.mark.asyncio
async def test_biletinial_adapter_uses_detail_page_for_istanbul_detection():
    adapter = BiletinialEventsAdapter()

    async def cache_side_effect(_key, callback, _ttl):
        return await callback()

    async def fetch_side_effect(url, **_kwargs):
        if url == "/tr-tr/muzik/demir-demirkan":
            return """
            <html><body>
              <a href='/tr-tr/mekan/blind-istanbul-7' title='Blind İstanbul'>Blind İstanbul</a>
              <a href='/tr-tr/mekan/dorock-xl-kadikoy-13' title='Dorock XL Kadıköy'>Dorock XL Kadıköy</a>
            </body></html>
            """
        return """
        <html>
          <body>
                                        <div>Birden fazla mekanda <a href='/tr-tr/muzik/demir-demirkan' title='Demir Demirkan'></a></div>
            <a href='/tr-tr/muzik/ankara-etkinligi'>Ankara Konseri</a>
          </body>
        </html>
        """

    adapter.cache_hook = AsyncMock(side_effect=cache_side_effect)
    adapter.fetch = AsyncMock(side_effect=fetch_side_effect)

    events = await adapter.fetch_events()

    demir_event = next((event for event in events if event.source_id == "demir-demirkan"), None)
    assert demir_event is not None
    assert demir_event.venue == "Blind İstanbul"
    assert demir_event.lat is not None
    assert demir_event.lon is not None


@pytest.mark.asyncio
async def test_biletinial_adapter_normalizes_generic_detail_venue():
        adapter = BiletinialEventsAdapter()

        async def cache_side_effect(_key, callback, _ttl):
                return await callback()

        async def fetch_side_effect(url, **_kwargs):
                if url == "/tr-tr/muzik/sehir-tiyatrolari-etkinligi":
                        return """
                        <html><body>
                            <a href='/tr-tr/mekan/istanbul-sehir-tiyatrolari-1' title='İstanbul Şehir Tiyatroları'>İstanbul Şehir Tiyatroları</a>
                        </body></html>
                        """
                return """
                <html>
                    <body>
                        <div>Birden fazla mekanda <a href='/tr-tr/muzik/sehir-tiyatrolari-etkinligi' title='Şehir Tiyatroları Etkinliği'></a></div>
                    </body>
                </html>
                """

        adapter.cache_hook = AsyncMock(side_effect=cache_side_effect)
        adapter.fetch = AsyncMock(side_effect=fetch_side_effect)

        events = await adapter.fetch_events()

        assert len(events) == 1
        assert events[0].source_id == "sehir-tiyatrolari-etkinligi"
        assert events[0].venue == "İstanbul"


class _DummyAdapter(BaseEventAdapter):
    def __init__(self, source: str):
        self._source = source

    @property
    def source_name(self) -> str:
        return self._source

    async def fetch_events(self) -> list[Event]:
        return []


def test_event_service_filters_enabled_connectors_only():
    adapters = [_DummyAdapter("ibb_kultur"), _DummyAdapter("akm"), _DummyAdapter("passo")]
    svc = EventService(
        adapters=adapters,
        enabled_connectors={"akm"},
        disabled_connectors=set(),
    )

    assert [adapter.source_name for adapter in svc.adapters] == ["akm"]


def test_event_service_filters_disabled_connectors():
    adapters = [_DummyAdapter("ibb_kultur"), _DummyAdapter("akm"), _DummyAdapter("passo")]
    svc = EventService(
        adapters=adapters,
        enabled_connectors={"*"},
        disabled_connectors={"passo"},
    )

    assert [adapter.source_name for adapter in svc.adapters] == ["ibb_kultur", "akm"]
