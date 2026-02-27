from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://traffic_user:traffic_pass@localhost:5432/istanbul_traffic"
    REDIS_URL: str = "redis://localhost:6379"
    GOOGLE_MAPS_API_KEY: str = ""
    IBB_OPEN_DATA_API_KEY: str = ""
    SECRET_KEY: str = "supersecretkey"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
