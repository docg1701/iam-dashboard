"""
Pytest configuration and fixtures for testing.

This module provides shared fixtures and configuration for all tests.
"""

import os
from collections.abc import Callable, Generator
from datetime import timedelta
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
from src.core.security import TokenData, get_current_user  # noqa: E402
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
def authenticated_sysadmin_headers() -> dict[str, str]:
    """Create sysadmin authentication headers for testing."""
    return {"Authorization": "Bearer sysadmin_mock_token"}


@pytest.fixture(name="authenticated_admin_headers")
def authenticated_admin_headers() -> dict[str, str]:
    """Create admin authentication headers for testing."""
    return {"Authorization": "Bearer admin_mock_token"}


@pytest.fixture(name="auth_headers")
def auth_headers() -> dict[str, str]:
    """Create authentication headers for testing."""
    return {"Authorization": "Bearer mock_token"}


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


@pytest.fixture(name="client")
def client(test_session: Session, mock_user: TokenData) -> Generator[TestClient]:
    """Create test client with test database and mocked authentication."""
    def get_test_session() -> Session:
        return test_session

    def get_mock_user(credentials: Any = None) -> TokenData:
        # If credentials are provided, extract token and return appropriate user
        if credentials and hasattr(credentials, "credentials"):
            token = credentials.credentials
            if token == "sysadmin_mock_token":
                return TokenData(
                    user_id=uuid4(),
                    email="sysadmin@example.com",
                    role=UserRole.SYSADMIN.value,
                    session_id="sysadmin_session",
                    jti="sysadmin_jti",
                )
            elif token == "admin_mock_token":
                return TokenData(
                    user_id=uuid4(),
                    email="admin@example.com",
                    role=UserRole.ADMIN.value,
                    session_id="admin_session",
                    jti="admin_jti",
                )
        return mock_user

    # Clear any existing overrides
    app.dependency_overrides.clear()

    # Override database session
    app.dependency_overrides[get_session] = get_test_session

    # Note: PermissionService dependency is NOT overridden here
    # Individual tests can override it with their own mock services

    # Override authentication dependencies using dependency overrides
    app.dependency_overrides[security.get_current_user_token] = get_mock_user
    app.dependency_overrides[security.require_authenticated] = get_mock_user
    app.dependency_overrides[security.require_admin_or_above] = get_mock_user

    # Mock get_current_user to return admin user
    def mock_current_user() -> User:
        """Mock current user as admin for tests."""
        return User(
            user_id=mock_user.user_id,
            email=f"{mock_user.user_id}@example.com",
            role=UserRole.ADMIN,
            is_active=True,
            password_hash="mock_hash",
            full_name="Test Admin User",
        )

    app.dependency_overrides[get_current_user] = mock_current_user

    # For require_any_role, we need to override the actual dependency
    def mock_require_any_role(required_roles: list[str]) -> Callable[[TokenData], TokenData]:
        def dependency(token_data: TokenData) -> TokenData:
            return get_mock_user()

        return dependency

    # Store original function
    original_require_any_role = security.require_any_role
    security.require_any_role = mock_require_any_role

    # Mock permission-based dependencies
    def mock_require_agent_permission(agent_name: str, operation: str) -> Callable[[], TokenData]:
        def dependency() -> TokenData:
            return get_mock_user()

        return dependency

    original_require_agent_permission = security.require_agent_permission
    security.require_agent_permission = mock_require_agent_permission

    # Mock the core permission check function
    async def mock_check_user_agent_permission(
        user_id: UUID, agent_name: str, operation: str, session: Any = None
    ) -> bool:
        # Always return True for tests
        return True

    original_check_user_agent_permission = security.check_user_agent_permission
    security.check_user_agent_permission = mock_check_user_agent_permission

    # Mock auth service for middleware compatibility
    original_verify_token = security.auth_service.verify_token

    def mock_verify_token(token: str, check_session: bool = True) -> TokenData:
        # Handle different mock tokens for different user types
        if token == "sysadmin_mock_token":
            return TokenData(
                user_id=uuid4(),
                email="sysadmin@example.com",
                role=UserRole.SYSADMIN.value,
                session_id="sysadmin_session",
                jti="sysadmin_jti",
            )
        elif token == "admin_mock_token":
            return TokenData(
                user_id=uuid4(),
                email="admin@example.com",
                role=UserRole.ADMIN.value,
                session_id="admin_session",
                jti="admin_jti",
            )
        else:
            return mock_user

    security.auth_service.verify_token = mock_verify_token  # type: ignore[method-assign]

    client = TestClient(app)
    yield client

    # Restore original functions
    security.require_any_role = original_require_any_role
    security.require_agent_permission = original_require_agent_permission
    security.check_user_agent_permission = original_check_user_agent_permission
    security.auth_service.verify_token = original_verify_token  # type: ignore[method-assign]
    app.dependency_overrides.clear()


@pytest.fixture(name="mock_permission_service")
def mock_permission_service() -> MagicMock:
    """Create a mock PermissionService for testing."""
    mock_service = MagicMock()
    mock_service.check_user_permission = AsyncMock(return_value=True)
    mock_service.assign_permission = AsyncMock(return_value=True)
    mock_service.revoke_permission = AsyncMock(return_value=True)
    mock_service.get_user_permissions = AsyncMock(return_value={"create": True, "read": True, "update": True, "delete": True})
    mock_service.bulk_assign_permissions = AsyncMock(return_value={"successful": [], "failed": []})
    mock_service.apply_template = AsyncMock(return_value=True)
    mock_service.list_templates = AsyncMock(return_value=([], 0))
    mock_service.create_template = AsyncMock()
    mock_service.update_template = AsyncMock()
    mock_service.delete_template = AsyncMock(return_value=True)
    mock_service.get_audit_log = AsyncMock(return_value=([], 0))
    mock_service.get_permission_stats = AsyncMock(return_value={"total_permissions": 0, "active_permissions": 0})
    mock_service.close = AsyncMock()
    return mock_service
