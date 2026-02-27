# Faz 6: Test & Deploy

---

## Görev 6.1 — Backend Unit Testleri
- **Girdi:** Faz 1-4 çıktıları
- **Çıktı:** `backend/tests/` dosyaları
- **Talimat:** pytest + pytest-asyncio ile:
  - `test_event_repo.py`: CRUD + spatial query testleri
  - `test_prediction_engine.py`: Bilinen senaryolar ile skor doğrulama
  - `test_cache.py`: Cache set/get/ttl testleri
  - `test_auth.py`: Register/login/token doğrulama
  - Test DB için SQLite in-memory veya test PostgreSQL container.
- **Doğrulama:** `pytest --cov` ile %80+ kapsam hedefi.

---

## Görev 6.2 — Backend Dockerfile & Production Compose
- **Girdi:** Görev 0.1, tüm backend görevleri
- **Çıktı:** `backend/Dockerfile` + `docker-compose.prod.yml`
- **Talimat:** Multi-stage Dockerfile: build stage (pip install) + runtime stage (slim image). Production compose: Nginx + FastAPI (2 replica) + Celery worker + Celery beat + PostgreSQL + Redis. Health check'ler tanımlı. `.env` ile secret yönetimi.
- **Doğrulama:** `docker compose -f docker-compose.prod.yml up` ile tüm servisler sağlıklı başlamalı.

---

## Görev 6.3 — CI/CD Pipeline (GitHub Actions)
- **Girdi:** Görev 6.1, 6.2
- **Çıktı:** `.github/workflows/ci.yml`
- **Talimat:** Push/PR → lint (ruff) + type check (mypy) + test (pytest) + Docker build. Main branch merge → otomatik deploy (placeholder, hangi cloud'a deploy edileceğine göre güncellenir).
- **Doğrulama:** GitHub'a push sonrası workflow başarılı çalışmalı.
