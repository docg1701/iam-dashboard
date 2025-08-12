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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiration time (1 hour)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, description="Refresh token expiration time (30 days)")
    
    # 2FA Settings
    TOTP_SECRET_LENGTH: int = Field(default=32, description="TOTP secret length in bytes")
    TOTP_TOKEN_VALIDITY: int = Field(default=30, description="TOTP token validity window in seconds")
    TOTP_ISSUER_NAME: str = Field(default="IAM Dashboard", description="TOTP issuer name")
    BACKUP_CODES_COUNT: int = Field(default=10, description="Number of backup codes to generate")
    BACKUP_CODE_LENGTH: int = Field(default=8, description="Length of backup codes")
    MFA_SETUP_TOKEN_EXPIRE_MINUTES: int = Field(default=10, description="MFA setup token expiration")
    
    # Rate Limiting Configuration
    USER_RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Rate limit for regular users (requests/minute)")
    ADMIN_RATE_LIMIT_PER_MINUTE: int = Field(default=500, description="Rate limit for admin users (requests/minute)")
    SYSADMIN_RATE_LIMIT_PER_MINUTE: int = Field(default=1000, description="Rate limit for sysadmin users (requests/minute)")
    GLOBAL_RATE_LIMIT_PER_MINUTE: int = Field(default=5000, description="Global rate limit (requests/minute)")
    RATE_LIMIT_STORAGE_URL: Optional[str] = Field(default=None, description="Redis URL for rate limiting storage")
    
    # Session Management
    MAX_CONCURRENT_SESSIONS: int = Field(default=5, description="Maximum concurrent sessions per user")
    SESSION_TIMEOUT_MINUTES: int = Field(default=480, description="Session timeout in minutes (8 hours)")
    SESSION_REFRESH_THRESHOLD_MINUTES: int = Field(default=60, description="Refresh session if expires within X minutes")
    SESSION_COOKIE_SECURE: bool = Field(default=True, description="Use secure cookies in production")
    SESSION_COOKIE_HTTPONLY: bool = Field(default=True, description="HTTP-only cookies")
    SESSION_COOKIE_SAMESITE: str = Field(default="lax", description="SameSite cookie policy")
    
    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = Field(default=True, description="Enable security headers")
    HSTS_MAX_AGE: int = Field(default=31536000, description="HSTS max age in seconds (1 year)")
    CSP_POLICY: str = Field(
        default="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com",
        description="Content Security Policy"
    )
    REFERRER_POLICY: str = Field(default="strict-origin-when-cross-origin", description="Referrer policy")
    
    # Production Security Settings
    PRODUCTION_CORS_ORIGINS: List[str] = Field(
        default=["https://*.com.br", "https://iam-dashboard.com.br"],
        description="Production CORS origins"
    )
    COOKIE_DOMAIN: Optional[str] = Field(default=None, description="Cookie domain for production")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS: int = Field(default=1, description="Number of workers")
    
    # CORS and security
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins for development"
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
    
    @computed_field  # type: ignore[misc]
    @property
    def EFFECTIVE_CORS_ORIGINS(self) -> List[str]:
        """Get effective CORS origins based on environment."""
        if self.DEBUG:
            return self.ALLOWED_ORIGINS
        return self.PRODUCTION_CORS_ORIGINS
    
    @computed_field  # type: ignore[misc]
    @property
    def EFFECTIVE_RATE_LIMIT_STORAGE(self) -> str:
        """Get effective rate limit storage URL."""
        return self.RATE_LIMIT_STORAGE_URL or self.REDIS_URL
    
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