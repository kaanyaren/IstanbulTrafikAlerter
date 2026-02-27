import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─── TrafficZone Schemas ───────────────────────────────────────────────────────

class PolygonCoordinates(BaseModel):
    """GeoJSON-style polygon — list of [lon, lat] ring coordinates."""
    type: str = "Polygon"
    coordinates: list[list[list[float]]]  # [[[lon, lat], ...]]


class TrafficZoneCreate(BaseModel):
    name: str = Field(..., max_length=255)
    # Accept GeoJSON polygon for input
    polygon: PolygonCoordinates
    base_congestion_level: float = Field(0.5, ge=0.0, le=1.0)
    rush_hour_multiplier: float = Field(1.5, ge=1.0)


class TrafficZoneUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    polygon: Optional[PolygonCoordinates] = None
    base_congestion_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    rush_hour_multiplier: Optional[float] = Field(None, ge=1.0)


class TrafficZoneResponse(BaseModel):
    id: uuid.UUID
    name: str
    polygon: PolygonCoordinates
    base_congestion_level: float
    rush_hour_multiplier: float
    created_at: datetime

    model_config = {"from_attributes": True}
