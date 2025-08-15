"""
Comprehensive Cookie Utils tests to improve coverage from 0% to full coverage.
Following CLAUDE.md guidelines: Never mock internal business logic.
Mock only external dependencies (settings, datetime, request/response objects).
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.utils.cookie_utils import (
    CookieConfig,
    SecureCookieManager,
    cookie_manager,
    get_cookie_manager,
)


class TestSecureCookieManager:
    """Test SecureCookieManager functionality."""

    def test_secure_cookie_manager_initialization(self):
        """Test SecureCookieManager initialization."""
        manager = SecureCookieManager()

        assert manager.settings is not None

    def test_set_auth_cookies_with_default_expiration(self):
        """Test setting auth cookies with default expiration."""
        manager = SecureCookieManager()
        mock_response = MagicMock(spec=Response)

        access_token = "access.jwt.token"
        refresh_token = "refresh.jwt.token"

        # Mock datetime - APPROVED external dependency
        with patch("src.utils.cookie_utils.datetime") as mock_datetime:
            mock_now = datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            manager.set_auth_cookies(mock_response, access_token, refresh_token)

            # Verify set_cookie was called twice (access and refresh tokens)
            assert mock_response.set_cookie.call_count == 2

            # Verify access token cookie
            access_call = mock_response.set_cookie.call_args_list[0]
            access_args, access_kwargs = access_call
            assert access_kwargs["key"] == "access_token"
            assert access_kwargs["value"] == f"Bearer {access_token}"
            assert access_kwargs["path"] == "/"

            # Verify refresh token cookie
            refresh_call = mock_response.set_cookie.call_args_list[1]
            refresh_args, refresh_kwargs = refresh_call
            assert refresh_kwargs["key"] == "refresh_token"
            assert refresh_kwargs["value"] == f"Bearer {refresh_token}"
            assert refresh_kwargs["path"] == "/"

    def test_set_auth_cookies_with_custom_expiration(self):
        """Test setting auth cookies with custom expiration."""
        manager = SecureCookieManager()
        mock_response = MagicMock(spec=Response)

        access_token = "access.jwt.token"
        refresh_token = "refresh.jwt.token"
        custom_expires = datetime(2025, 1, 2, 12, 0, 0)

        # Mock datetime - APPROVED external dependency
        with patch("src.utils.cookie_utils.datetime") as mock_datetime:
            mock_now = datetime(2025, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now

            manager.set_auth_cookies(
                mock_response, access_token, refresh_token, expires_at=custom_expires
            )

            # Verify set_cookie was called twice
            assert mock_response.set_cookie.call_count == 2

            # Verify access token cookie uses custom expiration
            access_call = mock_response.set_cookie.call_args_list[0]
            access_args, access_kwargs = access_call
            assert access_kwargs["expires"] == custom_expires

    def test_set_auth_cookies_production_settings(self):
        """Test setting auth cookies with production settings."""
        manager = SecureCookieManager()
        mock_response = MagicMock(spec=Response)

        access_token = "access.jwt.token"
        refresh_token = "refresh.jwt.token"

        # Mock settings for production - APPROVED external dependency
        with patch.object(manager, "settings") as mock_settings:
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
            mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
            mock_settings.SESSION_COOKIE_HTTPONLY = True
            mock_settings.SESSION_COOKIE_SECURE = True
            mock_settings.SESSION_COOKIE_SAMESITE = "strict"
            mock_settings.COOKIE_DOMAIN = "example.com"
            mock_settings.DEBUG = False

            # Mock datetime - APPROVED external dependency
            with patch("src.utils.cookie_utils.datetime") as mock_datetime:
                mock_now = datetime(2025, 1, 1, 12, 0, 0)
                mock_datetime.now.return_value = mock_now

                manager.set_auth_cookies(mock_response, access_token, refresh_token)

                # Verify production security settings
                access_call = mock_response.set_cookie.call_args_list[0]
                access_args, access_kwargs = access_call
                assert access_kwargs["httponly"] is True
                assert access_kwargs["secure"] is True
                assert access_kwargs["samesite"] == "strict"
                assert access_kwargs["domain"] == "example.com"

    def test_set_auth_cookies_debug_settings(self):
        """Test setting auth cookies with debug/development settings."""
        manager = SecureCookieManager()
        mock_response = MagicMock(spec=Response)

        access_token = "access.jwt.token"
        refresh_token = "refresh.jwt.token"

        # Mock settings for debug mode - APPROVED external dependency
        with patch.object(manager, "settings") as mock_settings:
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
            mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
            mock_settings.SESSION_COOKIE_HTTPONLY = True
            mock_settings.SESSION_COOKIE_SECURE = True
            mock_settings.SESSION_COOKIE_SAMESITE = "lax"
            mock_settings.COOKIE_DOMAIN = "localhost"
            mock_settings.DEBUG = True  # Debug mode

            # Mock datetime - APPROVED external dependency
            with patch("src.utils.cookie_utils.datetime") as mock_datetime:
                mock_now = datetime(2025, 1, 1, 12, 0, 0)
                mock_datetime.now.return_value = mock_now

                manager.set_auth_cookies(mock_response, access_token, refresh_token)

                # Verify debug settings (secure should be False, domain should be None)
                access_call = mock_response.set_cookie.call_args_list[0]
                access_args, access_kwargs = access_call
                assert access_kwargs["secure"] is False
                assert access_kwargs["domain"] is None

    def test_clear_auth_cookies(self):
        """Test clearing authentication cookies."""
        manager = SecureCookieManager()
        mock_response = MagicMock(spec=Response)

        # Mock settings - APPROVED external dependency
        with patch.object(manager, "settings") as mock_settings:
            mock_settings.SESSION_COOKIE_HTTPONLY = True
            mock_settings.SESSION_COOKIE_SECURE = True
            mock_settings.SESSION_COOKIE_SAMESITE = "strict"
            mock_settings.COOKIE_DOMAIN = "example.com"
            mock_settings.DEBUG = False

            manager.clear_auth_cookies(mock_response)

            # Verify set_cookie was called twice (access and refresh tokens)
            assert mock_response.set_cookie.call_count == 2

            # Verify access token cookie is cleared
            access_call = mock_response.set_cookie.call_args_list[0]
            access_args, access_kwargs = access_call
            assert access_kwargs["key"] == "access_token"
            assert access_kwargs["value"] == ""
            assert access_kwargs["max_age"] == 0
            assert access_kwargs["expires"] == datetime(1970, 1, 1)

            # Verify refresh token cookie is cleared
            refresh_call = mock_response.set_cookie.call_args_list[1]
            refresh_args, refresh_kwargs = refresh_call
            assert refresh_kwargs["key"] == "refresh_token"
            assert refresh_kwargs["value"] == ""
            assert refresh_kwargs["max_age"] == 0
            assert refresh_kwargs["expires"] == datetime(1970, 1, 1)

    def test_get_token_from_cookies_with_valid_token(self):
        """Test extracting access token from cookies."""
        manager = SecureCookieManager()
        mock_request = MagicMock(spec=Request)
        mock_request.cookies.get.return_value = "Bearer valid.access.token"

        result = manager.get_token_from_cookies(mock_request)

        assert result == "valid.access.token"
        mock_request.cookies.get.assert_called_once_with("access_token")

    def test_get_token_from_cookies_with_invalid_format(self):
        """Test extracting access token from cookies with invalid format."""
        manager = SecureCookieManager()
        mock_request = MagicMock(spec=Request)
        mock_request.cookies.get.return_value = "InvalidFormat token"

        result = manager.get_token_from_cookies(mock_request)

        assert result is None

    def test_get_token_from_cookies_with_no_cookie(self):
        """Test extracting access token when no cookie exists."""
        manager = SecureCookieManager()
        mock_request = MagicMock(spec=Request)
        mock_request.cookies.get.return_value = None

        result = manager.get_token_from_cookies(mock_request)

        assert result is None

    def test_get_refresh_token_from_cookies_with_valid_token(self):
        """Test extracting refresh token from cookies."""
        manager = SecureCookieManager()
        mock_request = MagicMock(spec=Request)
        mock_request.cookies.get.return_value = "Bearer valid.refresh.token"

        result = manager.get_refresh_token_from_cookies(mock_request)

        assert result == "valid.refresh.token"
        mock_request.cookies.get.assert_called_once_with("refresh_token")

    def test_get_refresh_token_from_cookies_with_invalid_format(self):
        """Test extracting refresh token from cookies with invalid format."""
        manager = SecureCookieManager()
        mock_request = MagicMock(spec=Request)
        mock_request.cookies.get.return_value = "InvalidFormat token"

        result = manager.get_refresh_token_from_cookies(mock_request)

        assert result is None

    def test_get_refresh_token_from_cookies_with_no_cookie(self):
        """Test extracting refresh token when no cookie exists."""
        manager = SecureCookieManager()
        mock_request = MagicMock(spec=Request)
        mock_request.cookies.get.return_value = None

        result = manager.get_refresh_token_from_cookies(mock_request)

        assert result is None

    def test_create_secure_response_basic(self):
        """Test creating secure response without tokens."""
        manager = SecureCookieManager()

        content = {"message": "success", "data": {"id": 1}}

        response = manager.create_secure_response(content, status_code=200)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 200

        # Verify security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert (
            response.headers["Cache-Control"]
            == "no-store, no-cache, must-revalidate, private"
        )
        assert response.headers["Pragma"] == "no-cache"
        assert response.headers["Expires"] == "0"

    def test_create_secure_response_with_tokens(self):
        """Test creating secure response with authentication tokens."""
        manager = SecureCookieManager()

        content = {"message": "login success"}
        access_token = "access.jwt.token"
        refresh_token = "refresh.jwt.token"

        # Mock the set_auth_cookies method
        with patch.object(manager, "set_auth_cookies") as mock_set_cookies:
            response = manager.create_secure_response(
                content,
                status_code=200,
                access_token=access_token,
                refresh_token=refresh_token,
            )

            assert isinstance(response, JSONResponse)
            assert response.status_code == 200

            # Verify set_auth_cookies was called
            mock_set_cookies.assert_called_once_with(
                response, access_token, refresh_token
            )

    def test_create_secure_response_custom_status_code(self):
        """Test creating secure response with custom status code."""
        manager = SecureCookieManager()

        content = {"error": "bad request"}

        response = manager.create_secure_response(content, status_code=400)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400


class TestGlobalFunctions:
    """Test global module functions."""

    def test_get_cookie_manager(self):
        """Test get_cookie_manager returns global instance."""
        result = get_cookie_manager()

        assert isinstance(result, SecureCookieManager)
        assert result == cookie_manager

    def test_cookie_manager_is_singleton(self):
        """Test cookie_manager is a singleton instance."""
        manager1 = get_cookie_manager()
        manager2 = get_cookie_manager()

        assert manager1 is manager2
        assert manager1 is cookie_manager


class TestCookieConfig:
    """Test CookieConfig validation functionality."""

    def test_validate_production_config_secure_setup(self):
        """Test production config validation with secure setup."""
        # Mock settings for secure production - APPROVED external dependency
        with patch("src.utils.cookie_utils.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.DEBUG = False
            mock_settings.SESSION_COOKIE_SECURE = True
            mock_settings.SESSION_COOKIE_HTTPONLY = True
            mock_settings.SESSION_COOKIE_SAMESITE = "strict"
            mock_settings.COOKIE_DOMAIN = "example.com"
            mock_get_settings.return_value = mock_settings

            result = CookieConfig.validate_production_config()

            assert result["valid"] is True
            assert len(result["issues"]) == 0
            assert len(result["recommendations"]) == 0
            assert result["current_config"]["secure"] is True
            assert result["current_config"]["httponly"] is True
            assert result["current_config"]["samesite"] == "strict"
            assert result["current_config"]["domain"] == "example.com"
            assert result["current_config"]["debug_mode"] is False

    def test_validate_production_config_insecure_setup(self):
        """Test production config validation with insecure setup."""
        # Mock settings for insecure production - APPROVED external dependency
        with patch("src.utils.cookie_utils.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.DEBUG = False
            mock_settings.SESSION_COOKIE_SECURE = False  # Insecure
            mock_settings.SESSION_COOKIE_HTTPONLY = False  # Insecure
            mock_settings.SESSION_COOKIE_SAMESITE = "invalid"  # Invalid
            mock_settings.COOKIE_DOMAIN = None
            mock_get_settings.return_value = mock_settings

            result = CookieConfig.validate_production_config()

            assert result["valid"] is False
            assert len(result["issues"]) == 3
            assert (
                "SESSION_COOKIE_SECURE should be True in production" in result["issues"]
            )
            assert (
                "SESSION_COOKIE_HTTPONLY should be True for security"
                in result["issues"]
            )
            assert "Invalid SESSION_COOKIE_SAMESITE: invalid" in result["issues"]

            assert (
                len(result["recommendations"]) == 4
            )  # 3 issues + 1 domain recommendation
            assert (
                "Set SESSION_COOKIE_SECURE=true in production environment"
                in result["recommendations"]
            )
            assert (
                "Set SESSION_COOKIE_HTTPONLY=true to prevent XSS attacks"
                in result["recommendations"]
            )
            assert (
                "Set SESSION_COOKIE_SAMESITE to 'strict', 'lax', or 'none'"
                in result["recommendations"]
            )
            assert (
                "Consider setting COOKIE_DOMAIN for production deployment"
                in result["recommendations"]
            )

    def test_validate_production_config_debug_mode(self):
        """Test production config validation in debug mode."""
        # Mock settings for debug mode - APPROVED external dependency
        with patch("src.utils.cookie_utils.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.DEBUG = True  # Debug mode
            mock_settings.SESSION_COOKIE_SECURE = False  # Acceptable in debug
            mock_settings.SESSION_COOKIE_HTTPONLY = True
            mock_settings.SESSION_COOKIE_SAMESITE = "lax"
            mock_settings.COOKIE_DOMAIN = None
            mock_get_settings.return_value = mock_settings

            result = CookieConfig.validate_production_config()

            # In debug mode, secure=False is acceptable
            assert result["valid"] is True
            assert len(result["issues"]) == 0
            assert result["current_config"]["debug_mode"] is True

    def test_validate_production_config_valid_samesite_values(self):
        """Test production config validation with various valid SameSite values."""
        valid_samesite_values = ["strict", "lax", "none", "STRICT", "LAX", "NONE"]

        for samesite_value in valid_samesite_values:
            # Mock settings - APPROVED external dependency
            with patch("src.utils.cookie_utils.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.DEBUG = False
                mock_settings.SESSION_COOKIE_SECURE = True
                mock_settings.SESSION_COOKIE_HTTPONLY = True
                mock_settings.SESSION_COOKIE_SAMESITE = samesite_value
                mock_settings.COOKIE_DOMAIN = "example.com"
                mock_get_settings.return_value = mock_settings

                result = CookieConfig.validate_production_config()

                # Should not have SameSite issues
                samesite_issues = [
                    issue
                    for issue in result["issues"]
                    if "SESSION_COOKIE_SAMESITE" in issue
                ]
                assert len(samesite_issues) == 0


class TestModuleExports:
    """Test module exports and structure."""

    def test_module_exports_all(self):
        """Test that __all__ contains expected exports."""
        from src.utils.cookie_utils import __all__

        expected_exports = [
            "SecureCookieManager",
            "cookie_manager",
            "get_cookie_manager",
            "CookieConfig",
        ]

        assert __all__ == expected_exports

    def test_global_cookie_manager_instance(self):
        """Test that global cookie_manager instance exists."""
        from src.utils.cookie_utils import cookie_manager

        assert isinstance(cookie_manager, SecureCookieManager)
