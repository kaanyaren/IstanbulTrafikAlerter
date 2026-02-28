"""
Etkinlik Veri Servisi (Görev 2.3)

İki kaynak adaptörü:
1. IBBKulturAdapter   — İBB Kültür açık veri API
2. SeatGeekAdapter    — SeatGeek açık API (API key gereksiz, İstanbul sorgusu)

Event modeli normalize edilir; duplikasyon (source + source_id) ile kontrol edilir.
"""

from __future__ import annotations

import logging
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError

from app.config import settings
from app.services.base_api import BaseAPIService

logger = logging.getLogger(__name__)

CACHE_TTL = 30 * 60  # 30 dakika

_TR_MONTHS: dict[str, int] = {
    "ocak": 1,
    "şubat": 2,
    "subat": 2,
    "mart": 3,
    "nisan": 4,
    "mayıs": 5,
    "mayis": 5,
    "haziran": 6,
    "temmuz": 7,
    "ağustos": 8,
    "agustos": 8,
    "eylül": 9,
    "eylul": 9,
    "ekim": 10,
    "kasım": 11,
    "kasim": 11,
    "aralık": 12,
    "aralik": 12,
}

_AKM_CATEGORY_KEYWORDS: dict[str, str] = {
    "opera": "opera",
    "tiyatro": "theatre",
    "konser": "concert",
    "müzik": "music",
    "muzik": "music",
    "dans": "dance",
    "bale": "ballet",
    "festival": "festival",
    "stand-up": "standup",
    "atölye": "workshop",
    "atolye": "workshop",
    "panel": "panel",
}

_TFF_DATETIME_RE = re.compile(r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+(?P<time>\d{2}:\d{2})")
_TR_DATE_YEAR_RE = re.compile(
    r"(?P<day>\d{1,2})\s+"
    r"(?P<month>Ocak|Şubat|Subat|Mart|Nisan|Mayıs|Mayis|Haziran|Temmuz|Ağustos|Agustos|Eylül|Eylul|Ekim|Kasım|Kasim|Aralık|Aralik)"
    r"(?:\s+(?P<year>\d{4}))?",
    re.IGNORECASE,
)
_AKM_DATE_RE = re.compile(
    r"(?P<day>\d{1,2})(?:[-/]\d{1,2})?\s+"
    r"(?P<month>Ocak|Şubat|Subat|Mart|Nisan|Mayıs|Mayis|Haziran|Temmuz|Ağustos|Agustos|Eylül|Eylul|Ekim|Kasım|Kasim|Aralık|Aralik)",
    re.IGNORECASE,
)

_SPORT_KEYWORDS = (
    "maç",
    "mac",
    "fikstür",
    "futbol",
    "basketbol",
    "voleybol",
    "biletleri",
)


def _search_text(value: str) -> str:
    table = str.maketrans(
        {
            "ı": "i",
            "İ": "i",
            "ş": "s",
            "Ş": "s",
            "ğ": "g",
            "Ğ": "g",
            "ü": "u",
            "Ü": "u",
            "ö": "o",
            "Ö": "o",
            "ç": "c",
            "Ç": "c",
        }
    )
    return value.translate(table).casefold()


def _parse_turkish_date(text: str, default_year: int | None = None) -> datetime | None:
    match = _TR_DATE_YEAR_RE.search(text)
    if not match:
        return None

    day = int(match.group("day"))
    month = _TR_MONTHS.get(match.group("month").lower())
    if not month:
        return None

    year = int(match.group("year")) if match.group("year") else (default_year or datetime.now().year)

    try:
        return datetime(year, month, day)
    except ValueError:
        return None


def _extract_slug_from_href(href: str) -> str:
    return href.rstrip("/").split("/")[-1]


def _humanize_slug(slug: str) -> str:
    return re.sub(r"[-_]+", " ", slug).strip().title()


def _extract_paths_from_text(text: str, prefix: str) -> list[str]:
    pattern = re.compile(rf"{re.escape(prefix)}/[^\"'\s)]+", re.IGNORECASE)
    return sorted(set(pattern.findall(text or "")))


def _extract_ibb_items_from_text(
    text: str,
    section_prefix: str,
    source_name: str,
    source_id_prefix: str = "",
    category_fallback: str = "culture",
) -> list[Event]:
    normalized = (text or "").replace("\\/", "/")
    seen: set[str] = set()
    events: list[Event] = []
    for path in _extract_paths_from_text(normalized, section_prefix):
        slug = _extract_slug_from_href(path)
        if (
            not slug
            or slug in {"etkinlikler", "duyurular"}
            or slug.endswith(".js")
            or slug in {"state.js", "payload.js"}
        ):
            continue
        source_id = f"{source_id_prefix}{slug}" if source_id_prefix else slug
        if source_id in seen:
            continue
        seen.add(source_id)
        title = _humanize_slug(slug)
        events.append(
            Event(
                source=source_name,
                source_id=source_id,
                title=title,
                venue="İstanbul",
                start_at=_parse_turkish_date(title),
                url=urljoin("https://www.ibb.istanbul", path),
                category=_infer_category(title, fallback=category_fallback),
            )
        )
    return events


def _walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _infer_category(text: str, fallback: str = "other") -> str:
    lowered = _search_text(text)
    if any(keyword in lowered for keyword in ("konser", "müzik", "muzik", "opera", "bale")):
        return "music"
    if any(keyword in lowered for keyword in _SPORT_KEYWORDS):
        return "sport"
    if any(keyword in lowered for keyword in ("miting", "buluşma", "toplantı", "toplanti", "duyuru")):
        return "political"
    if any(keyword in lowered for keyword in ("tiyatro", "festival", "gösteri", "gosteri", "etkinlik")):
        return "culture"
    return fallback


def _parse_connector_csv(raw: str) -> set[str]:
    items = [part.strip().lower() for part in (raw or "").split(",") if part.strip()]
    return set(items)


# ------------------------------------------------------------------
# Pydantic schema
# ------------------------------------------------------------------

class Event(BaseModel):
    """Normalize edilmiş etkinlik modeli."""

    source: str
    source_id: str
    title: str
    description: str = ""
    venue: str = ""
    city: str = "İstanbul"
    lat: float | None = None
    lon: float | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    url: str = ""
    category: str = ""

    @property
    def dedup_key(self) -> str:
        return f"{self.source}:{self.source_id}"


class IBBKulturEventSchema(BaseModel):
    """İBB Kültür response item şema doğrulaması."""

    model_config = ConfigDict(extra="ignore")

    source_id: str | int = Field(validation_alias=AliasChoices("id", "Id"))
    title: str = Field(validation_alias=AliasChoices("name", "Name"))
    description: str = Field(default="", validation_alias=AliasChoices("description", "Description"))
    venue: str = Field(default="", validation_alias=AliasChoices("place", "Place"))
    start_raw: str | None = Field(default=None, validation_alias=AliasChoices("startDate", "StartDate"))
    end_raw: str | None = Field(default=None, validation_alias=AliasChoices("endDate", "EndDate"))
    url: str = Field(default="", validation_alias=AliasChoices("url", "Url"))
    category: str = Field(default="", validation_alias=AliasChoices("category", "Category"))


# ------------------------------------------------------------------
# Soyut adaptör
# ------------------------------------------------------------------

class BaseEventAdapter(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    async def fetch_events(self) -> list[Event]: ...


# ------------------------------------------------------------------
# Adaptör 1: İBB Kültür API
# ------------------------------------------------------------------

class IBBKulturAdapter(BaseAPIService, BaseEventAdapter):
    """İBB Kültür portalından etkinlik çeker."""

    _BASE = "https://kultursanat.ibb.istanbul"
    _ENDPOINT = "/api/event/geteventlist"

    @property
    def source_name(self) -> str:
        return "ibb_kultur"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=15.0)

    async def fetch(self, url: str, **kwargs: Any) -> Any:
        response = await self.request("GET", url, **kwargs)
        return response.json()

    async def fetch_events(self) -> list[Event]:
        cache_key = "events:ibb_kultur"

        async def _fetch() -> list[dict]:
            try:
                data = await self.fetch(
                    self._ENDPOINT,
                    params={"pageSize": 50, "pageIndex": 0},
                )
                return data if isinstance(data, list) else data.get("data", [])
            except Exception:
                logger.exception("IBBKultur fetch hatası")
                return []

        raw = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        events: list[Event] = []
        for item in (raw or []):
            try:
                parsed = IBBKulturEventSchema.model_validate(item)
                events.append(
                    Event(
                        source=self.source_name,
                        source_id=str(parsed.source_id),
                        title=parsed.title,
                        description=parsed.description,
                        venue=parsed.venue,
                        start_at=self._parse_dt(parsed.start_raw),
                        end_at=self._parse_dt(parsed.end_raw),
                        url=parsed.url,
                        category=parsed.category,
                    )
                )
            except ValidationError:
                logger.debug("IBBKultur şema doğrulama hatası: %s", item)
            except Exception:
                logger.debug("IBBKultur parse hatası: %s", item)
        return events

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None


# ------------------------------------------------------------------
# Adaptör 2: SeatGeek API (ücretsiz, İstanbul filtreleme)
# ------------------------------------------------------------------

class SeatGeekAdapter(BaseAPIService, BaseEventAdapter):
    """SeatGeek açık API — İstanbul etkinlikleri."""

    _BASE = "https://api.seatgeek.com"
    _ENDPOINT = "/2/events"

    @property
    def source_name(self) -> str:
        return "seatgeek"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=15.0)

    async def fetch(self, url: str, **kwargs: Any) -> Any:
        response = await self.request("GET", url, **kwargs)
        return response.json()

    async def fetch_events(self) -> list[Event]:
        cache_key = "events:seatgeek:istanbul"

        async def _fetch() -> list[dict]:
            try:
                data = await self.fetch(
                    self._ENDPOINT,
                    params={
                        "venue.city": "Istanbul",
                        "per_page": 50,
                        "sort": "datetime_local.asc",
                    },
                )
                return data.get("events", [])
            except Exception:
                logger.exception("SeatGeek fetch hatası")
                return []

        raw = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        events: list[Event] = []
        for item in (raw or []):
            try:
                venue = item.get("venue", {})
                events.append(
                    Event(
                        source=self.source_name,
                        source_id=str(item.get("id", "")),
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        venue=venue.get("name", ""),
                        city=venue.get("city", "İstanbul"),
                        lat=venue.get("location", {}).get("lat"),
                        lon=venue.get("location", {}).get("lon"),
                        start_at=self._parse_dt(item.get("datetime_local")),
                        url=item.get("url", ""),
                        category=item.get("type", ""),
                    )
                )
            except Exception:
                logger.debug("SeatGeek parse hatası: %s", item)
        return events

    @staticmethod
    def _parse_dt(value: Any) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except Exception:
            return None


class AKMEventsAdapter(BaseAPIService, BaseEventAdapter):
    """AKM etkinlik listesi sayfasından event parse eder."""

    _BASE = "https://www.akmistanbul.gov.tr"
    _ENDPOINT = "/tr/etkinlikler"

    @property
    def source_name(self) -> str:
        return "akm"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=20.0)

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        cache_key = "events:akm"

        async def _fetch() -> str:
            try:
                return await self.fetch(self._ENDPOINT)
            except Exception:
                logger.exception("AKM fetch hatası")
                return ""

        html = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        seen: set[str] = set()

        for anchor in soup.select('a[href*="/tr/etkinlik/"]'):
            href = anchor.get("href")
            if not href:
                continue

            absolute_url = urljoin(self._BASE, href)
            source_id = self._extract_slug(href)
            if not source_id or source_id in seen:
                continue

            card = anchor.find_parent(["article", "li", "div"]) or anchor
            card_text = card.get_text(" ", strip=True)
            title = self._extract_title(anchor)
            if not title:
                continue

            seen.add(source_id)
            events.append(
                Event(
                    source=self.source_name,
                    source_id=source_id,
                    title=title,
                    venue="Atatürk Kültür Merkezi (AKM)",
                    start_at=self._extract_start_datetime(card_text),
                    url=absolute_url,
                    category=self._extract_category(card_text),
                )
            )

        if not events:
            events.extend(self._extract_events_from_next_data(html))

        return events

    def _extract_events_from_next_data(self, html: str) -> list[Event]:
        soup = BeautifulSoup(html, "lxml")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            return []

        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            return []

        events: list[Event] = []
        seen: set[str] = set()
        for node in _walk_dicts(payload):
            raw_slug = str(node.get("slug", "")).strip("/")
            if not raw_slug:
                continue

            title = str(node.get("title") or node.get("name") or "").strip()
            if not title:
                title = _humanize_slug(raw_slug)

            if raw_slug.startswith("tr/etkinlik/"):
                href = f"/{raw_slug}"
                source_id = _extract_slug_from_href(raw_slug)
            elif "/tr/etkinlik/" in raw_slug:
                href = raw_slug if raw_slug.startswith("/") else f"/{raw_slug}"
                source_id = _extract_slug_from_href(raw_slug)
            else:
                source_id = _extract_slug_from_href(raw_slug)
                href = f"/tr/etkinlik/{source_id}"

            if not source_id or source_id in seen:
                continue

            text_blob = " ".join(
                str(node.get(key, ""))
                for key in ("title", "name", "type", "category", "date", "startDate")
            )
            seen.add(source_id)
            events.append(
                Event(
                    source=self.source_name,
                    source_id=source_id,
                    title=title,
                    venue="Atatürk Kültür Merkezi (AKM)",
                    start_at=self._extract_start_datetime(text_blob),
                    url=urljoin(self._BASE, href),
                    category=self._extract_category(text_blob or title),
                )
            )

            if len(events) >= 80:
                break

        return events

    @staticmethod
    def _extract_slug(href: str) -> str:
        return href.rstrip("/").split("/")[-1]

    @staticmethod
    def _extract_title(anchor: Any) -> str:
        text = anchor.get_text(" ", strip=True)
        if text.startswith("AKM Etkinlik -"):
            text = text.replace("AKM Etkinlik -", "", 1).strip()
        if text:
            return text

        title_attr = anchor.get("title", "").strip()
        if title_attr:
            return title_attr

        img = anchor.find("img")
        if img:
            return str(img.get("alt", "")).strip()

        return ""

    @staticmethod
    def _extract_start_datetime(text: str) -> datetime | None:
        match = _AKM_DATE_RE.search(text)
        if not match:
            return None

        day = int(match.group("day"))
        month_raw = match.group("month").lower()
        month = _TR_MONTHS.get(month_raw)
        if not month:
            return None

        now = datetime.now()
        try:
            return datetime(now.year, month, day)
        except ValueError:
            return None

    @staticmethod
    def _extract_category(text: str) -> str:
        lowered = text.lower()
        for keyword, category in _AKM_CATEGORY_KEYWORDS.items():
            if keyword in lowered:
                return category
        return "culture"


# İstanbul merkezli futbol kulüpleri (normalize edilmiş)
_ISTANBUL_CLUBS: set[str] = {
    "galatasaray", "fenerbahce", "besiktas", "bjk",
    "istanbulspor", "istanbul basaksehir", "basaksehir",
    "medipol basaksehir", "rams basaksehir",
    "kasimpasa", "kasimpasaspor",
    "fatih karagumruk", "karagumruk",
    "eyupspor", "eyup",
    "pendikspor", "pendik",
    "umraniyespor", "umraniye",
    "tuzlaspor", "tuzla",
    "sariyer", "sariyerspor",
    "vefa", "vefaspor",
    "beyoglu", "beyogluspor",
}


def _is_istanbul_match(home: str, away: str) -> bool:
    """Takımlardan en az biri İstanbul kulübü ise True döner."""
    for team in (home, away):
        normalized = _search_text(team)
        if any(club in normalized for club in _ISTANBUL_CLUBS):
            return True
    return False


class TFFFixtureAdapter(BaseAPIService, BaseEventAdapter):
    """TFF fikstür sayfasından maç kayıtları üretir (yalnızca İstanbul maçları)."""

    _BASE = "https://www.tff.org"

    def __init__(
        self,
        page_id: int = 198,
        league: str = "trendyol-super-lig",
        branch: str = "football",
    ) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=20.0)
        self.page_id = page_id
        self.league = league
        self.branch = branch

    @property
    def source_name(self) -> str:
        return f"tff_{self.branch}_{self.league}"

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        cache_key = f"events:tff:{self.page_id}:{self.branch}:{self.league}"

        async def _fetch() -> str:
            try:
                return await self.fetch(f"/default.aspx?pageID={self.page_id}")
            except Exception:
                logger.exception("TFF fetch hatası")
                return ""

        html = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        seen: set[str] = set()

        all_links = soup.find_all("a", href=True)
        match_links = []
        for link in all_links:
            href = str(link.get("href", ""))
            lowered = href.lower()
            if "pageid=29" in lowered and "macid=" in lowered:
                match_links.append(link)

        for match_link in match_links:
            href = match_link.get("href")
            if not href:
                continue

            source_id = self._extract_query_value(href, "macId")
            if not source_id or source_id in seen:
                continue

            container = match_link.find_parent(["tr", "div", "li", "td"]) or match_link
            container_text = container.get_text(" ", strip=True)
            team_links = container.select('a[href*="pageId=28&kulupID="]')
            home_team = team_links[0].get_text(" ", strip=True) if len(team_links) > 0 else ""
            away_team = team_links[1].get_text(" ", strip=True) if len(team_links) > 1 else ""

            if not home_team or not away_team:
                parsed_home, parsed_away = self._extract_teams_from_text(container_text)
                home_team = home_team or parsed_home
                away_team = away_team or parsed_away

            if not home_team or not away_team:
                fallback_home, fallback_away = self._extract_teams_from_links(container)
                home_team = home_team or fallback_home
                away_team = away_team or fallback_away

            title = f"{home_team} vs {away_team}".strip(" vs") if (home_team and away_team) else f"TFF Match {source_id}"

            # Takım adlarından İstanbul maçı mı kontrol et
            if not _is_istanbul_match(home_team, away_team):
                continue

            # İstanbul takımının stadını venue olarak belirle
            venue = self._infer_istanbul_venue(home_team)

            seen.add(source_id)
            events.append(
                Event(
                    source=self.source_name,
                    source_id=source_id,
                    title=title,
                    venue=venue,
                    start_at=self._extract_start_datetime(container_text),
                    url=urljoin(self._BASE, href),
                    category="sport",
                )
            )

        return events

    @staticmethod
    def _infer_istanbul_venue(home_team: str) -> str:
        """Ev sahibi İstanbul takımıysa stadyum adını döndür."""
        norm = _search_text(home_team)
        if "galatasaray" in norm:
            return "Rams Park"
        if "fenerbahce" in norm:
            return "Ülker Stadyumu"
        if "besiktas" in norm or "bjk" in norm:
            return "Tüpraş Stadyumu"
        if "basaksehir" in norm:
            return "Fatih Terim Stadyumu"
        if "kasimpasa" in norm:
            return "Recep Tayyip Erdoğan Stadyumu"
        if "karagumruk" in norm:
            return "Atatürk Olimpiyat Stadyumu"
        if "eyupspor" in norm or "eyup" in norm:
            return "Alibeyköy Stadyumu"
        if "pendikspor" in norm or "pendik" in norm:
            return "Pendik Stadyumu"
        if "istanbulspor" in norm:
            return "Başakşehir Fatih Terim Stadyumu"
        return "İstanbul"

    @staticmethod
    def _extract_query_value(url: str, key: str) -> str:
        parsed = urlparse(url)
        values = parse_qs(parsed.query).get(key, [])
        return values[0] if values else ""

    @staticmethod
    def _extract_start_datetime(text: str) -> datetime | None:
        match = _TFF_DATETIME_RE.search(text)
        if not match:
            return None

        try:
            return datetime.strptime(
                f"{match.group('date')} {match.group('time')}",
                "%d.%m.%Y %H:%M",
            )
        except ValueError:
            return None

    @staticmethod
    def _extract_teams_from_text(text: str) -> tuple[str, str]:
        normalized = re.sub(r"\s+", " ", text or " ").strip()
        normalized = re.sub(r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}", " ", normalized)
        match = re.search(
            r"(?P<home>[A-ZÇĞİÖŞÜ0-9 .&'\-]{3,}?)\s+\d+\s*-\s*\d+\s+(?P<away>[A-ZÇĞİÖŞÜ0-9 .&'\-]{3,}?)(?:\s+\d+\s*-\s*\d+|$)",
            normalized,
        )
        if not match:
            return "", ""

        return match.group("home").strip(), match.group("away").strip()

    @staticmethod
    def _extract_teams_from_links(container: Any) -> tuple[str, str]:
        candidates: list[str] = []
        for link in container.find_all("a", href=True):
            text = link.get_text(" ", strip=True)
            if not text:
                continue
            if re.match(r"^\d+\s*-\s*\d+$", text):
                continue
            candidates.append(text)

        unique_candidates = []
        seen: set[str] = set()
        for candidate in candidates:
            normalized = _search_text(candidate)
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_candidates.append(candidate)

        if len(unique_candidates) >= 2:
            return unique_candidates[0], unique_candidates[1]
        return "", ""


class IBBEventsPortalAdapter(BaseAPIService, BaseEventAdapter):
    """İBB etkinlik portalından duyuru bazlı etkinlik toplar."""

    _BASE = "https://www.ibb.istanbul"
    _ENDPOINT = "/gundem/etkinlikler"

    @property
    def source_name(self) -> str:
        return "ibb_events_portal"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=20.0)

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        cache_key = "events:ibb:portal"

        async def _fetch() -> str:
            try:
                return await self.fetch(self._ENDPOINT)
            except Exception:
                logger.exception("IBB Etkinlik portal fetch hatası")
                return ""

        html = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href*="/gundem/etkinlikler/"]'):
            href = anchor.get("href")
            if not href:
                continue
            slug = _extract_slug_from_href(href)
            if not slug or slug == "etkinlikler" or slug in seen:
                continue

            title = anchor.get_text(" ", strip=True)
            if not title:
                continue

            seen.add(slug)
            events.append(
                Event(
                    source=self.source_name,
                    source_id=slug,
                    title=title,
                    venue="İstanbul",
                    start_at=_parse_turkish_date(title),
                    url=urljoin(self._BASE, href),
                    category=_infer_category(title, fallback="culture"),
                )
            )

        if not events:
            events.extend(
                _extract_ibb_items_from_text(
                    html,
                    section_prefix="/gundem/etkinlikler",
                    source_name=self.source_name,
                    category_fallback="culture",
                )
            )

        if not events:
            events.extend(await self._extract_from_payload(html, "/gundem/etkinlikler"))

        return events

    async def _extract_from_payload(self, html: str, section_prefix: str) -> list[Event]:
        payload_paths = _extract_paths_from_text(html, "/_nuxt/static")
        if not payload_paths:
            return []

        payload_text = ""
        for path in payload_paths:
            if not path.endswith("payload.js"):
                continue
            try:
                payload_text = await self.fetch(path)
                if payload_text:
                    break
            except Exception:
                logger.debug("IBB payload fetch failed: %s", path)

        if not payload_text:
            return []

        return _extract_ibb_items_from_text(
            payload_text,
            section_prefix=section_prefix,
            source_name=self.source_name,
            category_fallback="culture",
        )


class BiletinialEventsAdapter(BaseAPIService, BaseEventAdapter):
    """Biletinial'den minimum İstanbul odaklı etkinlik listesi toplar."""

    _BASE = "https://www.biletinial.com"
    _ENDPOINTS = (
        "/tr-tr/muzik",
        "/tr-tr/futbol",
        "/tr-tr/etkinlikleri/konserler",
    )

    @property
    def source_name(self) -> str:
        return "biletinial"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=20.0)

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        events: list[Event] = []
        seen: set[str] = set()

        for endpoint in self._ENDPOINTS:
            cache_key = f"events:biletinial:{endpoint}"

            async def _fetch(url: str = endpoint) -> str:
                try:
                    return await self.fetch(url)
                except Exception:
                    logger.exception("Biletinial fetch hatası: %s", url)
                    return ""

            html = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
            if not html:
                continue

            soup = BeautifulSoup(html, "lxml")
            selectors = [
                'a[href*="/tr-tr/muzik/"]',
                'a[href*="/tr-tr/futbol/"]',
                'a[href*="/tr-tr/tiyatro/"]',
                'a[href*="/tr-tr/etkinlik/"]',
                'a[href*="/tr-tr/opera-bale/"]',
            ]

            anchors = []
            for selector in selectors:
                anchors.extend(soup.select(selector))

            if not anchors:
                anchors = [
                    anchor
                    for anchor in soup.find_all("a", href=True)
                    if "/tr-tr/" in str(anchor.get("href", ""))
                ]

            endpoint_candidates: list[Event] = []

            for anchor in anchors:
                    href = anchor.get("href")
                    if not href:
                        continue
                    slug = _extract_slug_from_href(href)
                    if not slug or slug in seen:
                        continue

                    text = anchor.get_text(" ", strip=True)
                    if not text:
                        text = str(anchor.get("title", "")).strip()
                    if not text:
                        continue

                    card_text = (anchor.find_parent(["article", "li", "div"]) or anchor).get_text(" ", strip=True)
                    city_blob = _search_text(f"{text} {href} {card_text}")
                    if not any(
                        token in city_blob
                        for token in (
                            "istanbul",
                            "besiktas",
                            "kadikoy",
                            "uskudar",
                            "sisli",
                            "bakirkoy",
                            "atasehir",
                            "sariyer",
                        )
                    ):
                        continue

                    seen.add(slug)
                    endpoint_candidates.append(
                        Event(
                            source=self.source_name,
                            source_id=slug,
                            title=text,
                            venue="İstanbul",
                            start_at=_parse_turkish_date(text),
                            url=urljoin(self._BASE, href),
                            category=_infer_category(f"{href} {text}", fallback="culture"),
                        )
                    )

            if not endpoint_candidates:
                for anchor in anchors:
                    href = anchor.get("href")
                    if not href:
                        continue
                    slug = _extract_slug_from_href(href)
                    if not slug or slug in seen:
                        continue

                    text = anchor.get_text(" ", strip=True) or str(anchor.get("title", "")).strip()
                    if len(text) < 6:
                        continue

                    lowered = _search_text(text)
                    if any(token in lowered for token in ("giris", "uye ol", "iletisim", "anasayfa")):
                        continue

                    seen.add(slug)
                    endpoint_candidates.append(
                        Event(
                            source=self.source_name,
                            source_id=slug,
                            title=text,
                            venue="İstanbul",
                            start_at=_parse_turkish_date(text),
                            url=urljoin(self._BASE, href),
                            category=_infer_category(f"{href} {text}", fallback="culture"),
                        )
                    )

                    if len(endpoint_candidates) >= 30:
                        break

            if not endpoint_candidates:
                route_pattern = re.compile(
                    r"/tr-tr/(?:muzik|futbol|tiyatro|etkinlikleri|opera-bale|etkinlik)/[a-z0-9\-]+",
                    re.IGNORECASE,
                )
                for href in sorted(set(route_pattern.findall(html.replace("\\/", "/")))):
                    slug = _extract_slug_from_href(href)
                    if not slug or slug in seen:
                        continue

                    seen.add(slug)
                    title = _humanize_slug(slug)
                    endpoint_candidates.append(
                        Event(
                            source=self.source_name,
                            source_id=slug,
                            title=title,
                            venue="İstanbul",
                            start_at=_parse_turkish_date(title),
                            url=urljoin(self._BASE, href),
                            category=_infer_category(f"{href} {title}", fallback="culture"),
                        )
                    )

                    if len(endpoint_candidates) >= 30:
                        break

            events.extend(endpoint_candidates)

        return events


class ZorluPSMAdapter(BaseAPIService, BaseEventAdapter):
    """Zorlu PSM etkinlik listesi parse eder (HTML/cookie toleranslı)."""

    _BASE = "https://www.zorlupsm.com"
    _ENDPOINT = "/etkinlikler"

    @property
    def source_name(self) -> str:
        return "zorlu_psm"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=20.0)

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        cache_key = "events:zorlu_psm"

        async def _fetch() -> str:
            try:
                return await self.fetch(self._ENDPOINT)
            except Exception:
                logger.exception("Zorlu PSM fetch hatası")
                return ""

        html = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        seen: set[str] = set()

        for anchor in soup.select('a[href*="/etkinlikler/"]'):
            href = anchor.get("href")
            if not href:
                continue
            slug = _extract_slug_from_href(href)
            if not slug or slug == "etkinlikler" or slug in seen:
                continue

            title = anchor.get_text(" ", strip=True)
            if not title:
                continue

            seen.add(slug)
            events.append(
                Event(
                    source=self.source_name,
                    source_id=slug,
                    title=title,
                    venue="Zorlu PSM",
                    start_at=_parse_turkish_date(title),
                    url=urljoin(self._BASE, href),
                    category=_infer_category(title, fallback="culture"),
                )
            )

        return events


class PassoEventsAdapter(BaseAPIService, BaseEventAdapter):
    """Passo'dan minimum etkinlik sinyali toplar."""

    _BASE = "https://www.passo.com.tr"
    _ENDPOINT = "/tr"

    @property
    def source_name(self) -> str:
        return "passo"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=20.0)

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        cache_key = "events:passo"

        async def _fetch() -> str:
            try:
                return await self.fetch(self._ENDPOINT)
            except Exception:
                logger.exception("Passo fetch hatası")
                return ""

        html = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        seen: set[str] = set()

        for anchor in soup.select('a[href*="/tr/etkinlik/"]'):
            href = anchor.get("href")
            if not href:
                continue

            slug = _extract_slug_from_href(href)
            if not slug or slug in seen:
                continue

            title = anchor.get_text(" ", strip=True)
            if not title:
                continue

            seen.add(slug)
            events.append(
                Event(
                    source=self.source_name,
                    source_id=slug,
                    title=title,
                    venue="İstanbul",
                    start_at=_parse_turkish_date(title),
                    url=urljoin(self._BASE, href),
                    category=_infer_category(title, fallback="sport"),
                )
            )

        return events


class ClubSitesAdapter(BaseAPIService, BaseEventAdapter):
    """Kulüp siteleri için RSS/HTML hibrit sinyal adaptörü."""

    @property
    def source_name(self) -> str:
        return "club_sites"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url="", timeout=20.0)

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        events = await self._fetch_gs_rss()
        events.extend(await self._fetch_bjk_html())
        return events

    async def _fetch_gs_rss(self) -> list[Event]:
        cache_key = "events:clubsites:gs_rss"

        async def _fetch() -> str:
            try:
                return await self.fetch("https://www.galatasaray.org/xml/gs.rss")
            except Exception:
                logger.exception("GS RSS fetch hatası")
                return ""

        xml = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        if not xml:
            return []

        soup = BeautifulSoup(xml, "xml")
        events: list[Event] = []
        for item in soup.find_all("item"):
            title = (item.find("title").text if item.find("title") else "").strip()
            if not title:
                continue
            link = (item.find("link").text if item.find("link") else "").strip()
            guid = (item.find("guid").text if item.find("guid") else link).strip()
            pub_date = (item.find("pubDate").text if item.find("pubDate") else "").strip()
            start_at = None
            if pub_date:
                try:
                    start_at = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                except Exception:
                    start_at = None

            events.append(
                Event(
                    source=self.source_name,
                    source_id=f"gs:{guid}",
                    title=title,
                    venue="İstanbul",
                    start_at=start_at,
                    url=link,
                    category=_infer_category(title, fallback="sport"),
                )
            )

        return events

    async def _fetch_bjk_html(self) -> list[Event]:
        cache_key = "events:clubsites:bjk"

        async def _fetch() -> str:
            try:
                return await self.fetch("https://www.bjk.com.tr/tr/")
            except Exception:
                logger.exception("BJK fetch hatası")
                return ""

        html = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href*="/tr/haber/"]'):
            title = anchor.get_text(" ", strip=True)
            if not title:
                continue
            if not any(k in title.lower() for k in _SPORT_KEYWORDS):
                continue

            href = anchor.get("href")
            if not href:
                continue
            slug = _extract_slug_from_href(href)
            source_id = f"bjk:{slug}"
            if source_id in seen:
                continue
            seen.add(source_id)

            events.append(
                Event(
                    source=self.source_name,
                    source_id=source_id,
                    title=title,
                    venue="İstanbul",
                    start_at=_parse_turkish_date(title),
                    url=urljoin("https://www.bjk.com.tr", href),
                    category="sport",
                )
            )

        return events


class IstanbulValilikDuyuruAdapter(BaseAPIService, BaseEventAdapter):
    """İstanbul Valiliği duyurularından siyasi/kamusal sinyal toplar."""

    _BASE = "https://istanbul.gov.tr"
    _ENDPOINT = "/duyurular"

    @property
    def source_name(self) -> str:
        return "istanbul_valilik"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=20.0)

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        cache_key = "events:valilik:duyurular"

        async def _fetch() -> str:
            try:
                return await self.fetch(self._ENDPOINT)
            except Exception:
                logger.exception("Valilik duyuru fetch hatası")
                return ""

        html = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href^="/"]'):
            href = anchor.get("href")
            title = anchor.get_text(" ", strip=True)
            if not href or not title:
                continue
            if any(word in title.lower() for word in ("ihale", "başvuru", "basvuru")):
                continue

            slug = _extract_slug_from_href(href)
            source_id = f"valilik:{slug}"
            if source_id in seen:
                continue
            seen.add(source_id)

            events.append(
                Event(
                    source=self.source_name,
                    source_id=source_id,
                    title=title,
                    venue="İstanbul",
                    start_at=_parse_turkish_date(title),
                    url=urljoin(self._BASE, href),
                    category="political",
                )
            )
            if len(events) >= 50:
                break

        return events


class IBBDuyuruAdapter(BaseAPIService, BaseEventAdapter):
    """İBB duyurularından kamusal etki sinyali toplar."""

    _BASE = "https://www.ibb.istanbul"
    _ENDPOINT = "/gundem/duyurular"

    @property
    def source_name(self) -> str:
        return "ibb_duyuru"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url=self._BASE, timeout=20.0)

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        cache_key = "events:ibb:duyurular"

        async def _fetch() -> str:
            try:
                return await self.fetch(self._ENDPOINT)
            except Exception:
                logger.exception("İBB duyuru fetch hatası")
                return ""

        html = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        events: list[Event] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href*="/gundem/duyurular/"]'):
            href = anchor.get("href")
            if not href:
                continue
            slug = _extract_slug_from_href(href)
            if not slug or slug == "duyurular":
                continue
            source_id = f"ibbduyuru:{slug}"
            if source_id in seen:
                continue

            title = anchor.get_text(" ", strip=True)
            if not title:
                continue

            seen.add(source_id)
            events.append(
                Event(
                    source=self.source_name,
                    source_id=source_id,
                    title=title,
                    venue="İstanbul",
                    start_at=_parse_turkish_date(title),
                    url=urljoin(self._BASE, href),
                    category="political",
                )
            )

        if not events:
            events.extend(
                _extract_ibb_items_from_text(
                    html,
                    section_prefix="/gundem/duyurular",
                    source_name=self.source_name,
                    source_id_prefix="ibbduyuru:",
                    category_fallback="political",
                )
            )

        if not events:
            events.extend(await self._extract_from_payload(html))

        return events

    async def _extract_from_payload(self, html: str) -> list[Event]:
        payload_paths = _extract_paths_from_text(html, "/_nuxt/static")
        if not payload_paths:
            return []

        payload_text = ""
        for path in payload_paths:
            if not path.endswith("payload.js"):
                continue
            try:
                payload_text = await self.fetch(path)
                if payload_text:
                    break
            except Exception:
                logger.debug("IBB duyuru payload fetch failed: %s", path)

        if not payload_text:
            return []

        return _extract_ibb_items_from_text(
            payload_text,
            section_prefix="/gundem/duyurular",
            source_name=self.source_name,
            source_id_prefix="ibbduyuru:",
            category_fallback="political",
        )


class PartySitesBestEffortAdapter(BaseAPIService, BaseEventAdapter):
    """Parti sitelerinden best-effort duyuru sinyali toplar."""

    _URLS = (
        "https://www.akpartiistanbul.com.tr/",
        "https://istanbulchp.org.tr/",
    )

    @property
    def source_name(self) -> str:
        return "party_sites_best_effort"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url="", timeout=20.0)

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        events: list[Event] = []
        seen: set[str] = set()
        keywords = ("miting", "etkinlik", "buluşma", "toplantı", "toplanti", "program")

        for source_url in self._URLS:
            cache_key = f"events:party:{source_url}"

            async def _fetch(url: str = source_url) -> str:
                try:
                    return await self.fetch(url)
                except Exception:
                    logger.exception("Parti sitesi fetch hatası: %s", url)
                    return ""

            html = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
            if not html:
                continue

            soup = BeautifulSoup(html, "lxml")
            for anchor in soup.select("a[href]"):
                title = anchor.get_text(" ", strip=True)
                if not title:
                    continue
                if not any(keyword in title.lower() for keyword in keywords):
                    continue

                href = anchor.get("href")
                slug = _extract_slug_from_href(str(href))
                source_id = f"party:{slug}:{abs(hash(source_url))}"
                if source_id in seen:
                    continue
                seen.add(source_id)

                events.append(
                    Event(
                        source=self.source_name,
                        source_id=source_id,
                        title=title,
                        venue="İstanbul",
                        start_at=_parse_turkish_date(title),
                        url=urljoin(source_url, str(href)),
                        category="political",
                    )
                )

                if len(events) >= 80:
                    return events

        return events


class SocialSignalAdapter(BaseAPIService, BaseEventAdapter):
    """Resmi sosyal linklerden event sinyali toplamak için best-effort adapter."""

    @property
    def source_name(self) -> str:
        return "social_signal"

    def __init__(self) -> None:
        BaseAPIService.__init__(self, base_url="", timeout=20.0)

    async def fetch(self, url: str, **kwargs: Any) -> str:
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def fetch_events(self) -> list[Event]:
        # Public social APIs çoğunlukla auth gerektirdiği için,
        # burada açık RSS/HTML sinyal kaynakları kullanılmaktadır.
        cache_key = "events:social:gsrss"

        async def _fetch() -> str:
            try:
                return await self.fetch("https://www.galatasaray.org/xml/gs.rss")
            except Exception:
                logger.exception("Social signal RSS fetch hatası")
                return ""

        xml = await self.cache_hook(cache_key, _fetch, CACHE_TTL)
        if not xml:
            return []

        soup = BeautifulSoup(xml, "xml")
        events: list[Event] = []
        for item in soup.find_all("item")[:20]:
            title = (item.find("title").text if item.find("title") else "").strip()
            if not title:
                continue

            link = (item.find("link").text if item.find("link") else "").strip()
            guid = (item.find("guid").text if item.find("guid") else link).strip()
            events.append(
                Event(
                    source=self.source_name,
                    source_id=f"signal:{guid}",
                    title=title,
                    venue="İstanbul",
                    url=link,
                    category=_infer_category(title, fallback="other"),
                )
            )

        return events


# ------------------------------------------------------------------
# Ana servis
# ------------------------------------------------------------------

class EventService:
    """Tüm kaynaklardan etkinlik çekip duplikasyon kontrolü yapar."""

    def __init__(
        self,
        adapters: list[BaseEventAdapter] | None = None,
        enabled_connectors: set[str] | None = None,
        disabled_connectors: set[str] | None = None,
    ) -> None:
        self.last_source_health: dict[str, dict[str, int]] = {}
        base_adapters: list[BaseEventAdapter] = adapters or [
            IBBKulturAdapter(),
            IBBEventsPortalAdapter(),
            AKMEventsAdapter(),
            TFFFixtureAdapter(page_id=198, league="super-lig", branch="football"),
            TFFFixtureAdapter(page_id=142, league="1-lig", branch="football"),
            BiletinialEventsAdapter(),
            ZorluPSMAdapter(),
            PassoEventsAdapter(),
            ClubSitesAdapter(),
            IstanbulValilikDuyuruAdapter(),
            IBBDuyuruAdapter(),
            PartySitesBestEffortAdapter(),
            SocialSignalAdapter(),
            SeatGeekAdapter(),
        ]

        enabled = enabled_connectors
        if enabled is None:
            enabled = _parse_connector_csv(settings.ENABLED_EVENT_CONNECTORS)

        disabled = disabled_connectors
        if disabled is None:
            disabled = _parse_connector_csv(settings.DISABLED_EVENT_CONNECTORS)

        self.adapters = self._filter_adapters(base_adapters, enabled, disabled)

    @staticmethod
    def _filter_adapters(
        adapters: list[BaseEventAdapter],
        enabled: set[str],
        disabled: set[str],
    ) -> list[BaseEventAdapter]:
        filtered = adapters

        # enabled boş veya '*' ise tümü aktif
        if enabled and "*" not in enabled and "all" not in enabled:
            filtered = [adapter for adapter in filtered if adapter.source_name.lower() in enabled]

        if disabled:
            filtered = [adapter for adapter in filtered if adapter.source_name.lower() not in disabled]

        logger.info(
            "Active connectors: %s",
            ", ".join(adapter.source_name for adapter in filtered) if filtered else "none",
        )
        return filtered

    async def get_events(self) -> list[Event]:
        """
        Tüm adaptörlerden etkinlik çekip birleştirir.
        Duplikasyonlar (source + source_id) çıkarılır.
        """
        seen: set[str] = set()
        events: list[Event] = []
        source_health: dict[str, dict[str, int]] = {}

        for adapter in self.adapters:
            try:
                batch = await adapter.fetch_events()
                unique_added = 0
                for event in batch:
                    if event.dedup_key not in seen:
                        seen.add(event.dedup_key)
                        events.append(event)
                        unique_added += 1

                source_health[adapter.source_name] = {
                    "fetched": len(batch),
                    "unique_added": unique_added,
                    "errors": 0,
                }
                logger.info(
                    "%s: %d etkinlik alındı.", adapter.source_name, len(batch)
                )
            except Exception:
                source_health[adapter.source_name] = {
                    "fetched": 0,
                    "unique_added": 0,
                    "errors": 1,
                }
                logger.exception(
                    "%s adaptörü hata verdi.", adapter.source_name
                )

        self.last_source_health = source_health
        logger.info("Toplam %d eşsiz etkinlik.", len(events))
        return events
