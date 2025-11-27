from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Turneo API
    turneo_api_root: str = "https://api.san.turneo.co"
    turneo_api_key: str

    # FX Rates API
    fx_api_root: str | None = None
    fx_api_key: str | None = None

    # LLM
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
