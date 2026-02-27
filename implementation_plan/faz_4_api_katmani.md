# Faz 4: API Katmanı & Auth

---

## Görev 4.1 — JWT Authentication
- **Girdi:** Görev 0.2
- **Çıktı:** `backend/app/auth/` klasörü
- **Talimat:** `auth/jwt.py`: JWT token oluşturma / doğrulama. `auth/dependencies.py`: `get_current_user` dependency. `auth/router.py`: `POST /auth/register`, `POST /auth/login` → JWT dönsün. User modeli: `id`, `email`, `hashed_password`, `role` (user/admin), `created_at`.
- **Doğrulama:** Register → Login → Protected endpoint erişim akışı çalışmalı.

---

## Görev 4.2 — Event CRUD Router
- **Girdi:** Görev 1.1, 1.4, 1.5
- **Çıktı:** `backend/app/routers/events.py`
- **Talimat:** `GET /api/v1/events` (filtreler: tarih aralığı, kategori, konum+yarıçap), `GET /api/v1/events/{id}`, `POST /api/v1/events` (admin only), `PUT /api/v1/events/{id}` (admin only). Pagination destekle (offset/limit).
- **Doğrulama:** CRUD işlemleri Swagger UI'dan test edilmeli.

---

## Görev 4.3 — WebSocket Real-time Güncellemeler
- **Girdi:** Görev 0.2, 3.3
- **Çıktı:** `backend/app/routers/ws.py`
- **Talimat:** FastAPI WebSocket endpoint: `ws://host/ws/predictions?zone_ids=z1,z2,z3`. Client bağlandığında ilgili bölgelerin tahminlerini Redis Pub/Sub üzerinden dinleyip real-time push et. Connection management (heartbeat, reconnect bilgisi).
- **Doğrulama:** WebSocket client ile bağlanıp tahmin güncellemelerini dinleme testi.

---

## Görev 4.4 — API Gateway Nginx Konfigürasyonu
- **Girdi:** Görev 0.1
- **Çıktı:** `nginx/nginx.conf` + docker-compose'a nginx servisi eklenmesi
- **Talimat:** Nginx reverse proxy: `/api/` → FastAPI backend, `/ws/` → WebSocket backend. Rate limiting: 100 req/min per IP. CORS headers. SSL sertifika placeholder. Gzip compression.
- **Doğrulama:** `curl` ile API'ye nginx üzerinden erişim testi.
