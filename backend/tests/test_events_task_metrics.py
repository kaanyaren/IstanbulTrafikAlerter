from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.tasks.events import _record_source_health_metrics


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

    await _record_source_health_metrics(source_health, total_events=11, upserted_events=9)

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
