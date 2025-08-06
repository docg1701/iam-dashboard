"""
Comprehensive tests for core.permissions module to achieve 80%+ coverage.

This module tests all functions, decorators, and middleware in the core.permissions module.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, Request

from src.core.exceptions import AuthorizationError
from src.core.permissions import (
    PermissionMiddleware,
    check_admin_or_sysadmin,
    check_sysadmin_only,
    check_user_permission_sync,
    permission_required,
    require_admin_or_sysadmin,
    require_audio_recording_create,
    require_audio_recording_delete,
    require_audio_recording_read,
    require_audio_recording_update,
    require_client_management_create,
    require_client_management_delete,
    require_client_management_read,
    require_client_management_update,
    require_pdf_processing_create,
    require_pdf_processing_delete,
    require_pdf_processing_read,
    require_pdf_processing_update,
    require_permission,
    require_reports_analysis_create,
    require_reports_analysis_delete,
    require_reports_analysis_read,
    require_reports_analysis_update,
    require_sysadmin_only,
)
from src.models.permissions import AgentName
from src.models.user import User, UserRole


class TestRequirePermissionFunctions:
    """Test all require_* permission functions."""

    def test_require_client_management_create(self) -> None:
        """Test require_client_management_create function."""
        dependency = require_client_management_create()
        assert dependency is not None

    def test_require_client_management_read(self) -> None:
        """Test require_client_management_read function."""
        dependency = require_client_management_read()
        assert dependency is not None

    def test_require_client_management_update(self) -> None:
        """Test require_client_management_update function."""
        dependency = require_client_management_update()
        assert dependency is not None

    def test_require_client_management_delete(self) -> None:
        """Test require_client_management_delete function."""
        dependency = require_client_management_delete()
        assert dependency is not None

    def test_require_pdf_processing_create(self) -> None:
        """Test require_pdf_processing_create function."""
        dependency = require_pdf_processing_create()
        assert dependency is not None

    def test_require_pdf_processing_read(self) -> None:
        """Test require_pdf_processing_read function."""
        dependency = require_pdf_processing_read()
        assert dependency is not None

    def test_require_pdf_processing_update(self) -> None:
        """Test require_pdf_processing_update function."""
        dependency = require_pdf_processing_update()
        assert dependency is not None

    def test_require_pdf_processing_delete(self) -> None:
        """Test require_pdf_processing_delete function."""
        dependency = require_pdf_processing_delete()
        assert dependency is not None

    def test_require_reports_analysis_create(self) -> None:
        """Test require_reports_analysis_create function."""
        dependency = require_reports_analysis_create()
        assert dependency is not None

    def test_require_reports_analysis_read(self) -> None:
        """Test require_reports_analysis_read function."""
        dependency = require_reports_analysis_read()
        assert dependency is not None

    def test_require_reports_analysis_update(self) -> None:
        """Test require_reports_analysis_update function."""
        dependency = require_reports_analysis_update()
        assert dependency is not None

    def test_require_reports_analysis_delete(self) -> None:
        """Test require_reports_analysis_delete function."""
        dependency = require_reports_analysis_delete()
        assert dependency is not None

    def test_require_audio_recording_create(self) -> None:
        """Test require_audio_recording_create function."""
        dependency = require_audio_recording_create()
        assert dependency is not None

    def test_require_audio_recording_read(self) -> None:
        """Test require_audio_recording_read function."""
        dependency = require_audio_recording_read()
        assert dependency is not None

    def test_require_audio_recording_update(self) -> None:
        """Test require_audio_recording_update function."""
        dependency = require_audio_recording_update()
        assert dependency is not None

    def test_require_audio_recording_delete(self) -> None:
        """Test require_audio_recording_delete function."""
        dependency = require_audio_recording_delete()
        assert dependency is not None


class TestPermissionMiddleware:
    """Test PermissionMiddleware class."""

    def test_init(self) -> None:
        """Test PermissionMiddleware initialization."""
        app = MagicMock()
        middleware = PermissionMiddleware(app)
        assert middleware.app == app

    async def test_call_success(self) -> None:
        """Test PermissionMiddleware call method success."""
        app = MagicMock()
        middleware = PermissionMiddleware(app)

        request = MagicMock(spec=Request)
        request.state = MagicMock()

        call_next = AsyncMock(return_value="response")

        with patch("src.core.permissions.PermissionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service

            result = await middleware(request, call_next)

            assert result == "response"
            call_next.assert_called_once_with(request)
            assert hasattr(request.state, "permission_service")
            mock_service.close.assert_called_once()

    async def test_call_exception_cleanup(self) -> None:
        """Test PermissionMiddleware handles exceptions and cleans up."""
        app = MagicMock()
        middleware = PermissionMiddleware(app)

        request = MagicMock(spec=Request)
        request.state = MagicMock()

        call_next = AsyncMock(side_effect=Exception("Test error"))

        with patch("src.core.permissions.PermissionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service

            with pytest.raises(Exception, match="Test error"):
                await middleware(request, call_next)

            # Service should still be closed even with exception
            mock_service.close.assert_called_once()


class TestCheckUserPermissionSync:
    """Test check_user_permission_sync function."""

    def test_sync_permission_check_no_loop(self) -> None:
        """Test sync permission check when no event loop exists."""
        user_id = uuid4()

        with patch("src.core.permissions.PermissionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.check_user_permission = AsyncMock(return_value=True)
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service

            with patch("asyncio.get_event_loop", side_effect=RuntimeError("No loop")), \
                 patch("asyncio.run") as mock_run:
                    mock_run.return_value = True

                    checker = check_user_permission_sync(user_id, AgentName.CLIENT_MANAGEMENT, "read")
                    result = checker()

                    assert result is True
                    mock_run.assert_called_once()

    def test_sync_permission_check_with_running_loop(self) -> None:
        """Test sync permission check when event loop is running."""
        user_id = uuid4()

        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True

        with patch("asyncio.get_event_loop", return_value=mock_loop):
            checker = check_user_permission_sync(user_id, AgentName.CLIENT_MANAGEMENT, "read")
            result = checker()

            # Should return False when called from async context
            assert result is False

    def test_sync_permission_check_with_stopped_loop(self) -> None:
        """Test sync permission check when event loop is stopped."""
        user_id = uuid4()

        mock_loop = MagicMock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.return_value = True

        with patch("asyncio.get_event_loop", return_value=mock_loop):
            checker = check_user_permission_sync(user_id, AgentName.CLIENT_MANAGEMENT, "read")
            result = checker()

            assert result is True
            mock_loop.run_until_complete.assert_called_once()


class TestPermissionRequiredDecorator:
    """Test permission_required decorator."""

    async def test_decorator_with_user_id_kwarg(self) -> None:
        """Test decorator with user_id as keyword argument."""
        user_id = uuid4()

        @permission_required(AgentName.CLIENT_MANAGEMENT, "create")
        async def test_function(user_id: UUID, data: str) -> str:
            return f"Success: {data}"

        with patch("src.core.permissions.PermissionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.check_user_permission = AsyncMock(return_value=True)
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service

            result = await test_function(user_id=user_id, data="test")

            assert result == "Success: test"
            mock_service.check_user_permission.assert_called_once_with(
                user_id, AgentName.CLIENT_MANAGEMENT, "create"
            )

    async def test_decorator_with_user_object_kwarg(self) -> None:
        """Test decorator with user object as keyword argument."""
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="hash",
            role=UserRole.USER,
            is_active=True
        )

        @permission_required(AgentName.CLIENT_MANAGEMENT, "read")
        async def test_function(user: User, data: str) -> str:
            return f"Success: {data}"

        with patch("src.core.permissions.PermissionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.check_user_permission = AsyncMock(return_value=True)
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service

            result = await test_function(user=user, data="test")

            assert result == "Success: test"
            mock_service.check_user_permission.assert_called_once_with(
                user.user_id, AgentName.CLIENT_MANAGEMENT, "read"
            )

    async def test_decorator_with_user_id_positional_arg(self) -> None:
        """Test decorator with user_id as positional argument."""
        user_id = uuid4()

        @permission_required(AgentName.CLIENT_MANAGEMENT, "update")
        async def test_function(user_id: UUID, data: str) -> str:
            return f"Success: {data}"

        with patch("src.core.permissions.PermissionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.check_user_permission = AsyncMock(return_value=True)
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service

            result = await test_function(user_id, "test")

            assert result == "Success: test"
            mock_service.check_user_permission.assert_called_once_with(
                user_id, AgentName.CLIENT_MANAGEMENT, "update"
            )

    async def test_decorator_with_user_object_positional_arg(self) -> None:
        """Test decorator with user object as positional argument."""
        user = User(
            user_id=uuid4(),
            email="test@example.com",
            password_hash="hash",
            role=UserRole.USER,
            is_active=True
        )

        @permission_required(AgentName.CLIENT_MANAGEMENT, "delete")
        async def test_function(user: User, data: str) -> str:
            return f"Success: {data}"

        with patch("src.core.permissions.PermissionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.check_user_permission = AsyncMock(return_value=True)
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service

            result = await test_function(user, "test")

            assert result == "Success: test"
            mock_service.check_user_permission.assert_called_once_with(
                user.user_id, AgentName.CLIENT_MANAGEMENT, "delete"
            )

    async def test_decorator_no_user_id_raises_error(self) -> None:
        """Test decorator raises ValueError when user_id cannot be extracted."""
        @permission_required(AgentName.CLIENT_MANAGEMENT, "create")
        async def test_function(data: str) -> str:
            return f"Success: {data}"

        with pytest.raises(ValueError, match="Could not extract user_id"):
            await test_function("test")

    async def test_decorator_permission_denied(self) -> None:
        """Test decorator raises AuthorizationError when permission denied."""
        user_id = uuid4()

        @permission_required(AgentName.CLIENT_MANAGEMENT, "create")
        async def test_function(user_id: UUID, data: str) -> str:
            return f"Success: {data}"

        with patch("src.core.permissions.PermissionService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.check_user_permission = AsyncMock(return_value=False)
            mock_service.close = AsyncMock()
            mock_service_class.return_value = mock_service

            with pytest.raises(AuthorizationError, match="does not have create permission"):
                await test_function(user_id=user_id, data="test")

            mock_service.close.assert_called_once()


class TestRoleCheckFunctions:
    """Test role checking utility functions."""

    async def test_check_admin_or_sysadmin_with_admin(self) -> None:
        """Test check_admin_or_sysadmin with admin user."""
        user = User(
            user_id=uuid4(),
            email="admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True
        )

        result = await check_admin_or_sysadmin(user)
        assert result is True

    async def test_check_admin_or_sysadmin_with_sysadmin(self) -> None:
        """Test check_admin_or_sysadmin with sysadmin user."""
        user = User(
            user_id=uuid4(),
            email="sysadmin@example.com",
            password_hash="hash",
            role=UserRole.SYSADMIN,
            is_active=True
        )

        result = await check_admin_or_sysadmin(user)
        assert result is True

    async def test_check_admin_or_sysadmin_with_user(self) -> None:
        """Test check_admin_or_sysadmin with regular user."""
        user = User(
            user_id=uuid4(),
            email="user@example.com",
            password_hash="hash",
            role=UserRole.USER,
            is_active=True
        )

        result = await check_admin_or_sysadmin(user)
        assert result is False

    async def test_check_sysadmin_only_with_sysadmin(self) -> None:
        """Test check_sysadmin_only with sysadmin user."""
        user = User(
            user_id=uuid4(),
            email="sysadmin@example.com",
            password_hash="hash",
            role=UserRole.SYSADMIN,
            is_active=True
        )

        result = await check_sysadmin_only(user)
        assert result is True

    async def test_check_sysadmin_only_with_admin(self) -> None:
        """Test check_sysadmin_only with admin user."""
        user = User(
            user_id=uuid4(),
            email="admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True
        )

        result = await check_sysadmin_only(user)
        assert result is False

    async def test_check_sysadmin_only_with_user(self) -> None:
        """Test check_sysadmin_only with regular user."""
        user = User(
            user_id=uuid4(),
            email="user@example.com",
            password_hash="hash",
            role=UserRole.USER,
            is_active=True
        )

        result = await check_sysadmin_only(user)
        assert result is False


class TestRoleDependencies:
    """Test role-based FastAPI dependencies."""

    def test_require_admin_or_sysadmin_dependency(self) -> None:
        """Test require_admin_or_sysadmin returns a dependency."""
        dependency = require_admin_or_sysadmin()
        assert dependency is not None

    def test_require_sysadmin_only_dependency(self) -> None:
        """Test require_sysadmin_only returns a dependency."""
        dependency = require_sysadmin_only()
        assert dependency is not None

    async def test_require_admin_or_sysadmin_success(self) -> None:
        """Test require_admin_or_sysadmin dependency with valid user."""
        admin_user = User(
            user_id=uuid4(),
            email="admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True
        )

        dependency = require_admin_or_sysadmin()
        # Get the actual dependency function
        dep_func = dependency.dependency

        result = await dep_func(current_user=admin_user)
        assert result == admin_user

    async def test_require_admin_or_sysadmin_failure(self) -> None:
        """Test require_admin_or_sysadmin dependency with invalid user."""
        regular_user = User(
            user_id=uuid4(),
            email="user@example.com",
            password_hash="hash",
            role=UserRole.USER,
            is_active=True
        )

        dependency = require_admin_or_sysadmin()
        dep_func = dependency.dependency

        with pytest.raises(HTTPException) as exc_info:
            await dep_func(current_user=regular_user)

        assert exc_info.value.status_code == 403
        assert "Admin or sysadmin role required" in exc_info.value.detail

    async def test_require_sysadmin_only_success(self) -> None:
        """Test require_sysadmin_only dependency with valid user."""
        sysadmin_user = User(
            user_id=uuid4(),
            email="sysadmin@example.com",
            password_hash="hash",
            role=UserRole.SYSADMIN,
            is_active=True
        )

        dependency = require_sysadmin_only()
        dep_func = dependency.dependency

        result = await dep_func(current_user=sysadmin_user)
        assert result == sysadmin_user

    async def test_require_sysadmin_only_failure(self) -> None:
        """Test require_sysadmin_only dependency with invalid user."""
        admin_user = User(
            user_id=uuid4(),
            email="admin@example.com",
            password_hash="hash",
            role=UserRole.ADMIN,
            is_active=True
        )

        dependency = require_sysadmin_only()
        dep_func = dependency.dependency

        with pytest.raises(HTTPException) as exc_info:
            await dep_func(current_user=admin_user)

        assert exc_info.value.status_code == 403
        assert "Sysadmin role required" in exc_info.value.detail


class TestRequirePermissionFunction:
    """Test require_permission function."""

    def test_require_permission_returns_dependency(self) -> None:
        """Test require_permission returns a FastAPI dependency."""
        dependency = require_permission(AgentName.CLIENT_MANAGEMENT, "create")
        assert dependency is not None
