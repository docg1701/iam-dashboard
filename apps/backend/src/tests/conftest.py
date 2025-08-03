"""
Pytest configuration and fixtures for testing.

This module provides shared fixtures and configuration for all tests.
"""

from typing import Generator

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, StaticPool, create_engine

from src.core.database import get_session


# Mock Redis before importing main app
class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.expirations: dict[str, float] = {}

    def ping(self) -> bool:
        return True

    def setex(self, key: str, _time: int, value: str) -> bool:
        self.data[key] = value
        return True

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def delete(self, key: str) -> bool:
        if key in self.data:
            del self.data[key]
        return True

    def exists(self, key: str) -> bool:
        return key in self.data
    
    def incr(self, key: str) -> int:
        if key in self.data:
            self.data[key] = str(int(self.data[key]) + 1)
        else:
            self.data[key] = "1"
        return int(self.data[key])


# Global mock Redis instance
mock_redis_instance = MockRedis()


def mock_redis_from_url(*args: object, **kwargs: object) -> MockRedis:
    """Mock redis.from_url function."""
    return mock_redis_instance


# Apply Redis mocking globally
redis.from_url = mock_redis_from_url

# Now import the app after mocking Redis
from src.main import app


@pytest.fixture(name="test_engine")
def test_engine() -> Engine:
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="test_session")
def test_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Create test database session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="client")
def client(test_session: Session) -> Generator[TestClient, None, None]:
    """Create test client with test database."""

    def get_test_session() -> Session:
        return test_session

    app.dependency_overrides[get_session] = get_test_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
