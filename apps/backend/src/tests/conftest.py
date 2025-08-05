"""
Pytest configuration and fixtures for testing.

This module provides shared fixtures and configuration for all tests.
"""

import os
from collections.abc import Callable, Generator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, StaticPool, create_engine

from src.core.database import get_session

# Set testing environment before any imports
os.environ["ENVIRONMENT"] = "testing"

# Now import the app after mocking Redis
from src.core.security import TokenData  # noqa: E402
from src.main import app  # noqa: E402
from src.models.user import UserRole  # noqa: E402


@pytest.fixture(name="test_engine")
def test_engine() -> Generator[Engine]:
    """Create test database engine with proper cleanup."""
    from sqlalchemy import MetaData

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create a copy of metadata without PostgreSQL-specific constraints
    original_metadata = SQLModel.metadata

    # Import all models to ensure they're registered
    from src.models import audit, client, permissions, user  # noqa: F401

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
    mock.get = AsyncMock(return_value=None)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=0)
    mock.keys = AsyncMock(return_value=[])
    mock.close = AsyncMock()
    return mock


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

    # Note: PermissionService dependency is NOT overridden here
    # Individual tests can override it with their own mock services

    # Override authentication dependencies using dependency overrides
    app.dependency_overrides[security.get_current_user_token] = get_mock_user
    app.dependency_overrides[security.require_authenticated] = get_mock_user
    app.dependency_overrides[security.require_admin_or_above] = get_mock_user

    # Mock get_current_user to return admin user
    from src.core.permissions import get_current_user
    from src.models.user import User

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
        def dependency(user: TokenData) -> TokenData:
            return get_mock_user()

        return dependency

    # Store original function
    original_require_any_role = security.require_any_role
    security.require_any_role = mock_require_any_role

    # Mock permission-based dependencies
    def mock_require_agent_permission(agent_name: str, operation: str) -> Callable:
        def dependency() -> TokenData:
            return get_mock_user()

        return dependency

    original_require_agent_permission = security.require_agent_permission
    security.require_agent_permission = mock_require_agent_permission

    # Mock the core permission check function
    async def mock_check_user_agent_permission(
        user_id, agent_name: str, operation: str, session=None
    ) -> bool:
        # Always return True for tests
        return True

    original_check_user_agent_permission = security.check_user_agent_permission
    security.check_user_agent_permission = mock_check_user_agent_permission

    # Mock auth service for middleware compatibility
    original_verify_token = security.auth_service.verify_token

    def mock_verify_token(token: str, check_session: bool = True) -> TokenData:
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
