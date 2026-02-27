import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ─── Event Schemas ────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    venue_name: str = Field(..., max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    start_time: datetime
    end_time: Optional[datetime] = None
    capacity: Optional[int] = Field(None, ge=0)
    category: str = Field(..., pattern="^(concert|sports|conference|other)$")
    source: str = Field(..., max_length=100)
    source_id: str = Field(..., max_length=255)


class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    venue_name: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    capacity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, pattern="^(concert|sports|conference|other)$")


class EventResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    venue_name: str
    latitude: float
    longitude: float
    start_time: datetime
    end_time: Optional[datetime]
    capacity: Optional[int]
    category: str
    source: str
    source_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
