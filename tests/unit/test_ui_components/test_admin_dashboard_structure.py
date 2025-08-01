"""Tests for the admin dashboard structure implementation."""

from unittest.mock import patch

import pytest

from app.ui_components.admin_dashboard import AdminDashboard


class TestAdminDashboardStructure:
    """Test admin dashboard main structure implementation."""

    @pytest.fixture
    def admin_dashboard(self):
        """Create admin dashboard instance for testing."""
        return AdminDashboard()

    def test_admin_dashboard_initialization(self, admin_dashboard):
        """Test admin dashboard initializes with all required components."""
        assert admin_dashboard.status_monitor is not None
        assert admin_dashboard.config_manager is not None
        assert admin_dashboard.plugin_manager is not None

    @patch('app.ui_components.admin_dashboard.AuthManager.get_current_user')
    @patch('app.ui_components.admin_dashboard.ui')
    def test_create_main_layout_responsive_grid(self, mock_ui, mock_get_user, admin_dashboard):
        """Test main layout uses responsive grid structure."""
        mock_get_user.return_value = {"username": "test_admin", "role": "SYSADMIN"}

        # Mock the async components to prevent event loop issues
        with patch.object(admin_dashboard, '_check_admin_access', return_value=True), \
             patch.object(admin_dashboard.status_monitor, 'create'), \
             patch.object(admin_dashboard.config_manager, 'create'), \
             patch.object(admin_dashboard.plugin_manager, 'create'), \
             patch.object(admin_dashboard.status_monitor, 'load_initial_data'):
            admin_dashboard.create()

        # Verify responsive grid layout was called
        mock_ui.grid.assert_called()

        # Verify the grid has proper responsive classes
        grid_call = mock_ui.grid.return_value
        grid_call.classes.assert_called_with("row q-gutter-md")

    @patch('app.ui_components.admin_dashboard.AuthManager.get_current_user')
    @patch('app.ui_components.admin_dashboard.ui')
    def test_sidebar_navigation_creation(self, mock_ui, mock_get_user, admin_dashboard):
        """Test sidebar navigation is created with proper structure."""
        mock_get_user.return_value = {"username": "test_admin", "role": "SYSADMIN"}

        with patch.object(admin_dashboard, '_check_admin_access', return_value=True), \
             patch.object(admin_dashboard.status_monitor, 'create'), \
             patch.object(admin_dashboard.config_manager, 'create'), \
             patch.object(admin_dashboard.plugin_manager, 'create'), \
             patch.object(admin_dashboard.status_monitor, 'load_initial_data'):
            admin_dashboard.create()

        # Verify grid and card components are created
        mock_ui.grid.assert_called()
        mock_ui.card.assert_called()

        # Verify navigation buttons are created
        assert mock_ui.button.call_count >= 5  # At least 5 navigation buttons

    @patch('app.ui_components.admin_dashboard.AuthManager.get_current_user')
    @patch('app.ui_components.admin_dashboard.ui')
    def test_main_content_area_creation(self, mock_ui, mock_get_user, admin_dashboard):
        """Test main content area is created with responsive structure."""
        mock_get_user.return_value = {"username": "test_admin", "role": "SYSADMIN"}

        with patch.object(admin_dashboard, '_check_admin_access', return_value=True), \
             patch.object(admin_dashboard.status_monitor, 'create'), \
             patch.object(admin_dashboard.config_manager, 'create'), \
             patch.object(admin_dashboard.plugin_manager, 'create'), \
             patch.object(admin_dashboard.status_monitor, 'load_initial_data'):
            admin_dashboard.create()

        # Verify tabs and tab panels are created for main content
        mock_ui.tabs.assert_called()
        mock_ui.tab_panels.assert_called()

        # Verify tab components are created (tab calls)
        assert mock_ui.tab.call_count >= 5  # At least 5 admin section tabs

    @patch('app.ui_components.admin_dashboard.AuthManager.get_current_user')
    @patch('app.ui_components.admin_dashboard.ui')
    def test_admin_sections_tabs_created(self, mock_ui, mock_get_user, admin_dashboard):
        """Test all required admin section tabs are created."""
        mock_get_user.return_value = {"username": "test_admin", "role": "SYSADMIN"}

        with patch.object(admin_dashboard, '_check_admin_access', return_value=True), \
             patch.object(admin_dashboard.status_monitor, 'create'), \
             patch.object(admin_dashboard.config_manager, 'create'), \
             patch.object(admin_dashboard.plugin_manager, 'create'), \
             patch.object(admin_dashboard.status_monitor, 'load_initial_data'):
            admin_dashboard.create()

        # Verify tabs are created
        mock_ui.tabs.assert_called()
        mock_ui.tab_panels.assert_called()

    def test_dashboard_overview_creation(self, admin_dashboard):
        """Test dashboard overview creates status cards."""
        with patch('app.ui_components.admin_dashboard.ui') as mock_ui:
            admin_dashboard._create_dashboard_overview()

            # Verify status cards are created
            mock_ui.grid.assert_called()
            mock_ui.card.assert_called()
            mock_ui.icon.assert_called()

    def test_security_center_integration(self, admin_dashboard):
        """Test security center is properly integrated."""
        # SecurityCenter is created during initialization
        assert admin_dashboard.security_center is not None
        assert hasattr(admin_dashboard.security_center, 'create')

    def test_performance_monitoring_placeholder(self, admin_dashboard):
        """Test performance monitoring placeholder is created."""
        with patch('app.ui_components.admin_dashboard.ui') as mock_ui:
            admin_dashboard._create_performance_monitoring()

            mock_ui.label.assert_called()
            mock_ui.card.assert_called()

    def test_audit_logs_integration(self, admin_dashboard):
        """Test audit logs is properly integrated."""
        # AuditLogs is created during initialization
        assert admin_dashboard.audit_logs is not None
        assert hasattr(admin_dashboard.audit_logs, 'create')

    def test_navigation_section_method(self, admin_dashboard):
        """Test navigation section method works correctly."""
        with patch('app.ui_components.admin_dashboard.ui') as mock_ui:
            admin_dashboard._navigate_section("dashboard")

            # Verify notification is shown
            mock_ui.notify.assert_called_with("Navegando para: dashboard", type="info")

    @patch('app.ui_components.admin_dashboard.AuthManager.require_auth')
    @patch('app.ui_components.admin_dashboard.AuthManager.get_current_user')
    @patch('app.ui_components.admin_dashboard.AuthManager.has_admin_access')
    def test_admin_access_checking(self, mock_has_admin, mock_get_user, mock_require_auth, admin_dashboard):
        """Test admin access checking works correctly."""
        # Test successful admin access
        mock_require_auth.return_value = True
        mock_get_user.return_value = {"username": "admin", "role": "SYSADMIN"}
        mock_has_admin.return_value = True

        result = admin_dashboard._check_admin_access()
        assert result is True

        # Test failed admin access
        mock_has_admin.return_value = False
        with patch('app.ui_components.admin_dashboard.ui'):
            result = admin_dashboard._check_admin_access()
            assert result is False
