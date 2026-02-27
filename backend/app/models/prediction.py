import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Prediction(Base):
    """Traffic congestion prediction for a specific zone at a specific time."""

    __tablename__ = "predictions"

    # Foreign keys
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("traffic_zones.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timing
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )  # when the prediction was made
    target_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )  # what time the prediction is for

    # Prediction values
    congestion_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0-1.0

    # Contributing factors as JSONB
    factors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    zone = relationship("TrafficZone", backref="predictions", lazy="select")
    event = relationship("Event", backref="predictions", lazy="select")

    __table_args__ = (
        Index("ix_predictions_zone_id", "zone_id"),
        Index("ix_predictions_target_time", "target_time"),
        Index("ix_predictions_zone_target", "zone_id", "target_time"),
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} zone_id={self.zone_id} "
            f"congestion={self.congestion_score} target={self.target_time}>"
        )
