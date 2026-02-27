import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure backend/app is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.repositories.event_repo import EventRepository


async def test_find_near_location():
    async with AsyncSessionLocal() as session:
        repo = EventRepository(session)
        
        # 1. Create a test event in Kadıköy (approx)
        test_event = await repo.create(
            name="Test Concert",
            venue_name="Kadıköy Meydan",
            latitude=40.990,
            longitude=29.020,
            start_time=datetime.now(timezone.utc) + timedelta(days=1),
            category="concert",
            source="test",
            source_id="test_001"
        )
        print(f"Created event: {test_event}")
        
        # 2. Search within 2km from a nearby point
        print("\nSearching within 2km...")
        nearby_events = await repo.find_near_location(
            lat=40.995,
            lon=29.025,
            radius_km=2.0
        )
        
        found = False
        for ev in nearby_events:
            print(f"Found: {ev.name} at {ev.venue_name}")
            if ev.id == test_event.id:
                found = True
                
        if found:
            print("\n✅ Test passed! The event was found within the radius.")
        else:
            print("\n❌ Test failed! The event was not found.")
            
        # Cleanup
        await repo.delete(test_event)
        print("Test event cleaned up.")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(test_find_near_location())
