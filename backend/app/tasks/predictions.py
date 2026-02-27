import asyncio
import logging
from app.celery_app import celery_app

logger = logging.getLogger(__name__)

from app.database import AsyncSessionLocal
from app.models.traffic_zone import TrafficZone
from app.prediction.rule_engine import predict
from app.models.prediction import Prediction
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

async def generate_predictions():
    async with AsyncSessionLocal() as session:
        # Get all zones
        zones_result = await session.execute(select(TrafficZone))
        zones = zones_result.scalars().all()
        
        now = datetime.now(timezone.utc)
        
        for zone in zones:
            for i in range(1, 25):
                target_time = now + timedelta(hours=i)
                pred_res = await predict(zone.id, target_time, session)
                
                prediction = Prediction(
                    zone_id=zone.id,
                    event_id=pred_res.event_id,
                    predicted_at=now,
                    target_time=target_time,
                    congestion_score=pred_res.congestion_score,
                    confidence=pred_res.confidence,
                    factors=pred_res.factors
                )
                session.add(prediction)
                
        await session.commit()

@celery_app.task
def run_predictions_task():
    """
    Periodic task to generate predictions for all zones for next 24 hours.
    """
    logger.info("Starting run_predictions_task...")
    asyncio.run(generate_predictions())
    return "Predictions generated successfully"
