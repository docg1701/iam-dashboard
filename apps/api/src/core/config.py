"""
Application configuration management.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings configuration."""
    
    # Application settings
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    SECRET_KEY: str = Field(..., description="Secret key for JWT token generation")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration time")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration time")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS: int = Field(default=1, description="Number of workers")
    
    # CORS and security
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    ALLOWED_HOSTS: Optional[List[str]] = Field(
        default=None,
        description="Allowed hosts for TrustedHostMiddleware"
    )
    
    # Database settings
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=5432, description="Database port")
    DB_USER: str = Field(default="postgres", description="Database user")
    DB_PASSWORD: str = Field(..., description="Database password")
    DB_NAME: str = Field(default="iam_dashboard", description="Database name")
    DB_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow connections")
    
    # Redis settings
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_TTL: int = Field(default=3600, description="Redis default TTL in seconds")
    
    # Permission system settings
    PERMISSION_CACHE_TTL: int = Field(default=300, description="Permission cache TTL in seconds")
    PERMISSION_CHECK_TIMEOUT: int = Field(default=10, description="Permission check timeout in milliseconds")
    
    # Audit settings
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=90, description="Audit log retention in days")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Maximum file size in bytes (10MB)")
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(
        default=[".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv"],
        description="Allowed file extensions for uploads"
    )
    
    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        """Generate database URL from components."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @computed_field  # type: ignore[misc]
    @property
    def REDIS_URL(self) -> str:
        """Generate Redis URL from components."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()