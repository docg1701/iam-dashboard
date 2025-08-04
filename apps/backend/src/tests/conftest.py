"""
Pytest configuration and fixtures for testing.

This module provides shared fixtures and configuration for all tests.
"""

from collections.abc import Generator
from uuid import uuid4

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
        self.lists: dict[str, list[str]] = {}
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
        if key in self.lists:
            del self.lists[key]
        return True

    def exists(self, key: str) -> bool:
        return key in self.data

    def incr(self, key: str) -> int:
        if key in self.data:
            self.data[key] = str(int(self.data[key]) + 1)
        else:
            self.data[key] = "1"
        return int(self.data[key])

    def lpush(self, key: str, value: str) -> int:
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].insert(0, value)
        return len(self.lists[key])

    def lrange(self, key: str, start: int, end: int) -> list[str]:
        if key not in self.lists:
            return []
        items = self.lists[key]
        if end == -1:
            return items[start:]
        return items[start : end + 1]

    def ltrim(self, key: str, start: int, end: int) -> bool:
        if key in self.lists:
            items = self.lists[key]
            self.lists[key] = items[start : end + 1]
        return True

    def expire(self, _key: str, _time: int) -> bool:
        return True


# Global mock Redis instance
mock_redis_instance = MockRedis()


def mock_redis_from_url(*args: object, **kwargs: object) -> MockRedis:
    """Mock redis.from_url function."""
    return mock_redis_instance


# Apply Redis mocking globally
redis.from_url = mock_redis_from_url

# Now import the app after mocking Redis
from src.core.security import TokenData  # noqa: E402
from src.main import app  # noqa: E402
from src.models.user import UserRole  # noqa: E402


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
def test_session(test_engine: Engine) -> Generator[Session]:
    """Create test database session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="mock_user")
def mock_user() -> TokenData:
    """Create a mock authenticated user for testing."""
    return TokenData(
        user_id=uuid4(),
        email="test@example.com",
        role=UserRole.ADMIN.value,
        session_id="test_session",
        jti="test_jti",
    )


@pytest.fixture(name="auth_headers")
def auth_headers() -> dict[str, str]:
    """Create authentication headers for testing."""
    return {"Authorization": "Bearer mock_token"}


@pytest.fixture(name="mock_redis_client")
def mock_redis_client() -> MockRedis:
    """Provide mock Redis client for testing."""
    return mock_redis_instance


@pytest.fixture(name="client")
def client(test_session: Session, mock_user: TokenData) -> Generator[TestClient]:
    """Create test client with test database and mocked authentication."""
    from src.core import security  # noqa: PLC0415

    def get_test_session() -> Session:
        return test_session

    def get_mock_user() -> TokenData:
        return mock_user

    # Clear any existing overrides
    app.dependency_overrides.clear()

    # Override database session
    app.dependency_overrides[get_session] = get_test_session

    # Override authentication dependencies using dependency overrides
    app.dependency_overrides[security.get_current_user_token] = get_mock_user
    app.dependency_overrides[security.require_authenticated] = get_mock_user
    app.dependency_overrides[security.require_admin_or_above] = get_mock_user

    # For require_any_role, we need to override the actual dependency
    def mock_require_any_role(required_roles: list[str]):
        def dependency() -> TokenData:
            return get_mock_user()

        return dependency

    # Store original function
    original_require_any_role = security.require_any_role
    security.require_any_role = mock_require_any_role

    # Mock auth service for middleware compatibility
    original_verify_token = security.auth_service.verify_token
    security.auth_service.verify_token = lambda _token: mock_user

    client = TestClient(app)
    yield client

    # Restore original functions
    security.require_any_role = original_require_any_role
    security.auth_service.verify_token = original_verify_token
    app.dependency_overrides.clear()
