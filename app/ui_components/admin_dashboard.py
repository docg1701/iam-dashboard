"""Administrative dashboard main layout component."""

from dependency_injector.wiring import Provide, inject
from nicegui import ui

from app.containers import Container
from app.core.auth import AuthManager
from app.services.audit_log_service import AuditLogService
from app.ui_components.agent_config_manager import AgentConfigManager
from app.ui_components.agent_status_monitor import AgentStatusMonitor
from app.ui_components.audit_logs import AuditLogs
from app.ui_components.performance_monitor import PerformanceMonitor
from app.ui_components.plugin_manager import PluginManager
from app.ui_components.security_center import SecurityCenter


class AdminDashboard:
    """Main administrative dashboard layout and navigation."""

    @inject
    def __init__(
        self,
        audit_log_service: AuditLogService = Provide[Container.audit_log_service],
    ) -> None:
        """Initialize the admin dashboard."""
        self.audit_log_service = audit_log_service
        self.status_monitor = AgentStatusMonitor()
        self.config_manager = AgentConfigManager(
            refresh_callback=self.status_monitor._refresh_data
        )
        self.plugin_manager = PluginManager()
        self.security_center = SecurityCenter()
        self.performance_monitor = PerformanceMonitor()
        self.audit_logs = AuditLogs(audit_log_service)

    def create(self) -> None:
        """Create the administrative dashboard UI."""
        # Check authentication and admin access
        if not self._check_admin_access():
            return

        current_user = AuthManager.get_current_user()

        # Main responsive container
        with ui.grid().classes("row q-gutter-md"):
            # Sidebar navigation - responsive column
            with ui.card().classes("col-xs-12 col-md-3 q-pa-md"):
                self._create_sidebar_navigation()

            # Main content area - responsive column
            with ui.card().classes("col-xs-12 col-md-9 q-pa-md"):
                self._create_main_content_area(current_user)

    def _create_sidebar_navigation(self) -> None:
        """Create the navigation sidebar with admin sections."""
        ui.label("Painel Administrativo").classes("text-h5 q-mb-md text-weight-bold")

        # Navigation menu
        with ui.column().classes("q-gutter-sm w-full"):
            ui.button("Dashboard", icon="dashboard", on_click=lambda: self._navigate_section("dashboard")).classes("w-full text-left justify-start")
            ui.button("Gerenciamento de Agentes", icon="smart_toy", on_click=lambda: self._navigate_section("agents")).classes("w-full text-left justify-start")
            ui.button("Centro de Segurança", icon="security", on_click=lambda: self._navigate_section("security")).classes("w-full text-left justify-start")
            ui.button("Monitoramento", icon="monitoring", on_click=lambda: self._navigate_section("monitoring")).classes("w-full text-left justify-start")
            ui.button("Logs de Auditoria", icon="history", on_click=lambda: self._navigate_section("audit")).classes("w-full text-left justify-start")

            ui.separator().classes("q-my-md")

            # User info and logout
            current_user = AuthManager.get_current_user()
            username = current_user.get("username", "Unknown") if current_user else "Unknown"
            ui.label(f"Admin: {username}").classes("text-body2 text-grey-7")

            ui.button("Voltar ao Dashboard", icon="home", on_click=lambda: ui.navigate.to("/dashboard")).classes("w-full text-left justify-start")
            ui.button("Logout", icon="logout", on_click=self._handle_logout).classes("w-full text-left justify-start text-red")

    def _create_main_content_area(self, current_user: dict) -> None:
        """Create the main content area with tabs."""
        # Create tabs for different admin sections
        with ui.tabs().classes("w-full") as tabs:
            ui.tab("dashboard", label="Dashboard", icon="dashboard")
            ui.tab("agents", label="Agentes", icon="smart_toy")
            ui.tab("security", label="Segurança", icon="security")
            ui.tab("monitoring", label="Monitoramento", icon="monitoring")
            ui.tab("audit", label="Auditoria", icon="history")

        with ui.tab_panels(tabs, value="dashboard").classes("w-full q-mt-md"):
            # Dashboard Overview
            with ui.tab_panel("dashboard"):
                self._create_dashboard_overview()

            # Agent Management
            with ui.tab_panel("agents"):
                with ui.column().classes("w-full q-gutter-md"):
                    ui.label("Gerenciamento de Agentes").classes("text-h6 q-mb-md")

                    # Agent status monitoring
                    with ui.expansion("Status dos Agentes", icon="monitor").classes("w-full"):
                        self.status_monitor.create()

                    # Agent configuration
                    with ui.expansion("Configuração de Agentes", icon="settings").classes("w-full"):
                        self.config_manager.create()

                    # Plugin management
                    with ui.expansion("Gerenciamento de Plugins", icon="extension").classes("w-full"):
                        self.plugin_manager.create()

            # Security Center - User Management
            with ui.tab_panel("security"):
                self.security_center.create()

            # Performance Monitoring
            with ui.tab_panel("monitoring"):
                self.performance_monitor.create()

            # Audit Logs
            with ui.tab_panel("audit"):
                self.audit_logs.create()

        # Load initial data
        self.status_monitor.load_initial_data()

    def _create_dashboard_overview(self) -> None:
        """Create the main dashboard overview."""
        ui.label("Visão Geral do Sistema").classes("text-h6 q-mb-md")

        # System status cards
        with ui.grid().classes("row q-gutter-md"):
            # System health card
            with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                ui.icon("health_and_safety", size="2rem", color="green").classes("q-mb-sm")
                ui.label("Sistema").classes("text-subtitle1")
                ui.label("Operacional").classes("text-h6 text-green")

            # Active agents card
            with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                ui.icon("smart_toy", size="2rem", color="blue").classes("q-mb-sm")
                ui.label("Agentes Ativos").classes("text-subtitle1")
                ui.label("3/4").classes("text-h6 text-blue")

            # Users online card
            with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                ui.icon("people", size="2rem", color="orange").classes("q-mb-sm")
                ui.label("Usuários Online").classes("text-subtitle1")
                ui.label("12").classes("text-h6 text-orange")

            # System load card
            with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                ui.icon("memory", size="2rem", color="purple").classes("q-mb-sm")
                ui.label("Carga do Sistema").classes("text-subtitle1")
                ui.label("65%").classes("text-h6 text-purple")

    def _create_performance_monitoring(self) -> None:
        """Create the performance monitoring interface."""
        ui.label("Monitoramento de Performance").classes("text-h6 q-mb-md")
        ui.label("Métricas de performance em tempo real e alertas em desenvolvimento.").classes("text-body1 text-grey-7")

        # Placeholder for performance charts
        with ui.card().classes("w-full q-pa-md"):
            ui.label("Gráficos de Performance").classes("text-subtitle1 q-mb-sm")
            ui.label("Gráficos com ui.plotly serão implementados aqui.").classes("text-body2 text-grey-6")


    def _navigate_section(self, section: str) -> None:
        """Navigate to a specific section."""
        # This will be enhanced with proper tab switching
        ui.notify(f"Navegando para: {section}", type="info")

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

            # Use the new AuthManager method for admin access checking
            if not AuthManager.has_admin_access(current_user):
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
