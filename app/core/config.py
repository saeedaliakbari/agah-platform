from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra="ignore")
    app_name: str = "Agah Platform API"
    environment: str = "development"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agah_platform"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    test_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/agah_platform_test"
    bale_bot_token: str = ""
    verification_channel_id: int = 0
    wallet_channel_id: int = 0
    
@lru_cache
def get_settings() -> Settings:
    return Settings()