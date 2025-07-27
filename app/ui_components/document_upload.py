"""Document upload UI component."""

import hashlib

import httpx
from nicegui import events, ui

from app.core.database import get_async_db
from app.models.client import Client
from app.models.document import DocumentType
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService


class DocumentUploadDialog:
    """Document upload dialog component."""

    def __init__(self, client: Client) -> None:
        """Initialize the document upload dialog."""
        self.client = client
        self.dialog: ui.dialog | None = None
        self.file_upload: ui.upload | None = None
        self.document_type_select: ui.select | None = None
        self.uploaded_file_info: dict | None = None
        self.processing_status_container: ui.column | None = None
        self.current_task_id: str | None = None
        self.status_timer: ui.timer | None = None

    def show(self) -> None:
        """Show the document upload dialog."""
        with ui.dialog() as self.dialog:
            with ui.card().classes("w-96 p-6"):
                ui.label(f"Upload de Documento - {self.client.name}").classes(
                    "text-xl font-bold mb-4"
                )

                with ui.column().classes("w-full gap-4"):
                    # File upload component
                    ui.label("Selecione um arquivo PDF:").classes("text-sm font-medium")
                    self.file_upload = (
                        ui.upload(
                            on_upload=self._handle_file_upload,
                            on_rejected=self._handle_file_rejected,
                            multiple=False,
                            max_file_size=50 * 1024 * 1024,  # 50MB limit
                            auto_upload=True,
                        )
                        .classes("w-full")
                        .props(
                            "accept='.pdf' label='Arrastar PDF aqui ou clicar para selecionar'"
                        )
                    )

                    # Document type selection
                    ui.label("Classificação do documento:").classes(
                        "text-sm font-medium"
                    )
                    self.document_type_select = ui.select(
                        options={
                            DocumentType.SIMPLE: "Simples (PDF digital com texto selecionável)",
                            DocumentType.COMPLEX: "Complexo (PDF escaneado, requer OCR)",
                        },
                        label="Tipo de documento",
                        value=DocumentType.SIMPLE,
                    ).classes("w-full")

                    # Information about the selected file
                    with ui.column().classes("w-full") as self.file_info_container:
                        pass

                    # Processing status information
                    with ui.column().classes(
                        "w-full"
                    ) as self.processing_status_container:
                        pass

                    # Action buttons
                    with ui.row().classes("w-full justify-end gap-2 mt-4"):
                        ui.button("Cancelar", on_click=self._close_dialog).classes(
                            "bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                        )

                        ui.button(
                            "Enviar Documento", on_click=self._submit_document
                        ).classes(
                            "bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                        ).bind_enabled_from(
                            self, "uploaded_file_info", lambda x: x is not None
                        )

        self.dialog.open()

    def _handle_file_upload(self, event: events.UploadEventArguments) -> None:
        """Handle file upload event."""
        try:
            filename = event.name
            file_content = event.content

            # Handle SpooledTemporaryFile or bytes content
            if hasattr(file_content, 'read'):
                # It's a file-like object (SpooledTemporaryFile)
                file_content.seek(0)  # Ensure we're at the beginning
                content_bytes = file_content.read()
                file_content.seek(0)  # Reset for potential future reads
            else:
                # It's already bytes
                content_bytes = file_content

            # Validate file type
            if not filename.lower().endswith(".pdf"):
                ui.notify("Apenas arquivos PDF são permitidos", type="negative")
                return

            # Store file info
            self.uploaded_file_info = {
                "filename": filename,
                "content": content_bytes,
                "size": len(content_bytes),
            }

            # Calculate file hash
            hash_obj = hashlib.sha256(content_bytes)
            file_hash = hash_obj.hexdigest()
            self.uploaded_file_info["hash"] = file_hash

            # Update file info display
            self._update_file_info()

            ui.notify(f"Arquivo '{filename}' carregado com sucesso", type="positive")

        except Exception as e:
            ui.notify(f"Erro ao carregar arquivo: {str(e)}", type="negative")

    def _handle_file_rejected(self, event) -> None:
        """Handle file rejection."""
        ui.notify(
            "Arquivo rejeitado. Verifique o tipo e tamanho do arquivo.", type="negative"
        )

    def _update_file_info(self) -> None:
        """Update the file information display."""
        if not self.uploaded_file_info:
            return

        self.file_info_container.clear()

        with self.file_info_container:
            ui.separator().classes("my-2")
            ui.label("Informações do arquivo:").classes("text-sm font-medium")

            with ui.column().classes("w-full gap-1 text-sm"):
                ui.label(f"Nome: {self.uploaded_file_info['filename']}")
                ui.label(
                    f"Tamanho: {self._format_file_size(self.uploaded_file_info['size'])}"
                )
                ui.label(f"Hash SHA256: {self.uploaded_file_info['hash'][:16]}...")

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    async def _submit_document(self) -> None:
        """Submit the document for processing."""
        if not self.uploaded_file_info:
            ui.notify("Nenhum arquivo selecionado", type="negative")
            return

        try:
            # Get selected document type
            document_type = self.document_type_select.value

            async for db_session in get_async_db():
                document_repository = DocumentRepository(db_session)
                document_service = DocumentService(document_repository)

                # Create the document
                result = await document_service.create_document(
                    client_id=self.client.id,
                    filename=self.uploaded_file_info["filename"],
                    content=self.uploaded_file_info["content"],
                    document_type=document_type,
                )

                if result.get("success"):
                    ui.notify(
                        "Documento enviado com sucesso! Processamento iniciado.",
                        type="positive",
                    )

                    # If we have a task ID, start tracking the processing status
                    task_id = result.get("task_id")
                    if task_id:
                        self.current_task_id = task_id
                        self._start_status_tracking()
                    else:
                        # No task ID means processing didn't start, close dialog
                        self._close_dialog()
                else:
                    ui.notify(result.get("error", "Erro desconhecido"), type="negative")

        except Exception as e:
            ui.notify(f"Erro ao enviar documento: {str(e)}", type="negative")

    def _start_status_tracking(self) -> None:
        """Start tracking the processing status."""
        if not self.current_task_id:
            return

        # Update UI to show processing state
        self._update_processing_status("PENDING", "Iniciando processamento...")

        # Hide upload controls
        self.file_upload.set_visibility(False)
        self.document_type_select.set_visibility(False)

        # Start polling for status updates
        self.status_timer = ui.timer(2.0, self._check_task_status)

    async def _check_task_status(self) -> None:
        """Check the current task status via API."""
        if not self.current_task_id:
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"/v1/documents/tasks/{self.current_task_id}"
                )

                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status", "UNKNOWN")
                    error = status_data.get("error")

                    if status == "SUCCESS":
                        self._update_processing_status(
                            "SUCCESS", "Documento processado com sucesso!"
                        )
                        self._stop_status_tracking()
                        ui.timer(
                            3.0, self._close_dialog, once=True
                        )  # Auto-close after 3 seconds

                    elif status == "FAILURE":
                        error_msg = error or "Erro desconhecido durante o processamento"
                        self._update_processing_status("FAILURE", f"Erro: {error_msg}")
                        self._stop_status_tracking()

                    elif status == "PENDING":
                        self._update_processing_status(
                            "PENDING", "Aguardando início do processamento..."
                        )

                    elif status == "STARTED":
                        self._update_processing_status(
                            "PROCESSING", "Processando documento..."
                        )

                    else:
                        self._update_processing_status(status, f"Status: {status}")

                else:
                    self._update_processing_status(
                        "ERROR", "Erro ao verificar status do processamento"
                    )

        except Exception as e:
            self._update_processing_status("ERROR", f"Erro de conexão: {str(e)}")

    def _update_processing_status(self, status: str, message: str) -> None:
        """Update the processing status display."""
        if not self.processing_status_container:
            return

        self.processing_status_container.clear()

        with self.processing_status_container:
            ui.separator().classes("my-4")
            ui.label("Status do Processamento:").classes("text-sm font-medium")

            # Status indicator with color coding
            if status in ["SUCCESS"]:
                status_color = "text-green-600"
                icon = "✅"
            elif status in ["FAILURE", "ERROR"]:
                status_color = "text-red-600"
                icon = "❌"
            elif status in ["PENDING", "STARTED", "PROCESSING"]:
                status_color = "text-blue-600"
                icon = "🔄"
            else:
                status_color = "text-gray-600"
                icon = "❓"

            with ui.row().classes("items-center gap-2"):
                ui.label(icon).classes("text-lg")
                ui.label(message).classes(f"text-sm {status_color}")

            # Show progress spinner for active states
            if status in ["PENDING", "STARTED", "PROCESSING"]:
                ui.spinner(size="sm").classes("mt-2")

    def _stop_status_tracking(self) -> None:
        """Stop the status tracking timer."""
        if self.status_timer:
            self.status_timer.cancel()
            self.status_timer = None

    def _close_dialog(self) -> None:
        """Close the upload dialog."""
        self._stop_status_tracking()
        if self.dialog:
            self.dialog.close()
