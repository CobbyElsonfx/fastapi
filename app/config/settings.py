"""Application configuration from environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised settings — extend as new AI endpoints are added."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Academic Intelligence Service"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Comma-separated list of allowed browser origins for CORS (Laravel + Vite).
    cors_origins: str = (
        "http://127.0.0.1:8000,http://localhost:8000,"
        "http://127.0.0.1:5173,http://localhost:5173"
    )

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def strip_api_key(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v).strip()

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
