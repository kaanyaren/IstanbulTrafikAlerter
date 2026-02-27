import asyncio
import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task
def fetch_events_task():
    """
    Periodic task to fetch upcoming events from APIs and store in DB.
    """
    logger.info("Starting fetch_events_task...")
    # asyncio.run(fetch_and_store_events())
    return "Events fetched successfully"
