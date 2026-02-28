import asyncio
import logging
from collections import Counter
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
    top_source_venues: list[dict[str, int | str]] | None = None,
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
        "top_source_venues": top_source_venues or [],
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

    venue_summary = ", ".join(
        f"{item['source']}|{item['venue_name']}:{item['count']}" for item in (top_source_venues or [])
    )

    logger.info(
        "Source health report | total=%d upserted=%d | %s | top_source_venues=%s",
        total_events,
        upserted_events,
        " | ".join(summary_parts),
        venue_summary or "none",
    )


async def _fetch_and_store_events():
    """Fetch events from all adapters and upsert into Supabase."""
    svc = EventService()
    events = await svc.get_events()
    source_health = svc.last_source_health
    client = get_supabase_client()

    upserted = 0
    skipped_missing_start_at = 0
    skipped_by_source: dict[str, int] = {}
    source_venue_counter: Counter[tuple[str, str]] = Counter()
    for event in events:
        event_name = _truncate((event.title or "").strip() or "İsimsiz Etkinlik", 255)
        venue_name = _truncate((event.venue or "").strip() or "Bilinmiyor", 255)

        start_time = event.start_at
        if start_time is None:
            skipped_missing_start_at += 1
            skipped_by_source[event.source] = skipped_by_source.get(event.source, 0) + 1
            logger.warning(
                "Skipping event without start_at: source=%s source_id=%s",
                event.source,
                event.source_id,
            )
            continue

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
            source_venue_counter[(event.source, venue_name)] += 1
        except Exception:
            logger.exception("Event upsert hatası: %s", event.dedup_key)

    if skipped_by_source:
        for source, skipped_count in skipped_by_source.items():
            metrics = source_health.get(source)
            if not isinstance(metrics, dict):
                source_health[source] = {
                    "fetched": 0,
                    "unique_added": 0,
                    "errors": 0,
                    "missing_start_at": skipped_count,
                }
                continue

            metrics["missing_start_at"] = metrics.get("missing_start_at", 0) + skipped_count

    logger.info(
        "Events upserted: %d / %d (skipped_missing_start_at=%d)",
        upserted,
        len(events),
        skipped_missing_start_at,
    )
    top_source_venues = [
        {"source": source, "venue_name": venue_name, "count": count}
        for (source, venue_name), count in source_venue_counter.most_common(10)
    ]
    await _record_source_health_metrics(
        source_health,
        len(events),
        upserted,
        top_source_venues=top_source_venues,
    )


@celery_app.task
def fetch_events_task():
    """
    Periodic task to fetch upcoming events from APIs and store in Supabase.
    """
    logger.info("Starting fetch_events_task...")
    asyncio.run(_fetch_and_store_events())
    return "Events fetched successfully"
