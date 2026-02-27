# Faz 0: Proje Altyapısı & DevOps Temelleri

---

## Görev 0.1 — Docker Compose Dosyası Oluştur
- **Girdi:** Yok (sıfırdan)
- **Çıktı:** `backend/docker-compose.yml`
- **Talimat:** PostgreSQL 16 + PostGIS 3.4, Redis 7 ve pgAdmin servislerini tanımlayan bir `docker-compose.yml` dosyası oluştur. Volumeler kalıcı olsun. PostgreSQL için `POSTGRES_DB=istanbul_traffic`, `POSTGRES_USER=traffic_user`, `POSTGRES_PASSWORD=traffic_pass` env değişkenleri tanımla. Redis varsayılan portta çalışsın. Network adı `traffic-net` olsun.
- **Doğrulama:** `docker compose up -d` ile 3 servis de hatasız başlamalı.

---

## Görev 0.2 — Python Proje İskeleti & Bağımlılıklar
- **Girdi:** Yok
- **Çıktı:** `backend/` klasör yapısı + `requirements.txt` + `pyproject.toml`
- **Talimat:** Aşağıdaki klasör yapısını oluştur:
  ```
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── database.py
  │   ├── models/
  │   │   └── __init__.py
  │   ├── schemas/
  │   │   └── __init__.py
  │   ├── services/
  │   │   └── __init__.py
  │   ├── routers/
  │   │   └── __init__.py
  │   ├── prediction/
  │   │   └── __init__.py
  │   └── tasks/
  │       └── __init__.py
  ├── tests/
  │   └── __init__.py
  ├── requirements.txt
  └── pyproject.toml
  ```
  `requirements.txt` içeriği: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `geoalchemy2`, `asyncpg`, `redis`, `celery[redis]`, `httpx`, `pydantic-settings`, `python-jose[cryptography]`, `passlib[bcrypt]`, `alembic`, `pytest`, `pytest-asyncio`.
  `main.py`: Basit bir FastAPI uygulaması, `/health` endpoint'i dönsün.
- **Doğrulama:** `uvicorn app.main:app --reload` çalışmalı, `GET /health` → `{"status": "ok"}` dönmeli.

---

## Görev 0.3 — Alembic Migration Altyapısı
- **Girdi:** Görev 0.2'nin çıktıları
- **Çıktı:** `backend/alembic/` klasörü + `alembic.ini`
- **Talimat:** Alembic'i async SQLAlchemy + PostGIS destekleyecek şekilde konfigüre et. `alembic init alembic` çalıştır, `env.py` dosyasını async engine kullanacak şekilde güncelle. `alembic.ini`'de database URL'ini `config.py`'den okuyan yapıyı kur.
- **Doğrulama:** `alembic revision --autogenerate -m "initial"` hata vermeden çalışmalı.

---

## Görev 0.4 — config.py (Pydantic Settings)
- **Girdi:** Yok
- **Çıktı:** `backend/app/config.py` + `.env.example`
- **Talimat:** `pydantic-settings` kullanarak `Settings` sınıfı oluştur. Alanlar: `DATABASE_URL`, `REDIS_URL`, `GOOGLE_MAPS_API_KEY`, `IBB_OPEN_DATA_API_KEY`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`. Değerler `.env` dosyasından okunmalı. `.env.example` dosyasını da oluştur.
- **Doğrulama:** Dosya import edildiğinde hata vermemeli, `.env` yokken default değerler kullanılmalı.
