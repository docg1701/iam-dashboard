"""Registration page UI component."""

import base64
import io

import qrcode
from nicegui import ui

from app.core.database import get_async_db
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


class RegisterPage:
    """Registration page component."""

    def __init__(self) -> None:
        """Initialize the registration page."""
        self.username_input: ui.input | None = None
        self.password_input: ui.input | None = None
        self.confirm_password_input: ui.input | None = None
        self.role_select: ui.select | None = None
        self.enable_2fa_checkbox: ui.checkbox | None = None
        self.qr_code_container: ui.element | None = None

    def create(self) -> None:
        """Create the registration page UI."""
        with ui.column().classes(
            "w-full max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md"
        ):
            ui.label("Registro de Usuário").classes(
                "text-2xl font-bold text-center mb-6"
            )

            # Username input
            self.username_input = ui.input(
                label="Nome de usuário", placeholder="Digite seu nome de usuário"
            ).classes("w-full mb-4")

            # Password inputs
            self.password_input = ui.input(
                label="Senha",
                placeholder="Digite sua senha",
                password=True,
                password_toggle_button=True,
            ).classes("w-full mb-4")

            self.confirm_password_input = ui.input(
                label="Confirmar senha",
                placeholder="Confirme sua senha",
                password=True,
                password_toggle_button=True,
            ).classes("w-full mb-4")

            # Role selection (for admin users)
            self.role_select = ui.select(
                options={
                    UserRole.COMMON_USER.value: "Usuário Comum",
                    UserRole.ADMIN_USER.value: "Usuário Administrador",
                    UserRole.SYSADMIN.value: "Administrador do Sistema",
                },
                value=UserRole.COMMON_USER.value,
                label="Função",
            ).classes("w-full mb-4")

            # 2FA option
            self.enable_2fa_checkbox = ui.checkbox(
                "Habilitar Autenticação em Dois Fatores (2FA)", value=True
            ).classes("mb-4")

            # QR Code container (hidden initially)
            self.qr_code_container = (
                ui.column().classes("w-full mb-4").style("display: none")
            )

            # Register button
            ui.button("Registrar", on_click=self._handle_register).classes(
                "w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
            )

            # Login link
            with ui.row().classes("w-full mt-4 justify-center"):
                ui.label("Já tem uma conta?")
                ui.link("Fazer login", "/login").classes(
                    "text-blue-500 hover:text-blue-700"
                )

    async def _handle_register(self) -> None:
        """Handle user registration."""
        try:
            # Validate inputs
            if not self._validate_inputs():
                return

            # Get form values
            username = self.username_input.value.strip()
            password = self.password_input.value
            role = self.role_select.value  # Already the correct enum value
            enable_2fa = self.enable_2fa_checkbox.value

            # Create user service
            async for db_session in get_async_db():
                user_repository = UserRepository(db_session)
                user_service = UserService(user_repository)

                try:
                    # Create user
                    user = await user_service.create_user(
                        username=username,
                        password=password,
                        role=role,
                        enable_2fa=enable_2fa,
                    )

                    if enable_2fa and user.totp_secret:
                        # Show QR code for 2FA setup
                        self._show_2fa_qr_code(user_service, user)
                        ui.notify(
                            "Usuário criado com sucesso! Configure o 2FA escaneando o QR code.",
                            type="positive",
                        )
                    else:
                        ui.notify("Usuário criado com sucesso!", type="positive")
                        ui.navigate.to("/login")

                except ValueError as e:
                    ui.notify(str(e), type="negative")

        except Exception as e:
            ui.notify(f"Erro interno: {str(e)}", type="negative")

    def _validate_inputs(self) -> bool:
        """Validate form inputs."""
        username = (
            self.username_input.value.strip() if self.username_input.value else ""
        )
        password = self.password_input.value if self.password_input.value else ""
        confirm_password = (
            self.confirm_password_input.value
            if self.confirm_password_input.value
            else ""
        )

        if not username:
            ui.notify("Nome de usuário é obrigatório", type="negative")
            return False

        if len(username) < 3:
            ui.notify(
                "Nome de usuário deve ter pelo menos 3 caracteres", type="negative"
            )
            return False

        if not password:
            ui.notify("Senha é obrigatória", type="negative")
            return False

        if len(password) < 8:
            ui.notify("Senha deve ter pelo menos 8 caracteres", type="negative")
            return False

        if password != confirm_password:
            ui.notify("Senhas não coincidem", type="negative")
            return False

        return True

    def _show_2fa_qr_code(self, user_service: UserService, user) -> None:
        """Show QR code for 2FA setup."""
        try:
            # Get provisioning URI
            provisioning_uri = user_service.get_totp_provisioning_uri(user)
            if not provisioning_uri:
                return

            # Generate QR code
            qr_code = qrcode.QRCode(version=1, box_size=10, border=5)
            qr_code.add_data(provisioning_uri)
            qr_code.make(fit=True)

            # Create QR code image
            qr_image = qr_code.make_image(fill_color="black", back_color="white")

            # Convert to base64 for display
            img_buffer = io.BytesIO()
            qr_image.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

            # Show QR code
            with self.qr_code_container:
                self.qr_code_container.clear()
                ui.label("Configure o 2FA escaneando o QR code:").classes(
                    "text-center mb-2"
                )
                ui.html(
                    f'<img src="data:image/png;base64,{img_base64}" class="mx-auto">'
                ).classes("mb-2")
                ui.label(f"Chave manual: {user.totp_secret}").classes(
                    "text-xs text-gray-600 text-center mb-4"
                )
                ui.button(
                    "Continuar para Login", on_click=lambda: ui.navigate.to("/login")
                ).classes(
                    "w-full bg-green-500 text-white py-2 px-4 rounded hover:bg-green-600"
                )

            self.qr_code_container.style("display: block")

        except Exception as e:
            ui.notify(f"Erro ao gerar QR code: {str(e)}", type="warning")


def register_page() -> None:
    """Create and display the registration page."""
    page = RegisterPage()
    page.create()
