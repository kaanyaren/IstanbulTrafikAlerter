from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.services.event_service import Event
from app.tasks.events import _record_source_health_metrics
from app.tasks.events import _fetch_and_store_events


class _EventsTableStub:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def upsert(self, row: dict, on_conflict: str):
        self.rows.append({"row": row, "on_conflict": on_conflict})
        return self

    def execute(self):
        return {"ok": True}


class _SupabaseStub:
    def __init__(self) -> None:
        self.events_table = _EventsTableStub()

    def table(self, name: str):
        assert name == "events"
        return self.events_table


class _EventServiceStub:
    def __init__(self, events: list[Event], source_health: dict[str, dict[str, int]]) -> None:
        self._events = events
        self.last_source_health = source_health

    async def get_events(self) -> list[Event]:
        return self._events


@pytest.mark.asyncio
async def test_record_source_health_metrics_writes_daily_payload(monkeypatch):
    fake_get = AsyncMock(return_value={"runs": []})
    fake_set = AsyncMock(return_value=True)

    monkeypatch.setattr("app.tasks.events.cache_service.get", fake_get)
    monkeypatch.setattr("app.tasks.events.cache_service.set", fake_set)

    source_health = {
        "ibb_kultur": {"fetched": 10, "unique_added": 8, "errors": 0},
        "akm": {"fetched": 3, "unique_added": 3, "errors": 0},
    }

    await _record_source_health_metrics(
        source_health,
        total_events=11,
        upserted_events=9,
        top_source_venues=[{"source": "ibb_kultur", "venue_name": "Harbiye", "count": 4}],
    )

    assert fake_get.await_count == 1
    assert fake_set.await_count == 1

    _, kwargs = fake_set.await_args
    payload = kwargs.get("value") if "value" in kwargs else fake_set.await_args.args[1]
    assert "runs" in payload
    assert len(payload["runs"]) == 1

    run = payload["runs"][0]
    assert run["total_events"] == 11
    assert run["upserted_events"] == 9
    assert "ibb_kultur" in run["sources"]
    assert run["top_source_venues"] == [
        {"source": "ibb_kultur", "venue_name": "Harbiye", "count": 4}
    ]


@pytest.mark.asyncio
async def test_fetch_and_store_events_skips_missing_start_at(monkeypatch):
    valid_start = datetime(2026, 3, 1, 20, 0, tzinfo=timezone.utc)
    events = [
        Event(
            source="akm",
            source_id="akm-1",
            title="Valid Event",
            venue="AKM",
            start_at=valid_start,
            category="culture",
        ),
        Event(
            source="social_signal",
            source_id="signal-1",
            title="Signal Without Date",
            venue="İstanbul",
            start_at=None,
            category="other",
        ),
    ]
    source_health = {
        "akm": {"fetched": 1, "unique_added": 1, "errors": 0},
        "social_signal": {"fetched": 1, "unique_added": 1, "errors": 0},
    }

    svc = _EventServiceStub(events=events, source_health=source_health)
    supabase = _SupabaseStub()
    fake_record_metrics = AsyncMock(return_value=None)

    monkeypatch.setattr("app.tasks.events.EventService", lambda: svc)
    monkeypatch.setattr("app.tasks.events.get_supabase_client", lambda: supabase)
    monkeypatch.setattr("app.tasks.events._record_source_health_metrics", fake_record_metrics)

    await _fetch_and_store_events()

    assert len(supabase.events_table.rows) == 1
    inserted_row = supabase.events_table.rows[0]["row"]
    assert inserted_row["source"] == "akm"
    assert inserted_row["source_id"] == "akm-1"
    assert inserted_row["start_time"] == valid_start.isoformat()

    assert source_health["social_signal"]["missing_start_at"] == 1

    fake_record_metrics.assert_awaited_once()
    args = fake_record_metrics.await_args.args
    kwargs = fake_record_metrics.await_args.kwargs
    assert args == (source_health, 2, 1)
    assert kwargs["top_source_venues"] == [{"source": "akm", "venue_name": "AKM", "count": 1}]


@pytest.mark.asyncio
async def test_fetch_and_store_events_skips_all_rows_without_start_at(monkeypatch):
    events = [
        Event(
            source="social_signal",
            source_id="signal-1",
            title="Signal One",
            venue="İstanbul",
            start_at=None,
            category="other",
        ),
        Event(
            source="social_signal",
            source_id="signal-2",
            title="Signal Two",
            venue="İstanbul",
            start_at=None,
            category="other",
        ),
    ]
    source_health = {
        "social_signal": {"fetched": 2, "unique_added": 2, "errors": 0},
    }

    svc = _EventServiceStub(events=events, source_health=source_health)
    supabase = _SupabaseStub()
    fake_record_metrics = AsyncMock(return_value=None)

    monkeypatch.setattr("app.tasks.events.EventService", lambda: svc)
    monkeypatch.setattr("app.tasks.events.get_supabase_client", lambda: supabase)
    monkeypatch.setattr("app.tasks.events._record_source_health_metrics", fake_record_metrics)

    await _fetch_and_store_events()

    assert supabase.events_table.rows == []
    assert source_health["social_signal"]["missing_start_at"] == 2
    fake_record_metrics.assert_awaited_once()
    args = fake_record_metrics.await_args.args
    kwargs = fake_record_metrics.await_args.kwargs
    assert args == (source_health, 2, 0)
    assert kwargs["top_source_venues"] == []
