"""
Integration Tests for Permission Middleware.

This module tests the permission checking middleware including
authorization logic, performance requirements, and error handling.
Follows CLAUDE.md directives: Use real PermissionService, never mock business logic.
"""

# External dependency mocking only - no internal business logic mocks
# from unittest.mock import patch  # Currently unused but kept for future external dependency mocks
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from src.core.permissions import (
    PermissionChecker,
    check_admin_or_sysadmin,
    check_sysadmin_only,
    require_permission,
)
from src.models.permissions import AgentName
from src.models.user import User, UserRole
from src.services.permission_service import PermissionService


class TestPermissionChecker:
    """Tests for PermissionChecker class."""

    # NOTE: Integration tests should NOT mock PermissionService according to CLAUDE.md
    # Use real PermissionService with test database session instead

    @pytest.fixture
    def test_user(self) -> User:
        """Create a test user."""
        return User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.USER,
            is_active=True,
            totp_secret_key=None,
            is_2fa_enabled=False,
        )

    @pytest.fixture
    def admin_user(self) -> User:
        """Create an admin user."""
        return User(
            user_id=uuid4(),
            email="admin@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
            is_active=True,
            totp_secret_key=None,
            is_2fa_enabled=False,
        )

    @pytest.fixture
    def sysadmin_user(self) -> User:
        """Create a sysadmin user."""
        return User(
            user_id=uuid4(),
            email="sysadmin@example.com",
            password_hash="hashed_password",
            role=UserRole.SYSADMIN,
            is_active=True,
            totp_secret_key=None,
            is_2fa_enabled=False,
        )

    async def test_permission_checker_success(
        self, test_user: User, test_session: Session
    ) -> None:
        """Test successful permission check using real PermissionService."""
        # Add user to database
        test_session.add(test_user)
        test_session.commit()
        
        # Create real PermissionService
        real_permission_service = PermissionService(session=test_session)
        
        # Create permission for user in database
        from src.tests.factories import create_test_permission
        permission = create_test_permission(
            user_id=test_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"read": True, "create": False, "update": False, "delete": False}
        )
        test_session.add(permission)
        test_session.commit()

        checker = PermissionChecker(AgentName.CLIENT_MANAGEMENT, "read")

        # Use real PermissionService with real database operations
        result = await checker(test_user, real_permission_service)

        assert result == test_user
        
        # Clean up service
        await real_permission_service.close()

    async def test_permission_checker_denied(
        self, test_user: User, test_session: Session
    ) -> None:
        """Test permission denied using real PermissionService."""
        # Add user to database without permissions
        test_session.add(test_user)
        test_session.commit()
        
        # Create real PermissionService
        real_permission_service = PermissionService(session=test_session)

        checker = PermissionChecker(AgentName.CLIENT_MANAGEMENT, "create")

        # User has no permissions in database, should be denied
        with pytest.raises(HTTPException) as exc_info:
            await checker(test_user, real_permission_service)

        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail
        
        # Clean up service
        await real_permission_service.close()

    async def test_permission_checker_service_error(
        self, test_user: User, test_session: Session
    ) -> None:
        """Test permission service error handling using real database connection issues."""
        # Add user to database
        test_session.add(test_user)
        test_session.commit()
        
        # Create real PermissionService
        real_permission_service = PermissionService(session=test_session)

        checker = PermissionChecker(AgentName.CLIENT_MANAGEMENT, "read")

        # Simulate a database connection error by closing the database connection
        # This creates a real external system failure scenario
        try:
            # Close the connection to force a real database error
            test_session.close()
            
            # This should raise an exception due to closed connection
            with pytest.raises(HTTPException) as exc_info:
                await checker(test_user, real_permission_service)

            assert exc_info.value.status_code == 500
            assert "Permission check failed" in exc_info.value.detail
        finally:
            # Clean up service (will handle the closed session gracefully)
            await real_permission_service.close()


class TestRoleCheckers:
    """Tests for role checking functions."""

    @pytest.fixture
    def test_user(self) -> User:
        """Create a regular user."""
        return User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.USER,
            is_active=True,
            totp_secret_key=None,
            is_2fa_enabled=False,
        )

    @pytest.fixture
    def admin_user(self) -> User:
        """Create an admin user."""
        return User(
            user_id=uuid4(),
            email="admin@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
            is_active=True,
            totp_secret_key=None,
            is_2fa_enabled=False,
        )

    @pytest.fixture
    def sysadmin_user(self) -> User:
        """Create a sysadmin user."""
        return User(
            user_id=uuid4(),
            email="sysadmin@example.com",
            password_hash="hashed_password",
            role=UserRole.SYSADMIN,
            is_active=True,
            totp_secret_key=None,
            is_2fa_enabled=False,
        )

    async def test_check_admin_or_sysadmin_with_admin(self, admin_user: User) -> None:
        """Test admin role check."""
        result = await check_admin_or_sysadmin(admin_user)
        assert result is True

    async def test_check_admin_or_sysadmin_with_sysadmin(self, sysadmin_user: User) -> None:
        """Test sysadmin role check."""
        result = await check_admin_or_sysadmin(sysadmin_user)
        assert result is True

    async def test_check_admin_or_sysadmin_with_user(self, test_user: User) -> None:
        """Test regular user role check."""
        result = await check_admin_or_sysadmin(test_user)
        assert result is False

    async def test_check_sysadmin_only_with_sysadmin(self, sysadmin_user: User) -> None:
        """Test sysadmin-only check with sysadmin."""
        result = await check_sysadmin_only(sysadmin_user)
        assert result is True

    async def test_check_sysadmin_only_with_admin(self, admin_user: User) -> None:
        """Test sysadmin-only check with admin."""
        result = await check_sysadmin_only(admin_user)
        assert result is False

    async def test_check_sysadmin_only_with_user(self, test_user: User) -> None:
        """Test sysadmin-only check with regular user."""
        result = await check_sysadmin_only(test_user)
        assert result is False


class TestPermissionDecorators:
    """Tests for permission decorators and dependencies."""

    def test_require_permission_returns_depends(self) -> None:
        """Test that require_permission returns a FastAPI Depends."""
        result = require_permission(AgentName.CLIENT_MANAGEMENT, "read")
        # The result should be a Depends object
        assert hasattr(result, "dependency")
        assert isinstance(result.dependency, PermissionChecker)
        assert result.dependency.agent_name == AgentName.CLIENT_MANAGEMENT
        assert result.dependency.operation == "read"
