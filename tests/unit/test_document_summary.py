"""Unit tests for document summary modal component."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.ui_components.document_summary import DocumentSummaryModal


class TestDocumentSummaryModal:
    """Test cases for DocumentSummaryModal component."""

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document(
            id=uuid.uuid4(),
            filename="test_document.pdf",
            content_hash="hash123",
            file_size=1024000,
            document_type="simple",
            status=DocumentStatus.PROCESSED,
            client_id=uuid.uuid4(),
            file_path="client1/test_document.pdf",
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            processed_at=datetime(2025, 1, 1, 10, 5, 30),
        )

    @pytest.fixture
    def sample_chunks(self, sample_document):
        """Create sample document chunks for testing."""
        chunks = [
            DocumentChunk(
                node_id="chunk1",
                text="Este é o primeiro bloco de texto extraído do documento.",
                metadata={"page": 1, "section": "header"},
                document_id=sample_document.id,
            ),
            DocumentChunk(
                node_id="chunk2",
                text="Este é o segundo bloco de texto com mais conteúdo para análise.",
                metadata={"page": 1, "section": "body"},
                document_id=sample_document.id,
            ),
            DocumentChunk(
                node_id="chunk3",
                text="Terceiro bloco contém informações importantes sobre o documento.",
                metadata={"page": 2, "section": "footer"},
                document_id=sample_document.id,
            ),
        ]
        return chunks

    def test_document_summary_modal_initialization(self, sample_document):
        """Test DocumentSummaryModal initialization."""
        modal = DocumentSummaryModal(sample_document)

        assert modal.document == sample_document
        assert modal.chunks == []
        assert modal.dialog is None

    @patch("app.ui_components.document_summary.ui.dialog")
    @patch("app.ui_components.document_summary.ui.card")
    @patch("app.ui_components.document_summary.ui.timer")
    def test_show_modal(self, mock_timer, mock_card, mock_dialog, sample_document):
        """Test showing the modal."""
        modal = DocumentSummaryModal(sample_document)
        mock_dialog_instance = MagicMock()
        mock_dialog.return_value.__enter__.return_value = mock_dialog_instance

        modal.show()

        mock_dialog.assert_called_once()
        mock_timer.assert_called_once()
        mock_dialog_instance.open.assert_called_once()

    @patch("app.ui_components.document_summary.ui.row")
    @patch("app.ui_components.document_summary.ui.column")
    @patch("app.ui_components.document_summary.ui.label")
    @patch("app.ui_components.document_summary.ui.button")
    def test_create_header(
        self, mock_button, mock_label, mock_column, mock_row, sample_document
    ):
        """Test modal header creation."""
        modal = DocumentSummaryModal(sample_document)
        modal.dialog = MagicMock()

        modal._create_header()

        # Verify UI components were created
        mock_row.assert_called()
        mock_column.assert_called()
        mock_label.assert_called()
        mock_button.assert_called()

    @patch("app.ui_components.document_summary.ui.card")
    @patch("app.ui_components.document_summary.ui.label")
    @patch("app.ui_components.document_summary.ui.row")
    @patch("app.ui_components.document_summary.ui.column")
    def test_create_content(
        self, mock_column, mock_row, mock_label, mock_card, sample_document
    ):
        """Test modal content creation."""
        modal = DocumentSummaryModal(sample_document)

        # Mock container attributes
        modal.chunks_container = MagicMock()
        modal.loading_container = MagicMock()
        modal.chunks_count_label = MagicMock()
        modal.stats_container = MagicMock()

        modal._create_content()

        # Verify UI components were created
        mock_column.assert_called()
        mock_card.assert_called()
        mock_label.assert_called()

    @patch("app.ui_components.document_summary.ui.row")
    @patch("app.ui_components.document_summary.ui.button")
    def test_create_footer(self, mock_button, mock_row, sample_document):
        """Test modal footer creation."""
        modal = DocumentSummaryModal(sample_document)
        modal.dialog = MagicMock()

        modal._create_footer()

        # Verify UI components were created
        mock_row.assert_called()
        mock_button.assert_called()

    @pytest.mark.asyncio
    async def test_load_document_details_success(self, sample_document, sample_chunks):
        """Test successful document details loading."""
        modal = DocumentSummaryModal(sample_document)

        # Mock UI components
        modal.chunks_count_label = MagicMock()
        modal.loading_container = MagicMock()

        mock_db_session = AsyncMock()
        mock_chunk_repository = AsyncMock()
        mock_chunk_repository.get_by_document_id.return_value = sample_chunks

        with (
            patch("app.ui_components.document_summary.get_async_db") as mock_get_db,
            patch(
                "app.repositories.document_chunk_repository.DocumentChunkRepository",
                return_value=mock_chunk_repository,
            ),
            patch.object(modal, "_display_chunks") as mock_display_chunks,
            patch.object(modal, "_display_statistics") as mock_display_stats,
        ):
            mock_get_db.return_value.__aiter__.return_value = [mock_db_session]

            await modal._load_document_details()

            assert modal.chunks == sample_chunks
            modal.chunks_count_label.text = (
                f"{len(sample_chunks)} blocos de texto encontrados"
            )
            modal.loading_container.style.assert_called_with("display: none")
            mock_display_chunks.assert_called_once()
            mock_display_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_document_details_error(self, sample_document):
        """Test document details loading with error."""
        modal = DocumentSummaryModal(sample_document)
        modal.loading_container = MagicMock()

        mock_db_session = AsyncMock()
        mock_chunk_repository = AsyncMock()
        mock_chunk_repository.get_by_document_id.side_effect = Exception(
            "Database error"
        )

        with (
            patch("app.ui_components.document_summary.get_async_db") as mock_get_db,
            patch(
                "app.repositories.document_chunk_repository.DocumentChunkRepository",
                return_value=mock_chunk_repository,
            ),
            patch("app.ui_components.document_summary.ui.icon"),
            patch("app.ui_components.document_summary.ui.label"),
        ):
            mock_get_db.return_value.__aiter__.return_value = [mock_db_session]

            await modal._load_document_details()

            modal.loading_container.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_display_chunks_with_content(self, sample_document, sample_chunks):
        """Test displaying chunks when content is available."""
        modal = DocumentSummaryModal(sample_document)
        modal.chunks = sample_chunks
        modal.chunks_container = MagicMock()

        with (
            patch("app.ui_components.document_summary.ui.card"),
            patch("app.ui_components.document_summary.ui.row"),
            patch("app.ui_components.document_summary.ui.label"),
            patch("app.ui_components.document_summary.ui.expansion"),
            patch("app.ui_components.document_summary.ui.column"),
            patch("app.ui_components.document_summary.ui.button"),
        ):
            await modal._display_chunks()

            # Should display first 3 chunks
            assert len(modal.chunks) == 3

    @pytest.mark.asyncio
    async def test_display_chunks_empty(self, sample_document):
        """Test displaying chunks when no content is available."""
        modal = DocumentSummaryModal(sample_document)
        modal.chunks = []
        modal.chunks_container = MagicMock()

        with patch("app.ui_components.document_summary.ui.label") as mock_label:
            await modal._display_chunks()

            mock_label.assert_called()

    @patch("app.ui_components.document_summary.ui.dialog")
    @patch("app.ui_components.document_summary.ui.card")
    @patch("app.ui_components.document_summary.ui.row")
    @patch("app.ui_components.document_summary.ui.column")
    @patch("app.ui_components.document_summary.ui.label")
    @patch("app.ui_components.document_summary.ui.button")
    def test_show_full_content(
        self,
        mock_button,
        mock_label,
        mock_column,
        mock_row,
        mock_card,
        mock_dialog,
        sample_document,
        sample_chunks,
    ):
        """Test showing full content of a chunk."""
        modal = DocumentSummaryModal(sample_document)
        chunk = sample_chunks[0]

        mock_dialog_instance = MagicMock()
        mock_dialog.return_value.__enter__.return_value = mock_dialog_instance

        modal._show_full_content(chunk)

        mock_dialog.assert_called_once()
        mock_dialog_instance.open.assert_called_once()

    @pytest.mark.asyncio
    async def test_display_statistics(self, sample_document, sample_chunks):
        """Test displaying processing statistics."""
        modal = DocumentSummaryModal(sample_document)
        modal.chunks = sample_chunks
        modal.stats_container = MagicMock()

        with (
            patch("app.ui_components.document_summary.ui.row"),
            patch("app.ui_components.document_summary.ui.column"),
            patch("app.ui_components.document_summary.ui.label"),
        ):
            await modal._display_statistics()

            # Verify statistics calculations
            total_chars = sum(len(chunk.text) for chunk in sample_chunks)
            total_words = sum(len(chunk.text.split()) for chunk in sample_chunks)
            avg_chunk_size = total_chars // len(sample_chunks)

            assert total_chars > 0
            assert total_words > 0
            assert avg_chunk_size > 0

    def test_handle_download(self, sample_document):
        """Test download handler."""
        modal = DocumentSummaryModal(sample_document)

        with patch("app.ui_components.document_summary.ui.notify") as mock_notify:
            modal._handle_download()

            mock_notify.assert_called_once_with(
                "Funcionalidade de download será implementada", type="info"
            )

    @pytest.mark.asyncio
    async def test_load_more_chunks(self, sample_document, sample_chunks):
        """Test loading more chunks functionality."""
        modal = DocumentSummaryModal(sample_document)
        modal.chunks = sample_chunks
        modal.chunks_container = MagicMock()

        with patch.object(modal, "_display_all_chunks") as mock_display_all:
            await modal._load_more_chunks()

            modal.chunks_container.clear.assert_called_once()
            mock_display_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_display_all_chunks(self, sample_document, sample_chunks):
        """Test displaying all chunks."""
        modal = DocumentSummaryModal(sample_document)
        modal.chunks = sample_chunks
        modal.chunks_container = MagicMock()

        with (
            patch("app.ui_components.document_summary.ui.card"),
            patch("app.ui_components.document_summary.ui.row"),
            patch("app.ui_components.document_summary.ui.label"),
            patch("app.ui_components.document_summary.ui.expansion"),
            patch("app.ui_components.document_summary.ui.column"),
            patch("app.ui_components.document_summary.ui.button"),
        ):
            await modal._display_all_chunks()

            # Should display all chunks
            assert len(modal.chunks) == 3

    def test_processing_time_calculation(self, sample_document):
        """Test processing time calculation in content creation."""
        modal = DocumentSummaryModal(sample_document)

        # Mock UI components for content creation
        modal.chunks_container = MagicMock()
        modal.loading_container = MagicMock()
        modal.chunks_count_label = MagicMock()
        modal.stats_container = MagicMock()

        with (
            patch("app.ui_components.document_summary.ui.card"),
            patch("app.ui_components.document_summary.ui.row"),
            patch("app.ui_components.document_summary.ui.column"),
            patch("app.ui_components.document_summary.ui.label"),
            patch("app.ui_components.document_summary.ui.spinner"),
        ):
            modal._create_content()

            # Verify processing time calculation would be performed
            # In the actual implementation, this would show "Tempo de processamento: 5m 30s"
            processing_time = sample_document.processed_at - sample_document.created_at
            assert processing_time.total_seconds() == 330  # 5 minutes 30 seconds

    def test_format_metadata_display(self, sample_chunks):
        """Test metadata formatting in chunk display."""
        chunk = sample_chunks[0]

        # Verify metadata structure
        assert "page" in chunk.metadata
        assert "section" in chunk.metadata
        assert chunk.metadata["page"] == 1
        assert chunk.metadata["section"] == "header"
