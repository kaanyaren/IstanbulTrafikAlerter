# Faz 2: Dış API Entegrasyonları

---

## Görev 2.1 — API Adaptör Temel Sınıfı
- **Girdi:** Görev 0.2
- **Çıktı:** `backend/app/services/base_api.py`
- **Talimat:** Tüm dış API servisleri için bir abstract temel sınıf oluştur. Özellikler: `httpx.AsyncClient` kullanımı, retry mekanizması (3 deneme, exponential backoff), rate limit tracking (kalan istek sayısı), circuit breaker pattern (5 ardışık hata → 60 saniye devre dışı), response caching hook. `BaseAPIService` abstract sınıfı, `fetch()` abstract metoduna sahip olmalı.
- **Doğrulama:** Mock test ile retry ve circuit breaker davranışları doğrulanmalı.

---

## Görev 2.2 — İBB Açık Veri Entegrasyonu (Trafik)
- **Girdi:** Görev 2.1
- **Çıktı:** `backend/app/services/ibb_traffic_service.py`
- **Talimat:** İstanbul Büyükşehir Belediyesi Açık Veri Portalı'ndan trafik yoğunluk verisi çeken servis. Endpoint: `https://data.ibb.gov.tr/api/3/action/datastore_search`. Veriyi parse edip `TrafficZone` modeline normalize et. Redis'te 5 dakika önbellek.
- **Doğrulama:** Gerçek API'ye istek atılıp veri alınmalı, cache'ten tekrar servis edilmeli.

---

## Görev 2.3 — Etkinlik Veri Servisi (Web Scraping / API)
- **Girdi:** Görev 2.1
- **Çıktı:** `backend/app/services/event_service.py`
- **Talimat:** Biletix, Passo veya açık kaynak etkinlik API'lerinden İstanbul etkinliklerini çeken servis. En az 2 kaynak desteklenmeli. Her kaynağın adaptörü ayrı olsun. Veri normalize edilip `Event` modeline dönüştürülsün. Duplikasyon kontrolü (source + source_id ile).
- **Doğrulama:** En az 5 gerçek etkinlik çekilmeli, DB'ye kaydedilmeli.

---

## Görev 2.4 — Geocoding Servisi
- **Girdi:** Görev 2.1
- **Çıktı:** `backend/app/services/geocoding.py`
- **Talimat:** Mekan adından koordinat çözen servis. Birincil: Nominatim (OpenStreetMap, ücretsiz). Yedek: Google Geocoding API. Cache: aynı adres tekrar sorgulanmamalı (Redis'te saklama, TTL 30 gün). Rate limit: Nominatim max 1 istek/saniye.
- **Doğrulama:** "Vodafone Park, İstanbul" → yaklaşık (41.0425, 29.0068) koordinatları dönmeli.

---

## Görev 2.5 — Redis Cache Yardımcı Modülü
- **Girdi:** Görev 0.4
- **Çıktı:** `backend/app/services/cache.py`
- **Talimat:** Redis cache wrapper: `get(key)`, `set(key, value, ttl)`, `delete(key)`, `get_or_set(key, callback, ttl)` metodları. JSON serialization/deserialization otomatik. Connection pool kullan.
- **Doğrulama:** Set → Get → TTL süresi sonrası None dönme testi.
