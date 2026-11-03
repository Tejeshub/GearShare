from functools import lru_cache
from typing import List, Optional, Union
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "GearShare API"
    APP_ENV: str = "development"
    DEBUG: bool = False
    DATABASE_URL: SecretStr
    SECRET_KEY: Optional[SecretStr] = None
    ALLOWED_ORIGINS: Union[str, List[str]] = ["*"]

    # Database Pool Settings for Supabase
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Admin API Authentication
    ADMIN_API_KEY: Optional[SecretStr] = None

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]], info) -> List[str]:
        if isinstance(v, str):
            if not v.strip():
                return ["*"]
            origins = [i.strip() for i in v.split(",") if i.strip()]
            return origins if origins else ["*"]
        return v

    @property
    def sqlalchemy_database_uri(self) -> str:
        """
        Normalizes the connection URI for SQLAlchemy + psycopg 3.
        Supabase provides URLs starting with 'postgresql://' or 'postgres://'.
        SQLAlchemy requires 'postgresql+psycopg://' when using psycopg 3.
        Ensures sslmode=require for secure Supabase connectivity.
        """
        raw_url = self.DATABASE_URL.get_secret_value()
        if raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif raw_url.startswith("postgresql://"):
            raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif not raw_url.startswith("postgresql+psycopg://"):
            raw_url = f"postgresql+psycopg://{raw_url.split('://', 1)[-1]}" if "://" in raw_url else raw_url

        # Ensure sslmode is present if dealing with remote postgres/supabase
        if "sslmode=" not in raw_url and ("supabase.co" in raw_url or self.APP_ENV != "test"):
            separator = "&" if "?" in raw_url else "?"
            raw_url = f"{raw_url}{separator}sslmode=require"

        return raw_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
