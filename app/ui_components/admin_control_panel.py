"""Administrative control panel UI component for agent management.

This file now serves as a compatibility layer that delegates to the
decomposed components for better maintainability.
"""

from typing import Any

from app.ui_components.admin_dashboard import AdminDashboard


class AdminControlPanel:
    """Administrative control panel for agent management.

    This class now acts as a facade that delegates to the decomposed
    AdminDashboard component for better code organization.
    """

    def __init__(self) -> None:
        """Initialize the admin control panel."""
        self.dashboard = AdminDashboard()

    def create(self) -> None:
        """Create the administrative control panel UI."""
        self.dashboard.create()

    # Compatibility methods for existing tests
    def _check_admin_access(self) -> bool:
        """Check if current user has admin access."""
        return self.dashboard._check_admin_access()

    def _refresh_data(self) -> None:
        """Refresh system health and agents data."""
        self.dashboard.status_monitor._refresh_data()

    def _load_system_health(self) -> None:
        """Load system health data."""
        self.dashboard.status_monitor._load_system_health()

    def _load_agents_data(self) -> None:
        """Load agents data from API."""
        self.dashboard.status_monitor._load_agents_data()

    def _create_performance_summary(self) -> None:
        """Create performance summary cards."""
        self.dashboard.status_monitor._create_performance_summary()

    def _create_agent_row(self, agent: dict[str, Any]) -> None:
        """Create a row for an agent in the table."""
        self.dashboard.status_monitor._create_agent_row(agent)

    def _start_agent(self, agent_id: str) -> None:
        """Start an agent."""
        self.dashboard.status_monitor._start_agent(agent_id)

    def _stop_agent(self, agent_id: str) -> None:
        """Stop an agent."""
        self.dashboard.status_monitor._stop_agent(agent_id)

    def _restart_agent(self, agent_id: str) -> None:
        """Restart an agent."""
        self.dashboard.status_monitor._restart_agent(agent_id)

    def _perform_restart_all(self) -> None:
        """Perform the actual restart of all agents."""
        self.dashboard.status_monitor._perform_restart_all()

    def _validate_config(self, agent_id: str) -> None:
        """Validate agent configuration."""
        self.dashboard.config_manager._validate_config(agent_id)

    def _apply_config(self, agent_id: str, dialog: Any) -> None:
        """Apply configuration changes."""
        self.dashboard.config_manager._apply_config(agent_id, dialog)

    def _rollback_config(self, agent_id: str) -> None:
        """Rollback configuration to previous state."""
        self.dashboard.config_manager._rollback_config(agent_id)

    def _perform_rollback(self, agent_id: str) -> None:
        """Perform the actual configuration rollback."""
        self.dashboard.config_manager._perform_rollback(agent_id)

    def _show_agent_details(self, agent_id: str) -> None:
        """Show detailed information about an agent."""
        self.dashboard.status_monitor._show_agent_details(agent_id)

    def _handle_logout(self) -> None:
        """Handle user logout."""
        self.dashboard._handle_logout()

    # Additional compatibility methods for tests
    def _update_system_health_display(self) -> None:
        """Update system health display (compatibility method)."""
        pass  # This is handled internally by the status monitor

    def _update_agents_table(self) -> None:
        """Update agents table display (compatibility method)."""
        pass  # This is handled internally by the status monitor

    @property
    def refresh_timer(self) -> Any:
        """Get refresh timer from status monitor."""
        return self.dashboard.status_monitor.refresh_timer

    @refresh_timer.setter
    def refresh_timer(self, value: Any) -> None:
        """Set refresh timer in status monitor."""
        self.dashboard.status_monitor.refresh_timer = value

    # Properties for test compatibility
    @property
    def agents_data(self) -> list[dict[str, Any]]:
        """Get agents data from status monitor."""
        return self.dashboard.status_monitor.agents_data

    @agents_data.setter
    def agents_data(self, value: list[dict[str, Any]]) -> None:
        """Set agents data in status monitor."""
        self.dashboard.status_monitor.agents_data = value

    @property
    def system_health(self) -> dict[str, Any]:
        """Get system health data from status monitor."""
        return self.dashboard.status_monitor.system_health

    @system_health.setter
    def system_health(self, value: dict[str, Any]) -> None:
        """Set system health data in status monitor."""
        self.dashboard.status_monitor.system_health = value

    @property
    def config_forms(self) -> dict[str, Any]:
        """Get config forms from config manager."""
        return self.dashboard.config_manager.config_forms

    @config_forms.setter
    def config_forms(self, value: dict[str, Any]) -> None:
        """Set config forms in config manager."""
        self.dashboard.config_manager.config_forms = value

    # Plugin manager delegation methods
    async def _refresh_dependency(self, dep_name: str) -> None:
        """Refresh a specific dependency."""
        await self.dashboard.plugin_manager._refresh_dependency(dep_name)

    def _resolve_conflict(self, conflict: dict[str, Any]) -> None:
        """Resolve a dependency conflict."""
        self.dashboard.plugin_manager._resolve_conflict(conflict)

    def _install_plugin(self, plugin_name: str) -> None:
        """Install a plugin."""
        self.dashboard.plugin_manager._install_plugin(plugin_name)


def admin_control_panel_page() -> None:
    """Create the admin control panel page."""
    panel = AdminControlPanel()
    panel.create()
