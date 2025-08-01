"""Document upload UI component with drag-and-drop functionality and real-time progress tracking."""

import asyncio
import hashlib
import logging
import uuid
from typing import Any

import httpx
from nicegui import events, ui

from app.core.auth import AuthManager
from app.core.database import get_async_db
from app.models.client import Client
from app.models.document import DocumentType
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)


class DocumentUploadComponent:
    """Advanced document upload component with drag-and-drop and real-time progress tracking."""

    def __init__(self, client_id: uuid.UUID) -> None:
        """Initialize the document upload component."""
        self.client_id = client_id
        self.processing_documents: dict[str, dict[str, Any]] = {}
        self.websocket_connection: ui.websocket | None = None
        self.progress_containers: dict[str, ui.column] = {}

    def create(self) -> None:
        """Create the document upload interface."""
        with ui.card().classes('w-full p-6'):
            ui.label('Processamento de Documentos PDF').classes('text-xl font-semibold mb-4')

            # Drag and drop upload area
            with ui.column().classes('w-full'):
                ui.upload(
                    on_upload=self._handle_pdf_upload,
                    on_rejected=self._handle_upload_rejected,
                    multiple=False,
                    auto_upload=True,
                    max_file_size=50 * 1024 * 1024  # 50MB limit
                ).classes('w-full min-h-32 border-2 border-dashed border-blue-300 rounded-lg bg-blue-50 hover:bg-blue-100').props(
                    'accept=".pdf" '
                    'drag-over-text="Solte o PDF aqui para processar" '
                    'label="Clique ou arraste um PDF aqui"'
                )

                # Instructions
                with ui.column().classes('w-full mt-2 text-sm text-gray-600'):
                    ui.label('• Apenas arquivos PDF são aceitos')
                    ui.label('• Tamanho máximo: 50MB')
                    ui.label('• Processamento automático com OCR e análise de IA')
                    ui.label('• Vetorização para busca de similaridade')

            # Processing status area
            with ui.column().classes('w-full mt-6') as self.processing_container:
                ui.label('Status de Processamento').classes('text-lg font-medium mb-2')

                # Active processing documents will be displayed here
                with ui.column().classes('w-full') as self.active_processing:
                    pass

                # Completed processing results
                with ui.column().classes('w-full mt-4') as self.completed_processing:
                    ui.label('Documentos Processados').classes('text-md font-medium')

    async def _handle_pdf_upload(self, upload_event: events.UploadEventArguments) -> None:
        """Handle PDF file upload with comprehensive validation and processing."""
        try:
            filename = upload_event.name
            file_content = upload_event.content

            # Handle file content (SpooledTemporaryFile or bytes)
            if hasattr(file_content, "read"):
                file_content.seek(0)
                content_bytes = file_content.read()
                file_content.seek(0)
            else:
                content_bytes = file_content

            # Validate file type
            if not filename.lower().endswith('.pdf'):
                ui.notify('Apenas arquivos PDF são permitidos', type='negative')
                return

            # Validate file size
            if len(content_bytes) > 50 * 1024 * 1024:
                ui.notify('Arquivo muito grande. Máximo 50MB permitido.', type='negative')
                return

            # Get current user context
            try:
                current_user = AuthManager.get_current_user()
                user_id = current_user['id']
            except Exception:
                ui.notify('Usuário não autenticado', type='negative')
                return

            # Create unique processing ID
            processing_id = str(uuid.uuid4())

            ui.notify(f'Iniciando processamento de: {filename}', type='positive')

            # Start processing with progress tracking
            await self._start_document_processing(
                processing_id, filename, content_bytes, user_id
            )

        except Exception as e:
            logger.error(f"Error handling PDF upload: {str(e)}")
            ui.notify(f'Erro no upload: {str(e)}', type='negative')

    def _handle_upload_rejected(self, event) -> None:
        """Handle file upload rejection."""
        ui.notify(
            'Arquivo rejeitado. Verifique o tipo (PDF) e tamanho (máx 50MB).',
            type='negative'
        )

    async def _start_document_processing(
        self, processing_id: str, filename: str, content_bytes: bytes, user_id: int
    ) -> None:
        """Start document processing with progress tracking."""

        # Create progress display
        with self.active_processing:
            progress_card = ui.card().classes('w-full p-4 mb-2 border-l-4 border-blue-500')
            with progress_card:
                ui.label(f'Processando: {filename}').classes('font-medium')

                # Progress bar
                progress_bar = ui.linear_progress(value=0).classes('w-full mt-2')

                # Status label
                status_label = ui.label('Iniciando processamento...').classes(
                    'text-sm text-gray-600 mt-2'
                )

                # Processing steps
                with ui.column().classes('w-full mt-3 text-xs text-gray-500'):
                    step_extract = ui.label('1. Extração de texto - Aguardando...').classes('mb-1')
                    step_ocr = ui.label('2. OCR (se necessário) - Aguardando...').classes('mb-1')
                    step_embeddings = ui.label('3. Geração de embeddings - Aguardando...').classes('mb-1')
                    step_storage = ui.label('4. Armazenamento - Aguardando...').classes('mb-1')

                # Store references for updates
                self.progress_containers[processing_id] = {
                    'card': progress_card,
                    'progress_bar': progress_bar,
                    'status_label': status_label,
                    'steps': {
                        'extract': step_extract,
                        'ocr': step_ocr,
                        'embeddings': step_embeddings,
                        'storage': step_storage
                    }
                }

        # Store processing info
        self.processing_documents[processing_id] = {
            'filename': filename,
            'status': 'uploading',
            'progress': 0,
            'start_time': asyncio.get_event_loop().time()
        }

        # Start processing via API call
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
                # Prepare multipart data
                files = {'file': (filename, content_bytes, 'application/pdf')}
                data = {
                    'user_id': user_id,
                    'perform_ocr': True
                }

                # Update status
                self._update_processing_status(
                    processing_id, 'processing', 10,
                    'Enviando para processamento...'
                )

                # Start WebSocket connection for progress updates
                websocket_task = None
                api_processing_id = None

                try:
                    # Make API call to upload endpoint
                    response = await client.post(
                        '/v1/documents/upload',
                        files=files,
                        data=data
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result['success']:
                            # Get the API processing ID for WebSocket tracking
                            api_processing_id = result.get('processing_id')

                            # If we have a processing ID, connect to WebSocket for real-time updates
                            if api_processing_id:
                                websocket_task = asyncio.create_task(
                                    self._start_websocket_progress_tracking(processing_id, api_processing_id)
                                )

                            await self._handle_processing_success(processing_id, result)
                        else:
                            await self._handle_processing_error(
                                processing_id, result.get('error', 'Processing failed')
                            )
                    else:
                        await self._handle_processing_error(
                            processing_id, f'API Error: {response.status_code}'
                        )
                finally:
                    # Clean up WebSocket connection if it was started
                    if websocket_task and not websocket_task.done():
                        websocket_task.cancel()
                        try:
                            await websocket_task
                        except asyncio.CancelledError:
                            pass

        except TimeoutError:
            await self._handle_processing_error(processing_id, 'Processing timeout (>5 minutes)')
        except Exception as e:
            logger.error(f"Document processing error: {str(e)}")
            await self._handle_processing_error(processing_id, f'Processing error: {str(e)}')

    def _update_processing_status(
        self, processing_id: str, status: str, progress: int, message: str, step: str = None
    ) -> None:
        """Update processing status in real-time."""
        if processing_id not in self.progress_containers:
            return

        containers = self.progress_containers[processing_id]

        # Update progress bar
        containers['progress_bar'].value = progress / 100.0

        # Update status label
        containers['status_label'].text = message

        # Update specific step if provided
        if step and step in containers['steps']:
            step_label = containers['steps'][step]
            if status == 'completed':
                step_label.text = step_label.text.replace('Aguardando...', '✓ Concluído')
                step_label.classes('text-green-600')
            elif status == 'processing':
                step_label.text = step_label.text.replace('Aguardando...', '⏳ Processando...')
                step_label.classes('text-blue-600')
            elif status == 'error':
                step_label.text = step_label.text.replace('Aguardando...', '❌ Erro')
                step_label.classes('text-red-600')

        # Update internal status
        if processing_id in self.processing_documents:
            self.processing_documents[processing_id].update({
                'status': status,
                'progress': progress,
                'message': message
            })

    async def _handle_processing_success(self, processing_id: str, result: dict[str, Any]) -> None:
        """Handle successful document processing."""
        self._update_processing_status(
            processing_id, 'completed', 100,
            'Documento processado com sucesso!'
        )

        # Update all steps as completed
        for step in ['extract', 'ocr', 'embeddings', 'storage']:
            self._update_processing_status(processing_id, 'completed', 100, '', step)

        # Show results
        filename = result.get('filename')
        processing_summary = result.get('processing_summary', {})

        ui.notify(
            f'✓ {filename} processado com sucesso! '
            f'({processing_summary.get("pages_processed", 0)} páginas, '
            f'{processing_summary.get("embeddings_stored", 0)} embeddings)',
            type='positive'
        )

        # Move to completed section after delay
        await asyncio.sleep(3)
        await self._move_to_completed(processing_id, result)

    async def _handle_processing_error(self, processing_id: str, error_message: str) -> None:
        """Handle processing error."""
        self._update_processing_status(
            processing_id, 'error', 0,
            f'Erro: {error_message}'
        )

        ui.notify(f'❌ Erro no processamento: {error_message}', type='negative')

        # Remove from active processing after delay
        await asyncio.sleep(5)
        if processing_id in self.progress_containers:
            self.progress_containers[processing_id]['card'].delete()
            del self.progress_containers[processing_id]

        if processing_id in self.processing_documents:
            del self.processing_documents[processing_id]

    async def _move_to_completed(self, processing_id: str, result: dict[str, Any]) -> None:
        """Move processed document to completed section."""
        if processing_id not in self.progress_containers:
            return

        # Remove from active processing
        self.progress_containers[processing_id]['card'].delete()
        del self.progress_containers[processing_id]

        # Add to completed section
        with self.completed_processing:
            completed_card = ui.card().classes('w-full p-3 mb-2 border-l-4 border-green-500')
            with completed_card:
                filename = result.get('filename', 'Documento')
                processing_summary = result.get('processing_summary', {})

                with ui.row().classes('w-full items-center justify-between'):
                    ui.label(f'✓ {filename}').classes('font-medium text-green-700')
                    ui.label('Processado').classes('text-xs bg-green-100 text-green-800 px-2 py-1 rounded')

                with ui.row().classes('w-full text-sm text-gray-600 mt-2'):
                    ui.label(f"Páginas: {processing_summary.get('pages_processed', 0)}")
                    ui.label(f"Embeddings: {processing_summary.get('embeddings_stored', 0)}")
                    ui.label(f"OCR: {processing_summary.get('ocr_pages', 0)} páginas")

        # Clean up
        if processing_id in self.processing_documents:
            del self.processing_documents[processing_id]

    async def _start_websocket_progress_tracking(self, ui_processing_id: str, api_processing_id: str) -> None:
        """Start WebSocket connection to track real-time processing progress."""
        try:
            import json

            import websockets

            # Connect to the document-specific WebSocket endpoint
            websocket_url = f"ws://localhost:8000/ws/documents/{api_processing_id}/progress"

            async with websockets.connect(websocket_url) as websocket:
                logger.info(f"WebSocket connected for processing ID: {api_processing_id}")

                # Listen for progress updates
                async for message in websocket:
                    try:
                        data = json.loads(message)

                        if data.get("type") == "document_progress":
                            progress_data = data.get("data", {})

                            # Extract progress information
                            step = progress_data.get("step", "processing")
                            progress = progress_data.get("progress", 0)
                            message_text = progress_data.get("message", "Processando...")
                            status = progress_data.get("status", "processing")

                            # Update UI with real-time progress
                            self._update_processing_status(
                                ui_processing_id, status, progress, message_text, step
                            )

                            # If processing is complete, break the loop
                            if status in ["completed", "error"] and progress >= 100:
                                break

                        elif data.get("type") == "pong":
                            # Keep-alive response
                            continue

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse WebSocket message: {str(e)}")
                    except Exception as e:
                        logger.warning(f"Error processing WebSocket message: {str(e)}")

        except Exception as e:
            logger.warning(f"WebSocket connection failed: {str(e)}")
            # Fall back to polling or static progress updates


class DocumentUploadDialog:
    """Legacy document upload dialog component (maintained for backwards compatibility)."""

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
            if hasattr(file_content, "read"):
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
