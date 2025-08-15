"""
Pytest configuration and fixtures for backend testing.
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.core.config import Settings, get_settings
from src.core.database import get_async_session
from src.main import create_app

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create test session maker
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        SECRET_KEY="test-secret-key-change-in-production",
        DB_PASSWORD="test-password",
        DEBUG=True,
        ALLOWED_HOSTS=[
            "testserver",
            "localhost",
            "127.0.0.1",
            "test",
        ],  # Allow test hosts
        ALLOWED_ORIGINS=["http://testserver", "http://test"],  # Add test hosts for CORS
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession]:
    """Create a test database session."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session with proper async context
    session = TestAsyncSessionLocal()
    try:
        # Start transaction
        await session.begin()
        yield session
        # Rollback any uncommitted changes
        await session.rollback()
    except Exception:
        # Ensure rollback on error
        await session.rollback()
        raise
    finally:
        # Close session
        await session.close()

    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def override_get_async_session(async_session: AsyncSession):
    """Override database session dependency."""

    async def _override_get_async_session():
        yield async_session

    return _override_get_async_session


@pytest_asyncio.fixture
async def app(override_get_async_session, test_settings: Settings):
    """Create FastAPI test application."""
    # Clear settings cache and override before creating app
    get_settings.cache_clear()

    def get_test_settings() -> Settings:
        return test_settings

    # Temporarily override the settings function
    import src.core.config

    original_get_settings = src.core.config.get_settings
    src.core.config.get_settings = get_test_settings

    try:
        app = create_app()
        app.dependency_overrides[get_async_session] = override_get_async_session
        app.dependency_overrides[get_settings] = get_test_settings
        return app
    finally:
        # Restore original function
        src.core.config.get_settings = original_get_settings


@pytest_asyncio.fixture
async def client(app) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Mock fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_file_storage():
    """Mock file storage service."""
    mock = AsyncMock()
    return mock


# Sample data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "is_active": True,
    }


@pytest.fixture
def sample_client_data():
    """Sample client data for testing."""
    return {
        "name": "Test Client",
        "email": "client@example.com",
        "cpf_cnpj": "12345678901",
        "phone": "+55 11 99999-9999",
        "status": "active",
        "metadata": {"custom_field": "value"},
    }


# Configuration fixtures


# Markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )


# Test environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Store original values to restore later
    original_values = {}

    # Override environment variables for testing
    test_env_vars = {
        "TESTING": "true",
        "SECRET_KEY": "test-secret-key",
        "DATABASE_URL": TEST_DATABASE_URL,
        "DEBUG": "true",
        "ALLOWED_HOSTS": "[]",  # Empty list to disable TrustedHostMiddleware
        "ALLOWED_ORIGINS": '["http://testserver", "http://test"]',  # Add test hosts
    }

    for key, value in test_env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    # Clear settings cache to force reload with test env vars
    get_settings.cache_clear()

    yield

    # Restore original environment variables
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value

    # Clear cache again to restore original settings
    get_settings.cache_clear()
