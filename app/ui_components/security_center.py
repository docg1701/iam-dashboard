"""Security Center component for user management and security operations."""

from typing import Any

import requests
from nicegui import ui

from app.core.auth import AuthManager
from app.core.config import config


class SecurityCenter:
    """Security center for user management and security operations."""

    def __init__(self) -> None:
        """Initialize the security center."""
        self.users_data: list[dict[str, Any]] = []
        self.users_table: ui.table | None = None
        self.users_container: ui.element | None = None
        self.filter_role: str = "all"
        self.filter_status: str = "all"
        self.search_query: str = ""

    def create(self) -> None:
        """Create the security center UI."""
        with ui.column().classes("w-full q-gutter-md"):
            # Header with actions
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("Centro de Segurança").classes("text-h5 text-weight-bold")
                ui.button(
                    "Novo Usuário",
                    icon="person_add",
                    on_click=self._show_create_user_dialog,
                ).classes("bg-primary text-white")

            # Filters and search
            with ui.card().classes("w-full q-pa-md"):
                with ui.row().classes("w-full q-gutter-md items-center"):
                    # Search input
                    search_input = ui.input(
                        label="Buscar usuários",
                        placeholder="Nome de usuário..."
                    ).classes("flex-grow")
                    search_input.on('update:model-value', self._on_search_change)

                    # Role filter
                    role_filter = ui.select(
                        ["all", "sysadmin", "admin_user", "common_user"],
                        label="Função",
                        value="all"
                    ).classes("min-w-32")
                    role_filter.on('update:model-value', self._on_role_filter_change)

                    # Status filter
                    status_filter = ui.select(
                        ["all", "active", "inactive"],
                        label="Status",
                        value="all"
                    ).classes("min-w-32")
                    status_filter.on('update:model-value', self._on_status_filter_change)

                    # Refresh button
                    ui.button(
                        "Atualizar",
                        icon="refresh",
                        on_click=self._refresh_users_data,
                    ).classes("bg-grey-6 text-white")

            # Users table
            with ui.card().classes("w-full q-pa-md"):
                ui.label("Usuários do Sistema").classes("text-h6 q-mb-md")

                # Table container
                with ui.column().classes("w-full") as users_container:
                    self.users_container = users_container
                    ui.label("Carregando usuários...").classes("text-center q-pa-lg text-grey-6")

        # Load initial data
        self._load_users_data()

    def _on_search_change(self, value: str) -> None:
        """Handle search input change."""
        self.search_query = value.lower()
        self._filter_and_update_table()

    def _on_role_filter_change(self, value: str) -> None:
        """Handle role filter change."""
        self.filter_role = value
        self._filter_and_update_table()

    def _on_status_filter_change(self, value: str) -> None:
        """Handle status filter change."""
        self.filter_status = value
        self._filter_and_update_table()

    def _filter_and_update_table(self) -> None:
        """Apply filters and update the users table."""
        filtered_users = []

        for user in self.users_data:
            # Apply search filter
            if self.search_query and self.search_query not in user.get("username", "").lower():
                continue

            # Apply role filter
            if self.filter_role != "all" and user.get("role") != self.filter_role:
                continue

            # Apply status filter
            if self.filter_status != "all":
                is_active = user.get("is_active", True)
                if self.filter_status == "active" and not is_active:
                    continue
                if self.filter_status == "inactive" and is_active:
                    continue

            filtered_users.append(user)

        self._update_users_table(filtered_users)

    def _update_users_table(self, users: list[dict[str, Any]] | None = None) -> None:
        """Update the users table display."""
        if users is None:
            users = self.users_data

        # Clear existing content
        if self.users_container:
            self.users_container.clear()

        if not users:
            with self.users_container:
                ui.label("Nenhum usuário encontrado").classes("text-center q-pa-lg text-grey-6")
            return

        # Create responsive table
        with self.users_container:
            with ui.grid().classes("row q-gutter-sm"):
                # Table header
                with ui.row().classes("w-full q-pa-sm bg-grey-2 text-weight-bold"):
                    ui.label("Usuário").classes("col-3")
                    ui.label("Função").classes("col-2")
                    ui.label("Status").classes("col-2")
                    ui.label("2FA").classes("col-2")
                    ui.label("Ações").classes("col-3")

                # Table rows
                for user in users:
                    self._create_user_row(user)

    def _create_user_row(self, user: dict[str, Any]) -> None:
        """Create a row for a user in the table."""
        username = user.get("username", "Unknown")
        role = user.get("role", "common_user")
        is_active = user.get("is_active", True)
        is_2fa_enabled = user.get("is_2fa_enabled", False)
        user_id = user.get("id")

        with ui.row().classes("w-full q-pa-sm border-bottom items-center"):
            # Username
            ui.label(username).classes("col-3 text-weight-medium")

            # Role with badge
            role_color = {
                "sysadmin": "red",
                "admin_user": "orange",
                "common_user": "blue"
            }.get(role, "grey")

            with ui.column().classes("col-2"):
                ui.badge(
                    role.replace("_", " ").title(),
                    color=role_color,
                    text_color="white"
                ).classes("text-caption")

            # Status
            with ui.column().classes("col-2"):
                status_icon = "check_circle" if is_active else "cancel"
                status_color = "green" if is_active else "red"
                status_text = "Ativo" if is_active else "Inativo"

                with ui.row().classes("items-center q-gutter-xs"):
                    ui.icon(status_icon, color=status_color, size="sm")
                    ui.label(status_text).classes("text-caption")

            # 2FA Status
            with ui.column().classes("col-2"):
                tfa_icon = "security" if is_2fa_enabled else "no_encryption"
                tfa_color = "green" if is_2fa_enabled else "grey"

                with ui.row().classes("items-center q-gutter-xs"):
                    ui.icon(tfa_icon, color=tfa_color, size="sm")
                    ui.label("Ativo" if is_2fa_enabled else "Inativo").classes("text-caption")

            # Actions
            with ui.row().classes("col-3 q-gutter-xs"):
                ui.button(
                    icon="edit",
                    on_click=lambda u=user: self._show_edit_user_dialog(u),
                ).classes("bg-blue-6 text-white").props("size=sm dense")

                if is_2fa_enabled:
                    ui.button(
                        icon="refresh",
                        on_click=lambda uid=user_id: self._reset_2fa(uid),
                    ).classes("bg-orange-6 text-white").props("size=sm dense")

                if user_id != AuthManager.get_current_user().get("id"):  # Don't allow self-deletion
                    ui.button(
                        icon="delete",
                        on_click=lambda u=user: self._show_delete_user_dialog(u),
                    ).classes("bg-red-6 text-white").props("size=sm dense")

    def _show_create_user_dialog(self) -> None:
        """Show dialog for creating a new user."""
        with ui.dialog() as create_dialog, ui.card().classes("w-96"):
            ui.label("Criar Novo Usuário").classes("text-h6 q-mb-md")

            username_input = ui.input("Nome de usuário").classes("w-full q-mb-sm")
            password_input = ui.input("Senha", password=True).classes("w-full q-mb-sm")
            confirm_password_input = ui.input("Confirmar senha", password=True).classes("w-full q-mb-sm")

            role_select = ui.select({
                "common_user": "Usuário Comum",
                "admin_user": "Administrador",
                "sysadmin": "Super Administrador"
            }, label="Função", value="common_user").classes("w-full q-mb-sm")

            enable_2fa = ui.checkbox("Habilitar 2FA").classes("q-mb-md")

            with ui.row().classes("w-full justify-end q-gutter-sm"):
                ui.button("Cancelar", on_click=create_dialog.close).classes("bg-grey-6 text-white")
                ui.button(
                    "Criar",
                    on_click=lambda: self._create_user(
                        create_dialog,
                        username_input.value,
                        password_input.value,
                        confirm_password_input.value,
                        role_select.value,
                        enable_2fa.value
                    )
                ).classes("bg-primary text-white")

        create_dialog.open()

    def _show_edit_user_dialog(self, user: dict[str, Any]) -> None:
        """Show dialog for editing a user."""
        with ui.dialog() as edit_dialog, ui.card().classes("w-96"):
            ui.label(f"Editar Usuário: {user.get('username')}").classes("text-h6 q-mb-md")

            username_input = ui.input("Nome de usuário", value=user.get("username", "")).classes("w-full q-mb-sm")

            role_select = ui.select({
                "common_user": "Usuário Comum",
                "admin_user": "Administrador",
                "sysadmin": "Super Administrador"
            }, label="Função", value=user.get("role", "common_user")).classes("w-full q-mb-sm")

            is_active = ui.checkbox("Usuário ativo", value=user.get("is_active", True)).classes("q-mb-md")

            # Password reset section
            ui.separator().classes("q-my-md")
            ui.label("Redefinir Senha (opcional)").classes("text-subtitle2 q-mb-sm")
            new_password_input = ui.input("Nova senha", password=True).classes("w-full q-mb-sm")
            confirm_new_password_input = ui.input("Confirmar nova senha", password=True).classes("w-full q-mb-md")

            with ui.row().classes("w-full justify-end q-gutter-sm"):
                ui.button("Cancelar", on_click=edit_dialog.close).classes("bg-grey-6 text-white")
                ui.button(
                    "Salvar",
                    on_click=lambda: self._update_user(
                        edit_dialog,
                        user.get("id"),
                        username_input.value,
                        role_select.value,
                        is_active.value,
                        new_password_input.value,
                        confirm_new_password_input.value
                    )
                ).classes("bg-primary text-white")

        edit_dialog.open()

    def _show_delete_user_dialog(self, user: dict[str, Any]) -> None:
        """Show confirmation dialog for deleting a user."""
        with ui.dialog() as delete_dialog, ui.card().classes("w-96"):
            ui.label("Confirmar Exclusão").classes("text-h6 q-mb-md")
            ui.label(f"Tem certeza que deseja excluir o usuário '{user.get('username')}'?").classes("q-mb-md")
            ui.label("Esta ação não pode ser desfeita.").classes("text-red q-mb-md")

            with ui.row().classes("w-full justify-end q-gutter-sm"):
                ui.button("Cancelar", on_click=delete_dialog.close).classes("bg-grey-6 text-white")
                ui.button(
                    "Excluir",
                    on_click=lambda: self._delete_user(delete_dialog, user.get("id"))
                ).classes("bg-red text-white")

        delete_dialog.open()

    def _validate_user_input(self, username: str, password: str, confirm_password: str = "") -> bool:
        """Validate user input fields."""
        if not username or not password:
            ui.notify("Nome de usuário e senha são obrigatórios", type="negative")
            return False

        if confirm_password and password != confirm_password:
            ui.notify("Senhas não coincidem", type="negative")
            return False

        if len(password) < 6:
            ui.notify("Senha deve ter pelo menos 6 caracteres", type="negative")
            return False

        return True

    def _create_user(
        self,
        dialog: ui.dialog,
        username: str,
        password: str,
        confirm_password: str,
        role: str,
        enable_2fa: bool
    ) -> None:
        """Create a new user."""
        try:
            if not self._validate_user_input(username, password, confirm_password):
                return

            # API call to create user
            response = requests.post(
                config.get_api_endpoint("/admin/users"),
                json={
                    "username": username,
                    "password": password,
                    "role": role,
                    "enable_2fa": enable_2fa
                },
                timeout=10
            )

            if response.status_code == 201:
                ui.notify(f"Usuário '{username}' criado com sucesso!", type="positive")
                dialog.close()
                self._refresh_users_data()
            else:
                error_msg = response.json().get("detail", "Erro desconhecido")
                ui.notify(f"Erro ao criar usuário: {error_msg}", type="negative")

        except Exception as e:
            ui.notify(f"Erro de conexão: {str(e)}", type="negative")

    def _update_user(
        self,
        dialog: ui.dialog,
        user_id: str,
        username: str,
        role: str,
        is_active: bool,
        new_password: str,
        confirm_new_password: str
    ) -> None:
        """Update an existing user."""
        try:
            # Validation
            if not username:
                ui.notify("Nome de usuário é obrigatório", type="negative")
                return

            if new_password and not self._validate_user_input(username, new_password, confirm_new_password):
                return

            # Prepare update data
            update_data = {
                "username": username,
                "role": role,
                "is_active": is_active
            }

            if new_password:
                update_data["password"] = new_password

            # API call to update user
            response = requests.put(
                config.get_api_endpoint(f"/admin/users/{user_id}"),
                json=update_data,
                timeout=10
            )

            if response.status_code == 200:
                ui.notify(f"Usuário '{username}' atualizado com sucesso!", type="positive")
                dialog.close()
                self._refresh_users_data()
            else:
                error_msg = response.json().get("detail", "Erro desconhecido")
                ui.notify(f"Erro ao atualizar usuário: {error_msg}", type="negative")

        except Exception as e:
            ui.notify(f"Erro de conexão: {str(e)}", type="negative")

    def _delete_user(self, dialog: ui.dialog, user_id: str) -> None:
        """Delete a user."""
        try:
            # API call to delete user
            response = requests.delete(
                config.get_api_endpoint(f"/admin/users/{user_id}"),
                timeout=10
            )

            if response.status_code == 204:
                ui.notify("Usuário excluído com sucesso!", type="positive")
                dialog.close()
                self._refresh_users_data()
            else:
                error_msg = response.json().get("detail", "Erro desconhecido")
                ui.notify(f"Erro ao excluir usuário: {error_msg}", type="negative")

        except Exception as e:
            ui.notify(f"Erro de conexão: {str(e)}", type="negative")

    def _reset_2fa(self, user_id: str) -> None:
        """Reset 2FA for a user."""
        try:
            response = requests.post(
                config.get_api_endpoint(f"/admin/users/{user_id}/reset-2fa"),
                timeout=10
            )

            if response.status_code == 200:
                ui.notify("2FA resetado com sucesso!", type="positive")
                self._refresh_users_data()
            else:
                error_msg = response.json().get("detail", "Erro desconhecido")
                ui.notify(f"Erro ao resetar 2FA: {error_msg}", type="negative")

        except Exception as e:
            ui.notify(f"Erro de conexão: {str(e)}", type="negative")

    def _load_users_data(self) -> None:
        """Load users data from API."""
        try:
            response = requests.get(
                config.get_api_endpoint("/admin/users"),
                timeout=10
            )
            if response.status_code == 200:
                self.users_data = response.json()
                self._filter_and_update_table()
            else:
                self.users_data = []
                ui.notify("Erro ao carregar dados dos usuários", type="warning")
        except Exception as e:
            ui.notify(f"Erro de conexão com API: {str(e)}", type="negative")
            self.users_data = []
            if self.users_container:
                self.users_container.clear()
                with self.users_container:
                    ui.label("Erro ao carregar usuários").classes("text-center q-pa-lg text-red")

    def _refresh_users_data(self) -> None:
        """Refresh users data."""
        self._load_users_data()
