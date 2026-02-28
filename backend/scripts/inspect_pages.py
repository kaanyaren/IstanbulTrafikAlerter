from __future__ import annotations

import re

import httpx


def inspect(url: str, pattern: str) -> None:
    text = httpx.get(url, follow_redirects=True, timeout=20.0).text
    print("URL:", url)
    print("len:", len(text))
    print("contains payload.js:", "payload.js" in text)
    print("contains _nuxt/static:", "_nuxt/static" in text)
    print("contains __NEXT_DATA__:", "__NEXT_DATA__" in text)
    print("contains application/ld+json:", "application/ld+json" in text)
    print("pattern in html:", pattern in text)
    print("count of 'event':", text.lower().count("event"))
    match = re.search(r"/_nuxt/static/[^\"']+/[\w\-/]+/payload\.js", text)
    print("payload path:", match.group(0) if match else None)
    print("-----")


if __name__ == "__main__":
    inspect("https://www.akmistanbul.gov.tr/tr/etkinlikler", "/tr/etkinlik/")
    inspect("https://www.ibb.istanbul/gundem/etkinlikler", "/gundem/etkinlikler/")
    inspect("https://www.ibb.istanbul/gundem/duyurular", "/gundem/duyurular/")
