#!/usr/bin/env python
"""
Seed script for Istanbul traffic zones.

Usage (from the backend/ directory with venv active):
    python -m scripts.seed_zones

This creates the core İstanbul traffic zones used by the prediction engine.
"""
import asyncio
import sys
from pathlib import Path

# Ensure backend/app is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.models.traffic_zone import TrafficZone

# ─── Zone Definitions ─────────────────────────────────────────────────────────
# Polygons are rough bounding boxes — refine with actual district boundaries.
# Coordinates: [longitude, latitude] pairs (GeoJSON order)

ZONES = [
    {
        "name": "Taksim - Beyoğlu",
        "polygon_wkt": (
            "SRID=4326;POLYGON(("
            "28.969 41.028,"
            "28.990 41.028,"
            "28.990 41.040,"
            "28.969 41.040,"
            "28.969 41.028"
            "))"
        ),
        "base_congestion_level": 0.65,
        "rush_hour_multiplier": 1.8,
    },
    {
        "name": "Kadıköy",
        "polygon_wkt": (
            "SRID=4326;POLYGON(("
            "29.015 40.975,"
            "29.045 40.975,"
            "29.045 40.995,"
            "29.015 40.995,"
            "29.015 40.975"
            "))"
        ),
        "base_congestion_level": 0.60,
        "rush_hour_multiplier": 1.7,
    },
    {
        "name": "Beşiktaş",
        "polygon_wkt": (
            "SRID=4326;POLYGON(("
            "28.986 41.036,"
            "29.010 41.036,"
            "29.010 41.050,"
            "28.986 41.050,"
            "28.986 41.036"
            "))"
        ),
        "base_congestion_level": 0.55,
        "rush_hour_multiplier": 1.6,
    },
    {
        "name": "Fatih - Tarihi Yarımada",
        "polygon_wkt": (
            "SRID=4326;POLYGON(("
            "28.911 41.005,"
            "28.970 41.005,"
            "28.970 41.030,"
            "28.911 41.030,"
            "28.911 41.005"
            "))"
        ),
        "base_congestion_level": 0.50,
        "rush_hour_multiplier": 1.5,
    },
    {
        "name": "Şişli - Mecidiyeköy",
        "polygon_wkt": (
            "SRID=4326;POLYGON(("
            "28.979 41.050,"
            "29.005 41.050,"
            "29.005 41.070,"
            "28.979 41.070,"
            "28.979 41.050"
            "))"
        ),
        "base_congestion_level": 0.70,
        "rush_hour_multiplier": 1.9,
    },
    {
        "name": "Ümraniye",
        "polygon_wkt": (
            "SRID=4326;POLYGON(("
            "29.085 41.010,"
            "29.130 41.010,"
            "29.130 41.050,"
            "29.085 41.050,"
            "29.085 41.010"
            "))"
        ),
        "base_congestion_level": 0.55,
        "rush_hour_multiplier": 1.6,
    },
    {
        "name": "Maltepe - Kartal",
        "polygon_wkt": (
            "SRID=4326;POLYGON(("
            "29.120 40.900,"
            "29.200 40.900,"
            "29.200 40.940,"
            "29.120 40.940,"
            "29.120 40.900"
            "))"
        ),
        "base_congestion_level": 0.45,
        "rush_hour_multiplier": 1.5,
    },
    {
        "name": "Bakırköy - Florya",
        "polygon_wkt": (
            "SRID=4326;POLYGON(("
            "28.840 40.960,"
            "28.900 40.960,"
            "28.900 40.990,"
            "28.840 40.990,"
            "28.840 40.960"
            "))"
        ),
        "base_congestion_level": 0.50,
        "rush_hour_multiplier": 1.6,
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        print("Seeding traffic zones...")
        created = 0
        skipped = 0

        for zone_data in ZONES:
            # Check if already exists
            from sqlalchemy import select
            result = await session.execute(
                select(TrafficZone).where(TrafficZone.name == zone_data["name"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  [SKIP] {zone_data['name']} already exists")
                skipped += 1
                continue

            zone = TrafficZone(
                name=zone_data["name"],
                polygon=zone_data["polygon_wkt"],
                base_congestion_level=zone_data["base_congestion_level"],
                rush_hour_multiplier=zone_data["rush_hour_multiplier"],
            )
            session.add(zone)
            created += 1
            print(f"  [CREATE] {zone_data['name']}")

        await session.commit()
        print(f"\nDone! Created: {created}, Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(seed())
