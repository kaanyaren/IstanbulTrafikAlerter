import asyncio
import logging
from app.celery_app import celery_app
from app.services.ibb_traffic_service import IBBTrafficService
from app.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


async def _fetch_and_store_traffic():
    """Fetch live traffic data from IBB and cache / log results."""
    svc = IBBTrafficService()
    zones = await svc.get_traffic_zones()
    client = get_supabase_client()

    logger.info("IBB trafik verisi: %d kayıt alındı.", len(zones))

    # Traffic data is transient; we log it but primarily use it for predictions.
    # For now we store a summary in Redis cache via the service layer.
    # Future: a dedicated traffic_snapshots table can be added.


@celery_app.task
def fetch_traffic_task():
    """
    Periodic task to fetch live traffic data and update cache.
    """
    logger.info("Starting fetch_traffic_task...")
    asyncio.run(_fetch_and_store_traffic())
    return "Traffic data fetched successfully"
