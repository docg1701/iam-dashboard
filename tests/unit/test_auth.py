"""Unit tests for AuthManager."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from app.core.auth import AuthManager


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
        with patch('app.core.auth.ACCESS_TOKEN_EXPIRE_MINUTES', -1):  # Force expiration
            user_id = "123e4567-e89b-12d3-a456-426614174000"
            username = "testuser"

            # Create expired token
            token = AuthManager.create_access_token(user_id, username)

            # Verify expired token
            payload = AuthManager.verify_token(token)

            assert payload is None

    @patch('app.core.auth.app')
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

    @patch('app.core.auth.app')
    def test_logout_user(self, mock_app) -> None:
        """Test user logout."""
        mock_storage = MagicMock()
        mock_app.storage.user = mock_storage

        AuthManager.logout_user()

        mock_storage.clear.assert_called_once()

    @patch('app.core.auth.app')
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
            "login_time": login_time
        }.get(key, default)
        mock_app.storage.user = mock_storage

        current_user = AuthManager.get_current_user()

        assert current_user is not None
        assert current_user["user_id"] == user_id
        assert current_user["username"] == username
        assert current_user["login_time"] == login_time

    @patch('app.core.auth.app')
    def test_get_current_user_not_authenticated(self, mock_app) -> None:
        """Test getting current user when not authenticated."""
        mock_storage = MagicMock()
        mock_storage.get.return_value = False  # Not authenticated
        mock_app.storage.user = mock_storage

        current_user = AuthManager.get_current_user()

        assert current_user is None

    @patch('app.core.auth.app')
    def test_get_current_user_invalid_token(self, mock_app) -> None:
        """Test getting current user with invalid token."""
        mock_storage = MagicMock()
        mock_storage.get.side_effect = lambda key: {
            "authenticated": True,
            "token": "invalid.token.here"
        }.get(key)
        mock_app.storage.user = mock_storage

        current_user = AuthManager.get_current_user()

        assert current_user is None
        # Should clear session when token is invalid
        mock_storage.clear.assert_called_once()

    @patch('app.core.auth.AuthManager.get_current_user')
    def test_is_authenticated_true(self, mock_get_current_user) -> None:
        """Test is_authenticated when user is authenticated."""
        mock_get_current_user.return_value = {"user_id": "123", "username": "test"}

        is_auth = AuthManager.is_authenticated()

        assert is_auth is True

    @patch('app.core.auth.AuthManager.get_current_user')
    def test_is_authenticated_false(self, mock_get_current_user) -> None:
        """Test is_authenticated when user is not authenticated."""
        mock_get_current_user.return_value = None

        is_auth = AuthManager.is_authenticated()

        assert is_auth is False
