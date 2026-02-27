import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, cast
from geoalchemy2 import Geography

from app.models.traffic_zone import TrafficZone
from app.models.event import Event
from pydantic import BaseModel


class PredictionResult(BaseModel):
    zone_id: uuid.UUID
    target_time: datetime
    congestion_score: int
    confidence: float
    factors: dict
    event_id: Optional[uuid.UUID] = None


async def predict(
    zone_id: uuid.UUID,
    target_time: datetime,
    db_session: AsyncSession,
    is_raining: bool = False,
) -> PredictionResult:
    """
    Rules:
    1. base_score = zone.base_congestion_level * 100
    2. Saat 07-09, 17-19 arası -> +25 points
    3. Cuma, Cumartesi -> +15 points
    4. Bölge 2km çevresinde etkinlik var ve kapasite > 5.000 -> +20 points
    5. Etkinlik kapasite > 20.000 -> +15 ek puan
    6. Yağmur / kötü hava -> +10 points
    7. Toplam puan max 100
    """
    # 1. Fetch zone
    stmt = select(TrafficZone).where(TrafficZone.id == zone_id)
    result = await db_session.execute(stmt)
    zone = result.scalar_one_or_none()
    
    if not zone:
        raise ValueError(f"Zone {zone_id} not found")

    factors = {}
    base_score = zone.base_congestion_level * 100
    factors["base_score"] = float(base_score)
    score = base_score
    confidence = 0.8  # Default confidence for rule-based engine

    # 2. Rush hour (07-09, 17-19)
    # Using local time or UTC? The requirement implies local time for Istanbul, but target_time is timezone aware.
    # Assuming target_time is converted to local time or we just check hour.
    hour = target_time.hour
    if (7 <= hour < 9) or (17 <= hour < 19):
        score += 25
        factors["rush_hour"] = 25

    # 3. Friday (4) or Saturday (5)
    weekday = target_time.weekday()
    if weekday in (4, 5):
        score += 15
        factors["weekend_start"] = 15

    # 4 & 5. Events
    # Check if there's an event overlapping with target_time or close to it.
    # We will check if target_time is within [start_time - 2h, end_time + 1h]
    # If end_time is null, assume it lasts 4 hours.
    time_condition = or_(
        and_(
            Event.start_time - timedelta(hours=2) <= target_time,
            Event.end_time != None,
            Event.end_time + timedelta(hours=1) >= target_time,
        ),
        and_(
            Event.start_time - timedelta(hours=2) <= target_time,
            Event.end_time == None,
            Event.start_time + timedelta(hours=4) >= target_time,
        )
    )

    event_stmt = (
        select(Event)
        .where(
            func.ST_DWithin(
                cast(zone.polygon, Geography),
                cast(Event.location, Geography),
                2000  # meters
            ),
            Event.capacity > 5000,
            time_condition
        )
        .order_by(Event.capacity.desc())
        .limit(1)
    )

    event_result = await db_session.execute(event_stmt)
    event = event_result.scalar_one_or_none()

    event_id = None
    if event:
        event_id = event.id
        score += 20
        factors["event_nearby"] = 20
        if event.capacity and event.capacity > 20000:
            score += 15
            factors["large_event"] = 15

    # 6. Rain
    if is_raining:
        score += 10
        factors["rain"] = 10
        confidence = 0.7  # Weather reduces confidence slightly without real-time data

    # 7. Max 100 limit
    score = min(score, 100)
    score = max(score, 0)

    factors["total_score"] = float(score)

    return PredictionResult(
        zone_id=zone_id,
        target_time=target_time,
        congestion_score=int(score),
        confidence=confidence,
        factors=factors,
        event_id=event_id
    )
