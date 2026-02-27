import asyncio
import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)

from app.database import AsyncSessionLocal
from app.models.traffic_zone import TrafficZone
from app.prediction.rule_engine import predict
from app.supabase_client import get_supabase_client
from sqlalchemy import select
from datetime import datetime, timezone, timedelta


async def generate_predictions():
    """Generate predictions for all zones and write to Supabase."""
    client = get_supabase_client()

    async with AsyncSessionLocal() as session:
        # Get all zones
        zones_result = await session.execute(select(TrafficZone))
        zones = zones_result.scalars().all()

        now = datetime.now(timezone.utc)
        rows_to_insert = []

        for zone in zones:
            for i in range(1, 25):
                target_time = now + timedelta(hours=i)
                pred_res = await predict(zone.id, target_time, session)

                row = {
                    "zone_id": str(pred_res.zone_id),
                    "predicted_at": now.isoformat(),
                    "target_time": target_time.isoformat(),
                    "congestion_score": pred_res.congestion_score,
                    "confidence": pred_res.confidence,
                    "factors": pred_res.factors,
                }
                if pred_res.event_id:
                    row["event_id"] = str(pred_res.event_id)

                rows_to_insert.append(row)

    # Batch insert into Supabase (chunks of 100)
    chunk_size = 100
    inserted = 0
    for i in range(0, len(rows_to_insert), chunk_size):
        chunk = rows_to_insert[i : i + chunk_size]
        try:
            client.table("predictions").insert(chunk).execute()
            inserted += len(chunk)
        except Exception:
            logger.exception("Prediction insert hatası (chunk %d)", i)

    logger.info("Predictions inserted: %d / %d", inserted, len(rows_to_insert))


@celery_app.task
def run_predictions_task():
    """
    Periodic task to generate predictions for all zones for next 24 hours.
    Results are written directly to Supabase.
    """
    logger.info("Starting run_predictions_task...")
    asyncio.run(generate_predictions())
    return "Predictions generated successfully"
