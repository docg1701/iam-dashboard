"""
Pytest configuration and fixtures for backend testing.
"""
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from src.main import create_app
from src.core.database import get_async_session
from src.core.config import get_settings


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
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Create session
    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
def override_get_async_session(async_session: AsyncSession):
    """Override database session dependency."""
    async def _override_get_async_session():
        yield async_session
    
    return _override_get_async_session


@pytest.fixture
def app(override_get_async_session):
    """Create FastAPI test application."""
    app = create_app()
    app.dependency_overrides[get_async_session] = override_get_async_session
    return app


@pytest.fixture
def client(app) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
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
@pytest.fixture
def test_settings():
    """Override application settings for tests."""
    settings = get_settings()
    settings.DEBUG = True
    settings.SECRET_KEY = "test-secret-key"
    settings.DATABASE_URL = TEST_DATABASE_URL
    return settings


# Markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "external: mark test as requiring external services")


# Test environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["TESTING"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    # Cleanup is handled by pytest automatically