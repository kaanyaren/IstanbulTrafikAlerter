from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Supabase ──────────────────────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # ── Direct DB connection (worker uses this for SQLAlchemy/PostGIS) ───
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

    # ── Redis (Celery broker) ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── External API keys ────────────────────────────────────────────────
    GOOGLE_MAPS_API_KEY: str = ""
    IBB_OPEN_DATA_API_KEY: str = ""

    # ── Event connector selection ───────────────────────────────────────
    # "*" => tüm connector'lar aktif
    # Virgülle ayrılmış liste => sadece bu connector'lar aktif
    # Örn: "ibb_kultur,akm,tff_football_super-lig"
    ENABLED_EVENT_CONNECTORS: str = "*"
    # Virgülle ayrılmış connector isimleri hariç tutulur
    # Örn: "party_sites_best_effort,social_signal"
    DISABLED_EVENT_CONNECTORS: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
