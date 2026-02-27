import uuid
from datetime import datetime
from typing import Optional, Sequence

from geoalchemy2.functions import ST_DWithin, ST_GeogFromWKB, ST_MakePoint, ST_SetSRID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


class EventRepository:
    """Repository for Event model database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ─── Create ───────────────────────────────────────────────────────────────

    async def create(
        self,
        *,
        name: str,
        venue_name: str,
        latitude: float,
        longitude: float,
        start_time: datetime,
        category: str,
        source: str,
        source_id: str,
        description: Optional[str] = None,
        end_time: Optional[datetime] = None,
        capacity: Optional[int] = None,
    ) -> Event:
        """Create and persist a new Event."""
        location = f"SRID=4326;POINT({longitude} {latitude})"
        event = Event(
            name=name,
            description=description,
            venue_name=venue_name,
            location=location,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            category=category,
            source=source,
            source_id=source_id,
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    # ─── Read ─────────────────────────────────────────────────────────────────

    async def get_by_id(self, event_id: uuid.UUID) -> Optional[Event]:
        """Fetch a single Event by primary key."""
        result = await self.session.execute(
            select(Event).where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> Sequence[Event]:
        """List all events with pagination."""
        result = await self.session.execute(
            select(Event).order_by(Event.start_time).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def find_near_location(
        self,
        lat: float,
        lon: float,
        radius_km: float,
    ) -> Sequence[Event]:
        """Find events within radius_km kilometres of the given point.

        Uses PostGIS ST_DWithin with geography cast for accurate distance
        calculation (radius in metres).
        """
        radius_m = radius_km * 1000
        point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)

        result = await self.session.execute(
            select(Event).where(
                ST_DWithin(
                    ST_GeogFromWKB(Event.location),
                    ST_GeogFromWKB(point),
                    radius_m,
                )
            ).order_by(Event.start_time)
        )
        return result.scalars().all()

    async def find_by_date_range(
        self,
        start: datetime,
        end: datetime,
    ) -> Sequence[Event]:
        """Find events whose start_time falls within [start, end]."""
        result = await self.session.execute(
            select(Event)
            .where(Event.start_time >= start, Event.start_time <= end)
            .order_by(Event.start_time)
        )
        return result.scalars().all()

    # ─── Update ───────────────────────────────────────────────────────────────

    async def update(self, event: Event, **kwargs) -> Event:
        """Update fields on an existing Event."""
        for key, value in kwargs.items():
            if hasattr(event, key) and value is not None:
                setattr(event, key, value)
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    # ─── Delete ───────────────────────────────────────────────────────────────

    async def delete(self, event: Event) -> None:
        """Delete an Event from the database."""
        await self.session.delete(event)
        await self.session.flush()
