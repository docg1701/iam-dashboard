"""Tests for SecurityCenter UI component."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from nicegui import ui

from app.ui_components.security_center import SecurityCenter


class TestSecurityCenter:
    """Test cases for SecurityCenter component."""

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

    @patch('app.ui_components.security_center.AuthManager')
    @patch('asyncio.create_task')
    def test_create_ui_structure(self, mock_create_task, mock_auth_manager) -> None:
        """Test that the create method builds the correct UI structure."""
        mock_auth_manager.get_current_user.return_value = {"id": "test-user-id"}
        mock_create_task.return_value = MagicMock()

        with ui.column():  # Create container for test
            self.security_center.create()

        # Verify asyncio.create_task was called for loading data
        mock_create_task.assert_called_once()

    def test_search_filter_functionality(self) -> None:
        """Test search filtering functionality."""
        # Set up test data
        self.security_center.users_data = [
            {"username": "john_doe", "role": "common_user", "is_active": True},
            {"username": "jane_admin", "role": "admin_user", "is_active": True},
            {"username": "bob_inactive", "role": "common_user", "is_active": False},
        ]

        # Mock the container and filter method
        mock_container = MagicMock()
        self.security_center.users_container = mock_container

        with patch.object(self.security_center, '_filter_and_update_table') as mock_filter:
            self.security_center._on_search_change("john")
            assert self.security_center.search_query == "john"
            mock_filter.assert_called_once()

    def test_role_filter_functionality(self) -> None:
        """Test role filtering functionality."""
        mock_container = MagicMock()
        self.security_center.users_container = mock_container

        with patch.object(self.security_center, '_filter_and_update_table') as mock_filter:
            self.security_center._on_role_filter_change("admin_user")
            assert self.security_center.filter_role == "admin_user"
            mock_filter.assert_called_once()

    def test_status_filter_functionality(self) -> None:
        """Test status filtering functionality."""
        mock_container = MagicMock()
        self.security_center.users_container = mock_container

        with patch.object(self.security_center, '_filter_and_update_table') as mock_filter:
            self.security_center._on_status_filter_change("inactive")
            assert self.security_center.filter_status == "inactive"
            mock_filter.assert_called_once()

    def test_filter_and_update_table_search(self) -> None:
        """Test filtering users by search query."""
        # Set up test data
        self.security_center.users_data = [
            {"username": "john_doe", "role": "common_user", "is_active": True},
            {"username": "jane_admin", "role": "admin_user", "is_active": True},
            {"username": "bob_user", "role": "common_user", "is_active": False},
        ]

        # Create mock container
        mock_container = MagicMock()
        self.security_center.users_container = mock_container

        # Test search filter
        self.security_center.search_query = "john"

        with patch.object(self.security_center, '_update_users_table') as mock_update:
            self.security_center._filter_and_update_table()

            # Should only pass users matching "john"
            mock_update.assert_called_once()
            filtered_users = mock_update.call_args[0][0]
            assert len(filtered_users) == 1
            assert filtered_users[0]["username"] == "john_doe"

    def test_filter_and_update_table_role(self) -> None:
        """Test filtering users by role."""
        # Set up test data
        self.security_center.users_data = [
            {"username": "john_doe", "role": "common_user", "is_active": True},
            {"username": "jane_admin", "role": "admin_user", "is_active": True},
            {"username": "bob_user", "role": "common_user", "is_active": False},
        ]

        # Create mock container
        mock_container = MagicMock()
        self.security_center.users_container = mock_container

        # Test role filter
        self.security_center.filter_role = "admin_user"

        with patch.object(self.security_center, '_update_users_table') as mock_update:
            self.security_center._filter_and_update_table()

            # Should only pass admin users
            mock_update.assert_called_once()
            filtered_users = mock_update.call_args[0][0]
            assert len(filtered_users) == 1
            assert filtered_users[0]["role"] == "admin_user"

    def test_filter_and_update_table_status(self) -> None:
        """Test filtering users by status."""
        # Set up test data
        self.security_center.users_data = [
            {"username": "john_doe", "role": "common_user", "is_active": True},
            {"username": "jane_admin", "role": "admin_user", "is_active": True},
            {"username": "bob_inactive", "role": "common_user", "is_active": False},
        ]

        # Create mock container
        mock_container = MagicMock()
        self.security_center.users_container = mock_container

        # Test active status filter
        self.security_center.filter_status = "active"

        with patch.object(self.security_center, '_update_users_table') as mock_update:
            self.security_center._filter_and_update_table()

            # Should only pass active users
            mock_update.assert_called_once()
            filtered_users = mock_update.call_args[0][0]
            assert len(filtered_users) == 2
            assert all(user["is_active"] for user in filtered_users)

    def test_update_users_table_empty(self) -> None:
        """Test updating users table with empty data."""
        mock_container = MagicMock()
        self.security_center.users_container = mock_container

        self.security_center._update_users_table([])

        # Should clear container and show "no users" message
        mock_container.clear.assert_called_once()

    def test_update_users_table_with_data(self) -> None:
        """Test updating users table with user data."""
        mock_container = MagicMock()
        mock_container.__enter__ = MagicMock(return_value=mock_container)
        mock_container.__exit__ = MagicMock(return_value=None)
        self.security_center.users_container = mock_container

        users = [
            {"id": "1", "username": "john", "role": "common_user", "is_active": True, "is_2fa_enabled": False},
            {"id": "2", "username": "jane", "role": "admin_user", "is_active": True, "is_2fa_enabled": True},
        ]

        with patch.object(self.security_center, '_create_user_row') as mock_create_row:
            self.security_center._update_users_table(users)

            # Should create a row for each user
            assert mock_create_row.call_count == 2
            mock_create_row.assert_any_call(users[0])
            mock_create_row.assert_any_call(users[1])

    @patch('app.ui_components.security_center.AuthManager')
    def test_create_user_row_structure(self, mock_auth_manager) -> None:
        """Test user row creation structure."""
        mock_auth_manager.get_current_user.return_value = {"id": "current-user-id"}

        user = {
            "id": "test-user-id",
            "username": "testuser",
            "role": "admin_user",
            "is_active": True,
            "is_2fa_enabled": True
        }

        with ui.column():  # Create container for test
            self.security_center._create_user_row(user)

    @patch('app.ui_components.security_center.config.get_api_endpoint')
    @patch('app.ui_components.security_center.ui.notify')
    @patch('requests.post')
    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_post, mock_notify, mock_config) -> None:
        """Test successful user creation."""
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": "new-user-id"}

        mock_dialog = MagicMock()
        mock_dialog.close = MagicMock()

        with patch.object(self.security_center, '_refresh_users_data', new_callable=AsyncMock) as mock_refresh:
            await self.security_center._create_user(
                mock_dialog,
                "newuser",
                "password123",
                "password123",
                "common_user",
                False
            )

            mock_post.assert_called_once()
            mock_dialog.close.assert_called_once()
            mock_refresh.assert_called_once()
            mock_notify.assert_called_with("Usuário 'newuser' criado com sucesso!", type="positive")

    @patch('app.ui_components.security_center.ui.notify')
    @pytest.mark.asyncio
    async def test_create_user_validation_errors(self, mock_notify) -> None:
        """Test user creation validation errors."""
        mock_dialog = MagicMock()

        # Test empty username
        await self.security_center._create_user(
            mock_dialog, "", "password", "password", "common_user", False
        )
        mock_dialog.close.assert_not_called()
        mock_notify.assert_called_with("Nome de usuário e senha são obrigatórios", type="negative")

        # Test password mismatch
        await self.security_center._create_user(
            mock_dialog, "user", "pass1", "pass2", "common_user", False
        )
        mock_dialog.close.assert_not_called()

        # Test short password
        await self.security_center._create_user(
            mock_dialog, "user", "123", "123", "common_user", False
        )
        mock_dialog.close.assert_not_called()

    @patch('app.ui_components.security_center.ui.notify')
    @patch('requests.put')
    @pytest.mark.asyncio
    async def test_update_user_success(self, mock_put, mock_notify) -> None:
        """Test successful user update."""
        mock_put.return_value.status_code = 200
        mock_put.return_value.json.return_value = {"id": "user-id"}

        mock_dialog = MagicMock()
        mock_dialog.close = MagicMock()

        with patch.object(self.security_center, '_refresh_users_data', new_callable=AsyncMock) as mock_refresh:
            await self.security_center._update_user(
                mock_dialog,
                "user-id",
                "updateduser",
                "admin_user",
                True,
                "newpass123",
                "newpass123"
            )

            mock_put.assert_called_once()
            mock_dialog.close.assert_called_once()
            mock_refresh.assert_called_once()
            mock_notify.assert_called_with("Usuário 'updateduser' atualizado com sucesso!", type="positive")

    @patch('app.ui_components.security_center.ui.notify')
    @patch('requests.delete')
    @pytest.mark.asyncio
    async def test_delete_user_success(self, mock_delete, mock_notify) -> None:
        """Test successful user deletion."""
        mock_delete.return_value.status_code = 204

        mock_dialog = MagicMock()
        mock_dialog.close = MagicMock()

        with patch.object(self.security_center, '_refresh_users_data', new_callable=AsyncMock) as mock_refresh:
            await self.security_center._delete_user(mock_dialog, "user-id")

            mock_delete.assert_called_once()
            mock_dialog.close.assert_called_once()
            mock_refresh.assert_called_once()
            mock_notify.assert_called_with("Usuário excluído com sucesso!", type="positive")

    @patch('app.ui_components.security_center.ui.notify')
    @patch('requests.post')
    @pytest.mark.asyncio
    async def test_reset_2fa_success(self, mock_post, mock_notify) -> None:
        """Test successful 2FA reset."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"message": "2FA reset successfully"}

        with patch.object(self.security_center, '_refresh_users_data', new_callable=AsyncMock) as mock_refresh:
            await self.security_center._reset_2fa("user-id")

            mock_post.assert_called_once()
            mock_refresh.assert_called_once()
            mock_notify.assert_called_with("2FA resetado com sucesso!", type="positive")

    @patch('requests.get')
    @pytest.mark.asyncio
    async def test_load_users_data_success(self, mock_get) -> None:
        """Test successful loading of users data."""
        mock_users_data = [
            {"id": "1", "username": "user1", "role": "common_user"},
            {"id": "2", "username": "user2", "role": "admin_user"},
        ]
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_users_data

        with patch.object(self.security_center, '_filter_and_update_table') as mock_filter:
            await self.security_center._load_users_data()

            assert self.security_center.users_data == mock_users_data
            mock_filter.assert_called_once()

    @patch('app.ui_components.security_center.ui.notify')
    @patch('requests.get')
    @pytest.mark.asyncio
    async def test_load_users_data_error(self, mock_get, mock_notify) -> None:
        """Test error handling in users data loading."""
        mock_get.side_effect = Exception("Connection error")

        # Mock the container for error display
        mock_container = MagicMock()
        mock_container.__enter__ = MagicMock(return_value=mock_container)
        mock_container.__exit__ = MagicMock(return_value=None)
        self.security_center.users_container = mock_container

        await self.security_center._load_users_data()

        assert self.security_center.users_data == []
        mock_notify.assert_called_with("Erro de conexão com API: Connection error", type="negative")

    @pytest.mark.asyncio
    async def test_refresh_users_data(self) -> None:
        """Test refresh users data functionality."""
        with patch.object(self.security_center, '_load_users_data', new_callable=AsyncMock) as mock_load:
            await self.security_center._refresh_users_data()
            mock_load.assert_called_once()
