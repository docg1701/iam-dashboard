"""Unit tests for client details UI component."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.client import Client
from app.models.document import Document, DocumentStatus
from app.ui_components.client_details import ClientDetailsPage


class TestClientDetailsPage:
    """Test cases for ClientDetailsPage component."""

    @pytest.fixture
    def sample_client(self):
        """Create a sample client for testing."""
        client = Client(
            id=uuid.uuid4(),
            name="João Silva",
            cpf="12345678901",
            birth_date=datetime(1990, 1, 15).date(),
            created_at=datetime(2025, 1, 1, 10, 0, 0),
        )
        return client

    @pytest.fixture
    def sample_documents(self, sample_client):
        """Create sample documents for testing."""
        documents = [
            Document(
                id=uuid.uuid4(),
                filename="documento1.pdf",
                content_hash="hash1",
                file_size=1024000,
                document_type="simple",
                status=DocumentStatus.PROCESSED,
                client_id=sample_client.id,
                file_path="client1/doc1.pdf",
                created_at=datetime(2025, 1, 1, 11, 0, 0),
                processed_at=datetime(2025, 1, 1, 11, 5, 0),
            ),
            Document(
                id=uuid.uuid4(),
                filename="documento2.pdf",
                content_hash="hash2",
                file_size=512000,
                document_type="complex",
                status=DocumentStatus.PROCESSING,
                client_id=sample_client.id,
                file_path="client1/doc2.pdf",
                created_at=datetime(2025, 1, 1, 12, 0, 0),
            ),
            Document(
                id=uuid.uuid4(),
                filename="documento3.pdf",
                content_hash="hash3",
                file_size=2048000,
                document_type="simple",
                status=DocumentStatus.FAILED,
                client_id=sample_client.id,
                file_path="client1/doc3.pdf",
                error_message="OCR processing failed",
                created_at=datetime(2025, 1, 1, 13, 0, 0),
            ),
        ]
        return documents

    def test_client_details_page_initialization(self):
        """Test ClientDetailsPage initialization."""
        client_id = str(uuid.uuid4())
        page = ClientDetailsPage(client_id)

        assert page.client_id == uuid.UUID(client_id)
        assert page.client is None
        assert page.document_list_component is None

    @pytest.mark.asyncio
    @patch("app.ui_components.client_details.AuthManager")
    @patch("app.ui_components.client_details.get_async_db")
    async def test_client_not_found(self, mock_get_db, mock_auth_manager, sample_client):
        """Test behavior when client is not found."""
        # Setup mocks
        mock_auth_manager.require_auth.return_value = True
        mock_auth_manager.get_current_user.return_value = {"username": "testuser"}

        mock_db_session = AsyncMock()
        mock_get_db.return_value.__aiter__.return_value = [mock_db_session]

        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = None

        client_id = str(uuid.uuid4())
        page = ClientDetailsPage(client_id)

        # Create mock UI components
        with patch("app.ui_components.client_details.ui.column"), \
             patch("app.ui_components.client_details.ui.row"), \
             patch("app.ui_components.client_details.ui.button"), \
             patch("app.ui_components.client_details.ui.label"), \
             patch("app.ui_components.client_details.ui.timer"), \
             patch("app.ui_components.client_details.ui.notify") as mock_notify, \
             patch("app.ui_components.client_details.ui.navigate") as mock_navigate, \
             patch("app.ui_components.client_details.ClientService", return_value=mock_client_service):

            # Mock the client_info_container
            page.client_info_container = MagicMock()

            # Call _load_client directly to test the logic
            await page._load_client()

            # Verify navigation to clients page occurs
            mock_notify.assert_called_once_with("Cliente não encontrado", type="negative")
            mock_navigate.to.assert_called_once_with("/clients")

    def test_handle_view_summary_processed_document(self, sample_documents):
        """Test viewing summary for a processed document."""
        client_id = str(uuid.uuid4())
        page = ClientDetailsPage(client_id)

        processed_doc = sample_documents[0]  # Status: PROCESSED

        with patch("app.ui_components.document_summary.DocumentSummaryModal") as mock_modal:
            mock_modal_instance = MagicMock()
            mock_modal.return_value = mock_modal_instance

            page._handle_view_summary(processed_doc)

            mock_modal.assert_called_once_with(processed_doc)
            mock_modal_instance.show.assert_called_once()

    def test_handle_view_summary_unprocessed_document(self, sample_documents):
        """Test viewing summary for an unprocessed document."""
        client_id = str(uuid.uuid4())
        page = ClientDetailsPage(client_id)

        processing_doc = sample_documents[1]  # Status: PROCESSING

        with patch("app.ui_components.client_details.ui.notify") as mock_notify:
            page._handle_view_summary(processing_doc)

            mock_notify.assert_called_once_with(
                "Resumo disponível apenas para documentos processados", type="warning"
            )

    def test_handle_download(self, sample_documents):
        """Test document download handler."""
        client_id = str(uuid.uuid4())
        page = ClientDetailsPage(client_id)

        document = sample_documents[0]

        with patch("app.ui_components.client_details.ui.notify") as mock_notify:
            page._handle_download(document)

            mock_notify.assert_called_once_with(
                "Funcionalidade de download será implementada", type="info"
            )

    def test_cleanup(self):
        """Test cleanup method."""
        client_id = str(uuid.uuid4())
        page = ClientDetailsPage(client_id)

        # Create mock document list component
        mock_component = MagicMock()
        page.document_list_component = mock_component

        page.cleanup()

        mock_component.cleanup.assert_called_once()

    def test_cleanup_without_component(self):
        """Test cleanup when no component exists."""
        client_id = str(uuid.uuid4())
        page = ClientDetailsPage(client_id)

        # Should not raise any exception
        page.cleanup()

    @patch("app.ui_components.client_details.AuthManager")
    def test_handle_logout(self, mock_auth_manager):
        """Test logout handler."""
        client_id = str(uuid.uuid4())
        page = ClientDetailsPage(client_id)

        with patch("app.ui_components.client_details.ui.notify") as mock_notify, \
             patch("app.ui_components.client_details.ui.navigate") as mock_navigate:

            page._handle_logout()

            mock_auth_manager.logout_user.assert_called_once()
            mock_notify.assert_called_once_with("Saída realizada com sucesso", type="positive")
            mock_navigate.to.assert_called_once_with("/login")

    @pytest.mark.asyncio
    async def test_load_client_success(self, sample_client):
        """Test successful client loading."""
        client_id = str(sample_client.id)
        page = ClientDetailsPage(client_id)

        # Mock client info container
        page.client_info_container = MagicMock()

        mock_db_session = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = sample_client

        with patch("app.ui_components.client_details.get_async_db") as mock_get_db, \
             patch("app.ui_components.client_details.ClientService", return_value=mock_client_service), \
             patch("app.ui_components.client_details.ui.card"), \
             patch("app.ui_components.client_details.ui.label"), \
             patch("app.ui_components.client_details.ui.row"), \
             patch("app.ui_components.client_details.ui.column"):

            mock_get_db.return_value.__aiter__.return_value = [mock_db_session]

            await page._load_client()

            assert page.client == sample_client
            mock_client_service.get_client_by_id.assert_called_once_with(sample_client.id)
            page.client_info_container.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_client_error(self):
        """Test client loading with database error."""
        client_id = str(uuid.uuid4())
        page = ClientDetailsPage(client_id)

        mock_db_session = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.side_effect = Exception("Database error")

        with patch("app.ui_components.client_details.get_async_db") as mock_get_db, \
             patch("app.ui_components.client_details.ClientService", return_value=mock_client_service), \
             patch("app.ui_components.client_details.ui.notify") as mock_notify:

            mock_get_db.return_value.__aiter__.return_value = [mock_db_session]

            await page._load_client()

            mock_notify.assert_called_once_with(
                "Erro ao carregar dados do cliente: Database error", type="negative"
            )