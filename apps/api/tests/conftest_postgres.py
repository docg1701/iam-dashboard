"""
PostgreSQL-based test configuration for production-like testing.

This configuration uses an actual PostgreSQL database to ensure
compatibility with production and proper enum handling.
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

# PostgreSQL test database URL (connects to Docker PostgreSQL)
TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:password@localhost:5432/iam_dashboard_test"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
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
    """Override settings for PostgreSQL testing."""
    return Settings(
        SECRET_KEY="test-secret-key-change-in-production",
        DB_PASSWORD="password",
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_USER="postgres",
        DB_NAME="iam_dashboard_test",
        DATABASE_URL=TEST_DATABASE_URL,
        DEBUG=True,
        ALLOWED_HOSTS=[
            "testserver",
            "localhost",
            "127.0.0.1",
            "test",
        ],
        ALLOWED_ORIGINS=["http://testserver", "http://test"],
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_test_database():
    """Set up test database schema once per session."""
    # Create test database engine
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:password@localhost:5432/postgres",
        echo=False,
        isolation_level="AUTOCOMMIT",
    )

    async with engine.connect() as conn:
        # Drop and recreate test database
        await conn.execute("DROP DATABASE IF EXISTS iam_dashboard_test")
        await conn.execute("CREATE DATABASE iam_dashboard_test")

    await engine.dispose()

    # Create all tables in test database
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Cleanup: Drop test database
    cleanup_engine = create_async_engine(
        "postgresql+asyncpg://postgres:password@localhost:5432/postgres",
        echo=False,
        isolation_level="AUTOCOMMIT",
    )

    async with cleanup_engine.connect() as conn:
        await conn.execute("DROP DATABASE IF EXISTS iam_dashboard_test")

    await cleanup_engine.dispose()


@pytest_asyncio.fixture
async def async_session(setup_test_database) -> AsyncGenerator[AsyncSession]:
    """Create a test database session with transaction rollback."""
    # Create session with proper async context
    session = TestAsyncSessionLocal()
    try:
        # Start transaction that will be rolled back
        transaction = await session.begin()
        yield session
        # Rollback transaction to clean up test data
        await transaction.rollback()
    except Exception:
        # Ensure rollback on error
        await session.rollback()
        raise
    finally:
        # Close session
        await session.close()


@pytest_asyncio.fixture
async def override_get_async_session(async_session: AsyncSession):
    """Override database session dependency."""

    async def _override_get_async_session():
        yield async_session

    return _override_get_async_session


@pytest_asyncio.fixture
async def app(override_get_async_session, test_settings: Settings):
    """Create FastAPI test application with PostgreSQL."""
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


# Configuration fixtures and markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "postgres: mark test as PostgreSQL test")
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
    """Set up test environment variables for PostgreSQL."""
    # Store original values to restore later
    original_values = {}

    # Override environment variables for PostgreSQL testing
    test_env_vars = {
        "TESTING": "true",
        "SECRET_KEY": "test-secret-key",
        "DATABASE_URL": TEST_DATABASE_URL,
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_USER": "postgres",
        "DB_PASSWORD": "password",
        "DB_NAME": "iam_dashboard_test",
        "DEBUG": "true",
        "ALLOWED_HOSTS": "[]",  # Empty list to disable TrustedHostMiddleware
        "ALLOWED_ORIGINS": '["http://testserver", "http://test"]',
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
