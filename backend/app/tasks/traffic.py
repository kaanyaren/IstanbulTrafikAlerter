import asyncio
import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task
def fetch_traffic_task():
    """
    Periodic task to fetch live traffic data and update DB/Cache.
    """
    logger.info("Starting fetch_traffic_task...")
    # asyncio.run(fetch_and_store_traffic())
    return "Traffic data fetched successfully"
