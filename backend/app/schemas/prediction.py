import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─── Prediction Schemas ────────────────────────────────────────────────────────

class PredictionCreate(BaseModel):
    zone_id: uuid.UUID
    event_id: Optional[uuid.UUID] = None
    predicted_at: datetime
    target_time: datetime
    congestion_score: int = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0.0, le=1.0)
    factors: Optional[dict[str, Any]] = None


class PredictionUpdate(BaseModel):
    congestion_score: Optional[int] = Field(None, ge=0, le=100)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    factors: Optional[dict[str, Any]] = None


class PredictionResponse(BaseModel):
    id: uuid.UUID
    zone_id: uuid.UUID
    event_id: Optional[uuid.UUID]
    predicted_at: datetime
    target_time: datetime
    congestion_score: int
    confidence: float
    factors: Optional[dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}
