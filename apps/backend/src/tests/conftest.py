"""
Pytest configuration and fixtures for testing.

This module provides shared fixtures and configuration for all tests.
"""

import os
from collections.abc import Callable, Generator
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, MetaData
from sqlmodel import Session, SQLModel, StaticPool, create_engine

from src.core.database import get_session

# Set testing environment before any imports
os.environ["ENVIRONMENT"] = "testing"

# Now import the app after mocking Redis
from src.core import security  # noqa: E402
from src.core.security import TokenData, auth_service, get_current_user  # noqa: E402
from src.main import app  # noqa: E402
from src.models import audit, permissions  # noqa: F401, E402
from src.models import client as client_models  # noqa: F401, E402
from src.models import user as user_models  # noqa: F401, E402
from src.models.user import User, UserRole  # noqa: E402


@pytest.fixture(name="test_engine")
def test_engine() -> Generator[Engine]:
    """Create test database engine with proper cleanup."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create a copy of metadata without PostgreSQL-specific constraints
    original_metadata = SQLModel.metadata

    # Create new metadata and copy tables without problematic constraints
    test_metadata = MetaData()

    for table_name, table in original_metadata.tables.items():
        # Skip the problematic constraint for permission tables
        if table_name == "user_agent_permissions":
            # Create table with filtered constraints
            new_table = table.tometadata(test_metadata)
            # Remove PostgreSQL-specific constraints
            new_table.constraints = {
                constraint
                for constraint in new_table.constraints
                if not (
                    hasattr(constraint, "name") and constraint.name == "permissions_jsonb_structure"
                )
            }
        else:
            # Copy other tables as-is
            table.tometadata(test_metadata)

    # Create tables with the filtered metadata
    test_metadata.create_all(engine)

    yield engine

    # Ensure proper cleanup of engine connections
    engine.dispose()


@pytest.fixture(name="test_session")
def test_session(test_engine: Engine) -> Generator[Session]:
    """Create test database session with proper transaction isolation."""
    with Session(test_engine) as session:
        # Start a transaction for proper test isolation
        transaction = session.begin()
        try:
            yield session
        finally:
            # Only rollback if transaction is still active
            if transaction.is_active:
                transaction.rollback()
            # Session will be automatically closed by context manager


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


@pytest.fixture(name="authenticated_sysadmin_token_data")
def authenticated_sysadmin_token_data() -> TokenData:
    """Create a mock sysadmin token for testing."""
    return TokenData(
        user_id=uuid4(),
        email="sysadmin@example.com",
        role=UserRole.SYSADMIN.value,
        session_id="sysadmin_session",
        jti="sysadmin_jti",
    )


@pytest.fixture(name="authenticated_admin_token_data")
def authenticated_admin_token_data() -> TokenData:
    """Create a mock admin token for testing."""
    return TokenData(
        user_id=uuid4(),
        email="admin@example.com",
        role=UserRole.ADMIN.value,
        session_id="admin_session",
        jti="admin_jti",
    )


@pytest.fixture(name="authenticated_user_token_data")
def authenticated_user_token_data() -> TokenData:
    """Create a mock user token for testing."""
    return TokenData(
        user_id=uuid4(),
        email="user@example.com",
        role=UserRole.USER.value,
        session_id="user_session",
        jti="user_jti",
    )


@pytest.fixture(name="authenticated_sysadmin_headers")
def authenticated_sysadmin_headers(sysadmin_auth_token: str) -> dict[str, str]:
    """Create sysadmin authentication headers with real JWT token."""
    return {"Authorization": f"Bearer {sysadmin_auth_token}"}


@pytest.fixture(name="authenticated_admin_headers")
def authenticated_admin_headers(admin_auth_token: str) -> dict[str, str]:
    """Create admin authentication headers with real JWT token."""
    return {"Authorization": f"Bearer {admin_auth_token}"}


@pytest.fixture(name="auth_headers")
def auth_headers(admin_auth_token: str) -> dict[str, str]:
    """Create authentication headers with real JWT token."""
    return {"Authorization": f"Bearer {admin_auth_token}"}


@pytest.fixture(name="user_auth_headers")
def user_auth_headers(user_auth_token: str) -> dict[str, str]:
    """Create regular user authentication headers with real JWT token."""
    return {"Authorization": f"Bearer {user_auth_token}"}


@pytest.fixture(name="mock_redis_client")
def mock_redis_client() -> MagicMock:
    """Provide mock Redis client for testing."""
    mock = MagicMock()
    # Add data and lists attributes for password security tests
    mock.data = {}
    mock.lists = {}

    # Mock synchronous methods (for password security service)
    def mock_get_sync(key: str) -> str | None:
        return mock.data.get(key)

    def mock_setex_sync(key: str, timeout: int | timedelta, value: str) -> bool:
        mock.data[key] = value
        return True

    def mock_delete_sync(key: str) -> int:
        if key in mock.data:
            del mock.data[key]
            return 1
        if key in mock.lists:
            del mock.lists[key]
            return 1
        return 0

    def mock_lpush_sync(key: str, *values: str) -> int:
        if key not in mock.lists:
            mock.lists[key] = []
        for value in reversed(values):
            mock.lists[key].insert(0, value)
        return len(mock.lists[key])

    def mock_ltrim_sync(key: str, start: int, stop: int) -> bool:
        if key in mock.lists:
            mock.lists[key] = mock.lists[key][start:stop+1]
        return True

    def mock_lrange_sync(key: str, start: int, stop: int) -> list[str]:
        if key not in mock.lists:
            return []
        if stop == -1:
            return mock.lists[key][start:]
        return mock.lists[key][start:stop+1]

    def mock_llen_sync(key: str) -> int:
        return len(mock.lists.get(key, []))

    def mock_expire_sync(key: str, timeout: int | timedelta) -> bool:
        # Mock expire - don't actually implement expiration logic for tests
        return True

    def mock_exists_sync(key: str) -> bool:
        return key in mock.data

    # Mock async methods (for other services)
    async def mock_get_async(key: str) -> str | None:
        return mock.data.get(key)

    async def mock_setex_async(key: str, timeout: int, value: str) -> bool:
        mock.data[key] = value
        return True

    async def mock_delete_async(key: str) -> int:
        return mock_delete_sync(key)

    # Set both sync and async methods
    mock.get = mock_get_sync
    mock.setex = mock_setex_sync
    mock.delete = mock_delete_sync
    mock.lpush = mock_lpush_sync
    mock.ltrim = mock_ltrim_sync
    mock.lrange = mock_lrange_sync
    mock.llen = mock_llen_sync
    mock.expire = mock_expire_sync
    mock.exists = mock_exists_sync

    # Also set async versions for other tests
    mock.aget = mock_get_async
    mock.asetex = mock_setex_async
    mock.adelete = mock_delete_async
    mock.keys = AsyncMock(return_value=[])
    mock.close = AsyncMock()
    return mock


@pytest.fixture(name="test_user")
def test_user(test_session: Session) -> User:
    """Create a test user in the database for authentication tests."""
    user = User(
        user_id=uuid4(),
        email="test@example.com",
        role=UserRole.ADMIN,
        is_active=True,
        password_hash=auth_service.get_password_hash("password123"),
        full_name="Test Admin User",
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture(name="test_sysadmin")
def test_sysadmin(test_session: Session) -> User:
    """Create a test sysadmin user in the database."""
    user = User(
        user_id=uuid4(),
        email="sysadmin@example.com",
        role=UserRole.SYSADMIN,
        is_active=True,
        password_hash=auth_service.get_password_hash("password123"),
        full_name="Test Sysadmin User",
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture(name="test_regular_user")
def test_regular_user(test_session: Session) -> User:
    """Create a test regular user in the database."""
    user = User(
        user_id=uuid4(),
        email="user@example.com",
        role=UserRole.USER,
        is_active=True,
        password_hash=auth_service.get_password_hash("password123"),
        full_name="Test Regular User",
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture(name="admin_auth_token")
def admin_auth_token(test_user: User) -> str:
    """Create a real JWT token for admin user authentication."""
    token_response = auth_service.create_access_token(
        user_id=test_user.user_id,
        user_role=test_user.role.value,
        user_email=test_user.email,
    )
    return token_response.access_token


@pytest.fixture(name="sysadmin_auth_token")
def sysadmin_auth_token(test_sysadmin: User) -> str:
    """Create a real JWT token for sysadmin user authentication."""
    token_response = auth_service.create_access_token(
        user_id=test_sysadmin.user_id,
        user_role=test_sysadmin.role.value,
        user_email=test_sysadmin.email,
    )
    return token_response.access_token


@pytest.fixture(name="user_auth_token")
def user_auth_token(test_regular_user: User) -> str:
    """Create a real JWT token for regular user authentication."""
    token_response = auth_service.create_access_token(
        user_id=test_regular_user.user_id,
        user_role=test_regular_user.role.value,
        user_email=test_regular_user.email,
    )
    return token_response.access_token


@pytest.fixture(name="client")
def client(test_session: Session) -> Generator[TestClient]:
    """Create test client with test database session only."""
    def get_test_session() -> Session:
        return test_session

    # Clear any existing overrides
    app.dependency_overrides.clear()

    # Override database session ONLY - no business logic overrides
    app.dependency_overrides[get_session] = get_test_session

    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(name="mock_audit_logger")
def mock_audit_logger() -> MagicMock:
    """Mock audit logger to avoid external logging system calls."""
    mock_logger = MagicMock()
    mock_logger.log_permission_change = AsyncMock()
    mock_logger.log_user_action = AsyncMock()
    mock_logger.log_admin_action = AsyncMock()
    return mock_logger


@pytest.fixture(name="mock_email_service") 
def mock_email_service() -> MagicMock:
    """Mock email service to avoid external SMTP calls."""
    mock_service = MagicMock()
    mock_service.send_welcome_email = AsyncMock(return_value=True)
    mock_service.send_password_reset = AsyncMock(return_value=True)
    mock_service.send_notification = AsyncMock(return_value=True)
    return mock_service


@pytest.fixture(name="mock_time") 
def mock_time() -> MagicMock:
    """Mock time functions for deterministic testing."""
    mock = MagicMock()
    # Set a fixed datetime for testing
    fixed_datetime = datetime(2024, 1, 1, 12, 0, 0)
    mock.datetime.now.return_value = fixed_datetime
    mock.datetime.utcnow.return_value = fixed_datetime
    return mock


@pytest.fixture(name="mock_uuid")
def mock_uuid() -> MagicMock:
    """Mock UUID generation for deterministic testing."""
    mock = MagicMock()
    # Return predictable UUIDs for testing
    test_uuid = UUID('12345678-1234-5678-9abc-123456789abc')
    mock.uuid4.return_value = test_uuid
    return mock


