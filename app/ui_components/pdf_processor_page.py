"""Standalone PDF processor page using DocumentUploadComponent with client selection."""

import uuid
from typing import Any

from nicegui import ui

from app.core.auth import AuthManager
from app.core.database import get_async_db
from app.repositories.client_repository import ClientRepository
from app.ui_components.document_upload import DocumentUploadComponent


class PDFProcessorPage:
    """Standalone PDF processor page with client selection and document upload."""
    
    def __init__(self) -> None:
        """Initialize the PDF processor page."""
        self.selected_client_id: uuid.UUID | None = None
        self.client_select: ui.select | None = None
        self.upload_container: ui.column | None = None

    def create(self) -> None:
        """Create the PDF processor page."""
        if not AuthManager.require_auth():
            return
            
        current_user = AuthManager.get_current_user()
        
        with ui.column().classes("w-full max-w-6xl mx-auto mt-6 p-6"):
            # Header with navigation
            with ui.row().classes("w-full justify-between items-center mb-8"):
                ui.button("← Dashboard", on_click=lambda: ui.navigate.to("/dashboard")).classes(
                    "bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                )
                ui.label("Processador de PDFs").classes("text-3xl font-bold text-blue-600")
                ui.label(f"Olá, {current_user['username']}").classes("text-lg text-gray-600")
            
            # Client selection section
            with ui.card().classes("w-full p-6 mb-6"):
                ui.label("Selecione o Cliente").classes("text-xl font-semibold mb-4")
                ui.label("Escolha o cliente para associar os documentos processados").classes(
                    "text-gray-600 mb-4"
                )
                
                # Client dropdown
                with ui.row().classes("w-full items-end gap-4"):
                    self.client_select = ui.select(
                        label="Cliente",
                        options={},
                        on_change=self._on_client_selected
                    ).classes("flex-1")
                    
                    ui.button("Atualizar Lista", on_click=self._refresh_clients).classes(
                        "bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                    )
            
            # Upload container (shown after client selection)
            self.upload_container = ui.column().classes("w-full")
            
            # Load clients on page creation
            ui.timer(0.1, self._refresh_clients, once=True)
    
    async def _refresh_clients(self) -> None:
        """Refresh the client list."""
        try:
            async for db in get_async_db():
                client_repo = ClientRepository(db)
                clients = await client_repo.get_all()
                
                # Update client options
                client_options = {str(client.id): f"{client.name} - CPF: {client.cpf}" 
                                for client in clients}
                
                if client_options:
                    self.client_select.options = client_options
                    self.client_select.update()
                else:
                    ui.notify("Nenhum cliente encontrado. Crie um cliente primeiro.", type="warning")
                break
                    
        except Exception as e:
            ui.notify(f"Erro ao carregar clientes: {str(e)}", type="negative")
    
    def _on_client_selected(self, event: Any) -> None:
        """Handle client selection."""
        if not event.value:
            self.selected_client_id = None
            self.upload_container.clear()
            return
            
        try:
            self.selected_client_id = uuid.UUID(event.value)
            self._show_upload_component()
        except ValueError:
            ui.notify("ID de cliente inválido", type="negative")
    
    def _show_upload_component(self) -> None:
        """Show the document upload component."""
        if not self.selected_client_id:
            return
            
        self.upload_container.clear()
        
        with self.upload_container:
            # Create and show the document upload component
            document_upload = DocumentUploadComponent(self.selected_client_id)
            document_upload.create()


def pdf_processor_page() -> None:
    """Create the standalone PDF processor page."""
    page = PDFProcessorPage()
    page.create()