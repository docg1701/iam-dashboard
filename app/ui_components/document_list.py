"""Document list component with status information and real-time updates."""

import uuid
from collections.abc import Callable
from datetime import datetime

from nicegui import ui

from app.core.database import get_async_db
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService


class DocumentListComponent:
    """Document list component with real-time status updates."""

    def __init__(
        self,
        client_id: uuid.UUID,
        on_view_summary: Callable[[Document], None] | None = None,
        on_download: Callable[[Document], None] | None = None,
    ) -> None:
        """Initialize the document list component."""
        self.client_id = client_id
        self.on_view_summary = on_view_summary
        self.on_download = on_download
        self.documents: list[Document] = []
        self.documents_table: ui.table | None = None
        self.container: ui.column | None = None
        self.status_timer: ui.timer | None = None
        self.last_update_time: datetime | None = None

    def create(self) -> ui.column:
        """Create the document list component UI."""
        with ui.column().classes("w-full") as self.container:
            # Header with refresh button
            with ui.row().classes("w-full justify-between items-center mb-4"):
                ui.label("Documentos").classes("text-xl font-bold")

                with ui.row().classes("gap-2"):
                    # Last update indicator
                    self.last_update_label = ui.label("").classes(
                        "text-sm text-gray-500"
                    )

                    ui.button(
                        "", icon="refresh", on_click=self._manual_refresh
                    ).classes(
                        "bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
                    ).props("size=sm")

            # Documents table
            self._create_documents_table()

            # Empty state message
            self.empty_state = (
                ui.column().classes("w-full text-center py-8").style("display: none")
            )
            with self.empty_state:
                ui.icon("description", size="3em").classes("text-gray-400")
                ui.label("Nenhum documento encontrado").classes(
                    "text-lg text-gray-500 mt-2"
                )
                ui.label("Faça upload de documentos para este cliente").classes(
                    "text-sm text-gray-400"
                )

        # Load initial data
        ui.timer(0.1, self._load_documents, once=True)

        # Setup auto-refresh timer (every 5 seconds)
        self.status_timer = ui.timer(5.0, self._auto_refresh)

        return self.container

    def _create_documents_table(self) -> None:
        """Create the documents table with enhanced formatting."""
        columns = [
            {
                "name": "filename",
                "label": "Nome do Arquivo",
                "field": "filename",
                "required": True,
                "align": "left",
                "sortable": True,
            },
            {
                "name": "uploaded_at",
                "label": "Data de Upload",
                "field": "uploaded_at",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "status",
                "label": "Status",
                "field": "status",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "file_size",
                "label": "Tamanho",
                "field": "file_size",
                "align": "right",
                "sortable": True,
            },
            {
                "name": "processed_at",
                "label": "Processado em",
                "field": "processed_at",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "actions",
                "label": "Ações",
                "field": "actions",
                "align": "center",
            },
        ]

        self.documents_table = ui.table(
            columns=columns,
            rows=[],
            row_key="id",
            pagination=10,  # Enable pagination for large lists
        ).classes("w-full")

        # Enhanced status cell with animations and better indicators
        self.documents_table.add_slot(
            "body-cell-status",
            """
            <q-td key="status" :props="props">
                <q-chip
                    :color="props.row.status_color"
                    text-color="white"
                    :icon="props.row.status_icon"
                    :label="props.row.status_text"
                    size="sm"
                    :class="props.row.status === 'processing' ? 'animate-pulse' : ''"
                />
                <q-tooltip v-if="props.row.error_message">
                    {{ props.row.error_message }}
                </q-tooltip>
            </q-td>
        """,
        )

        # Enhanced actions cell with conditional buttons
        self.documents_table.add_slot(
            "body-cell-actions",
            """
            <q-td key="actions" :props="props">
                <q-btn
                    v-if="props.row.status === 'processed'"
                    flat round icon="visibility" size="sm" color="primary"
                    @click="$parent.$emit('view_summary', props.row)"
                    title="Ver Resumo do Documento"
                    class="mr-1"
                />
                <q-btn
                    v-if="props.row.status === 'failed'"
                    flat round icon="refresh" size="sm" color="orange"
                    @click="$parent.$emit('retry_processing', props.row)"
                    title="Tentar Processar Novamente"
                    class="mr-1"
                />
                <q-btn
                    flat round icon="download" size="sm" color="secondary"
                    @click="$parent.$emit('download', props.row)"
                    title="Baixar Documento Original"
                />
            </q-td>
        """,
        )

        # Handle table events
        self.documents_table.on("view_summary", self._handle_view_summary)
        self.documents_table.on("download", self._handle_download)
        self.documents_table.on("retry_processing", self._handle_retry_processing)

    async def _load_documents(self) -> None:
        """Load documents for the client."""
        try:
            async for db_session in get_async_db():
                document_repository = DocumentRepository(db_session)
                document_service = DocumentService(document_repository)

                self.documents = await document_service.get_documents_by_client(
                    self.client_id
                )

                # Update table data with enhanced formatting
                rows = []
                for document in self.documents:
                    # Enhanced status mapping with colors and icons
                    status_config = self._get_status_config(str(document.status))

                    uploaded_at_str = (
                        document.created_at.strftime("%d/%m/%Y às %H:%M")
                        if document.created_at
                        else "Não informado"
                    )

                    processed_at_str = (
                        document.processed_at.strftime("%d/%m/%Y às %H:%M")
                        if document.processed_at
                        else (
                            "Processando..." if document.status == "processing" else "-"
                        )
                    )

                    rows.append(
                        {
                            "id": str(document.id),
                            "filename": document.filename,
                            "uploaded_at": uploaded_at_str,
                            "status": document.status,
                            "status_text": status_config["text"],
                            "status_color": status_config["color"],
                            "status_icon": status_config["icon"],
                            "file_size": document.formatted_file_size,
                            "processed_at": processed_at_str,
                            "error_message": document.error_message,
                        }
                    )

                if self.documents_table:
                    self.documents_table.rows = rows
                self.last_update_time = datetime.now()
                self._update_last_update_label()

                # Show/hide empty state
                if not self.documents:
                    if self.documents_table:
                        self.documents_table.style("display: none")
                    self.empty_state.style("display: flex")
                else:
                    if self.documents_table:
                        self.documents_table.style("display: block")
                    self.empty_state.style("display: none")

        except Exception as e:
            ui.notify(f"Erro ao carregar documentos: {str(e)}", type="negative")

    def _get_status_config(self, status: str) -> dict[str, str]:
        """Get status display configuration."""
        status_configs = {
            "uploaded": {"text": "Enviado", "color": "blue", "icon": "cloud_upload"},
            "processing": {
                "text": "Processando",
                "color": "orange",
                "icon": "hourglass_empty",
            },
            "processed": {
                "text": "Concluído",
                "color": "green",
                "icon": "check_circle",
            },
            "failed": {"text": "Falha", "color": "red", "icon": "error"},
        }

        return status_configs.get(
            status, {"text": status.title(), "color": "grey", "icon": "help"}
        )

    async def _auto_refresh(self) -> None:
        """Auto-refresh document status for processing documents."""
        if not self.documents:
            return

        # Only refresh if there are documents being processed
        from app.models.document import DocumentStatus

        has_processing = any(
            doc.status in [DocumentStatus.UPLOADED, DocumentStatus.PROCESSING]
            for doc in self.documents
        )

        if has_processing:
            try:
                async for db_session in get_async_db():
                    document_repository = DocumentRepository(db_session)
                    document_service = DocumentService(document_repository)

                    # Check for status updates
                    updated_documents = []
                    for document in self.documents:
                        if document.status in [
                            DocumentStatus.UPLOADED,
                            DocumentStatus.PROCESSING,
                        ]:
                            current_doc = await document_service.get_document_by_id(
                                uuid.UUID(str(document.id))
                            )
                            if current_doc and current_doc.status != document.status:
                                updated_documents.append(current_doc)

                    if updated_documents:
                        # Reload all documents
                        await self._load_documents()

                        # Show notifications for completed/failed documents
                        for doc in updated_documents:
                            if doc.status == DocumentStatus.PROCESSED:
                                ui.notify(
                                    f"✅ Documento processado: {doc.filename}",
                                    type="positive",
                                    timeout=3000,
                                )
                            elif doc.status == DocumentStatus.FAILED:
                                ui.notify(
                                    f"❌ Erro ao processar: {doc.filename}",
                                    type="negative",
                                    timeout=5000,
                                )

            except Exception:
                # Silently handle auto-refresh errors
                pass

    async def _manual_refresh(self) -> None:
        """Manual refresh triggered by user."""
        await self._load_documents()
        ui.notify("Lista de documentos atualizada", type="positive", timeout=2000)

    def _update_last_update_label(self) -> None:
        """Update the last update time label."""
        if self.last_update_time:
            time_str = self.last_update_time.strftime("%H:%M:%S")
            self.last_update_label.text = f"Última atualização: {time_str}"

    def _handle_view_summary(self, event: object) -> None:
        """Handle view document summary action."""
        document_id = event.args["id"]
        document = next((d for d in self.documents if str(d.id) == document_id), None)

        if document and self.on_view_summary:
            self.on_view_summary(document)

    def _handle_download(self, event: object) -> None:
        """Handle document download action."""
        document_id = event.args["id"]
        document = next((d for d in self.documents if str(d.id) == document_id), None)

        if document and self.on_download:
            self.on_download(document)

    async def _handle_retry_processing(self, event: object) -> None:
        """Handle retry document processing action."""
        document_id = event.args["id"]
        document = next((d for d in self.documents if str(d.id) == document_id), None)

        if not document:
            ui.notify("Documento não encontrado", type="negative")
            return

        try:
            async for db_session in get_async_db():
                document_repository = DocumentRepository(db_session)
                document_service = DocumentService(document_repository)

                # Reset document to uploaded status and retry processing
                from app.workers.document_processor import process_document

                await document_service.update_document_status(
                    uuid.UUID(str(document.id)),
                    DocumentStatus.UPLOADED,
                    error_message=None,
                )

                task_result = process_document.delay(str(document.id))
                await document_repository.update_task_id(
                    uuid.UUID(str(document.id)), task_result.id
                )

                ui.notify(
                    f"Reprocessamento iniciado: {document.filename}", type="positive"
                )
                await self._load_documents()

        except Exception as e:
            ui.notify(f"Erro ao reprocessar documento: {str(e)}", type="negative")

    def cleanup(self) -> None:
        """Cleanup resources when component is destroyed."""
        if self.status_timer:
            self.status_timer.cancel()

    def refresh(self) -> None:
        """Public method to refresh the component."""
        ui.timer(0.1, self._load_documents, once=True)
