# Connector Backlog

Tarih: 2026-02-28
Kapsam: İstanbul etkinlik veri kaynaklarının connector bazında uygulanabilir iş planı.

## 1) Önceliklendirme Kriteri

- **P0:** Resmi, yüksek güven, düşük bakım maliyeti
- **P1:** Yüksek kapsama, orta bakım maliyeti
- **P2:** Fallback/sinyal kaynağı, kırılgan veya düşük hacim

## 2) Backlog Tablosu

| ID       | Connector                           | Kategori              | Kaynak                                         | Tür                 | Öncelik | Frekans  | Zorluk      | Çıktı                           |
| -------- | ----------------------------------- | --------------------- | ---------------------------------------------- | ------------------- | ------- | -------- | ----------- | ------------------------------- |
| CONN-001 | `ibb_kultur_api_connector`          | music/culture         | kultursanat.istanbul `/api/event/geteventlist` | API                 | P0      | 4x/gün   | Düşük       | Normalize event listesi         |
| CONN-002 | `ibb_events_portal_connector`       | culture/city-events   | ibb.istanbul `/gundem/etkinlikler`             | HTML                | P0      | 3x/gün   | Düşük-Orta  | Etkinlik duyuru akışı           |
| CONN-003 | `akm_events_connector`              | music/stage           | akmistanbul.gov.tr `/tr/etkinlikler`           | HTML                | P0      | 3x/gün   | Orta        | Etkinlik + kategori + tarih     |
| CONN-004 | `tff_fixture_connector`             | sport                 | tff.org `pageID=198,142`                       | HTML                | P0      | 4x/gün   | Orta        | Maç/fikstür kayıtları           |
| CONN-005 | `biletinial_events_connector`       | music/sport/stage     | biletinial.com                                 | HTML (+JS fallback) | P1      | 2x/gün   | Orta-Yüksek | Geniş etkinlik kapsaması        |
| CONN-006 | `zorlu_psm_connector`               | music/stage           | zorlupsm.com `/etkinlikler`                    | HTML (+cookie)      | P1      | 2x/gün   | Orta-Yüksek | Venue odaklı etkinlikler        |
| CONN-007 | `passo_events_connector`            | sport/music           | passo.com.tr                                   | Dynamic scraper     | P1      | 1-2x/gün | Yüksek      | Büyük etkinlik ve bilet sinyali |
| CONN-008 | `club_sites_connector`              | sport                 | bjk.com.tr, galatasaray.org vb.                | RSS/HTML            | P2      | 2x/gün   | Orta        | Kulüp bazlı maç/bilet duyurusu  |
| CONN-009 | `istanbul_valilik_connector`        | political/public      | istanbul.gov.tr `/duyurular`                   | HTML                | P2      | 2x/gün   | Düşük       | Toplantı/duyuru sinyalleri      |
| CONN-010 | `ibb_duyuru_connector`              | political/public      | ibb.istanbul `/gundem/duyurular`               | HTML                | P2      | 2x/gün   | Düşük       | Yol kapanışı/kamusal duyuru     |
| CONN-011 | `party_sites_best_effort_connector` | political             | il/ilçe parti siteleri                         | HTML                | P2      | 1x/gün   | Yüksek      | Best-effort siyasi duyuru       |
| CONN-012 | `social_signal_connector`           | political/sport/music | resmi X/Instagram/Youtube linkli gönderiler    | API/HTML ingest     | P2      | 2x/gün   | Yüksek      | Linklenmiş duyuru sinyali       |

## 3) Sprint Bazlı Uygulama Planı

### Sprint 1 (P0 çekirdek)

- CONN-001: İBB Kültür API stabilizasyonu
- CONN-002: İBB Etkinlik portal parser
- CONN-003: AKM parser
- CONN-004: TFF fikstür parser

**Definition of Done (Sprint 1):**

- Her connector için en az 7 gün geriye dönük başarılı çekim
- Normalize schema eksiksiz dolum oranı >= %90
- Kaynak başına hata oranı <= %5

### Sprint 2 (P1 genişleme)

- CONN-005: Biletinial parser
- CONN-006: Zorlu PSM parser
- CONN-007: Passo düşük frekanslı dynamic scraper

**Definition of Done (Sprint 2):**

- P1 kaynaklarında duplicate azaltma oranı >= %95
- Scraper runtime limitleri ve retry/backoff kuralları aktif
- Bot koruma kaynaklı hatalarda graceful degrade

### Sprint 3 (P2 sinyal katmanı)

- CONN-008: Kulüp siteleri + RSS (özellikle GS RSS)
- CONN-009: Valilik duyuruları
- CONN-010: İBB duyuruları
- CONN-011/012: Parti siteleri + sosyal sinyal ingest

**Definition of Done (Sprint 3):**

- Siyasi/sosyal sinyal kaynakları ana event pipeline’ını kesmeden çalışıyor
- Kaynak başarısızlığında izolasyon ve alert mekanizması aktif

## 4) Teknik Gereksinim Checklist

- [ ] Ortak normalize şema (`title,start_time,end_time,venue,district,lat,lon,category,source,source_id,url,last_seen_at`)
- [ ] Dedupe kuralı (`source+source_id`, fallback hash)
- [ ] Rate limit ve retry/backoff
- [ ] `If-Modified-Since` / `ETag` desteği olan kaynaklarda koşullu istek
- [ ] Robots/ToS kontrol bayrağı (source metadata)
- [ ] Kaynak bazlı health metric (`success_count,error_count,empty_ratio,latency`)
- [ ] Alert eşikleri (ani hacim düşüşü, parser kırılması, ardışık hata)

## 5) Önerilen Ownership

- `backend/app/services/event_service.py`: adapter orchestration
- `backend/app/tasks/events.py`: periyodik çekim + upsert
- Yeni öneri klasörü: `backend/app/services/connectors/`
  - `api/`
  - `rss/`
  - `html/`
  - `dynamic/`

## 6) İlk Uygulanacak 5 İş (Actionable)

1. [x] CONN-001 için response şema doğrulama + parser testlerini artır.
2. [x] CONN-003 için AKM event listesi parser’ını ekle.
3. [x] CONN-004 için TFF fixture parser’ını branch/lig parametreli hale getir.
4. [x] CONN-005 için Biletinial’de sadece İstanbul filtreli minimum parser başlat.
5. [x] `source_health` tablosu veya metriği ekleyip günlük rapor üret.
