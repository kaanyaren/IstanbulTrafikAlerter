from __future__ import annotations

import asyncio
from collections import Counter

from app.services.event_service import EventService


async def main() -> None:
    svc = EventService()
    events = await svc.get_events()

    print(f"TOTAL_EVENTS={len(events)}")
    print("SOURCES=")
    for source, count in Counter(event.source for event in events).most_common():
        print(f"  - {source}: {count}")

    print("\nSAMPLE_EVENTS=")
    for event in events[:30]:
        print(f"  - [{event.source}] {event.title} | {event.start_at} | {event.url}")

    print("\nSOURCE_HEALTH=")
    for source, metrics in svc.last_source_health.items():
        print(f"  - {source}: {metrics}")


if __name__ == "__main__":
    asyncio.run(main())
