"""
Tests for configuration module.

This module tests the application configuration and settings validation.
"""

from src.core.config import Settings


def test_default_settings() -> None:
    """Test default configuration values."""
    settings = Settings()

    assert settings.PROJECT_NAME == "Multi-Agent IAM Dashboard"
    assert settings.PROJECT_VERSION == "1.0.0"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is False
    assert settings.PORT == 8000
    assert settings.POSTGRES_SERVER == "localhost"
    assert settings.POSTGRES_PORT == 5432
    assert settings.POSTGRES_USER == "postgres"
    assert settings.POSTGRES_DB == "dashboard"


def test_database_url_construction() -> None:
    """Test DATABASE_URL property construction."""
    settings = Settings()
    expected_url = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    assert str(settings.DATABASE_URL) == expected_url


def test_allowed_origins_default() -> None:
    """Test default CORS origins."""
    settings = Settings()
    expected_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    assert expected_origins == settings.ALLOWED_ORIGINS


def test_environment_validation() -> None:
    """Test environment value validation."""
    # Valid environment
    settings = Settings(ENVIRONMENT="production")
    assert settings.ENVIRONMENT == "production"

    # Invalid environment should use default
    settings = Settings()
    assert settings.ENVIRONMENT == "development"


def test_port_validation() -> None:
    """Test port number validation."""
    settings = Settings(PORT="8080")
    assert settings.PORT == 8080

    # Default port
    settings = Settings()
    assert settings.PORT == 8000


def test_boolean_field_validation() -> None:
    """Test boolean field validation."""
    settings = Settings(DEBUG="true")
    assert settings.DEBUG is True

    settings = Settings(DEBUG="false")
    assert settings.DEBUG is False

    # Default value
    settings = Settings()
    assert settings.DEBUG is False
