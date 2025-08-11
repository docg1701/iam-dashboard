"""
Pytest configuration for model tests.

Provides fixtures and configuration for testing SQLModel classes.
"""
import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

# Set environment variables for testing
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"
os.environ["DB_PASSWORD"] = "test-password"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for fast testing
    # Note: This is for unit tests only, integration tests should use PostgreSQL
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,  # Set to True for SQL debugging
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Start a transaction that we'll rollback at the end
        transaction = await session.begin()
        
        try:
            yield session
        finally:
            # Rollback the transaction to clean up
            await transaction.rollback()
            await session.close()


@pytest.fixture(autouse=True)
def override_get_session(test_session: AsyncSession) -> None:
    """Override the database session for tests."""
    # This would be used in integration tests where we need actual database calls
    # For unit tests, we primarily test model behavior and validation
    pass


# Pytest marks for test organization
pytest_markers = [
    "unit: marks tests as unit tests (fast, no database)",
    "integration: marks tests as integration tests (slower, with database)",
    "model: marks tests as model-specific tests",
    "validation: marks tests for model validation",
    "factory: marks tests for factory classes",
]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    for marker in pytest_markers:
        config.addinivalue_line("markers", marker)