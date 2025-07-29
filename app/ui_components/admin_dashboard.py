"""Administrative dashboard main layout component."""

from nicegui import ui

from app.core.auth import AuthManager
from app.ui_components.agent_config_manager import AgentConfigManager
from app.ui_components.agent_status_monitor import AgentStatusMonitor
from app.ui_components.plugin_manager import PluginManager


class AdminDashboard:
    """Main administrative dashboard layout and navigation."""

    def __init__(self) -> None:
        """Initialize the admin dashboard."""
        self.status_monitor = AgentStatusMonitor()
        self.config_manager = AgentConfigManager(
            refresh_callback=self.status_monitor._refresh_data
        )
        self.plugin_manager = PluginManager()

    def create(self) -> None:
        """Create the administrative dashboard UI."""
        # Check authentication and admin access
        if not self._check_admin_access():
            return

        current_user = AuthManager.get_current_user()

        with ui.column().classes("w-full max-w-6xl mx-auto mt-10 p-6"):
            # Header
            with ui.row().classes("w-full justify-between items-center mb-8"):
                ui.label("Painel Administrativo - Gerenciamento de Agentes").classes(
                    "text-3xl font-bold"
                )

                with ui.row().classes("items-center gap-4"):
                    username = (
                        current_user.get("username", "Unknown")
                        if current_user
                        else "Unknown"
                    )
                    ui.label(f"Admin: {username}").classes("text-lg")
                    ui.button(
                        "Dashboard",
                        on_click=lambda: ui.navigate.to("/dashboard"),
                        icon="dashboard",
                    ).classes(
                        "bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                    )
                    ui.button(
                        "Logout",
                        on_click=self._handle_logout,
                        icon="logout",
                    ).classes(
                        "bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                    )

            # Create tabs for different admin sections
            with ui.tabs().classes("w-full") as tabs:
                monitoring_tab = ui.tab(
                    "monitoring", label="Monitoramento", icon="monitor"
                )
                config_tab = ui.tab("config", label="Configuração", icon="settings")
                plugins_tab = ui.tab("plugins", label="Plugins", icon="extension")

            with ui.tab_panels(tabs, value="monitoring").classes("w-full"):
                with ui.tab_panel("monitoring"):
                    self.status_monitor.create()

                with ui.tab_panel("config"):
                    self.config_manager.create()

                with ui.tab_panel("plugins"):
                    self.plugin_manager.create()

            # Load initial data
            self.status_monitor.load_initial_data()

    def _check_admin_access(self) -> bool:
        """Check if current user has admin access."""
        try:
            if not AuthManager.require_auth():
                ui.navigate.to("/login")
                return False

            current_user = AuthManager.get_current_user()
            if not current_user:
                ui.navigate.to("/login")
                return False

            # Check if user has admin role
            user_role = current_user.get("role", "")
            if user_role not in [
                "admin_user",
                "sysadmin",
            ]:
                with ui.column().classes("w-full max-w-md mx-auto mt-20 p-6"):
                    ui.label("Acesso Negado").classes(
                        "text-2xl font-bold text-red-600 text-center mb-4"
                    )
                    ui.label(
                        "Você não tem permissão para acessar o painel administrativo."
                    ).classes("text-center text-gray-600 mb-6")
                    ui.button(
                        "Voltar ao Dashboard",
                        on_click=lambda: ui.navigate.to("/dashboard"),
                    ).classes(
                        "w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
                    )
                return False

            return True

        except Exception:
            ui.navigate.to("/login")
            return False

    def _handle_logout(self) -> None:
        """Handle user logout."""
        try:
            # Clear authentication
            AuthManager.logout_user()

            # Show logout message
            ui.notify("Logout realizado com sucesso!", type="positive")

            # Redirect to login page
            ui.navigate.to("/login")

        except Exception as e:
            ui.notify(f"Erro durante logout: {str(e)}", type="negative")
            # Force redirect to login even if logout fails
            ui.navigate.to("/login")


def admin_dashboard_page() -> None:
    """Create the admin dashboard page."""
    dashboard = AdminDashboard()
    dashboard.create()
