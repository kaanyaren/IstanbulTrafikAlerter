import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, cast
from geoalchemy2 import Geography

from app.database import get_db
from app.models.prediction import Prediction
from app.models.traffic_zone import TrafficZone

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])


@router.get("", response_model=dict)
async def get_predictions_by_location(
    lat: float = Query(...),
    lon: float = Query(...),
    target_time: datetime = Query(...),
    radius_km: float = Query(5.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns predictions for zones within radius_km of the specified location.
    Response is in GeoJSON format.
    """
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    
    stmt = (
        select(Prediction, func.ST_AsGeoJSON(TrafficZone.polygon).label("geom_json"))
        .join(TrafficZone, Prediction.zone_id == TrafficZone.id)
        .where(
            func.ST_DWithin(
                cast(TrafficZone.polygon, Geography),
                cast(point, Geography),
                radius_km * 1000
            ),
            # match closest prediction to target_time
            Prediction.target_time == target_time
        )
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    features = []
    for pred, geom_json in rows:
        geom = json.loads(geom_json)
        feature = {
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "prediction_id": str(pred.id),
                "zone_id": str(pred.zone_id),
                "event_id": str(pred.event_id) if pred.event_id else None,
                "target_time": pred.target_time.isoformat(),
                "congestion_score": pred.congestion_score,
                "confidence": pred.confidence,
                "factors": pred.factors
            }
        }
        features.append(feature)
        
    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.get("/zones/{zone_id}", response_model=dict)
async def get_zone_predictions(
    zone_id: uuid.UUID = Path(...),
    hours_ahead: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns timeseries predictions for a specific zone up to hours_ahead.
    Response is GeoJSON format.
    """
    now = datetime.now(timezone.utc)
    end_time = now + timedelta(hours=hours_ahead)
    
    stmt = (
        select(Prediction, func.ST_AsGeoJSON(TrafficZone.polygon).label("geom_json"))
        .join(TrafficZone, Prediction.zone_id == TrafficZone.id)
        .where(
            Prediction.zone_id == zone_id,
            Prediction.target_time >= now,
            Prediction.target_time <= end_time
        )
        .order_by(Prediction.target_time.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    if not rows:
        return {"type": "FeatureCollection", "features": []}
        
    geom = json.loads(rows[0].geom_json)
    
    timeseries = []
    for pred, _ in rows:
        timeseries.append({
            "prediction_id": str(pred.id),
            "target_time": pred.target_time.isoformat(),
            "congestion_score": pred.congestion_score,
            "confidence": pred.confidence,
            "factors": pred.factors
        })
        
    feature = {
        "type": "Feature",
        "geometry": geom,
        "properties": {
            "zone_id": str(zone_id),
            "predictions": timeseries
        }
    }
    
    return {
        "type": "FeatureCollection",
        "features": [feature]
    }
