import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TrafficZone(Base):
    """Represents a geographic zone in Istanbul for traffic analysis."""

    __tablename__ = "traffic_zones"

    # Zone info
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Location — PostGIS POLYGON with SRID 4326
    polygon: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )

    # Congestion characteristics
    base_congestion_level: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5
    )  # 0.0 - 1.0 scale
    rush_hour_multiplier: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.5
    )  # multiplier during rush hours

    __table_args__ = (
        Index("ix_traffic_zones_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<TrafficZone id={self.id} name={self.name!r} base_congestion={self.base_congestion_level}>"
