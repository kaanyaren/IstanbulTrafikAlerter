from __future__ import annotations

import asyncio

from app.services.event_service import (
    AKMEventsAdapter,
    BiletinialEventsAdapter,
    ClubSitesAdapter,
    IBBEventsPortalAdapter,
    IBBDuyuruAdapter,
    IBBKulturAdapter,
    SeatGeekAdapter,
    TFFFixtureAdapter,
)


async def main() -> None:
    adapters = [
        IBBKulturAdapter(),
        IBBEventsPortalAdapter(),
        AKMEventsAdapter(),
        TFFFixtureAdapter(page_id=198, league="super-lig", branch="football"),
        TFFFixtureAdapter(page_id=142, league="1-lig", branch="football"),
        BiletinialEventsAdapter(),
        ClubSitesAdapter(),
        IBBDuyuruAdapter(),
        SeatGeekAdapter(),
    ]

    for adapter in adapters:
        try:
            events = await adapter.fetch_events()
            print(f"{adapter.source_name}: {len(events)}")
        except Exception as error:
            print(f"{adapter.source_name}: ERR {type(error).__name__} {error}")


if __name__ == "__main__":
    asyncio.run(main())
