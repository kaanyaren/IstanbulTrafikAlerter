import asyncio
import logging
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.services.cache import cache_service
from app.services.event_service import EventService
from app.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

_DEFAULT_LOCATION_WKT = "SRID=4326;POINT(28.9784 41.0082)"  # İstanbul merkez


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 1].rstrip() + "…"


async def _record_source_health_metrics(
    source_health: dict[str, dict[str, int]],
    total_events: int,
    upserted_events: int,
) -> None:
    """Kaynak bazlı sağlık metriklerini Redis'te sakla ve raporla."""
    if not source_health:
        return

    now = datetime.now(timezone.utc)
    daily_key = f"source_health:{now.date().isoformat()}"

    existing = await cache_service.get(daily_key)
    if not isinstance(existing, dict):
        existing = {"runs": []}

    run_payload = {
        "timestamp": now.isoformat(),
        "total_events": total_events,
        "upserted_events": upserted_events,
        "sources": source_health,
    }

    runs = existing.get("runs", [])
    if not isinstance(runs, list):
        runs = []
    runs.append(run_payload)
    existing["runs"] = runs[-200:]

    await cache_service.set(daily_key, existing, ttl=7 * 24 * 3600)

    summary_parts = []
    for source, metrics in source_health.items():
        summary_parts.append(
            f"{source}=f:{metrics.get('fetched', 0)},u:{metrics.get('unique_added', 0)},e:{metrics.get('errors', 0)}"
        )

    logger.info(
        "Source health report | total=%d upserted=%d | %s",
        total_events,
        upserted_events,
        " | ".join(summary_parts),
    )


async def _fetch_and_store_events():
    """Fetch events from all adapters and upsert into Supabase."""
    svc = EventService()
    events = await svc.get_events()
    source_health = svc.last_source_health
    client = get_supabase_client()

    upserted = 0
    for event in events:
        event_name = _truncate((event.title or "").strip() or "İsimsiz Etkinlik", 255)
        venue_name = _truncate((event.venue or "").strip() or "Bilinmiyor", 255)

        start_time = event.start_at
        if start_time is None:
            start_time = datetime.now(timezone.utc)

        row = {
            "name": event_name,
            "description": event.description or "",
            "venue_name": venue_name,
            "category": event.category or "other",
            "source": event.source,
            "source_id": event.source_id,
            "start_time": start_time.isoformat(),
            "end_time": event.end_at.isoformat() if event.end_at else None,
        }

        # Add PostGIS point; table requires NOT NULL location.
        if event.lat is not None and event.lon is not None:
            row["location"] = f"SRID=4326;POINT({event.lon} {event.lat})"
        else:
            row["location"] = _DEFAULT_LOCATION_WKT

        try:
            client.table("events").upsert(
                row,
                on_conflict="source,source_id",
            ).execute()
            upserted += 1
        except Exception:
            logger.exception("Event upsert hatası: %s", event.dedup_key)

    logger.info("Events upserted: %d / %d", upserted, len(events))
    await _record_source_health_metrics(source_health, len(events), upserted)


@celery_app.task
def fetch_events_task():
    """
    Periodic task to fetch upcoming events from APIs and store in Supabase.
    """
    logger.info("Starting fetch_events_task...")
    asyncio.run(_fetch_and_store_events())
    return "Events fetched successfully"
