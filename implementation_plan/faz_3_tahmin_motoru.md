# Faz 3: Tahmin Motoru

---

## Görev 3.1 — Kural Tabanlı Tahmin Motoru (v1)
- **Girdi:** Görev 1.1, 1.2, 1.3
- **Çıktı:** `backend/app/prediction/rule_engine.py`
- **Talimat:** Kural:
  1. `base_score` = bölgenin `base_congestion_level × 100`
  2. Saat 07-09, 17-19 arası → +25 puan
  3. Cuma, Cumartesi → +15 puan
  4. Bölge 2km çevresinde etkinlik var ve kapasite > 5.000 → +20 puan
  5. Etkinlik kapasite > 20.000 → +15 ek puan
  6. Yağmur / kötü hava → +10 puan (ileride eklenecek, şimdilik parametre olsun)
  7. Toplam puan max 100
  Fonksiyon imzası: `async def predict(zone_id, target_time, db_session) → PredictionResult`
- **Doğrulama:** Bilinen test senaryoları ile beklenen puanlar doğrulanmalı (ör. Cuma 18:00 + 30.000 kişilik konser = yüksek skor).

---

## Görev 3.2 — Feature Engineering Modülü
- **Girdi:** Görev 3.1
- **Çıktı:** `backend/app/prediction/features.py`
- **Talimat:** ML modeli için özellik çıkarma: `hour_of_day`, `day_of_week`, `is_weekend`, `is_rush_hour`, `nearby_event_count`, `max_event_capacity`, `total_event_capacity`, `zone_base_level`, `days_until_event`. Pandas DataFrame döndüren `extract_features(zone, target_time, events)` fonksiyonu.
- **Doğrulama:** Test verisi ile çıkarılan feature'lar kontrol edilmeli.

---

## Görev 3.3 — Trafik Yoğunluk Skoru API Endpoint'i
- **Girdi:** Görev 3.1, 1.4
- **Çıktı:** `backend/app/routers/predictions.py`
- **Talimat:** `GET /api/v1/predictions?lat={lat}&lon={lon}&radius_km={r}&target_time={iso_time}` → Bu koordinatın çevresindeki tüm bölgeler için tahminleri dön. `GET /api/v1/predictions/zones/{zone_id}?hours_ahead=24` → Belirli bölgenin saatlik tahmin zaman serisi. Response GeoJSON formatında.
- **Doğrulama:** Swagger UI'dan test, doğru format ve data kontrolü.

---

## Görev 3.4 — Celery Periyodik Görevler (Scheduled Tasks)
- **Girdi:** Görev 2.2, 2.3, 3.1
- **Çıktı:** `backend/app/tasks/` klasöründeki dosyalar + `celery_app.py`
- **Talimat:**
  - `fetch_events_task`: Her 6 saatte bir etkinlik verilerini çek ve DB'ye kaydet.
  - `fetch_traffic_task`: Her 15 dakikada bir trafik verisini çek.
  - `run_predictions_task`: Her saat başı tüm bölgeler için sonraki 24 saatin tahminlerini çalıştır.
  - Celery Beat ile schedule tanımla.
- **Doğrulama:** `celery -A app.celery_app worker --loglevel=info` çalışmalı, görevler tetiklenmeli.
