# 🚀 Supabase Göç ve Entegrasyon Planı (SUPABASE_IMPLEMENT)

Bu doküman, İstanbul Trafik Alerter projesinin mevcut (veya tamamlanmak üzere olan) klasik backend (FastAPI/Go + PostgreSQL) mimarisinden **Supabase (BaaS) + Python Worker + Flutter** hibrit mimarisine geçişi için hazırlanmış adım adım bir uygulama planıdır. 

Bu dosyayı okuyan yapay zeka (Agent) sırasıyla aşağıdaki adımları uygulamalıdır.

---

## 🏗️ Mimari Özeti
*   **Veritabanı, Auth, Realtime, API Gateway:** Supabase (PostgreSQL + PostgREST)
*   **Arka Plan İşlemleri (Veri Çekme, Tahmin Modeli, ML):** Python Worker (Celery/APScheduler)
*   **Önyüz:** Flutter (Supabase Flutter SDK ile)

---

## Faz 1: Supabase Kurulumu ve Veritabanı Göçü (Database Migration)

Bu fazda, mevcut yerel veritabanı yapısı Supabase'e taşınacaktır.

- [ ] **1.1. Supabase Projesinin Başlatılması:**
  - Supabase CLI kullanılarak projeye entegre edilmesi (`supabase init`) veya mevcut `docker-compose.yml` dosyasına Supabase servislerinin (Kong, Auth, Rest, Realtime, DB) eklenmesi.
- [ ] **1.2. Şema ve Tablo Göçleri:**
  - Mevcut SQLAlchemy / Alembic migration'larının Supabase PostgreSQL veritabanına uygulanması.
  - PostGIS eklentisinin (`create extension postgis;`) Supabase üzerinde aktif edildiğinden emin olunması.
  - `events`, `traffic_zones`, `predictions`, `users` (varsa) tablolarının Supabase'de hazır hale getirilmesi.
- [ ] **1.3. Row Level Security (RLS) Politikalarının Yazılması:**
  - Kuryelerin sadece görmesi gereken verileri görebilmesi veya public verilerin (trafik durumu vs.) anonim veya sadece oturum açmış kullanıcılara okuma izni (SELECT) verecek RLS poliçelerinin yazılıp veritabanına işlenmesi.
- [ ] **1.4. Özel SQL Fonksiyonları (RPC):**
  - Supabase'in standart REST yapısının yetmediği karmaşık PostGIS sorguları (örneğin: "belirtilen koordinata 5 km çapındaki trafik verilerini getir") için Supabase üzerinde Stored Procedure / RPC (`create function...`) yazılması.

---

## Faz 2: Python Backend'in "Worker" Servisine Dönüştürülmesi

Bu fazda, Python projesi dışarıya API hizmeti sunan bir yapıdan, sadece veri toplayıp hesaplama yapan ve sonuçları Supabase'e yazan kapalı bir işçi (worker) servise dönüşecektir.

- [ ] **2.1. API (FastAPI/Gin) Katmanının Temizlenmesi:**
  - `app/main.py` içerisindeki HTTP endpoint'lerinin (router, controller vb.) projeden tamamen silinmesi. API hizmetini artık Supabase (PostgREST) verecek.
- [ ] **2.2. Supabase İstemci (Client) Entegrasyonu:**
  - Python tarafında `supabase-py` kütüphanesinin kurulması veya veritabanına doğrudan `asyncpg`/`SQLAlchemy` ile bağlanarak yazma işlemlerinin Supabase veritabanı hedeflenerek güncellenmesi.
- [ ] **2.3. Celery / Periyodik Görevlerin Güncellenmesi:**
  - İBB, Biletix gibi dış kaynaklardan veri çeken görevlerin (`rule_engine.py`, `fetch_events.py` vb.) hesaplama bittikten sonra sonuçları HTTP API'ye değil, doğrudan Supabase tablolarına (`INSERT` / `UPDATE`) yazacak şekilde refactor edilmesi.

---

## Faz 3: Flutter İstemci (Client) Entegrasyonu

Frontend tarafında doğrudan Supabase ile konuşan bir yapıya geçilecektir.

- [ ] **3.1. Supabase Flutter SDK Kurulumu:**
  - `pubspec.yaml` dosyasına `supabase_flutter` paketinin eklenmesi.
  - `main.dart` içerisinde `Supabase.initialize(url, anonKey)` ile bağlantının kurulması.
- [ ] **3.2. API İsteklerinin Değiştirilmesi (REST -> Supabase SDK):**
  - Uygulama içindeki mevcut `http` paketiyle yapılan GET/POST (örneğin trafik yoğunluğunu getiren endpoint'ler) işlemlerini `supabase.from('predictions').select()` gibi Supabase SDK fonksiyonlarıyla değiştirme.
- [ ] **3.3. Kimlik Doğrulama (Auth) Taşıması (Varsa):**
  - Kullanıcı giriş/çıkış, token yönetimi gibi işlemlerin tamamen `supabase.auth` sistemine geçirilmesi.
- [ ] **3.4. Supabase Realtime (Canlı Güncelleme) Entegrasyonu:**
  - Harita üzerindeki trafik tahminlerinin veya yeni etkinliklerin anında güncellenmesi için `supabase.channel('public:predictions').on(...)` kullanılarak WebSocket dinleyicilerinin (listener) harita ekranına (MapScreen) entegre edilmesi.

---

## Faz 4: Test, Temizlik ve Kapanış

- [ ] **4.1. Ortam Değişkenlerinin (ENV) Güncellenmesi:**
  - Gerekiz backend port, API url vb. env değişkenlerinin silinmesi; yerine `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` gibi değişkenlerin projeye eklenmesi.
- [ ] **4.2. Uçtan Uca (E2E) Test:**
  - Python worker'ın fake bir veri oluşturması, bunun Supabase'e düşmesi ve Flutter uygulamasının bunu Realtime olarak haritada gösterip göstermediğinin test edilmesi.
- [ ] **4.3 Gereksiz Kod Temizliği:**
  - Eski API modelleri, gereksiz bağımlılıklar ve routing/controller dosyalarının projeden kalıcı olarak silinmesi.
