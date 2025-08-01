"""Dashboard page UI component."""

from nicegui import ui

from app.core.auth import AuthManager
from app.core.database import get_async_db
from app.repositories.user_repository import UserRepository


class DashboardPage:
    """Dashboard page component."""

    def create(self) -> None:
        """Create the dashboard page UI."""
        # Check authentication
        if not AuthManager.require_auth():
            return

        current_user = AuthManager.get_current_user()

        with ui.column().classes("w-full max-w-4xl mx-auto mt-10 p-6"):
            # Header
            with ui.row().classes("w-full justify-between items-center mb-8"):
                ui.label("IAM Dashboard").classes("text-3xl font-bold")

                with ui.row().classes("items-center gap-4"):
                    ui.label(f"Olá, {current_user['username']}").classes("text-lg")
                    ui.button("Sair", on_click=self._handle_logout).classes(
                        "bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                    )

            # Main content
            with ui.card().classes("w-full p-6"):
                ui.label("Bem-vindo ao Sistema de Advocacia SaaS").classes(
                    "text-xl font-semibold mb-4"
                )

                ui.label("Sistema inicializado com sucesso!").classes(
                    "text-gray-600 mb-4"
                )

                # MVP Feature cards
                with ui.row().classes("w-full gap-4 mt-6"):
                    with ui.card().classes(
                        "flex-1 p-4 hover:shadow-lg transition-shadow"
                    ):
                        ui.icon("description", size="3rem").classes(
                            "text-blue-500 mb-2"
                        )
                        ui.label("Processador de PDFs").classes("font-semibold mb-2")
                        ui.label("Upload e processamento de documentos PDF").classes(
                            "text-sm text-gray-600 mb-4"
                        )
                        ui.button(
                            "Acessar",
                            on_click=lambda: ui.notify(
                                "Funcionalidade em desenvolvimento", type="info"
                            ),
                        ).classes(
                            "w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
                        )

                    with ui.card().classes(
                        "flex-1 p-4 hover:shadow-lg transition-shadow"
                    ):
                        ui.icon("edit_note", size="3rem").classes("text-green-500 mb-2")
                        ui.label("Redator de Quesitos").classes("font-semibold mb-2")
                        ui.label("Geração automática de documentos legais").classes(
                            "text-sm text-gray-600 mb-4"
                        )
                        ui.button(
                            "Acessar",
                            on_click=lambda: ui.navigate.to("/questionnaire-writer"),
                        ).classes(
                            "w-full bg-green-500 text-white py-2 rounded hover:bg-green-600"
                        )

                    with ui.card().classes(
                        "flex-1 p-4 hover:shadow-lg transition-shadow"
                    ):
                        ui.icon("people", size="3rem").classes("text-purple-500 mb-2")
                        ui.label("Clientes").classes("font-semibold mb-2")
                        ui.label("Gerenciamento de clientes do escritório").classes(
                            "text-sm text-gray-600 mb-4"
                        )
                        ui.button(
                            "Gerenciar", on_click=lambda: ui.navigate.to("/clients")
                        ).classes(
                            "w-full bg-purple-500 text-white py-2 rounded hover:bg-purple-600"
                        )

                # User Management and Admin
                with ui.row().classes("w-full gap-4 mt-6"):
                    with ui.card().classes("flex-1 p-4"):
                        ui.icon("security", size="2rem").classes("text-orange-500 mb-2")
                        ui.label("Configurações de Segurança").classes(
                            "font-semibold mb-2"
                        )
                        ui.label("Gerenciar autenticação em dois fatores").classes(
                            "text-sm text-gray-600 mb-2"
                        )
                        ui.button(
                            "Configurar 2FA",
                            on_click=lambda: ui.navigate.to("/settings/2fa"),
                        ).classes(
                            "text-sm bg-orange-500 text-white px-3 py-1 rounded hover:bg-orange-600"
                        )

                    # Admin Panel - only show for admin users
                    if AuthManager.has_admin_access(current_user):
                        with ui.card().classes("flex-1 p-4"):
                            ui.icon("admin_panel_settings", size="2rem").classes(
                                "text-red-500 mb-2"
                            )
                            ui.label("Painel Administrativo").classes(
                                "font-semibold mb-2"
                            )
                            ui.label("Gerenciar agentes e sistema").classes(
                                "text-sm text-gray-600 mb-2"
                            )
                            ui.button(
                                "Acessar Admin",
                                on_click=lambda: ui.navigate.to("/admin"),
                            ).classes(
                                "text-sm bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
                            )

                # User info
                with ui.expansion("Informações da Sessão").classes("w-full mt-6"):
                    # Container for dynamic content
                    session_info_container = ui.column().classes(
                        "w-full p-4 bg-gray-50 rounded"
                    )

                    # Load user data asynchronously
                    ui.timer(
                        0.1,
                        lambda: self._load_session_info(
                            session_info_container, current_user
                        ),
                        once=True,
                    )

    def _get_role_display_name(self, role: str) -> str:
        """Convert technical role name to user-friendly display name."""
        role_map = {
            "sysadmin": "Administrador do Sistema",
            "admin_user": "Administrador",
            "common_user": "Usuário Comum",
        }
        return role_map.get(role, role)

    async def _load_session_info(self, container, session_user) -> None:
        """Load current user data from database."""
        try:
            async for db_session in get_async_db():
                user_repository = UserRepository(db_session)
                current_user_obj = await user_repository.get_by_username(
                    session_user["username"]
                )

                # Debug info
                print(f"Loading session info for: {session_user['username']}")
                if current_user_obj:
                    print(
                        f"Found user: {current_user_obj.role}, active: {current_user_obj.is_active}, 2fa: {current_user_obj.is_2fa_enabled}"
                    )

                with container:
                    container.clear()
                    ui.label("Dados da Sessão Atual").classes("font-semibold mb-3")

                    with ui.row().classes("w-full mb-2"):
                        ui.label("Usuário:").classes("font-medium w-24")
                        ui.label(session_user.get("username", "N/A")).classes(
                            "text-gray-700"
                        )

                    with ui.row().classes("w-full mb-2"):
                        ui.label("Função:").classes("font-medium w-24")
                        if current_user_obj:
                            # Handle enum - get the value, not the enum itself
                            raw_role = (
                                current_user_obj.role.value
                                if hasattr(current_user_obj.role, "value")
                                else str(current_user_obj.role)
                            )
                        else:
                            raw_role = session_user.get("role", "N/A")
                        role_display = (
                            self._get_role_display_name(raw_role)
                            if raw_role != "N/A"
                            else "N/A"
                        )
                        ui.label(role_display).classes("text-gray-700")

                    with ui.row().classes("w-full mb-2"):
                        ui.label("Ativo:").classes("font-medium w-24")
                        is_active = (
                            current_user_obj.is_active
                            if current_user_obj
                            else session_user.get("is_active", False)
                        )
                        status = "Sim" if is_active else "Não"
                        ui.label(status).classes("text-gray-700")

                    with ui.row().classes("w-full mb-2"):
                        ui.label("2FA:").classes("font-medium w-24")
                        is_2fa = (
                            current_user_obj.is_2fa_enabled
                            if current_user_obj
                            else session_user.get("is_2fa_enabled", False)
                        )
                        tfa_status = "Habilitado" if is_2fa else "Desabilitado"
                        ui.label(tfa_status).classes("text-gray-700")

                    if session_user.get("login_time"):
                        with ui.row().classes("w-full"):
                            ui.label("Login:").classes("font-medium w-24")
                            # Format the login time to be more readable
                            login_time = session_user.get("login_time", "N/A")
                            if login_time != "N/A":
                                try:
                                    from datetime import datetime

                                    dt = datetime.fromisoformat(
                                        login_time.replace("Z", "+00:00")
                                    )
                                    formatted_time = dt.strftime("%d/%m/%Y às %H:%M:%S")
                                except (ValueError, TypeError):
                                    formatted_time = login_time
                            else:
                                formatted_time = login_time
                            ui.label(formatted_time).classes("text-gray-700 text-sm")

        except Exception as e:
            with container:
                container.clear()
                ui.label(f"Erro ao carregar dados: {str(e)}").classes("text-red-500")

    def _handle_logout(self) -> None:
        """Handle user logout."""
        AuthManager.logout_user()
        ui.notify("Saída realizada com sucesso", type="positive")
        ui.navigate.to("/login")


def dashboard_page() -> None:
    """Create and display the dashboard page."""
    page = DashboardPage()
    page.create()
