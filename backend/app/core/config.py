from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Intent-Based Network Controller"
    api_prefix: str = "/api"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 120
    algorithm: str = "HS256"
    database_url: str = "sqlite:///./intent_controller.db"
    auto_remediate: bool = False
    telemetry_interval_seconds: int = 20
    compliance_interval_seconds: int = 30
    enable_drift_simulation: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT.parent / "frontend"
