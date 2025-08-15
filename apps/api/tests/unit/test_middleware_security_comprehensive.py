"""
Comprehensive Security Middleware tests to improve coverage.
Following CLAUDE.md guidelines: Never mock internal business logic.
Mock only external dependencies (Redis, settings, request/response objects).
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request, Response
from slowapi.errors import RateLimitExceeded

from src.middleware.security import (
    CORSSecurityMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    cors_security_middleware,
    get_rate_limit_by_role,
    get_rate_limit_key,
    get_rate_limit_storage,
    limiter,
    rate_limit_middleware,
    role_based_rate_limit,
    security_headers_middleware,
)
from src.models.user import UserRole


class TestRateLimitStorage:
    """Test rate limit storage functions."""

    def test_get_rate_limit_storage(self):
        """Test rate limit storage Redis connection."""
        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.EFFECTIVE_RATE_LIMIT_STORAGE = "redis://localhost:6379/1"
            mock_get_settings.return_value = mock_settings

            # Mock redis.from_url - APPROVED external dependency
            with patch("src.middleware.security.redis.from_url") as mock_redis_from_url:
                mock_redis_instance = MagicMock()
                mock_redis_from_url.return_value = mock_redis_instance

                result = get_rate_limit_storage()

                assert result == mock_redis_instance
                mock_redis_from_url.assert_called_once_with(
                    "redis://localhost:6379/1", decode_responses=True
                )


class TestRateLimitKey:
    """Test rate limit key generation."""

    def test_get_rate_limit_key_authenticated_user(self):
        """Test rate limit key generation for authenticated user."""
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_auth_context = MagicMock()
        mock_auth_context.user_id = "test-user-id"
        mock_request.state.auth_context = mock_auth_context

        # Mock get_current_user_role - APPROVED: mocking middleware function
        with patch("src.middleware.security.get_current_user_role") as mock_get_role:
            mock_get_role.return_value = UserRole.ADMIN

            result = get_rate_limit_key(mock_request)

            assert result == "user:admin:test-user-id"

    def test_get_rate_limit_key_authenticated_user_string_role(self):
        """Test rate limit key generation for authenticated user with string role."""
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_auth_context = MagicMock()
        mock_auth_context.user_id = "test-user-id"
        mock_request.state.auth_context = mock_auth_context

        # Mock get_current_user_role - APPROVED: mocking middleware function
        with patch("src.middleware.security.get_current_user_role") as mock_get_role:
            mock_get_role.return_value = "sysadmin"  # String instead of enum

            result = get_rate_limit_key(mock_request)

            assert result == "user:sysadmin:test-user-id"

    def test_get_rate_limit_key_authenticated_user_no_user_id(self):
        """Test rate limit key generation for authenticated user without user_id."""
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_auth_context = MagicMock()
        mock_auth_context.user_id = None
        mock_request.state.auth_context = mock_auth_context

        # Mock get_current_user_role - APPROVED: mocking middleware function
        with patch("src.middleware.security.get_current_user_role") as mock_get_role:
            mock_get_role.return_value = UserRole.USER

            # Mock get_remote_address - APPROVED external dependency
            with patch("src.middleware.security.get_remote_address") as mock_get_ip:
                mock_get_ip.return_value = "192.168.1.1"

                result = get_rate_limit_key(mock_request)

                assert result == "ip:192.168.1.1"

    def test_get_rate_limit_key_no_auth_context(self):
        """Test rate limit key generation for user without auth context."""
        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()

        # Mock getattr to return None for auth_context
        with patch("builtins.getattr", return_value=None):
            # Mock get_current_user_role - APPROVED: mocking middleware function
            with patch(
                "src.middleware.security.get_current_user_role"
            ) as mock_get_role:
                mock_get_role.return_value = UserRole.USER

                # Mock get_remote_address - APPROVED external dependency
                with patch("src.middleware.security.get_remote_address") as mock_get_ip:
                    mock_get_ip.return_value = "192.168.1.1"

                    result = get_rate_limit_key(mock_request)

                    assert result == "ip:192.168.1.1"

    def test_get_rate_limit_key_anonymous_user(self):
        """Test rate limit key generation for anonymous user."""
        # Mock request
        mock_request = MagicMock(spec=Request)

        # Mock get_current_user_role - APPROVED: mocking middleware function
        with patch("src.middleware.security.get_current_user_role") as mock_get_role:
            mock_get_role.return_value = None  # Anonymous user

            # Mock get_remote_address - APPROVED external dependency
            with patch("src.middleware.security.get_remote_address") as mock_get_ip:
                mock_get_ip.return_value = "192.168.1.100"

                result = get_rate_limit_key(mock_request)

                assert result == "ip:192.168.1.100"


class TestSecurityHeadersMiddleware:
    """Test SecurityHeadersMiddleware functionality."""

    def test_security_headers_middleware_initialization(self):
        """Test SecurityHeadersMiddleware initialization."""
        app = FastAPI()

        middleware = SecurityHeadersMiddleware(app)

        assert middleware.settings is not None

    @pytest.mark.asyncio
    async def test_security_headers_middleware_enabled(self):
        """Test security headers middleware when headers are enabled."""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)

        # Mock settings - APPROVED external dependency
        with patch.object(middleware, "settings") as mock_settings:
            mock_settings.ENABLE_SECURITY_HEADERS = True
            mock_settings.DEBUG = False
            mock_settings.HSTS_MAX_AGE = 31536000
            mock_settings.CSP_POLICY = "default-src 'self'"
            mock_settings.REFERRER_POLICY = "strict-origin-when-cross-origin"

            # Mock request and response
            mock_request = MagicMock(spec=Request)
            mock_response = MagicMock(spec=Response)
            mock_response.headers = {}

            call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, call_next)

            assert result == mock_response
            call_next.assert_called_once_with(mock_request)

            # Verify security headers were added
            assert "Strict-Transport-Security" in mock_response.headers
            assert (
                mock_response.headers["Content-Security-Policy"] == "default-src 'self'"
            )
            assert mock_response.headers["X-Frame-Options"] == "DENY"
            assert mock_response.headers["X-Content-Type-Options"] == "nosniff"
            assert (
                mock_response.headers["Referrer-Policy"]
                == "strict-origin-when-cross-origin"
            )
            assert mock_response.headers["X-XSS-Protection"] == "1; mode=block"
            assert "Permissions-Policy" in mock_response.headers
            assert (
                mock_response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
            )
            assert (
                mock_response.headers["Cross-Origin-Embedder-Policy"] == "require-corp"
            )
            assert mock_response.headers["Cross-Origin-Opener-Policy"] == "same-origin"

    @pytest.mark.asyncio
    async def test_security_headers_middleware_debug_mode(self):
        """Test security headers middleware in debug mode (no HSTS)."""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)

        # Mock settings - APPROVED external dependency
        with patch.object(middleware, "settings") as mock_settings:
            mock_settings.ENABLE_SECURITY_HEADERS = True
            mock_settings.DEBUG = True  # Debug mode
            mock_settings.CSP_POLICY = "default-src 'self'"
            mock_settings.REFERRER_POLICY = "strict-origin-when-cross-origin"

            # Mock request and response
            mock_request = MagicMock(spec=Request)
            mock_response = MagicMock(spec=Response)
            mock_response.headers = {}

            call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, call_next)

            assert result == mock_response

            # HSTS should not be set in debug mode
            assert "Strict-Transport-Security" not in mock_response.headers
            # Other headers should still be set
            assert mock_response.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    async def test_security_headers_middleware_disabled(self):
        """Test security headers middleware when headers are disabled."""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)

        # Mock settings - APPROVED external dependency
        with patch.object(middleware, "settings") as mock_settings:
            mock_settings.ENABLE_SECURITY_HEADERS = False

            # Mock request and response
            mock_request = MagicMock(spec=Request)
            mock_response = MagicMock(spec=Response)
            mock_response.headers = {}

            call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, call_next)

            assert result == mock_response
            call_next.assert_called_once_with(mock_request)

            # No security headers should be added
            assert len(mock_response.headers) == 0


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware functionality."""

    def test_rate_limit_middleware_initialization(self):
        """Test RateLimitMiddleware initialization."""
        app = FastAPI()

        # Mock get_rate_limit_storage - APPROVED external dependency
        with patch(
            "src.middleware.security.get_rate_limit_storage"
        ) as mock_get_storage:
            mock_redis = MagicMock()
            mock_get_storage.return_value = mock_redis

            middleware = RateLimitMiddleware(app)

            assert middleware.settings is not None
            assert middleware.redis_client == mock_redis
            assert UserRole.SYSADMIN in middleware.rate_limits
            assert UserRole.ADMIN in middleware.rate_limits
            assert UserRole.USER in middleware.rate_limits
            assert "anonymous" in middleware.rate_limits

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_skip_paths(self):
        """Test rate limiting middleware skips certain paths."""
        app = FastAPI()

        # Mock get_rate_limit_storage - APPROVED external dependency
        with patch(
            "src.middleware.security.get_rate_limit_storage"
        ) as mock_get_storage:
            mock_redis = MagicMock()
            mock_get_storage.return_value = mock_redis

            middleware = RateLimitMiddleware(app)

            skip_paths = ["/health", "/docs", "/redoc", "/openapi.json"]

            for path in skip_paths:
                # Mock request
                mock_request = MagicMock(spec=Request)
                mock_request.url.path = path

                # Mock response
                mock_response = MagicMock(spec=Response)
                call_next = AsyncMock(return_value=mock_response)

                result = await middleware.dispatch(mock_request, call_next)

                assert result == mock_response
                call_next.assert_called_once_with(mock_request)
                call_next.reset_mock()

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_authenticated_user(self):
        """Test rate limiting for authenticated user."""
        app = FastAPI()

        # Mock get_rate_limit_storage - APPROVED external dependency
        with patch(
            "src.middleware.security.get_rate_limit_storage"
        ) as mock_get_storage:
            mock_redis = MagicMock()
            mock_get_storage.return_value = mock_redis

            middleware = RateLimitMiddleware(app)

            # Mock request
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/api/test"
            mock_request.method = "GET"

            # Mock get_rate_limit_key - APPROVED: mocking helper function
            with patch("src.middleware.security.get_rate_limit_key") as mock_get_key:
                mock_get_key.return_value = "user:admin:test-user-id"

                # Mock get_current_user_role - APPROVED: mocking middleware function
                with patch(
                    "src.middleware.security.get_current_user_role"
                ) as mock_get_role:
                    mock_get_role.return_value = UserRole.ADMIN

                    # Mock _check_rate_limit
                    with patch.object(middleware, "_check_rate_limit") as mock_check:
                        mock_check.return_value = 5  # Current count

                        # Mock response
                        mock_response = MagicMock(spec=Response)
                        mock_response.headers = {}
                        call_next = AsyncMock(return_value=mock_response)

                        # Mock datetime - APPROVED external dependency
                        with patch("src.middleware.security.datetime") as mock_datetime:
                            mock_now = datetime(2025, 1, 1, 12, 0, 0)
                            mock_datetime.now.return_value = mock_now

                            result = await middleware.dispatch(mock_request, call_next)

                            assert result == mock_response
                            # Verify rate limit headers were added
                            assert "X-RateLimit-Limit" in mock_response.headers
                            assert "X-RateLimit-Remaining" in mock_response.headers
                            assert "X-RateLimit-Reset" in mock_response.headers

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_anonymous_user(self):
        """Test rate limiting for anonymous user."""
        app = FastAPI()

        # Mock get_rate_limit_storage - APPROVED external dependency
        with patch(
            "src.middleware.security.get_rate_limit_storage"
        ) as mock_get_storage:
            mock_redis = MagicMock()
            mock_get_storage.return_value = mock_redis

            middleware = RateLimitMiddleware(app)

            # Mock request
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/api/test"
            mock_request.method = "GET"

            # Mock get_rate_limit_key - APPROVED: mocking helper function
            with patch("src.middleware.security.get_rate_limit_key") as mock_get_key:
                mock_get_key.return_value = "ip:192.168.1.1"

                # Mock get_current_user_role - APPROVED: mocking middleware function
                with patch(
                    "src.middleware.security.get_current_user_role"
                ) as mock_get_role:
                    mock_get_role.return_value = None  # Anonymous

                    # Mock _check_rate_limit
                    with patch.object(middleware, "_check_rate_limit") as mock_check:
                        mock_check.return_value = 10  # Current count

                        # Mock response
                        mock_response = MagicMock(spec=Response)
                        mock_response.headers = {}
                        call_next = AsyncMock(return_value=mock_response)

                        # Mock datetime - APPROVED external dependency
                        with patch("src.middleware.security.datetime") as mock_datetime:
                            mock_datetime.now.return_value = datetime(
                                2025, 1, 1, 12, 0, 0
                            )

                            result = await middleware.dispatch(mock_request, call_next)

                            assert result == mock_response
                            # Should use anonymous rate limit (50)
                            assert mock_response.headers["X-RateLimit-Limit"] == "50"

    @pytest.mark.asyncio
    async def test_rate_limit_middleware_exceeded(self):
        """Test rate limiting when limit is exceeded."""
        app = FastAPI()

        # Mock get_rate_limit_storage - APPROVED external dependency
        with patch(
            "src.middleware.security.get_rate_limit_storage"
        ) as mock_get_storage:
            mock_redis = MagicMock()
            mock_get_storage.return_value = mock_redis

            middleware = RateLimitMiddleware(app)

            # Mock request
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/api/test"
            mock_request.method = "GET"

            # Mock get_rate_limit_key - APPROVED: mocking helper function
            with patch("src.middleware.security.get_rate_limit_key") as mock_get_key:
                mock_get_key.return_value = "user:user:test-user-id"

                # Mock get_current_user_role - APPROVED: mocking middleware function
                with patch(
                    "src.middleware.security.get_current_user_role"
                ) as mock_get_role:
                    mock_get_role.return_value = UserRole.USER

                    # Mock _check_rate_limit to raise exception
                    with patch.object(middleware, "_check_rate_limit") as mock_check:
                        mock_check.side_effect = RateLimitExceeded(
                            "Rate limit exceeded"
                        )

                        with pytest.raises(HTTPException) as exc_info:
                            await middleware.dispatch(mock_request, AsyncMock())

                        assert exc_info.value.status_code == 429
                        assert "Rate limit exceeded" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self):
        """Test rate limit checking when within limit."""
        app = FastAPI()

        # Mock get_rate_limit_storage - APPROVED external dependency
        with patch(
            "src.middleware.security.get_rate_limit_storage"
        ) as mock_get_storage:
            mock_redis = MagicMock()
            mock_get_storage.return_value = mock_redis

            middleware = RateLimitMiddleware(app)

            # Mock Redis pipeline operations
            mock_pipeline = AsyncMock()
            mock_pipeline.execute.return_value = [
                None,
                5,
                None,
                None,
            ]  # Current count = 5
            mock_redis.pipeline.return_value = mock_pipeline

            # Mock datetime - APPROVED external dependency
            with patch("src.middleware.security.datetime") as mock_datetime:
                mock_now = datetime(2025, 1, 1, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                mock_datetime.timestamp = datetime.timestamp

                result = await middleware._check_rate_limit("test-key", 100, 60)

                assert result == 6  # 5 + 1

                # Verify pipeline operations
                mock_pipeline.zremrangebyscore.assert_called_once()
                mock_pipeline.zcard.assert_called_once()
                mock_pipeline.zadd.assert_called_once()
                mock_pipeline.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """Test rate limit checking when limit is exceeded."""
        app = FastAPI()

        # Mock get_rate_limit_storage - APPROVED external dependency
        with patch(
            "src.middleware.security.get_rate_limit_storage"
        ) as mock_get_storage:
            mock_redis = MagicMock()
            mock_get_storage.return_value = mock_redis

            middleware = RateLimitMiddleware(app)

            # Mock Redis pipeline operations
            mock_pipeline = AsyncMock()
            mock_pipeline.execute.return_value = [
                None,
                100,
                None,
                None,
            ]  # Current count = 100 (at limit)
            mock_redis.pipeline.return_value = mock_pipeline

            # Mock datetime - APPROVED external dependency
            with patch("src.middleware.security.datetime") as mock_datetime:
                mock_now = datetime(2025, 1, 1, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                mock_datetime.timestamp = datetime.timestamp

                with pytest.raises(HTTPException) as exc_info:
                    await middleware._check_rate_limit("test-key", 100, 60)

                assert exc_info.value.status_code == 429
                assert "Rate limit exceeded" in str(exc_info.value.detail)


class TestRateLimitUtilities:
    """Test rate limiting utility functions."""

    def test_get_rate_limit_by_role_sysadmin(self):
        """Test rate limit by role for sysadmin."""
        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.SYSADMIN_RATE_LIMIT_PER_MINUTE = 1000
            mock_get_settings.return_value = mock_settings

            result = get_rate_limit_by_role(UserRole.SYSADMIN)

            assert result == "1000/minute"

    def test_get_rate_limit_by_role_admin(self):
        """Test rate limit by role for admin."""
        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.ADMIN_RATE_LIMIT_PER_MINUTE = 500
            mock_get_settings.return_value = mock_settings

            result = get_rate_limit_by_role(UserRole.ADMIN)

            assert result == "500/minute"

    def test_get_rate_limit_by_role_user(self):
        """Test rate limit by role for user."""
        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.USER_RATE_LIMIT_PER_MINUTE = 100
            mock_get_settings.return_value = mock_settings

            result = get_rate_limit_by_role(UserRole.USER)

            assert result == "100/minute"

    def test_get_rate_limit_by_role_anonymous(self):
        """Test rate limit by role for anonymous user."""
        result = get_rate_limit_by_role(None)

        assert result == "50/minute"

    def test_role_based_rate_limit_decorator(self):
        """Test role-based rate limit decorator."""
        decorator = role_based_rate_limit()

        # Mock function to decorate
        async def test_func(request, *args, **kwargs):
            return "success"

        decorated_func = decorator(test_func)

        # Verify the decorator returns a function
        assert callable(decorated_func)


class TestCORSSecurityMiddleware:
    """Test CORSSecurityMiddleware functionality."""

    def test_cors_security_middleware_initialization(self):
        """Test CORSSecurityMiddleware initialization."""
        app = FastAPI()

        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.EFFECTIVE_CORS_ORIGINS = [
                "https://example.com",
                "https://*.subdomain.com",
            ]
            mock_get_settings.return_value = mock_settings

            middleware = CORSSecurityMiddleware(app)

            assert middleware.settings is not None
            assert len(middleware.allowed_origins) == 2
            assert len(middleware.origin_patterns) == 1  # One wildcard pattern

    def test_is_origin_allowed_exact_match(self):
        """Test origin validation with exact match."""
        app = FastAPI()

        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.EFFECTIVE_CORS_ORIGINS = [
                "https://example.com",
                "https://app.example.com",
            ]
            mock_get_settings.return_value = mock_settings

            middleware = CORSSecurityMiddleware(app)

            assert middleware._is_origin_allowed("https://example.com") is True
            assert middleware._is_origin_allowed("https://app.example.com") is True
            assert middleware._is_origin_allowed("https://malicious.com") is False
            assert middleware._is_origin_allowed("") is False

    def test_is_origin_allowed_wildcard_match(self):
        """Test origin validation with wildcard pattern."""
        app = FastAPI()

        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.EFFECTIVE_CORS_ORIGINS = ["https://*.example.com"]
            mock_get_settings.return_value = mock_settings

            middleware = CORSSecurityMiddleware(app)

            assert middleware._is_origin_allowed("https://app.example.com") is True
            assert middleware._is_origin_allowed("https://api.example.com") is True
            assert middleware._is_origin_allowed("https://malicious.com") is False

    @pytest.mark.asyncio
    async def test_cors_middleware_preflight_allowed_origin(self):
        """Test CORS middleware with allowed preflight request."""
        app = FastAPI()

        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.EFFECTIVE_CORS_ORIGINS = ["https://example.com"]
            mock_get_settings.return_value = mock_settings

            middleware = CORSSecurityMiddleware(app)

            # Mock preflight request
            mock_request = MagicMock(spec=Request)
            mock_request.method = "OPTIONS"
            mock_request.headers.get.return_value = "https://example.com"

            call_next = AsyncMock()

            result = await middleware.dispatch(mock_request, call_next)

            assert result.status_code == 200
            assert (
                result.headers["Access-Control-Allow-Origin"] == "https://example.com"
            )
            assert result.headers["Access-Control-Allow-Credentials"] == "true"
            assert (
                "GET, POST, PUT, DELETE, PATCH, OPTIONS"
                in result.headers["Access-Control-Allow-Methods"]
            )

            # call_next should not be called for preflight
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_cors_middleware_preflight_forbidden_origin(self):
        """Test CORS middleware with forbidden preflight request."""
        app = FastAPI()

        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.EFFECTIVE_CORS_ORIGINS = ["https://example.com"]
            mock_get_settings.return_value = mock_settings

            middleware = CORSSecurityMiddleware(app)

            # Mock preflight request with unauthorized origin
            mock_request = MagicMock(spec=Request)
            mock_request.method = "OPTIONS"
            mock_request.headers.get.return_value = "https://malicious.com"

            call_next = AsyncMock()

            result = await middleware.dispatch(mock_request, call_next)

            assert result.status_code == 403
            assert "Content-Length" in result.headers

            # call_next should not be called for rejected preflight
            call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_cors_middleware_preflight_no_origin(self):
        """Test CORS middleware with preflight request without origin."""
        app = FastAPI()

        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.EFFECTIVE_CORS_ORIGINS = ["https://example.com"]
            mock_get_settings.return_value = mock_settings

            middleware = CORSSecurityMiddleware(app)

            # Mock preflight request without origin
            mock_request = MagicMock(spec=Request)
            mock_request.method = "OPTIONS"
            mock_request.headers.get.return_value = None

            call_next = AsyncMock()

            result = await middleware.dispatch(mock_request, call_next)

            assert result.status_code == 403

    @pytest.mark.asyncio
    async def test_cors_middleware_actual_request_allowed_origin(self):
        """Test CORS middleware with allowed actual request."""
        app = FastAPI()

        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.EFFECTIVE_CORS_ORIGINS = ["https://example.com"]
            mock_get_settings.return_value = mock_settings

            middleware = CORSSecurityMiddleware(app)

            # Mock actual request
            mock_request = MagicMock(spec=Request)
            mock_request.method = "GET"
            mock_request.headers.get.return_value = "https://example.com"

            # Mock response
            mock_response = MagicMock(spec=Response)
            mock_response.headers = {}
            call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, call_next)

            assert result == mock_response
            assert (
                result.headers["Access-Control-Allow-Origin"] == "https://example.com"
            )
            assert result.headers["Access-Control-Allow-Credentials"] == "true"
            assert result.headers["Vary"] == "Origin"

            call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_cors_middleware_actual_request_forbidden_origin(self):
        """Test CORS middleware with forbidden actual request."""
        app = FastAPI()

        # Mock settings - APPROVED external dependency
        with patch("src.middleware.security.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.EFFECTIVE_CORS_ORIGINS = ["https://example.com"]
            mock_get_settings.return_value = mock_settings

            middleware = CORSSecurityMiddleware(app)

            # Mock actual request with unauthorized origin
            mock_request = MagicMock(spec=Request)
            mock_request.method = "GET"
            mock_request.headers.get.return_value = "https://malicious.com"

            # Mock response
            mock_response = MagicMock(spec=Response)
            mock_response.headers = {}
            call_next = AsyncMock(return_value=mock_response)

            result = await middleware.dispatch(mock_request, call_next)

            assert result == mock_response
            # No CORS headers should be added for unauthorized origin
            assert "Access-Control-Allow-Origin" not in result.headers

            call_next.assert_called_once_with(mock_request)


class TestModuleExports:
    """Test module exports."""

    def test_middleware_exports(self):
        """Test that middleware classes are properly exported."""
        assert security_headers_middleware == SecurityHeadersMiddleware
        assert rate_limit_middleware == RateLimitMiddleware
        assert cors_security_middleware == CORSSecurityMiddleware

    def test_limiter_instance(self):
        """Test that limiter instance is available."""

        assert limiter is not None
        assert hasattr(limiter, "limit")
        assert hasattr(limiter, "key_func")
