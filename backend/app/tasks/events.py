import asyncio
import logging
from app.celery_app import celery_app
from app.services.event_service import EventService
from app.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


async def _fetch_and_store_events():
    """Fetch events from all adapters and upsert into Supabase."""
    svc = EventService()
    events = await svc.get_events()
    client = get_supabase_client()

    upserted = 0
    for event in events:
        row = {
            "name": event.title,
            "description": event.description or "",
            "venue_name": event.venue or "Bilinmiyor",
            "category": event.category or "other",
            "source": event.source,
            "source_id": event.source_id,
            "start_time": event.start_at.isoformat() if event.start_at else None,
            "end_time": event.end_at.isoformat() if event.end_at else None,
        }

        # Add PostGIS point if coords available
        if event.lat is not None and event.lon is not None:
            row["location"] = f"SRID=4326;POINT({event.lon} {event.lat})"

        try:
            client.table("events").upsert(
                row,
                on_conflict="source,source_id",
            ).execute()
            upserted += 1
        except Exception:
            logger.exception("Event upsert hatası: %s", event.dedup_key)

    logger.info("Events upserted: %d / %d", upserted, len(events))


@celery_app.task
def fetch_events_task():
    """
    Periodic task to fetch upcoming events from APIs and store in Supabase.
    """
    logger.info("Starting fetch_events_task...")
    asyncio.run(_fetch_and_store_events())
    return "Events fetched successfully"
