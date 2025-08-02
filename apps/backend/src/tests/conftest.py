"""
Pytest configuration and fixtures for testing.

This module provides shared fixtures and configuration for all tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.core.database import get_session


# Mock Redis before importing main app
class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self):
        self.data = {}
        self.expirations = {}

    def ping(self):
        return True

    def setex(self, key, time, value):
        self.data[key] = value
        return True

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        if key in self.data:
            del self.data[key]
        return True

    def exists(self, key):
        return key in self.data


# Global mock Redis instance
mock_redis_instance = MockRedis()


def mock_redis_from_url(*args, **kwargs):
    """Mock redis.from_url function."""
    return mock_redis_instance


# Apply Redis mocking globally
import redis

redis.from_url = mock_redis_from_url

# Now import the app after mocking Redis
from src.main import app


@pytest.fixture(name="test_engine")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="test_session")
def test_session(test_engine):
    """Create test database session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="client")
def client(test_session: Session):
    """Create test client with test database."""

    def get_test_session():
        return test_session

    app.dependency_overrides[get_session] = get_test_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
