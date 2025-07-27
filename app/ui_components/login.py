"""Login page UI component."""

from nicegui import ui

from app.core.auth import AuthManager
from app.core.database import get_async_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


class LoginPage:
    """Login page component."""

    def __init__(self) -> None:
        """Initialize the login page."""
        self.username_input: ui.input | None = None
        self.password_input: ui.input | None = None
        self.totp_input: ui.input | None = None
        self.totp_container: ui.element | None = None
        self.login_button: ui.button | None = None
        self.current_user = None
        self.pending_2fa = False

    def create(self) -> None:
        """Create the login page UI."""
        # Check if already authenticated
        if AuthManager.is_authenticated():
            ui.navigate.to("/dashboard")
            return

        with ui.column().classes(
            "w-full max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md"
        ):
            ui.label("Login").classes("text-2xl font-bold text-center mb-6")

            # Username input
            self.username_input = (
                ui.input(
                    label="Nome de usuário", placeholder="Digite seu nome de usuário"
                )
                .classes("w-full mb-4")
                .on("keydown.enter", self._handle_login)
            )

            # Password input
            self.password_input = (
                ui.input(
                    label="Senha",
                    placeholder="Digite sua senha",
                    password=True,
                    password_toggle_button=True,
                )
                .classes("w-full mb-4")
                .on("keydown.enter", self._handle_login)
            )

            # 2FA container (hidden initially)
            self.totp_container = (
                ui.column().classes("w-full mb-4").style("display: none")
            )
            with self.totp_container:
                ui.label("Código de Autenticação em Dois Fatores").classes(
                    "text-sm font-medium mb-2"
                )
                self.totp_input = (
                    ui.input(
                        label="Código 2FA", placeholder="Digite o código de 6 dígitos"
                    )
                    .classes("w-full")
                    .on("keydown.enter", self._handle_2fa_login)
                )

            # Login button
            self.login_button = ui.button(
                "Entrar", on_click=self._handle_login
            ).classes(
                "w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 mb-4"
            )

            # Register link
            with ui.row().classes("w-full justify-center"):
                ui.label("Não tem uma conta?")
                ui.link("Registrar-se", "/register").classes(
                    "text-blue-500 hover:text-blue-700"
                )

    async def _handle_login(self) -> None:
        """Handle user login (first step - username/password)."""
        try:
            if self.pending_2fa:
                await self._handle_2fa_login()
                return

            # Validate inputs
            if not self._validate_login_inputs():
                return

            username = self.username_input.value.strip()
            password = self.password_input.value

            # Authenticate user
            async for db_session in get_async_db():
                user_repository = UserRepository(db_session)
                user_service = UserService(user_repository)

                user = await user_service.authenticate_user(username, password)

                if not user:
                    ui.notify("Credenciais inválidas", type="negative")
                    return

                if not user.is_active:
                    ui.notify("Conta desativada", type="negative")
                    return

                # Check if 2FA is enabled
                if user.is_2fa_enabled:
                    self.current_user = user
                    self.pending_2fa = True
                    self._show_2fa_input()
                else:
                    # Complete login without 2FA
                    AuthManager.login_user(
                        str(user.id),
                        user.username,
                        user.role,
                        user.is_active,
                        user.is_2fa_enabled,
                    )
                    ui.notify(f"Bem-vindo, {user.username}!", type="positive")
                    ui.navigate.to("/dashboard")

        except Exception as e:
            ui.notify(f"Erro interno: {str(e)}", type="negative")

    async def _handle_2fa_login(self) -> None:
        """Handle 2FA verification."""
        try:
            if not self.current_user or not self.pending_2fa:
                ui.notify("Erro de estado de autenticação", type="negative")
                return

            totp_code = self.totp_input.value.strip() if self.totp_input.value else ""

            if not totp_code:
                ui.notify("Código 2FA é obrigatório", type="negative")
                return

            if len(totp_code) != 6 or not totp_code.isdigit():
                ui.notify("Código 2FA deve ter 6 dígitos", type="negative")
                return

            # Verify 2FA code
            async for db_session in get_async_db():
                user_repository = UserRepository(db_session)
                user_service = UserService(user_repository)

                is_valid = await user_service.verify_totp_code(
                    self.current_user, totp_code
                )

                if not is_valid:
                    ui.notify("Código 2FA inválido", type="negative")
                    return

                # Complete login
                AuthManager.login_user(
                    str(self.current_user.id),
                    self.current_user.username,
                    self.current_user.role,
                    self.current_user.is_active,
                    self.current_user.is_2fa_enabled,
                )
                ui.notify(f"Bem-vindo, {self.current_user.username}!", type="positive")
                ui.navigate.to("/dashboard")

        except Exception as e:
            ui.notify(f"Erro interno: {str(e)}", type="negative")

    def _validate_login_inputs(self) -> bool:
        """Validate login form inputs."""
        username = (
            self.username_input.value.strip() if self.username_input.value else ""
        )
        password = self.password_input.value if self.password_input.value else ""

        if not username:
            ui.notify("Nome de usuário é obrigatório", type="negative")
            return False

        if not password:
            ui.notify("Senha é obrigatória", type="negative")
            return False

        return True

    def _show_2fa_input(self) -> None:
        """Show 2FA input field."""
        self.totp_container.style("display: block")
        self.login_button.text = "Verificar 2FA"
        ui.notify("Digite o código de autenticação em dois fatores", type="info")


def login_page() -> None:
    """Create and display the login page."""
    page = LoginPage()
    page.create()
