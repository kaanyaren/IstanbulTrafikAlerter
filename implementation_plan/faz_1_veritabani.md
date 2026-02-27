# Faz 1: Veritabanı Modelleri & CRUD

---

## Görev 1.1 — Event (Etkinlik) SQLAlchemy Modeli
- **Girdi:** Görev 0.2, 0.3
- **Çıktı:** `backend/app/models/event.py`
- **Talimat:** SQLAlchemy + GeoAlchemy2 kullanarak `Event` modeli oluştur. Alanlar: `id` (UUID, PK), `name` (str), `description` (text, nullable), `venue_name` (str), `location` (Geometry POINT, SRID 4326), `start_time` (datetime with tz), `end_time` (datetime with tz, nullable), `capacity` (int, nullable), `category` (str — concert, sports, conference, other), `source` (str — hangi API'den geldiği), `source_id` (str — kaynak API'deki ID), `created_at`, `updated_at`. PostGIS spatial index ekle.
- **Doğrulama:** Alembic migration oluşturulup uygulanabilmeli, tabloda PostGIS geometri kolonu doğru gösterilmeli.

---

## Görev 1.2 — TrafficZone (Trafik Bölgesi) Modeli
- **Girdi:** Görev 0.2, 0.3
- **Çıktı:** `backend/app/models/traffic_zone.py`
- **Talimat:** `TrafficZone` modeli: `id` (UUID), `name` (str), `polygon` (Geometry POLYGON, SRID 4326), `base_congestion_level` (float 0-1 — normal günlerdeki ortalama yoğunluk), `rush_hour_multiplier` (float), `created_at`. İstanbul'un temel trafik bölgelerini seed olarak ekleyecek bir `seed_zones.py` scripti de yaz (Taksim, Kadıköy, Beşiktaş, Fatih vb.).
- **Doğrulama:** Seed script çalışmalı, `SELECT * FROM traffic_zones` ile bölgeler görülmeli.

---

## Görev 1.3 — Prediction (Tahmin) Modeli
- **Girdi:** Görev 1.1, 1.2
- **Çıktı:** `backend/app/models/prediction.py`
- **Talimat:** `Prediction` modeli: `id` (UUID), `zone_id` (FK → traffic_zones), `event_id` (FK → events, nullable), `predicted_at` (datetime — ne zaman tahmin yapıldığı), `target_time` (datetime — ne zaman için tahmin yapıldığı), `congestion_score` (int 0-100), `confidence` (float 0-1), `factors` (JSONB — skor'a katkıda bulunan faktörler), `created_at`.
- **Doğrulama:** Migration başarılı, foreign key ilişkileri doğru çalışmalı.

---

## Görev 1.4 — Pydantic Schema'ları
- **Girdi:** Görev 1.1, 1.2, 1.3
- **Çıktı:** `backend/app/schemas/event.py`, `schemas/prediction.py`, `schemas/traffic_zone.py`
- **Talimat:** Her model için `Create`, `Update`, `Response` Pydantic şemaları oluştur. GeoJSON formatında konum alanları dön. `EventResponse`'da `latitude`, `longitude` alanları olsun (Geometry'den çevrilen).
- **Doğrulama:** Şemalar import edilip örnek data ile doğrulanabilmeli.

---

## Görev 1.5 — Database Session & Repository Pattern
- **Girdi:** Görev 0.2, 0.4
- **Çıktı:** `backend/app/database.py` + `backend/app/repositories/event_repo.py`
- **Talimat:** Async session factory (`create_async_engine`, `async_sessionmaker`) kur. `EventRepository` sınıfı: `create()`, `get_by_id()`, `list_all()`, `find_near_location(lat, lon, radius_km)` (PostGIS ST_DWithin kullan), `find_by_date_range()`. Dependency injection ile FastAPI'ye entegre et.
- **Doğrulama:** `find_near_location` testi: bilinen bir noktanın 1km çevresindeki etkinlikleri başarıyla dönmeli.
