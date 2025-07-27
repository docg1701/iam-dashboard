"""Document summary modal component for displaying processed document information."""


from nicegui import ui

from app.core.database import get_async_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


class DocumentSummaryModal:
    """Modal component for displaying document summary and extracted content."""

    def __init__(self, document: Document) -> None:
        """Initialize the document summary modal."""
        self.document = document
        self.chunks: list[DocumentChunk] = []
        self.dialog: ui.dialog | None = None

    def show(self) -> None:
        """Show the document summary modal."""
        with ui.dialog() as self.dialog:
            with ui.card().style("width: 90vw; max-width: 1200px; max-height: 80vh"):
                self._create_header()
                self._create_content()
                self._create_footer()

        # Load document chunks and summary
        ui.timer(0.1, self._load_document_details, once=True)

        self.dialog.open()

    def _create_header(self) -> None:
        """Create the modal header."""
        with ui.row().classes("w-full justify-between items-center p-4 border-b"):
            with ui.column():
                ui.label("Resumo do Documento").classes("text-2xl font-bold")
                ui.label(self.document.filename).classes("text-lg text-gray-600")

            ui.button(
                "",
                icon="close",
                on_click=self.dialog.close
            ).classes("text-gray-500 hover:text-gray-700").props("flat round")

    def _create_content(self) -> None:
        """Create the modal content."""
        with ui.column().classes("w-full p-4 flex-1 overflow-auto"):
            # Document metadata section
            with ui.card().classes("w-full mb-6"):
                ui.label("Informações do Documento").classes("text-xl font-bold mb-4")

                with ui.row().classes("w-full gap-6"):
                    with ui.column().classes("flex-1"):
                        ui.label(f"Nome: {self.document.filename}").classes("text-base mb-2")
                        ui.label(f"Tamanho: {self.document.formatted_file_size}").classes("text-base mb-2")
                        ui.label(f"Tipo: {self.document.document_type.title()}").classes("text-base mb-2")

                    with ui.column().classes("flex-1"):
                        uploaded_at = (
                            self.document.created_at.strftime("%d/%m/%Y às %H:%M")
                            if self.document.created_at
                            else "Não informado"
                        )
                        processed_at = (
                            self.document.processed_at.strftime("%d/%m/%Y às %H:%M")
                            if self.document.processed_at
                            else "Não informado"
                        )

                        ui.label(f"Enviado em: {uploaded_at}").classes("text-base mb-2")
                        ui.label(f"Processado em: {processed_at}").classes("text-base mb-2")

                        # Calculate processing time
                        if self.document.created_at and self.document.processed_at:
                            processing_time = self.document.processed_at - self.document.created_at
                            hours, remainder = divmod(processing_time.total_seconds(), 3600)
                            minutes, seconds = divmod(remainder, 60)

                            if hours > 0:
                                time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
                            elif minutes > 0:
                                time_str = f"{int(minutes)}m {int(seconds)}s"
                            else:
                                time_str = f"{int(seconds)}s"

                            ui.label(f"Tempo de processamento: {time_str}").classes("text-base mb-2")

            # Document chunks section
            with ui.card().classes("w-full mb-6"):
                with ui.row().classes("w-full justify-between items-center mb-4"):
                    ui.label("Conteúdo Extraído").classes("text-xl font-bold")
                    self.chunks_count_label = ui.label("").classes("text-sm text-gray-500")

                # Chunks container
                self.chunks_container = ui.column().classes("w-full")

                # Loading indicator
                with ui.row().classes("w-full justify-center p-8") as self.loading_container:
                    ui.spinner(size="lg")
                    ui.label("Carregando conteúdo...").classes("ml-4 text-lg")

            # Statistics section
            with ui.card().classes("w-full"):
                ui.label("Estatísticas do Processamento").classes("text-xl font-bold mb-4")

                with ui.row().classes("w-full gap-6"):
                    self.stats_container = ui.column().classes("w-full")

    def _create_footer(self) -> None:
        """Create the modal footer."""
        with ui.row().classes("w-full justify-end gap-2 p-4 border-t"):
            ui.button(
                "Baixar Documento Original",
                icon="download",
                on_click=self._handle_download
            ).classes("bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600")

            ui.button(
                "Fechar",
                on_click=self.dialog.close
            ).classes("bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600")

    async def _load_document_details(self) -> None:
        """Load document chunks and create summary."""
        try:
            async for db_session in get_async_db():
                # Load document chunks
                from app.repositories.document_chunk_repository import (
                    DocumentChunkRepository,
                )

                chunk_repository = DocumentChunkRepository(db_session)
                self.chunks = await chunk_repository.get_by_document_id(self.document.id)

                # Update chunks count
                self.chunks_count_label.text = f"{len(self.chunks)} blocos de texto encontrados"

                # Hide loading indicator
                self.loading_container.style("display: none")

                # Display chunks
                await self._display_chunks()

                # Display statistics
                await self._display_statistics()

        except Exception as e:
            self.loading_container.clear()
            with self.loading_container:
                ui.icon("error", size="lg", color="red")
                ui.label(f"Erro ao carregar detalhes: {str(e)}").classes("ml-4 text-lg text-red-600")

    async def _display_chunks(self) -> None:
        """Display document chunks with syntax highlighting."""
        if not self.chunks:
            with self.chunks_container:
                ui.label("Nenhum conteúdo extraído encontrado").classes("text-center text-gray-500 py-8")
            return

        # Show first few chunks with option to expand
        chunks_to_show = min(3, len(self.chunks))

        for i, chunk in enumerate(self.chunks[:chunks_to_show]):
            with self.chunks_container:
                with ui.card().classes("w-full mb-4"):
                    with ui.row().classes("w-full justify-between items-center mb-2"):
                        ui.label(f"Bloco {i + 1}").classes("text-lg font-semibold")

                        # Character count
                        char_count = len(chunk.text) if chunk.text else 0
                        ui.label(f"{char_count} caracteres").classes("text-sm text-gray-500")

                    # Content preview (first 500 characters)
                    content_preview = chunk.text[:500] if chunk.text else "Conteúdo vazio"
                    if len(chunk.text) > 500:
                        content_preview += "..."

                    with ui.expansion("Ver conteúdo", icon="visibility").classes("w-full"):
                        with ui.column().classes("w-full p-4 bg-gray-50 rounded"):
                            ui.label(content_preview).classes("text-sm whitespace-pre-wrap")

                            if len(chunk.text) > 500:
                                with ui.row().classes("w-full justify-center mt-4"):
                                    ui.button(
                                        "Ver conteúdo completo",
                                        on_click=lambda c=chunk: self._show_full_content(c)
                                    ).classes("bg-blue-500 text-white px-4 py-2 rounded text-sm")

                    # Metadata if available
                    if chunk.metadata:
                        with ui.expansion("Metadados", icon="info").classes("w-full mt-2"):
                            with ui.column().classes("w-full p-4 bg-gray-50 rounded"):
                                # Display metadata in a formatted way
                                for key, value in chunk.metadata.items():
                                    if key != "text":  # Don't duplicate text content
                                        ui.label(f"{key}: {value}").classes("text-sm mb-1")

        # Show "Load more" button if there are more chunks
        if len(self.chunks) > chunks_to_show:
            with self.chunks_container:
                ui.button(
                    f"Carregar mais {len(self.chunks) - chunks_to_show} blocos",
                    on_click=self._load_more_chunks
                ).classes("bg-blue-500 text-white px-4 py-2 rounded mt-4")

    def _show_full_content(self, chunk: DocumentChunk) -> None:
        """Show full content of a chunk in a separate dialog."""
        with ui.dialog() as content_dialog:
            with ui.card().style("width: 90vw; max-width: 800px; max-height: 80vh"):
                with ui.row().classes("w-full justify-between items-center p-4 border-b"):
                    ui.label("Conteúdo Completo do Bloco").classes("text-xl font-bold")
                    ui.button("", icon="close", on_click=content_dialog.close).props("flat round")

                with ui.column().classes("w-full p-4 overflow-auto"):
                    ui.label(chunk.text or "Conteúdo vazio").classes("text-sm whitespace-pre-wrap")

                with ui.row().classes("w-full justify-end p-4 border-t"):
                    ui.button("Fechar", on_click=content_dialog.close).classes(
                        "bg-gray-500 text-white px-4 py-2 rounded"
                    )

        content_dialog.open()

    async def _load_more_chunks(self) -> None:
        """Load and display remaining chunks."""
        # Clear container and reload all chunks
        self.chunks_container.clear()
        await self._display_all_chunks()

    async def _display_all_chunks(self) -> None:
        """Display all document chunks."""
        for i, chunk in enumerate(self.chunks):
            with self.chunks_container:
                with ui.card().classes("w-full mb-4"):
                    with ui.row().classes("w-full justify-between items-center mb-2"):
                        ui.label(f"Bloco {i + 1}").classes("text-lg font-semibold")

                        char_count = len(chunk.text) if chunk.text else 0
                        ui.label(f"{char_count} caracteres").classes("text-sm text-gray-500")

                    content_preview = chunk.text[:200] if chunk.text else "Conteúdo vazio"
                    if len(chunk.text) > 200:
                        content_preview += "..."

                    with ui.expansion("Ver conteúdo", icon="visibility").classes("w-full"):
                        with ui.column().classes("w-full p-4 bg-gray-50 rounded"):
                            ui.label(content_preview).classes("text-sm whitespace-pre-wrap")

                            if len(chunk.text) > 200:
                                with ui.row().classes("w-full justify-center mt-2"):
                                    ui.button(
                                        "Ver completo",
                                        on_click=lambda c=chunk: self._show_full_content(c)
                                    ).classes("bg-blue-500 text-white px-2 py-1 rounded text-xs")

    async def _display_statistics(self) -> None:
        """Display processing statistics."""
        with self.stats_container:
            total_chars = sum(len(chunk.text) for chunk in self.chunks if chunk.text)
            total_words = sum(len(chunk.text.split()) for chunk in self.chunks if chunk.text)

            with ui.row().classes("w-full gap-8"):
                with ui.column().classes("text-center"):
                    ui.label(str(len(self.chunks))).classes("text-3xl font-bold text-blue-600")
                    ui.label("Blocos de Texto").classes("text-sm text-gray-600")

                with ui.column().classes("text-center"):
                    ui.label(f"{total_chars:,}").classes("text-3xl font-bold text-green-600")
                    ui.label("Caracteres").classes("text-sm text-gray-600")

                with ui.column().classes("text-center"):
                    ui.label(f"{total_words:,}").classes("text-3xl font-bold text-purple-600")
                    ui.label("Palavras").classes("text-sm text-gray-600")

                if self.chunks:
                    avg_chunk_size = total_chars // len(self.chunks)
                    with ui.column().classes("text-center"):
                        ui.label(f"{avg_chunk_size:,}").classes("text-3xl font-bold text-orange-600")
                        ui.label("Chars/Bloco").classes("text-sm text-gray-600")

    def _handle_download(self) -> None:
        """Handle document download."""
        # This would implement actual download functionality
        ui.notify("Funcionalidade de download será implementada", type="info")
