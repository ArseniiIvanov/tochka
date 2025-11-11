"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database settings
    postgres_user: str = Field(default="trading_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="secure_password_2024", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: str = Field(default="5432", alias="POSTGRES_PORT")
    postgres_db: str = Field(default="trading_platform_db", alias="POSTGRES_DB")

    # JWT settings
    secret_key: str = Field(default="ultra-secret-key", alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=999999, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Application settings
    base_instrument_ticker: str = Field(
        default="RUB", alias="BASE_INSTRUMENT_TICKER"
    )

    # API settings
    api_v1_prefix: str = "/api/v1"
    token_prefix: str = "TOKEN"
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def database_url(self) -> str:
        """Construct database URL from settings."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

