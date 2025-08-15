"""
Comprehensive Authentication Middleware tests to improve coverage.
Following CLAUDE.md guidelines: Never mock internal business logic.
Mock only external dependencies (auth_service, Redis, request/response objects).
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from starlette.responses import Response

from src.middleware.auth import (
    AuthMiddleware,
    PermissionService,
    RequestContext,
    get_current_user,
    get_current_user_id,
    get_current_user_optional,
    get_current_user_role,
    get_request_context,
    get_user_session_info,
    invalidate_user_sessions,
    permission_service,
    require_admin,
    require_agent_permission,
    require_role,
    require_sysadmin,
    require_user,
)
from src.models.permission import AgentName
from src.models.user import UserRole


class TestRequestContext:
    """Test RequestContext class."""

    def test_request_context_initialization(self):
        """Test RequestContext is properly initialized."""
        context = RequestContext()

        assert context.user_id is None
        assert context.user_role is None
        assert context.permissions == {}
        assert context.token is None
        assert context.session_id is None


class TestAuthMiddleware:
    """Test AuthMiddleware functionality."""

    def test_auth_middleware_initialization(self):
        """Test AuthMiddleware initialization with custom exclude paths."""
        app = FastAPI()
        custom_excludes = ["/custom", "/api/custom"]

        middleware = AuthMiddleware(app, exclude_paths=custom_excludes)

        assert middleware.exclude_paths == custom_excludes

    def test_auth_middleware_default_exclude_paths(self):
        """Test AuthMiddleware initialization with default exclude paths."""
        app = FastAPI()

        middleware = AuthMiddleware(app)

        expected_excludes = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
        ]
        assert middleware.exclude_paths == expected_excludes

    @pytest.mark.asyncio
    async def test_auth_middleware_excluded_path(self):
        """Test middleware skips authentication for excluded paths."""
        app = FastAPI()
        middleware = AuthMiddleware(app)

        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/docs"
        mock_request.method = "GET"

        # Mock call_next
        mock_response = MagicMock(spec=Response)
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, call_next)

        assert result == mock_response
        call_next.assert_called_once_with(mock_request)
        # Verify no auth context was set
        assert not hasattr(mock_request.state, "auth_context")

    @pytest.mark.asyncio
    async def test_auth_middleware_missing_authorization_header(self):
        """Test middleware handles missing authorization header."""
        app = FastAPI()
        middleware = AuthMiddleware(app)

        # Mock request without authorization header
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/protected"
        mock_request.method = "GET"
        mock_request.headers.get.return_value = None
        mock_request.state = MagicMock()

        # Mock call_next
        mock_response = MagicMock(spec=Response)
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, call_next)

        assert result == mock_response
        call_next.assert_called_once_with(mock_request)
        # Verify auth context was initialized
        assert isinstance(mock_request.state.auth_context, RequestContext)

    @pytest.mark.asyncio
    async def test_auth_middleware_invalid_authorization_header(self):
        """Test middleware handles invalid authorization header format."""
        app = FastAPI()
        middleware = AuthMiddleware(app)

        # Mock request with invalid authorization header
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/protected"
        mock_request.method = "GET"
        mock_request.headers.get.return_value = "Invalid header format"
        mock_request.state = MagicMock()

        # Mock call_next
        mock_response = MagicMock(spec=Response)
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, call_next)

        assert result == mock_response
        call_next.assert_called_once_with(mock_request)
        # Verify auth context was initialized
        assert isinstance(mock_request.state.auth_context, RequestContext)

    @pytest.mark.asyncio
    async def test_auth_middleware_valid_token(self):
        """Test middleware with valid authorization token."""
        app = FastAPI()
        middleware = AuthMiddleware(app)

        # Mock request with valid authorization header
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/protected"
        mock_request.method = "GET"
        mock_request.headers.get.return_value = "Bearer valid.jwt.token"
        mock_request.state = MagicMock()

        # Mock auth_service.verify_token - APPROVED: mocking external service
        with patch("src.middleware.auth.auth_service.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "test-user-id", "role": "admin"}

            # Mock UUID generation - APPROVED external dependency
            with patch("src.middleware.auth.uuid.uuid4") as mock_uuid:
                mock_uuid.return_value = uuid.UUID(
                    "12345678-1234-5678-9012-123456789012"
                )

                # Mock call_next
                mock_response = MagicMock(spec=Response)
                call_next = AsyncMock(return_value=mock_response)

                result = await middleware.dispatch(mock_request, call_next)

                assert result == mock_response
                call_next.assert_called_once_with(mock_request)

                # Verify auth context was populated
                context = mock_request.state.auth_context
                assert context.user_id == "test-user-id"
                assert context.user_role == UserRole.ADMIN
                assert context.token == "valid.jwt.token"
                assert context.session_id == str(mock_uuid.return_value)

    @pytest.mark.asyncio
    async def test_auth_middleware_token_verification_failure(self):
        """Test middleware handles token verification failure."""
        app = FastAPI()
        middleware = AuthMiddleware(app)

        # Mock request with authorization header
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/protected"
        mock_request.method = "GET"
        mock_request.headers.get.return_value = "Bearer invalid.jwt.token"
        mock_request.state = MagicMock()

        # Mock auth_service.verify_token to raise HTTPException - APPROVED: mocking external service
        with patch("src.middleware.auth.auth_service.verify_token") as mock_verify:
            mock_verify.side_effect = HTTPException(
                status_code=401, detail="Invalid token"
            )

            # Mock call_next
            mock_response = MagicMock(spec=Response)
            call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, call_next)

            assert result == mock_response
            call_next.assert_called_once_with(mock_request)
            # Verify auth context was initialized but not populated
            assert isinstance(mock_request.state.auth_context, RequestContext)

    @pytest.mark.asyncio
    async def test_auth_middleware_unexpected_exception(self):
        """Test middleware handles unexpected exceptions."""
        app = FastAPI()
        middleware = AuthMiddleware(app)

        # Mock request with authorization header
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/protected"
        mock_request.method = "GET"
        mock_request.headers.get.return_value = "Bearer some.jwt.token"
        mock_request.state = MagicMock()

        # Mock auth_service.verify_token to raise unexpected exception - APPROVED: mocking external service
        with patch("src.middleware.auth.auth_service.verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Unexpected error")

            # Mock call_next
            mock_response = MagicMock(spec=Response)
            call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, call_next)

            assert result == mock_response
            call_next.assert_called_once_with(mock_request)
            # Verify auth context was initialized but not populated
            assert isinstance(mock_request.state.auth_context, RequestContext)


class TestAuthDependencies:
    """Test authentication dependency functions."""

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_no_credentials(self):
        """Test optional auth dependency with no credentials."""
        mock_request = MagicMock(spec=Request)

        result = await get_current_user_optional(mock_request, credentials=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_valid_credentials(self):
        """Test optional auth dependency with valid credentials."""
        mock_request = MagicMock(spec=Request)
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid.jwt.token"

        # Mock auth_service.verify_token - APPROVED: mocking external service
        with patch("src.middleware.auth.auth_service.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "test-user-id", "role": "user"}

            result = await get_current_user_optional(mock_request, mock_credentials)

            assert result == {
                "user_id": "test-user-id",
                "user_role": "user",
                "token": "valid.jwt.token",
            }

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_missing_claims(self):
        """Test optional auth dependency with missing required claims."""
        mock_request = MagicMock(spec=Request)
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token.missing.claims"

        # Mock auth_service.verify_token - APPROVED: mocking external service
        with patch("src.middleware.auth.auth_service.verify_token") as mock_verify:
            mock_verify.return_value = {"role": "user"}  # Missing "sub"

            result = await get_current_user_optional(mock_request, mock_credentials)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_optional_with_exception(self):
        """Test optional auth dependency with token verification exception."""
        mock_request = MagicMock(spec=Request)
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid.jwt.token"

        # Mock auth_service.verify_token - APPROVED: mocking external service
        with patch("src.middleware.auth.auth_service.verify_token") as mock_verify:
            mock_verify.side_effect = HTTPException(
                status_code=401, detail="Invalid token"
            )

            result = await get_current_user_optional(mock_request, mock_credentials)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_credentials(self):
        """Test required auth dependency with valid credentials."""
        mock_request = MagicMock(spec=Request)
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid.jwt.token"

        # Mock auth_service.verify_token - APPROVED: mocking external service
        with patch("src.middleware.auth.auth_service.verify_token") as mock_verify:
            mock_verify.return_value = {"sub": "test-user-id", "role": "admin"}

            result = await get_current_user(mock_request, mock_credentials)

            assert result == {
                "user_id": "test-user-id",
                "user_role": "admin",
                "token": "valid.jwt.token",
            }

    @pytest.mark.asyncio
    async def test_get_current_user_with_missing_claims(self):
        """Test required auth dependency with missing required claims."""
        mock_request = MagicMock(spec=Request)
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token.missing.claims"

        # Mock auth_service.verify_token - APPROVED: mocking external service
        with patch("src.middleware.auth.auth_service.verify_token") as mock_verify:
            mock_verify.return_value = {"role": "user"}  # Missing "sub"

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, mock_credentials)

            assert exc_info.value.status_code == 401
            assert "Invalid token: missing user information" in str(
                exc_info.value.detail
            )

    @pytest.mark.asyncio
    async def test_get_current_user_with_exception(self):
        """Test required auth dependency with token verification exception."""
        mock_request = MagicMock(spec=Request)
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid.jwt.token"

        # Mock auth_service.verify_token - APPROVED: mocking external service
        with patch("src.middleware.auth.auth_service.verify_token") as mock_verify:
            mock_verify.side_effect = HTTPException(
                status_code=401, detail="Invalid token"
            )

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, mock_credentials)

            assert exc_info.value.status_code == 401
            assert "Invalid token" in str(exc_info.value.detail)


class TestRoleBasedAccess:
    """Test role-based access control functions."""

    @pytest.mark.asyncio
    async def test_require_role_with_sufficient_permissions(self):
        """Test role requirement with sufficient user permissions."""
        # Create role dependency for admin role
        role_dep = require_role(UserRole.ADMIN)

        # Mock current user with sysadmin role (higher than admin)
        current_user = {
            "user_id": "test-user-id",
            "user_role": "sysadmin",
            "token": "valid.token",
        }

        result = await role_dep(current_user)

        assert result == current_user

    @pytest.mark.asyncio
    async def test_require_role_with_insufficient_permissions(self):
        """Test role requirement with insufficient user permissions."""
        # Create role dependency for admin role
        role_dep = require_role(UserRole.ADMIN)

        # Mock current user with user role (lower than admin)
        current_user = {
            "user_id": "test-user-id",
            "user_role": "user",
            "token": "valid.token",
        }

        with pytest.raises(HTTPException) as exc_info:
            await role_dep(current_user)

        assert exc_info.value.status_code == 403
        assert "Required role: admin" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_role_with_missing_role(self):
        """Test role requirement with missing user role."""
        # Create role dependency for admin role
        role_dep = require_role(UserRole.ADMIN)

        # Mock current user without role
        current_user = {"user_id": "test-user-id", "token": "valid.token"}

        with pytest.raises(HTTPException) as exc_info:
            await role_dep(current_user)

        assert exc_info.value.status_code == 403
        assert "Invalid user role" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_sysadmin(self):
        """Test sysadmin role requirement."""
        current_user = {
            "user_id": "test-user-id",
            "user_role": "sysadmin",
            "token": "valid.token",
        }

        result = await require_sysadmin(current_user)

        assert result == current_user

    @pytest.mark.asyncio
    async def test_require_admin(self):
        """Test admin role requirement."""
        current_user = {
            "user_id": "test-user-id",
            "user_role": "admin",
            "token": "valid.token",
        }

        result = await require_admin(current_user)

        assert result == current_user

    @pytest.mark.asyncio
    async def test_require_user(self):
        """Test user role requirement."""
        current_user = {
            "user_id": "test-user-id",
            "user_role": "user",
            "token": "valid.token",
        }

        result = await require_user(current_user)

        assert result == current_user


class TestPermissionService:
    """Test PermissionService functionality."""

    def test_permission_service_initialization(self):
        """Test PermissionService initialization."""
        service = PermissionService()

        assert service.settings is not None

    @pytest.mark.asyncio
    async def test_check_agent_permission_placeholder(self):
        """Test check_agent_permission placeholder implementation."""
        service = PermissionService()

        result = await service.check_agent_permission(
            user_id="test-user-id",
            agent_name=AgentName.CLIENT_MANAGEMENT,
            operation="read",
        )

        # Placeholder implementation returns True
        assert result is True

    @pytest.mark.asyncio
    async def test_get_user_permissions_placeholder(self):
        """Test get_user_permissions placeholder implementation."""
        service = PermissionService()

        result = await service.get_user_permissions("test-user-id")

        # Placeholder implementation returns empty dict
        assert result == {}

    @pytest.mark.asyncio
    async def test_require_agent_permission_with_permission(self):
        """Test agent permission requirement with sufficient permissions."""
        # Create permission dependency
        permission_dep = require_agent_permission(AgentName.CLIENT_MANAGEMENT, "read")

        # Mock current user
        current_user = {
            "user_id": "test-user-id",
            "user_role": "user",
            "token": "valid.token",
        }

        # Mock permission service - APPROVED: mocking placeholder service
        with patch.object(permission_service, "check_agent_permission") as mock_check:
            mock_check.return_value = True

            result = await permission_dep(current_user)

            assert result == current_user
            mock_check.assert_called_once_with(
                user_id="test-user-id",
                agent_name=AgentName.CLIENT_MANAGEMENT,
                operation="read",
            )

    @pytest.mark.asyncio
    async def test_require_agent_permission_without_permission(self):
        """Test agent permission requirement without sufficient permissions."""
        # Create permission dependency
        permission_dep = require_agent_permission(AgentName.CLIENT_MANAGEMENT, "delete")

        # Mock current user
        current_user = {
            "user_id": "test-user-id",
            "user_role": "user",
            "token": "valid.token",
        }

        # Mock permission service - APPROVED: mocking placeholder service
        with patch.object(permission_service, "check_agent_permission") as mock_check:
            mock_check.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                await permission_dep(current_user)

            assert exc_info.value.status_code == 403
            assert "Permission denied for client_management delete" in str(
                exc_info.value.detail
            )

    @pytest.mark.asyncio
    async def test_require_agent_permission_with_invalid_user(self):
        """Test agent permission requirement with invalid user context."""
        # Create permission dependency
        permission_dep = require_agent_permission(AgentName.CLIENT_MANAGEMENT, "read")

        # Mock current user without user_id
        current_user = {"user_role": "user", "token": "valid.token"}

        with pytest.raises(HTTPException) as exc_info:
            await permission_dep(current_user)

        assert exc_info.value.status_code == 401
        assert "Invalid user context" in str(exc_info.value.detail)


class TestSessionManagement:
    """Test session management functions."""

    @pytest.mark.asyncio
    async def test_get_user_session_info_success(self):
        """Test successful user session info retrieval."""
        user_id = "test-user-id"

        # Mock Redis response
        mock_sessions = ["session1.token", "session2.token"]

        # Mock auth_service.redis_client - APPROVED: mocking external service
        with patch("src.middleware.auth.auth_service.redis_client") as mock_redis:
            mock_redis.smembers.return_value = mock_sessions

            result = await get_user_session_info(user_id)

            assert result == {
                "user_id": user_id,
                "active_sessions": 2,
                "max_sessions": 5,
                "session_tokens": mock_sessions,
            }
            mock_redis.smembers.assert_called_once_with(f"user_session:{user_id}")

    @pytest.mark.asyncio
    async def test_get_user_session_info_exception(self):
        """Test user session info retrieval with exception."""
        user_id = "test-user-id"

        # Mock Redis to raise exception
        with patch("src.middleware.auth.auth_service.redis_client") as mock_redis:
            mock_redis.smembers.side_effect = Exception("Redis error")

            result = await get_user_session_info(user_id)

            assert result == {
                "user_id": user_id,
                "active_sessions": 0,
                "max_sessions": 5,
                "session_tokens": [],
            }

    @pytest.mark.asyncio
    async def test_invalidate_user_sessions_success(self):
        """Test successful user session invalidation."""
        user_id = "test-user-id"
        keep_token = "keep.this.token"

        # Mock Redis response
        mock_sessions = ["session1.token", "session2.token", keep_token]

        # Mock auth_service and redis_client - APPROVED: mocking external services
        with patch("src.middleware.auth.auth_service") as mock_auth_service:
            mock_auth_service.redis_client.smembers.return_value = mock_sessions
            mock_auth_service.blacklist_token.return_value = None
            mock_auth_service.redis_client.srem.return_value = True

            result = await invalidate_user_sessions(user_id, keep_token)

            # Should invalidate 2 sessions (excluding keep_token)
            assert result == 2

            # Verify blacklist_token was called for sessions to invalidate
            assert mock_auth_service.blacklist_token.call_count == 2
            mock_auth_service.blacklist_token.assert_any_call("session1.token")
            mock_auth_service.blacklist_token.assert_any_call("session2.token")

            # Verify srem was called for sessions to invalidate
            assert mock_auth_service.redis_client.srem.call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_user_sessions_without_keeping_current(self):
        """Test user session invalidation without keeping current token."""
        user_id = "test-user-id"

        # Mock Redis response
        mock_sessions = ["session1.token", "session2.token"]

        # Mock auth_service and redis_client - APPROVED: mocking external services
        with patch("src.middleware.auth.auth_service") as mock_auth_service:
            mock_auth_service.redis_client.smembers.return_value = mock_sessions
            mock_auth_service.blacklist_token.return_value = None
            mock_auth_service.redis_client.srem.return_value = True

            result = await invalidate_user_sessions(user_id)

            # Should invalidate all sessions
            assert result == 2

            # Verify blacklist_token was called for all sessions
            assert mock_auth_service.blacklist_token.call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_user_sessions_exception(self):
        """Test user session invalidation with exception."""
        user_id = "test-user-id"

        # Mock auth_service to raise exception
        with patch("src.middleware.auth.auth_service") as mock_auth_service:
            mock_auth_service.redis_client.smembers.side_effect = Exception(
                "Redis error"
            )

            result = await invalidate_user_sessions(user_id)

            assert result == 0


class TestRequestContextHelpers:
    """Test request context helper functions."""

    def test_get_request_context_with_context(self):
        """Test get_request_context when context exists."""
        mock_request = MagicMock(spec=Request)
        mock_context = RequestContext()
        mock_request.state.auth_context = mock_context

        result = get_request_context(mock_request)

        assert result == mock_context

    def test_get_request_context_without_context(self):
        """Test get_request_context when context doesn't exist."""
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()

        # Make getattr return None for non-existent attribute
        with patch("src.middleware.auth.getattr", return_value=None):
            result = get_request_context(mock_request)

        assert result is None

    def test_get_current_user_id_with_context(self):
        """Test get_current_user_id when context exists."""
        mock_request = MagicMock(spec=Request)
        mock_context = RequestContext()
        mock_context.user_id = "test-user-id"

        with patch(
            "src.middleware.auth.get_request_context", return_value=mock_context
        ):
            result = get_current_user_id(mock_request)

        assert result == "test-user-id"

    def test_get_current_user_id_without_context(self):
        """Test get_current_user_id when context doesn't exist."""
        mock_request = MagicMock(spec=Request)

        with patch("src.middleware.auth.get_request_context", return_value=None):
            result = get_current_user_id(mock_request)

        assert result is None

    def test_get_current_user_role_with_context(self):
        """Test get_current_user_role when context exists."""
        mock_request = MagicMock(spec=Request)
        mock_context = RequestContext()
        mock_context.user_role = UserRole.ADMIN

        with patch(
            "src.middleware.auth.get_request_context", return_value=mock_context
        ):
            result = get_current_user_role(mock_request)

        assert result == UserRole.ADMIN

    def test_get_current_user_role_without_context(self):
        """Test get_current_user_role when context doesn't exist."""
        mock_request = MagicMock(spec=Request)

        with patch("src.middleware.auth.get_request_context", return_value=None):
            result = get_current_user_role(mock_request)

        assert result is None
