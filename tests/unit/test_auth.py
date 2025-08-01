"""Unit tests for AuthManager."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.core.auth import AuthManager
from app.models.user import UserRole


class TestAuthManager:
    """Test cases for AuthManager."""

    def test_create_access_token(self) -> None:
        """Test JWT token creation."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        username = "testuser"

        token = AuthManager.create_access_token(user_id, username)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self) -> None:
        """Test JWT token verification with valid token."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        username = "testuser"

        # Create token
        token = AuthManager.create_access_token(user_id, username)

        # Verify token
        payload = AuthManager.verify_token(token)

        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["username"] == username

    def test_verify_token_invalid(self) -> None:
        """Test JWT token verification with invalid token."""
        invalid_token = "invalid.token.here"

        payload = AuthManager.verify_token(invalid_token)

        assert payload is None

    def test_verify_token_expired(self) -> None:
        """Test JWT token verification with expired token."""
        with patch("app.core.auth.ACCESS_TOKEN_EXPIRE_MINUTES", -1):  # Force expiration
            user_id = "123e4567-e89b-12d3-a456-426614174000"
            username = "testuser"

            # Create expired token
            token = AuthManager.create_access_token(user_id, username)

            # Verify expired token
            payload = AuthManager.verify_token(token)

            assert payload is None

    @patch("app.core.auth.app")
    def test_login_user(self, mock_app) -> None:
        """Test user login."""
        mock_storage = MagicMock()
        mock_app.storage.user = mock_storage

        user_id = "123e4567-e89b-12d3-a456-426614174000"
        username = "testuser"

        token = AuthManager.login_user(user_id, username)

        assert token is not None
        mock_storage.update.assert_called_once()

        # Check that the update was called with correct data
        update_call = mock_storage.update.call_args[0][0]
        assert update_call["authenticated"] is True
        assert update_call["user_id"] == user_id
        assert update_call["username"] == username
        assert update_call["token"] == token
        assert "login_time" in update_call

    @patch("app.core.auth.app")
    def test_logout_user(self, mock_app) -> None:
        """Test user logout."""
        mock_storage = MagicMock()
        mock_app.storage.user = mock_storage

        AuthManager.logout_user()

        mock_storage.clear.assert_called_once()

    @patch("app.core.auth.app")
    def test_get_current_user_authenticated(self, mock_app) -> None:
        """Test getting current user when authenticated."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        username = "testuser"
        login_time = datetime.utcnow().isoformat()

        # Create valid token
        token = AuthManager.create_access_token(user_id, username)

        mock_storage = MagicMock()
        mock_storage.get.side_effect = lambda key, default=None: {
            "authenticated": True,
            "user_id": user_id,
            "username": username,
            "token": token,
            "login_time": login_time,
        }.get(key, default)
        mock_app.storage.user = mock_storage

        current_user = AuthManager.get_current_user()

        assert current_user is not None
        assert current_user["user_id"] == user_id
        assert current_user["username"] == username
        assert current_user["login_time"] == login_time

    @patch("app.core.auth.app")
    def test_get_current_user_not_authenticated(self, mock_app) -> None:
        """Test getting current user when not authenticated."""
        mock_storage = MagicMock()
        mock_storage.get.return_value = False  # Not authenticated
        mock_app.storage.user = mock_storage

        current_user = AuthManager.get_current_user()

        assert current_user is None

    @patch("app.core.auth.app")
    def test_get_current_user_invalid_token(self, mock_app) -> None:
        """Test getting current user with invalid token."""
        mock_storage = MagicMock()
        mock_storage.get.side_effect = lambda key: {
            "authenticated": True,
            "token": "invalid.token.here",
        }.get(key)
        mock_app.storage.user = mock_storage

        current_user = AuthManager.get_current_user()

        assert current_user is None
        # Should clear session when token is invalid
        mock_storage.clear.assert_called_once()

    @patch("app.core.auth.AuthManager.get_current_user")
    def test_is_authenticated_true(self, mock_get_current_user) -> None:
        """Test is_authenticated when user is authenticated."""
        mock_get_current_user.return_value = {"user_id": "123", "username": "test"}

        is_auth = AuthManager.is_authenticated()

        assert is_auth is True

    @patch("app.core.auth.AuthManager.get_current_user")
    def test_is_authenticated_false(self, mock_get_current_user) -> None:
        """Test is_authenticated when user is not authenticated."""
        mock_get_current_user.return_value = None

        is_auth = AuthManager.is_authenticated()

        assert is_auth is False

    def test_get_user_role_with_string_value(self) -> None:
        """Test getting user role from string value."""
        current_user = {"role": "sysadmin"}

        role = AuthManager.get_user_role(current_user)

        assert role == UserRole.SYSADMIN

    def test_get_user_role_with_enum(self) -> None:
        """Test getting user role from enum value."""
        current_user = {"role": UserRole.ADMIN_USER}

        role = AuthManager.get_user_role(current_user)

        assert role == UserRole.ADMIN_USER

    def test_get_user_role_invalid(self) -> None:
        """Test getting user role with invalid role."""
        current_user = {"role": "invalid_role"}

        role = AuthManager.get_user_role(current_user)

        assert role is None

    def test_get_user_role_no_role(self) -> None:
        """Test getting user role when no role is provided."""
        current_user = {}

        role = AuthManager.get_user_role(current_user)

        assert role is None

    def test_get_user_role_no_user(self) -> None:
        """Test getting user role when no user is provided."""
        role = AuthManager.get_user_role(None)

        assert role is None

    def test_check_permission_sysadmin_full_access(self) -> None:
        """Test SYSADMIN has full permissions."""
        current_user = {"role": "sysadmin"}

        # Test all permissions for SYSADMIN
        assert AuthManager.check_permission(current_user, "agent_management", "create") is True
        assert AuthManager.check_permission(current_user, "agent_management", "delete") is True
        assert AuthManager.check_permission(current_user, "user_management", "create") is True
        assert AuthManager.check_permission(current_user, "admin_panel", "full_access") is True
        assert AuthManager.check_permission(current_user, "system_admin", "full_access") is True

    def test_check_permission_admin_user_limited(self) -> None:
        """Test ADMIN_USER has limited permissions."""
        current_user = {"role": "admin_user"}

        # Test allowed permissions for ADMIN_USER
        assert AuthManager.check_permission(current_user, "agent_management", "execute") is True
        assert AuthManager.check_permission(current_user, "agent_management", "monitor") is True
        assert AuthManager.check_permission(current_user, "user_management", "read") is True
        assert AuthManager.check_permission(current_user, "admin_panel", "limited_access") is True

        # Test denied permissions for ADMIN_USER
        assert AuthManager.check_permission(current_user, "agent_management", "create") is False
        assert AuthManager.check_permission(current_user, "agent_management", "delete") is False
        assert AuthManager.check_permission(current_user, "user_management", "create") is False
        assert AuthManager.check_permission(current_user, "system_admin", "full_access") is False

    def test_check_permission_common_user_minimal(self) -> None:
        """Test COMMON_USER has minimal permissions."""
        current_user = {"role": "common_user"}

        # Test allowed permissions for COMMON_USER
        assert AuthManager.check_permission(current_user, "agent_management", "execute") is True

        # Test denied permissions for COMMON_USER
        assert AuthManager.check_permission(current_user, "agent_management", "create") is False
        assert AuthManager.check_permission(current_user, "agent_management", "delete") is False
        assert AuthManager.check_permission(current_user, "user_management", "read") is False
        assert AuthManager.check_permission(current_user, "admin_panel", "limited_access") is False

    def test_check_permission_no_user(self) -> None:
        """Test permission check with no user."""
        assert AuthManager.check_permission(None, "agent_management", "execute") is False

    def test_check_endpoint_access_admin_routes(self) -> None:
        """Test endpoint access for admin routes."""
        sysadmin_user = {"role": "sysadmin"}
        admin_user = {"role": "admin_user"}
        common_user = {"role": "common_user"}

        # Test /admin endpoint (SYSADMIN only)
        assert AuthManager.check_endpoint_access(sysadmin_user, "/admin") is True
        assert AuthManager.check_endpoint_access(admin_user, "/admin") is False
        assert AuthManager.check_endpoint_access(common_user, "/admin") is False

        # Test /admin/agents endpoint (SYSADMIN and ADMIN_USER)
        assert AuthManager.check_endpoint_access(sysadmin_user, "/admin/agents") is True
        assert AuthManager.check_endpoint_access(admin_user, "/admin/agents") is True
        assert AuthManager.check_endpoint_access(common_user, "/admin/agents") is False

    def test_has_admin_access(self) -> None:
        """Test admin access checking."""
        sysadmin_user = {"role": "sysadmin"}
        admin_user = {"role": "admin_user"}
        common_user = {"role": "common_user"}

        assert AuthManager.has_admin_access(sysadmin_user) is True
        assert AuthManager.has_admin_access(admin_user) is True
        assert AuthManager.has_admin_access(common_user) is False
        assert AuthManager.has_admin_access(None) is False

    def test_is_sysadmin(self) -> None:
        """Test system admin checking."""
        sysadmin_user = {"role": "sysadmin"}
        admin_user = {"role": "admin_user"}
        common_user = {"role": "common_user"}

        assert AuthManager.is_sysadmin(sysadmin_user) is True
        assert AuthManager.is_sysadmin(admin_user) is False
        assert AuthManager.is_sysadmin(common_user) is False
        assert AuthManager.is_sysadmin(None) is False

    @patch("app.core.auth.app")
    def test_login_user_with_role_enum(self, mock_app) -> None:
        """Test user login with UserRole enum."""
        mock_storage = MagicMock()
        mock_app.storage.user = mock_storage

        user_id = "123e4567-e89b-12d3-a456-426614174000"
        username = "testuser"
        role = UserRole.SYSADMIN

        token = AuthManager.login_user(user_id, username, role)

        assert token is not None
        mock_storage.update.assert_called_once()

        # Check that the role was stored as string value
        update_call = mock_storage.update.call_args[0][0]
        assert update_call["role"] == "sysadmin"

    @patch("app.core.auth.app")
    def test_login_user_with_role_string(self, mock_app) -> None:
        """Test user login with role as string."""
        mock_storage = MagicMock()
        mock_app.storage.user = mock_storage

        user_id = "123e4567-e89b-12d3-a456-426614174000"
        username = "testuser"
        role = "admin_user"

        token = AuthManager.login_user(user_id, username, role)

        assert token is not None
        mock_storage.update.assert_called_once()

        # Check that the role was stored correctly
        update_call = mock_storage.update.call_args[0][0]
        assert update_call["role"] == "admin_user"


class TestAuthorizationDecorators:
    """Test cases for authorization decorators."""

    def test_require_permission_decorator_success(self) -> None:
        """Test require_permission decorator with sufficient permissions."""
        @AuthManager.require_permission("agent_management", "execute")
        def test_function():
            return "success"

        with patch.object(AuthManager, 'get_current_user') as mock_get_user, \
             patch.object(AuthManager, 'check_permission') as mock_check_perm:

            mock_get_user.return_value = {"role": "sysadmin"}
            mock_check_perm.return_value = True

            result = test_function()

            assert result == "success"
            mock_check_perm.assert_called_once()

    def test_require_permission_decorator_failure(self) -> None:
        """Test require_permission decorator with insufficient permissions."""
        @AuthManager.require_permission("agent_management", "create")
        def test_function():
            return "success"

        with patch.object(AuthManager, 'get_current_user') as mock_get_user, \
             patch.object(AuthManager, 'check_permission') as mock_check_perm:

            mock_get_user.return_value = {"role": "common_user"}
            mock_check_perm.return_value = False

            with pytest.raises(Exception):  # HTTPException from decorator
                test_function()

    def test_require_admin_decorator_success(self) -> None:
        """Test require_admin decorator with admin user."""
        @AuthManager.require_admin()
        def test_function():
            return "success"

        with patch.object(AuthManager, 'get_current_user') as mock_get_user, \
             patch.object(AuthManager, 'has_admin_access') as mock_has_admin:

            mock_get_user.return_value = {"role": "sysadmin"}
            mock_has_admin.return_value = True

            result = test_function()

            assert result == "success"
            mock_has_admin.assert_called_once()

    def test_require_admin_decorator_failure(self) -> None:
        """Test require_admin decorator with non-admin user."""
        @AuthManager.require_admin()
        def test_function():
            return "success"

        with patch.object(AuthManager, 'get_current_user') as mock_get_user, \
             patch.object(AuthManager, 'has_admin_access') as mock_has_admin:

            mock_get_user.return_value = {"role": "common_user"}
            mock_has_admin.return_value = False

            with pytest.raises(Exception):  # HTTPException from decorator
                test_function()
