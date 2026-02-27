import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Event(Base):
    """Represents a city event (concert, sports, conference, etc.) that may affect traffic."""

    __tablename__ = "events"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    venue_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Location — PostGIS POINT with SRID 4326 (WGS84)
    location: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    # Timing
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Details
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # concert | sports | conference | other

    # Source tracking
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamps
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    )

    __table_args__ = (
        Index("ix_events_start_time", "start_time"),
        Index("ix_events_category", "category"),
        Index("ix_events_source_source_id", "source", "source_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} name={self.name!r} category={self.category!r}>"
