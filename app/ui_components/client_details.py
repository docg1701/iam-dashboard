"""Client details page UI component with document listing."""

import uuid

from nicegui import ui

from app.core.auth import AuthManager
from app.core.database import get_async_db
from app.models.client import Client
from app.models.document import Document
from app.repositories.client_repository import ClientRepository
from app.services.client_service import ClientService
from app.ui_components.document_list import DocumentListComponent


class ClientDetailsPage:
    """Client details page component with document listing."""

    def __init__(self, client_id: str) -> None:
        """Initialize the client details page."""
        self.client_id = uuid.UUID(client_id)
        self.client: Client | None = None
        self.document_list_component: DocumentListComponent | None = None

    def create(self) -> None:
        """Create the client details page UI."""
        # Check authentication
        if not AuthManager.require_auth():
            return

        current_user = AuthManager.get_current_user()
        if not current_user:
            ui.navigate.to("/login")
            return

        with ui.column().classes("w-full max-w-6xl mx-auto mt-10 p-6"):
            # Header
            with ui.row().classes("w-full justify-between items-center mb-8"):
                with ui.row().classes("items-center gap-4"):
                    ui.button(
                        "← Voltar para Clientes",
                        on_click=lambda: ui.navigate.to("/clients"),
                    ).classes(
                        "bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                    )

                with ui.row().classes("items-center gap-4"):
                    ui.label(f"Olá, {current_user['username']}").classes("text-lg")
                    ui.button("Sair", on_click=self._handle_logout).classes(
                        "bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                    )

            # Client information section (will be populated after loading)
            self.client_info_container = ui.column().classes("w-full")

            # Documents section
            with ui.column().classes("w-full mt-8"):
                # Create document list component
                self.document_list_component = DocumentListComponent(
                    client_id=self.client_id,
                    on_view_summary=self._handle_view_summary,
                    on_download=self._handle_download,
                )
                self.document_list_component.create()

        # Load initial data
        ui.timer(0.1, self._load_client, once=True)

    async def _load_client(self) -> None:
        """Load client information from database."""
        try:
            async for db_session in get_async_db():
                client_repository = ClientRepository(db_session)
                client_service = ClientService(client_repository)

                self.client = await client_service.get_client_by_id(self.client_id)

                if not self.client:
                    ui.notify("Cliente não encontrado", type="negative")
                    ui.navigate.to("/clients")
                    return

                # Update client info section
                self.client_info_container.clear()
                with self.client_info_container:
                    with ui.card().classes("w-full p-6"):
                        ui.label("Informações do Cliente").classes(
                            "text-2xl font-bold mb-4"
                        )

                        with ui.row().classes("w-full gap-8"):
                            with ui.column().classes("flex-1"):
                                ui.label(f"Nome: {self.client.name}").classes(
                                    "text-lg font-semibold"
                                )
                                ui.label(f"CPF: {self.client.formatted_cpf}").classes(
                                    "text-lg"
                                )

                            with ui.column().classes("flex-1"):
                                birth_date_str = (
                                    self.client.birth_date.strftime("%d/%m/%Y")
                                    if self.client.birth_date
                                    else "Não informado"
                                )
                                ui.label(
                                    f"Data de Nascimento: {birth_date_str}"
                                ).classes("text-lg")
                                created_at_str = (
                                    self.client.created_at.strftime("%d/%m/%Y às %H:%M")
                                    if self.client.created_at
                                    else "Não informado"
                                )
                                ui.label(f"Cliente desde: {created_at_str}").classes(
                                    "text-lg"
                                )

        except Exception as e:
            ui.notify(f"Erro ao carregar dados do cliente: {str(e)}", type="negative")

    def _handle_view_summary(self, document: Document) -> None:
        """Handle view document summary action."""
        if document.status != "processed":
            ui.notify(
                "Resumo disponível apenas para documentos processados", type="warning"
            )
            return

        # Import here to avoid circular imports
        from app.ui_components.document_summary import DocumentSummaryModal

        # Show document summary modal
        summary_modal = DocumentSummaryModal(document)
        summary_modal.show()

    def _handle_download(self, document: Document) -> None:
        """Handle document download action."""
        # This would implement document download functionality
        # For now, just show a notification
        ui.notify("Funcionalidade de download será implementada", type="info")

    def _handle_logout(self) -> None:
        """Handle user logout."""
        AuthManager.logout_user()
        ui.notify("Saída realizada com sucesso", type="positive")
        ui.navigate.to("/login")

    def cleanup(self) -> None:
        """Cleanup resources when page is destroyed."""
        if self.document_list_component:
            self.document_list_component.cleanup()


def client_details_page(client_id: str) -> None:
    """Create and display the client details page."""
    page = ClientDetailsPage(client_id)
    page.create()
