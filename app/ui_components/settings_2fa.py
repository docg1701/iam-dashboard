"""2FA settings page UI component."""

import base64
import io

import qrcode
from nicegui import ui

from app.core.auth import AuthManager
from app.core.database import get_async_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


class Settings2FAPage:
    """2FA settings page component."""

    def __init__(self) -> None:
        """Initialize the 2FA settings page."""
        self.current_user_data = None
        self.current_user_obj = None
        self.qr_code_container: ui.element | None = None
        self.totp_input: ui.input | None = None

    def create(self) -> None:
        """Create the 2FA settings page UI."""
        # Check authentication
        if not AuthManager.require_auth():
            return

        self.current_user_data = AuthManager.get_current_user()

        with ui.column().classes("w-full max-w-2xl mx-auto mt-10 p-6"):
            # Header
            with ui.row().classes("w-full justify-between items-center mb-8"):
                ui.label("Configurações de 2FA").classes("text-2xl font-bold")
                ui.button(
                    "Voltar", on_click=lambda: ui.navigate.to("/dashboard")
                ).classes("bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600")

            # Load current user status
            ui.timer(0.1, self._load_user_status, once=True)

    async def _load_user_status(self) -> None:
        """Load current user's 2FA status."""
        try:
            async for db_session in get_async_db():
                user_repository = UserRepository(db_session)
                user_service = UserService(user_repository)

                self.current_user_obj = await user_service.get_user_by_username(
                    self.current_user_data["username"]
                )

                if not self.current_user_obj:
                    ui.notify("Erro ao carregar dados do usuário", type="negative")
                    return

                self._render_2fa_status()

        except Exception as e:
            ui.notify(f"Erro interno: {str(e)}", type="negative")

    def _render_2fa_status(self) -> None:
        """Render the 2FA status and controls."""
        with ui.card().classes("w-full p-6"):
            ui.label("Status da Autenticação em Dois Fatores").classes(
                "text-xl font-semibold mb-4"
            )

            if self.current_user_obj.is_2fa_enabled:
                # 2FA is enabled
                ui.label("✅ 2FA está HABILITADO").classes(
                    "text-green-600 font-medium mb-4"
                )

                ui.label(
                    "Sua conta está protegida com autenticação em dois fatores."
                ).classes("text-gray-600 mb-4")

                ui.button("Desabilitar 2FA", on_click=self._handle_disable_2fa).classes(
                    "bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                )

            else:
                # 2FA is disabled
                ui.label("⚠️ 2FA está DESABILITADO").classes(
                    "text-orange-600 font-medium mb-4"
                )

                ui.label(
                    "Sua conta não está protegida com 2FA. Recomendamos habilitar para maior segurança."
                ).classes("text-gray-600 mb-4")

                ui.button("Habilitar 2FA", on_click=self._handle_enable_2fa).classes(
                    "bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                )

            # Container for QR code (initially hidden)
            self.qr_code_container = (
                ui.column().classes("w-full mt-6").style("display: none")
            )

    async def _handle_enable_2fa(self) -> None:
        """Handle enabling 2FA."""
        try:
            async for db_session in get_async_db():
                user_repository = UserRepository(db_session)
                user_service = UserService(user_repository)

                # Get fresh user object from current session
                current_user = await user_repository.get_by_id(self.current_user_obj.id)
                if not current_user:
                    ui.notify("Usuário não encontrado", type="negative")
                    return

                # Enable 2FA and get secret
                secret = await user_service.enable_2fa(current_user)

                # Show QR code for setup
                self._show_2fa_setup(user_service, secret)

        except Exception as e:
            ui.notify(f"Erro ao habilitar 2FA: {str(e)}", type="negative")

    async def _handle_disable_2fa(self) -> None:
        """Handle disabling 2FA."""
        try:
            async for db_session in get_async_db():
                user_repository = UserRepository(db_session)
                user_service = UserService(user_repository)

                # Get fresh user object from current session
                current_user = await user_repository.get_by_id(self.current_user_obj.id)
                if not current_user:
                    ui.notify("Usuário não encontrado", type="negative")
                    return

                # Disable 2FA
                await user_service.disable_2fa(current_user)

                ui.notify("2FA desabilitado com sucesso", type="positive")

                # Refresh the page
                ui.navigate.to("/settings/2fa")

        except Exception as e:
            ui.notify(f"Erro ao desabilitar 2FA: {str(e)}", type="negative")

    def _show_2fa_setup(self, user_service: UserService, secret: str) -> None:
        """Show QR code for 2FA setup."""
        try:
            # Get provisioning URI
            provisioning_uri = user_service.get_totp_provisioning_uri(
                self.current_user_obj
            )
            if not provisioning_uri:
                ui.notify("Erro ao gerar URI de configuração", type="negative")
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

            # Show QR code setup
            with self.qr_code_container:
                self.qr_code_container.clear()

                ui.label("Configure seu aplicativo 2FA").classes(
                    "text-lg font-semibold mb-4"
                )

                ui.label(
                    "1. Instale um aplicativo de autenticação (Google Authenticator, Authy, etc.)"
                ).classes("mb-2")
                ui.label("2. Escaneie o QR code abaixo:").classes("mb-4")

                ui.html(
                    f'<img src="data:image/png;base64,{img_base64}" class="mx-auto mb-4">'
                ).classes("w-full flex justify-center")

                ui.label("Ou digite manualmente esta chave:").classes(
                    "text-sm text-gray-600 mb-2"
                )
                ui.input(value=secret, readonly=True).classes("w-full mb-4")

                ui.label(
                    "3. Digite o código de 6 dígitos do seu aplicativo para confirmar:"
                ).classes("mb-2")
                self.totp_input = ui.input(
                    label="Código de verificação", placeholder="000000"
                ).classes("w-full mb-4")

                ui.button(
                    "Verificar e Ativar", on_click=self._handle_verify_2fa_setup
                ).classes(
                    "w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
                )

            self.qr_code_container.style("display: block")
            ui.notify(
                "2FA configurado! Escaneie o QR code para ativar.", type="positive"
            )

        except Exception as e:
            ui.notify(f"Erro ao gerar QR code: {str(e)}", type="negative")

    async def _handle_verify_2fa_setup(self) -> None:
        """Handle verification of 2FA setup."""
        try:
            totp_code = self.totp_input.value.strip() if self.totp_input.value else ""

            if not totp_code:
                ui.notify("Código de verificação é obrigatório", type="negative")
                return

            if len(totp_code) != 6 or not totp_code.isdigit():
                ui.notify("Código deve ter 6 dígitos", type="negative")
                return

            async for db_session in get_async_db():
                user_repository = UserRepository(db_session)
                user_service = UserService(user_repository)

                # Verify the code
                is_valid = await user_service.verify_totp_code(
                    self.current_user_obj, totp_code
                )

                if not is_valid:
                    ui.notify("Código inválido. Tente novamente.", type="negative")
                    return

                ui.notify("2FA ativado com sucesso!", type="positive")

                # Refresh the page
                ui.navigate.to("/settings/2fa")

        except Exception as e:
            ui.notify(f"Erro na verificação: {str(e)}", type="negative")


def settings_2fa_page() -> None:
    """Create and display the 2FA settings page."""
    page = Settings2FAPage()
    page.create()
