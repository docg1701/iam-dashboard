"""
Tests for Permission Middleware.

This module tests the permission checking middleware including
authorization logic, performance requirements, and error handling.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

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

    @pytest.fixture
    def mock_permission_service(self) -> MagicMock:
        """Create a mock permission service."""
        service = MagicMock(spec=PermissionService)
        service.check_user_permission = AsyncMock()
        service.close = AsyncMock()
        return service

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
        self, test_user: User, mock_permission_service: MagicMock
    ) -> None:
        """Test successful permission check."""
        mock_permission_service.check_user_permission.return_value = True

        checker = PermissionChecker(AgentName.CLIENT_MANAGEMENT, "read")

        with patch("src.core.permissions.PermissionService", return_value=mock_permission_service):
            result = await checker(test_user, mock_permission_service)

        assert result == test_user
        mock_permission_service.check_user_permission.assert_called_once_with(
            test_user.user_id, AgentName.CLIENT_MANAGEMENT, "read"
        )
        mock_permission_service.close.assert_called_once()

    async def test_permission_checker_denied(
        self, test_user: User, mock_permission_service: MagicMock
    ) -> None:
        """Test permission denied."""
        mock_permission_service.check_user_permission.return_value = False

        checker = PermissionChecker(AgentName.CLIENT_MANAGEMENT, "create")

        with patch("src.core.permissions.PermissionService", return_value=mock_permission_service):
            with pytest.raises(HTTPException) as exc_info:
                await checker(test_user, mock_permission_service)

        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail
        mock_permission_service.close.assert_called_once()

    async def test_permission_checker_service_error(
        self, test_user: User, mock_permission_service: MagicMock
    ) -> None:
        """Test permission service error handling."""
        mock_permission_service.check_user_permission.side_effect = Exception("Service error")

        checker = PermissionChecker(AgentName.CLIENT_MANAGEMENT, "read")

        with patch("src.core.permissions.PermissionService", return_value=mock_permission_service):
            with pytest.raises(HTTPException) as exc_info:
                await checker(test_user, mock_permission_service)

        assert exc_info.value.status_code == 500
        assert "Permission check failed" in exc_info.value.detail
        mock_permission_service.close.assert_called_once()


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
