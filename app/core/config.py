"""Configuration management for the application."""

import os


class Config:
    """Application configuration settings."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/advocacia_db"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Application
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "your-secret-key-here-change-in-production"
    )
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Google Gemini
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "embedding-001")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-here")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # 2FA
    TOTP_ISSUER_NAME: str = os.getenv("TOTP_ISSUER_NAME", "IAM Dashboard")

    # Agent Management API
    AGENT_API_BASE_URL: str = os.getenv(
        "AGENT_API_BASE_URL", "http://localhost:8080/v1"
    )

    @classmethod
    def get_agent_endpoint(cls, path: str) -> str:
        """Get full agent API endpoint URL."""
        return f"{cls.AGENT_API_BASE_URL}{path}"


# Global config instance
config = Config()
