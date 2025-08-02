"""
Application configuration module using Pydantic settings.

All configuration values are validated and type-checked.
Environment variables are loaded from .env files or system environment.
"""

from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="forbid"
    )

    # Project Information
    PROJECT_NAME: str = "Multi-Agent IAM Dashboard"
    PROJECT_DESCRIPTION: str = "Custom Implementation Service with Independent Agents"
    PROJECT_VERSION: str = "1.0.0"

    # Environment Configuration
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    PORT: int = Field(default=8000, description="Server port")

    # Security Configuration
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens and encryption",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15, description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration time in days"
    )

    # Database Configuration
    POSTGRES_SERVER: str = Field(default="localhost", description="PostgreSQL server")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="postgres", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="dashboard", description="PostgreSQL database name")

    @computed_field
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL database URL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379", description="Redis connection URL")

    # CORS Configuration
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    # Celery Configuration
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0", description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0", description="Celery result backend URL"
    )

    # Logging Configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = Field(default=10, description="Maximum file upload size in MB")
    ALLOWED_FILE_TYPES: list[str] = Field(
        default=["pdf", "doc", "docx", "txt"], description="Allowed file upload types"
    )

    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Rate limit per minute per IP")


# Create global settings instance
settings = Settings()
