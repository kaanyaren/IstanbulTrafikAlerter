# 🏗️ İstanbul Trafik Tahmin Uygulaması — Mimari İnceleme Raporu

## 1. Mevcut Mimarinin Eleştirisi

### ✅ Doğru Kararlar

| Karar | Neden Doğru |
|---|---|
| **PostgreSQL + PostGIS** | Coğrafi sorgular (yarıçap içi etkinlikler, rota hesaplamaları) için endüstri standardı. Doğru seçim. |
| **Redis önbellek** | Etkinlik verileri saatlik/günlük değişir; her istekte API çağırmak yerine cache'lemek hem maliyet hem gecikme açısından kritik. |
| **Cross-platform hedefi** | Kurye/lojistik kullanıcıları hem sahada (mobil) hem ofiste (web) kullanacak. Tek codebase mantıklı. |

### ⚠️ Sorunlu / Eksik Alanlar

#### 1.1 Go Backend — "Hızlı Geliştirme" İddiası Gerçekçi Mi?

Go **yüksek performans** için mükemmeldir, ancak **hızlı prototipleme** için değildir.

| Kriter | Go (Fiber/Gin) | Alternatif (FastAPI) |
|---|---|---|
| Geliştirme hızı | 🟡 Orta — boilerplate fazla, ORM desteği zayıf | 🟢 Yüksek — Pydantic, auto-docs, async native |
| Performans | 🟢 Çok yüksek | 🟢 Yüksek (yeterli) |
| GeoJSON/PostGIS entegrasyonu | 🟡 Manuel — `pgx` + raw SQL | 🟢 `GeoAlchemy2` ile ORM düzeyinde |
| Ekosistem (ML/tahmin) | 🔴 Yok — FFI veya mikroservis gerekir | 🟢 `scikit-learn`, `pandas` native |
| Background task (cron jobs) | 🟡 Manuel goroutine yönetimi | 🟢 Celery / APScheduler entegre |

> [!IMPORTANT]
> **"Trafik tahmini" bir ML/veri problemidir.** Go ile tahmin modeli geliştirmek veya entegre etmek son derece zordur. Python ekosistemi (scikit-learn, prophet, statsmodels) bu projenin çekirdeği için çok daha uygun.

#### 1.2 SvelteKit + Capacitor — Riskler

| Risk | Açıklama |
|---|---|
| **Harita performansı** | WebView içinde MapLibre/Leaflet çalıştırmak native harita SDK'larına göre belirgin şekilde yavaş. Kurye uygulamasında bu deneyimi bozar. |
| **Arka plan konum takibi** | Capacitor'da background geolocation sınırlı. Kurye uygulamasında uygulama kapalıyken konum takibi kritik. |
| **Push notification güvenilirliği** | "Yarın X bölgesinde trafik yoğun olacak" bildirimleri için native push gerekir. Capacitor bunu destekler ama edge case'lerde sorunlu olabilir. |
| **Capacitor ekosistem olgunluğu** | React Native veya Flutter'a kıyasla daha küçük topluluk, daha az 3rd-party plugin. |

> [!WARNING]
> Eğer harita etkileşimi (rota çizme, canlı trafik katmanı, pin'ler) uygulamanın çekirdeğiyse, **WebView tabanlı çözümler ciddi performans sorunu yaratır**. Flutter veya React Native ile native harita SDK'ları kullanmak çok daha akıllıca.

#### 1.3 Eksik Mimari Bileşenler

Mevcut tasarımda şu kritik bileşenler hiç yok:

| Eksik Bileşen | Neden Gerekli |
|---|---|
| **Message Queue (RabbitMQ / BullMQ)** | Birden fazla API'den veri çekme, işleme ve tahmin pipeline'ı asenkron olmalı. Senkron API çağrıları backend'i kilitler. |
| **Scheduled Job Sistemi** | Etkinlik takvimlerini periyodik olarak çekmek, tahmin modelini yeniden çalıştırmak için cron/scheduler gerekli. |
| **Rate Limiting & Circuit Breaker** | Ücretsiz API'ler sıkı rate limit'lere sahip. Bunları aşınca uygulamanın çökmemesi gerekir. |
| **Tahmin/ML Servisi** | "Trafik tahmini" yapan bir bileşen tanımlanmamış. Burada ne kullanılacak? Kural tabanlı mı, ML tabanlı mı? |
| **API Gateway / Reverse Proxy** | Rate limiting, auth, CORS, request logging tek noktadan yönetilmeli. |

---

## 2. Gözden Kaçan Darboğazlar ve Ölçeklenme Sorunları

### 🔴 Kritik Darboğazlar

#### 2.1 Ücretsiz API Rate Limitleri
| API | Tipik Ücretsiz Limit | Problem |
|---|---|---|
| Google Maps (Directions) | 40K istek/ay (~1.3K/gün) | 100 kurye × 13 rota sorgusu/gün = limit! |
| OpenRouteService | 2K istek/gün | Az sayıda kullanıcıda bile yetersiz |
| Eventbrite / Ticketmaster | 1K-5K istek/gün | Etkinlik verisi için yeterli, ama caching şart |

> [!CAUTION]
> **"Ücretsiz API" stratejisi ölçeklenmez.** 50+ aktif kurye ile bu limitlere hızla ulaşılır. Rota sorgularını **agresif cache'leme + batch işleme** ile minimize etmeli, ayrıca bir **fallback plan** (ücretli tier veya self-hosted OSRM) hazırlamalısınız.

#### 2.2 PostGIS Sorgu Performansı
- Canlı trafik verisi + etkinlik lokasyonları + kurye pozisyonları aynı DB'de olursa, spatial index'ler yetmeyebilir.
- **Çözüm:** Read replica + materialized view'lar ile okuma yükünü dağıtmak.

#### 2.3 Real-time Güncellemeler
- Kuryelere anlık trafik değişikliği göndermek gerekecek → **WebSocket / SSE** altyapısı tasarımda yok.
- Redis Pub/Sub veya dedicated bir WebSocket servisi planlanmalı.

#### 2.4 Cold Start / Veri Bağımlılığı
- Uygulama ilk açıldığında tüm API'lerden veri çekmek gerekecek. Bu **5-10 saniye** sürer.
- **Çözüm:** Ön-hesaplanmış tahminleri Redis'te tutmak. Kullanıcıya anında sonuç göstermek.

---

## 3. Alternatif Mimari Önerisi

Aşağıda, **geliştirme hızı** ve **performans** dengesini daha iyi kuran bir mimari öneriyorum:

### 🏗️ Önerilen Stack

```
┌──────────────────────────────────────────────────────┐
│                    CLIENT LAYER                       │
│  Flutter (Web + iOS + Android)                       │
│  - Native harita SDK'ları (Google Maps / Mapbox)     │
│  - Arka plan konum takibi (native plugin)            │
│  - Push notifications (Firebase)                     │
└──────────────────┬───────────────────────────────────┘
                   │ REST + WebSocket
┌──────────────────▼───────────────────────────────────┐
│                   API GATEWAY                         │
│  Nginx / Traefik                                     │
│  - Rate limiting, auth, CORS, SSL                    │
└──────────────────┬───────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────┐
│               BACKEND SERVICES                       │
│                                                      │
│  ┌─────────────────────┐  ┌───────────────────────┐ │
│  │  API Service         │  │  Prediction Service   │ │
│  │  Python / FastAPI    │  │  Python               │ │
│  │  - CRUD ops          │  │  - scikit-learn       │ │
│  │  - Auth (JWT)        │  │  - Scheduled jobs     │ │
│  │  - WebSocket         │  │  - Model training     │ │
│  │  - Rota optimizasyon │  │  - Tahmin pipeline    │ │
│  └────────┬────────────┘  └───────────┬───────────┘ │
│           │                           │              │
└───────────┼───────────────────────────┼──────────────┘
            │                           │
┌───────────▼───────────────────────────▼──────────────┐
│                   DATA LAYER                          │
│                                                      │
│  ┌──────────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ PostgreSQL   │  │  Redis   │  │ Task Queue    │  │
│  │ + PostGIS    │  │  Cache + │  │ (Celery +     │  │
│  │              │  │  Pub/Sub │  │  Redis broker) │  │
│  └──────────────┘  └──────────┘  └───────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Neden Bu Stack?

| Bileşen | Seçim | Gerekçe |
|---|---|---|
| **Frontend** | **Flutter** | Native harita performansı, arka plan konum, tek codebase (web+mobile). Capacitor'a göre çok daha olgun ekosistem. |
| **Backend API** | **Python / FastAPI** | Async native, otomatik API docs (Swagger), Pydantic ile validation, GeoAlchemy2 ile PostGIS entegrasyonu. Geliştirme hızı Go'ya göre 2-3x fazla. |
| **Tahmin Servisi** | **Python** | ML ekosistemi (scikit-learn, prophet) doğrudan kullanılır. Ayrı servis olarak deploy edilebilir. |
| **Task Queue** | **Celery + Redis** | API'lerden periyodik veri çekme, tahmin model güncelleme, batch rota hesaplama. |
| **Veritabanı** | **PostgreSQL + PostGIS** | Değişiklik yok — doğru seçim. |
| **Cache** | **Redis** | Değişiklik yok — ayrıca Pub/Sub ile real-time bildirimler. |

> [!NOTE]
> **Performans endişesi:** "FastAPI, Go kadar hızlı değil" diye düşünebilirsiniz. Ancak bu uygulamada darboğaz CPU değil, **I/O'dur** (API çağrıları, DB sorguları). FastAPI'nin async yapısı bu senaryoda Go ile neredeyse eşdeğer performans sunar. Eğer ileride CPU-bound bir darboğaz çıkarsa, sadece o servisi Go/Rust ile yeniden yazabilirsiniz.

### Neden Go Değil?

Go **yanlış bir seçim değildir**, ancak bu proje için **overkill + yavaş geliştirme** denklemi oluşturur:
- Tahmin motoru için Python'a zaten ihtiyacınız olacak → 2 dil yönetmek zorundasınız.
- Go'nun avantajı olan concurrency modeli, bu projede FastAPI'nin async/await'i ile karşılanır.
- Prototipten ürüne geçiş Go ile 2-3 ay daha uzun sürer.

### Neden .NET MAUI veya React Native Değil?

| Alternatif | Red Sebebi |
|---|---|
| **.NET MAUI** | Harita entegrasyonu zayıf, topluluk küçük, cross-platform web desteği yok. |
| **React Native** | Geçerli bir alternatif! Ancak Flutter'ın web desteği daha olgun ve harita performansı daha iyi. Eğer React ekosistemi deneyimiz varsa React Native da makul. |
| **SvelteKit + Capacitor** | Harita performansı ve arka plan servisleri için yetersiz (yukarıda detaylı açıklandı). |

---

## 4. Projeye Başlangıç: İlk 3 Adım

### Adım 1: Veri Katmanı & API Entegrasyon Prototipi (1-2 hafta)

**Hedef:** Kullanacağınız API'lerin gerçek limitlerini ve veri kalitesini test edin.

```
d:\IstanbulTrafikAlerter\
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # API keys, DB connection
│   │   ├── services/
│   │   │   ├── event_service.py # Etkinlik API'lerinden veri çekme
│   │   │   ├── traffic_service.py # Trafik verisi çekme
│   │   │   └── geocoding.py     # Adres → koordinat
│   │   └── models/
│   │       ├── event.py         # SQLAlchemy + PostGIS modelleri
│   │       └── traffic_zone.py
│   ├── requirements.txt
│   └── docker-compose.yml       # PostgreSQL + PostGIS + Redis
```

**Yapılacaklar:**
1. Docker ile PostgreSQL/PostGIS + Redis ayağa kaldırma
2. En az 2-3 etkinlik API'sine bağlanma (Biletix, Passo, belediye açık veri)
3. Veriyi PostGIS'e kaydetme ve basit bir spatial sorgu çalıştırma
4. Redis'te cache mekanizmasını kurma
5. "X stadyumunun 2km çevresinde yarın etkinlik var mı?" sorgusunu çalıştırma

> [!TIP]
> Bu adımda frontend'e hiç dokunmayın. Sadece API + DB + Cache prototipini çalıştırın. Swagger UI ile her şeyi test edebilirsiniz.

---

### Adım 2: Tahmin Motoru MVP (1-2 hafta)

**Hedef:** Basit kural tabanlı bir tahmin motoru oluşturun, sonra ML ile geliştirin.

```
backend/
├── app/
│   ├── prediction/
│   │   ├── rule_engine.py       # Kural tabanlı tahmin (v1)
│   │   ├── ml_model.py          # ML tabanlı tahmin (v2)
│   │   ├── features.py          # Feature engineering
│   │   └── scoring.py           # Trafik yoğunluk skoru (0-100)
│   ├── tasks/
│   │   ├── fetch_events.py      # Celery: periyodik etkinlik çekme
│   │   ├── fetch_traffic.py     # Celery: trafik verisi güncelleme
│   │   └── run_predictions.py   # Celery: tahmin pipeline
```

**v1 (Kural Tabanlı):**
```python
# Basit kural: Etkinlik kapasitesi + saat + lokasyon → skor
def predict_congestion(event, time_of_day, day_of_week):
    score = 0
    if event.capacity > 10_000:
        score += 40
    if 17 <= time_of_day.hour <= 19:  # Rush hour
        score += 30
    if day_of_week in [4, 5]:  # Cuma-Cumartesi
        score += 20
    return min(score, 100)
```

**v2 (ML — ileride):**
- Geçmiş trafik verisi + etkinlik verisi ile model eğitimi
- `scikit-learn` RandomForest veya XGBoost ile başlangıç

---

### Adım 3: Flutter Harita Arayüzü (1-2 hafta)

**Hedef:** Harita üzerinde tahmin sonuçlarını görselleştiren minimal ama çalışan bir mobil uygulama.

```
d:\IstanbulTrafikAlerter\
├── mobile/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   │   ├── map_screen.dart      # Ana harita ekranı
│   │   │   └── route_planner.dart   # Rota planlama
│   │   ├── services/
│   │   │   ├── api_service.dart     # Backend API çağrıları
│   │   │   └── location_service.dart
│   │   ├── models/
│   │   │   ├── congestion_zone.dart
│   │   │   └── event.dart
│   │   └── widgets/
│   │       ├── congestion_overlay.dart # Isı haritası katmanı
│   │       └── event_marker.dart
```

**Yapılacaklar:**
1. Flutter projesi oluşturup Google Maps / Mapbox entegrasyonu
2. Backend API'den tahmin verilerini çekme
3. Isı haritası (heatmap) ile trafik yoğunluğunu gösterme
4. Etkinlik pin'leri ve detay bottom sheet
5. Basit rota planlama (A → B, yoğun bölgelerden kaçınma)

---

## 5. Özet Karşılaştırma

| Kriter | Mevcut Tasarım | Önerilen Tasarım |
|---|---|---|
| Geliştirme hızı | 🟡 Orta | 🟢 Yüksek |
| Harita performansı | 🔴 WebView sınırlı | 🟢 Native SDK |
| ML/Tahmin entegrasyonu | 🔴 Go ile çok zor | 🟢 Python native |
| Arka plan servisleri | 🟡 Capacitor sınırlı | 🟢 Flutter native plugin |
| Ölçeklenebilirlik | 🟡 Monolitik risk | 🟢 Servis ayrımı hazır |
| Topluluk/Ekosistem | 🟡 Capacitor küçük | 🟢 Flutter büyük |
| Performans (backend) | 🟢 Go çok hızlı | 🟢 FastAPI yeterli |

> [!IMPORTANT]
> **Son söz:** Mevcut tasarım "çalışır" ama bu projenin doğasına (coğrafi veri + ML tahmin + harita ağırlıklı mobil) uymuyor. **Python (FastAPI) + Flutter** kombinasyonu hem daha hızlı geliştirilir hem de projenin ihtiyaçlarına daha iyi cevap verir.
