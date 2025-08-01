"""Simplified tests for SecurityCenter UI component."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ui_components.security_center import SecurityCenter


class TestSecurityCenterSimple:
    """Simplified test cases for SecurityCenter component."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.security_center = SecurityCenter()

    def test_init(self) -> None:
        """Test SecurityCenter initialization."""
        assert self.security_center.users_data == []
        assert self.security_center.users_table is None
        assert self.security_center.users_container is None
        assert self.security_center.filter_role == "all"
        assert self.security_center.filter_status == "all"
        assert self.security_center.search_query == ""

    def test_search_filter_change(self) -> None:
        """Test search filter changes."""
        with patch.object(self.security_center, '_filter_and_update_table') as mock_filter:
            self.security_center._on_search_change("john")
            assert self.security_center.search_query == "john"
            mock_filter.assert_called_once()

    def test_role_filter_change(self) -> None:
        """Test role filter changes."""
        with patch.object(self.security_center, '_filter_and_update_table') as mock_filter:
            self.security_center._on_role_filter_change("admin_user")
            assert self.security_center.filter_role == "admin_user"
            mock_filter.assert_called_once()

    def test_status_filter_change(self) -> None:
        """Test status filter changes."""
        with patch.object(self.security_center, '_filter_and_update_table') as mock_filter:
            self.security_center._on_status_filter_change("inactive")
            assert self.security_center.filter_status == "inactive"
            mock_filter.assert_called_once()

    def test_filter_logic_search(self) -> None:
        """Test filtering logic for search."""
        self.security_center.users_data = [
            {"username": "john_doe", "role": "common_user", "is_active": True},
            {"username": "jane_admin", "role": "admin_user", "is_active": True},
            {"username": "bob_user", "role": "common_user", "is_active": False},
        ]

        self.security_center.search_query = "john"

        with patch.object(self.security_center, '_update_users_table') as mock_update:
            self.security_center._filter_and_update_table()

            filtered_users = mock_update.call_args[0][0]
            assert len(filtered_users) == 1
            assert filtered_users[0]["username"] == "john_doe"

    def test_filter_logic_role(self) -> None:
        """Test filtering logic for role."""
        self.security_center.users_data = [
            {"username": "john_doe", "role": "common_user", "is_active": True},
            {"username": "jane_admin", "role": "admin_user", "is_active": True},
            {"username": "bob_user", "role": "common_user", "is_active": False},
        ]

        self.security_center.filter_role = "admin_user"

        with patch.object(self.security_center, '_update_users_table') as mock_update:
            self.security_center._filter_and_update_table()

            filtered_users = mock_update.call_args[0][0]
            assert len(filtered_users) == 1
            assert filtered_users[0]["role"] == "admin_user"

    def test_filter_logic_status(self) -> None:
        """Test filtering logic for status."""
        self.security_center.users_data = [
            {"username": "john_doe", "role": "common_user", "is_active": True},
            {"username": "jane_admin", "role": "admin_user", "is_active": True},
            {"username": "bob_inactive", "role": "common_user", "is_active": False},
        ]

        self.security_center.filter_status = "active"

        with patch.object(self.security_center, '_update_users_table') as mock_update:
            self.security_center._filter_and_update_table()

            filtered_users = mock_update.call_args[0][0]
            assert len(filtered_users) == 2
            assert all(user["is_active"] for user in filtered_users)

    @patch('app.ui_components.security_center.config')
    @patch('app.ui_components.security_center.ui.notify')
    @patch('app.ui_components.security_center.requests.post')
    def test_create_user_success(self, mock_post, mock_notify, mock_config) -> None:
        """Test successful user creation."""
        mock_config.get_api_endpoint.return_value = "/api/admin/users"
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": "new-user-id"}

        mock_dialog = MagicMock()

        with patch.object(self.security_center, '_refresh_users_data'):
            self.security_center._create_user(
                mock_dialog, "newuser", "password123", "password123", "common_user", False
            )

            mock_post.assert_called_once()
            mock_dialog.close.assert_called_once()

    @patch('app.ui_components.security_center.ui.notify')
    def test_create_user_validation_empty_username(self, mock_notify) -> None:
        """Test user creation validation for empty username."""
        mock_dialog = MagicMock()

        self.security_center._create_user(
            mock_dialog, "", "password", "password", "common_user", False
        )

        mock_dialog.close.assert_not_called()
        mock_notify.assert_called_with("Nome de usuário e senha são obrigatórios", type="negative")

    @patch('app.ui_components.security_center.ui.notify')
    def test_create_user_validation_password_mismatch(self, mock_notify) -> None:
        """Test user creation validation for password mismatch."""
        mock_dialog = MagicMock()

        self.security_center._create_user(
            mock_dialog, "user", "pass1", "pass2", "common_user", False
        )

        mock_dialog.close.assert_not_called()
        mock_notify.assert_called_with("Senhas não coincidem", type="negative")

    @patch('app.ui_components.security_center.ui.notify')
    def test_create_user_validation_short_password(self, mock_notify) -> None:
        """Test user creation validation for short password."""
        mock_dialog = MagicMock()

        self.security_center._create_user(
            mock_dialog, "user", "123", "123", "common_user", False
        )

        mock_dialog.close.assert_not_called()
        mock_notify.assert_called_with("Senha deve ter pelo menos 6 caracteres", type="negative")

    @patch('app.ui_components.security_center.config')
    @patch('app.ui_components.security_center.requests.get')
    def test_load_users_data_success(self, mock_get, mock_config) -> None:
        """Test successful loading of users data."""
        mock_config.get_api_endpoint.return_value = "/api/admin/users"
        mock_users_data = [
            {"id": "1", "username": "user1", "role": "common_user"},
            {"id": "2", "username": "user2", "role": "admin_user"},
        ]
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_users_data

        with patch.object(self.security_center, '_filter_and_update_table') as mock_filter:
            self.security_center._load_users_data()

            assert self.security_center.users_data == mock_users_data
            mock_filter.assert_called_once()

    @patch('app.ui_components.security_center.config')
    @patch('app.ui_components.security_center.ui.notify')
    @patch('app.ui_components.security_center.requests.get')
    def test_load_users_data_error(self, mock_get, mock_notify, mock_config) -> None:
        """Test error handling in users data loading."""
        mock_config.get_api_endpoint.return_value = "/api/admin/users"
        mock_get.side_effect = Exception("Connection error")

        self.security_center._load_users_data()

        assert self.security_center.users_data == []
        mock_notify.assert_called_with("Erro de conexão com API: Connection error", type="negative")

    def test_refresh_users_data(self) -> None:
        """Test refresh users data functionality."""
        with patch.object(self.security_center, '_load_users_data') as mock_load:
            self.security_center._refresh_users_data()
            mock_load.assert_called_once()
