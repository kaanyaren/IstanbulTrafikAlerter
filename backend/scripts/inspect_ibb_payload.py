from __future__ import annotations

import asyncio
import re

from app.services.event_service import IBBEventsPortalAdapter, IBBDuyuruAdapter


async def inspect(adapter, endpoint_prefix: str) -> None:
    html = await adapter.fetch(adapter._ENDPOINT)
    html_paths = re.findall(r"/_nuxt/static/[^\"'\s)]+", html)
    print(f"[{adapter.source_name}] html payload refs:", len(html_paths))
    if html_paths:
        print("first payload path:", html_paths[0])

    payload_text = ""
    for path in html_paths:
        if not path.endswith("payload.js"):
            continue
        try:
            payload_text = await adapter.fetch(path)
            if payload_text:
                break
        except Exception as error:
            print("payload fetch error:", type(error).__name__, error)

    print("payload length:", len(payload_text))
    print("payload head:", payload_text[:400].replace("\n", " "))
    normalized = payload_text.replace("\\/", "/")
    direct = re.findall(rf"{re.escape(endpoint_prefix)}/[a-z0-9\-]+", normalized)
    print("direct links found:", len(set(direct)))
    if direct:
        print("sample links:", sorted(set(direct))[:5])
    for pattern in (
        r'"slug"\s*:\s*"([^"]+)"',
        r'"url"\s*:\s*"([^"]+)"',
        r'"path"\s*:\s*"([^"]+)"',
        r'"title"\s*:\s*"([^"]+)"',
    ):
        matches = re.findall(pattern, normalized)
        print(f"pattern {pattern} count:", len(matches))
        if matches:
            print("sample:", matches[:5])
    print("contains escaped prefix:", endpoint_prefix.replace("/", "\\/") in payload_text)
    print("---")


async def main() -> None:
    await inspect(IBBEventsPortalAdapter(), "/gundem/etkinlikler")
    await inspect(IBBDuyuruAdapter(), "/gundem/duyurular")


if __name__ == "__main__":
    asyncio.run(main())
