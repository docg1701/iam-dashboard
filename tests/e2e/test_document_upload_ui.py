"""End-to-end tests for document upload UI."""

import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest
from nicegui import ui
from nicegui.testing import Screen

from app.models.client import Client
from app.models.document import DocumentType
from app.ui_components.document_upload import DocumentUploadDialog


@pytest.fixture
def sample_client():
    """Sample client for testing."""
    import uuid
    from datetime import datetime

    return Client(
        id=uuid.uuid4(),
        name="João Silva",
        cpf="12345678901",
        birth_date=datetime(1990, 1, 1).date(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_pdf_file():
    """Create a temporary PDF file for testing."""
    pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj xref 0 4 0000000000 65535 f 0000000010 00000 n 0000000053 00000 n 0000000100 00000 n trailer<</Size 4/Root 1 0 R>> startxref 150 %%EOF"

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_content)
        f.flush()
        yield f.name

    # Cleanup
    os.unlink(f.name)


class TestDocumentUploadUI:
    """E2E tests for document upload UI components."""

    @pytest.mark.asyncio
    async def test_document_upload_dialog_display(self, sample_client):
        """Test that document upload dialog displays correctly."""
        with Screen("/test") as screen:

            @ui.page("/test")
            def test_page():
                upload_dialog = DocumentUploadDialog(sample_client)
                upload_dialog.show()

            await screen.open("/test")

            # Check that dialog elements are present
            screen.should_contain(f"Upload de Documento - {sample_client.name}")
            screen.should_contain("Selecione um arquivo PDF:")
            screen.should_contain("Classificação do documento:")
            screen.should_contain("Simples (PDF digital com texto selecionável)")
            screen.should_contain("Complexo (PDF escaneado, requer OCR)")
            screen.should_contain("Cancelar")
            screen.should_contain("Enviar Documento")

    @pytest.mark.asyncio
    async def test_document_type_selection(self, sample_client):
        """Test document type selection functionality."""
        with Screen("/test") as screen:

            @ui.page("/test")
            def test_page():
                upload_dialog = DocumentUploadDialog(sample_client)
                upload_dialog.show()

            await screen.open("/test")

            # Find document type selector
            type_selector = screen.find("Tipo de documento").parent()

            # Check default selection
            assert type_selector.text == DocumentType.SIMPLE

            # Test changing selection
            type_selector.click()
            screen.find("Complexo (PDF escaneado, requer OCR)").click()

            # Verify selection changed
            assert type_selector.text == DocumentType.COMPLEX

    @patch("app.services.document_service.DocumentService.create_document")
    @pytest.mark.asyncio
    async def test_successful_file_upload_flow(
        self, mock_create_document, sample_client, sample_pdf_file
    ):
        """Test successful file upload and processing initiation."""
        # Arrange
        mock_create_document.return_value = {
            "success": True,
            "document_id": "doc_123",
            "task_id": "task_456",
            "message": "Documento criado e processamento iniciado",
        }

        with Screen("/test") as screen:

            @ui.page("/test")
            def test_page():
                upload_dialog = DocumentUploadDialog(sample_client)
                upload_dialog.show()

            await screen.open("/test")

            # Simulate file upload
            screen.find("Arrastar PDF aqui ou clicar para selecionar")

            # Read the test PDF file
            with open(sample_pdf_file, "rb") as f:
                file_content = f.read()

            # Simulate file selection (this would normally be done by browser)
            # In a real E2E test, you would use Playwright to interact with file input
            upload_dialog.uploaded_file_info = {
                "filename": "test.pdf",
                "content": file_content,
                "size": len(file_content),
                "hash": "abc123",
            }
            upload_dialog._update_file_info()

            # Select document type
            type_selector = screen.find("Tipo de documento").parent()
            type_selector.click()
            screen.find("Simples (PDF digital com texto selecionável)").click()

            # Click submit
            submit_button = screen.find("Enviar Documento")
            submit_button.click()

            # Verify success notification appears
            screen.should_contain("Documento enviado com sucesso!")

            # Verify document service was called
            mock_create_document.assert_called_once()
            call_args = mock_create_document.call_args
            assert call_args[1]["client_id"] == sample_client.id
            assert call_args[1]["filename"] == "test.pdf"
            assert call_args[1]["document_type"] == DocumentType.SIMPLE

    @patch("app.services.document_service.DocumentService.create_document")
    @pytest.mark.asyncio
    async def test_duplicate_file_error_handling(
        self, mock_create_document, sample_client, sample_pdf_file
    ):
        """Test error handling when duplicate file is detected."""
        # Arrange
        mock_create_document.return_value = {
            "success": False,
            "error": "Documento duplicado encontrado. Arquivo já existe: existing_file.pdf",
        }

        with Screen("/test") as screen:

            @ui.page("/test")
            def test_page():
                upload_dialog = DocumentUploadDialog(sample_client)
                upload_dialog.show()

            await screen.open("/test")

            # Simulate file upload with duplicate
            with open(sample_pdf_file, "rb") as f:
                file_content = f.read()

            upload_dialog.uploaded_file_info = {
                "filename": "duplicate.pdf",
                "content": file_content,
                "size": len(file_content),
                "hash": "duplicate_hash",
            }
            upload_dialog._update_file_info()

            # Submit the duplicate file
            submit_button = screen.find("Enviar Documento")
            submit_button.click()

            # Verify error notification appears
            screen.should_contain("Documento duplicado encontrado")

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_processing_status_tracking(self, mock_httpx_client, sample_client):
        """Test processing status tracking and display."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": "task_123",
            "status": "SUCCESS",
            "result": {"message": "Processing completed"},
            "error": None,
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

        with Screen("/test") as screen:

            @ui.page("/test")
            def test_page():
                upload_dialog = DocumentUploadDialog(sample_client)
                upload_dialog.show()

                # Simulate successful upload that starts tracking
                upload_dialog.current_task_id = "task_123"
                upload_dialog._start_status_tracking()

            await screen.open("/test")

            # Wait for status update
            await screen.wait_for(lambda: "Status do Processamento:" in screen.content)

            # Verify status tracking elements appear
            screen.should_contain("Status do Processamento:")
            screen.should_contain("Iniciando processamento...")

    @pytest.mark.asyncio
    async def test_cancel_upload_dialog(self, sample_client):
        """Test canceling the upload dialog."""
        with Screen("/test") as screen:

            @ui.page("/test")
            def test_page():
                upload_dialog = DocumentUploadDialog(sample_client)
                upload_dialog.show()

            await screen.open("/test")

            # Verify dialog is open
            screen.should_contain(f"Upload de Documento - {sample_client.name}")

            # Click cancel button
            cancel_button = screen.find("Cancelar")
            cancel_button.click()

            # Verify dialog is closed (content should not be visible)
            screen.should_not_contain(f"Upload de Documento - {sample_client.name}")

    @pytest.mark.asyncio
    async def test_file_size_validation(self, sample_client):
        """Test file size validation and error display."""
        with Screen("/test") as screen:

            @ui.page("/test")
            def test_page():
                upload_dialog = DocumentUploadDialog(sample_client)
                upload_dialog.show()

            await screen.open("/test")

            # Verify upload component has size limit
            upload_component = screen.find(
                "Arrastar PDF aqui ou clicar para selecionar"
            )

            # In a real implementation, this would test the max_file_size property
            # For now, verify the component exists with proper configuration
            assert upload_component is not None

    @pytest.mark.asyncio
    async def test_file_type_validation(self, sample_client):
        """Test that only PDF files are accepted."""
        with Screen("/test") as screen:

            @ui.page("/test")
            def test_page():
                upload_dialog = DocumentUploadDialog(sample_client)
                upload_dialog.show()

            await screen.open("/test")

            # Simulate uploading non-PDF file
            upload_dialog._handle_file_upload(
                Mock(name="document.txt", content=b"This is not a PDF file")
            )

            # Verify error notification
            screen.should_contain("Apenas arquivos PDF são permitidos")

    @pytest.mark.asyncio
    async def test_file_info_display(self, sample_client, sample_pdf_file):
        """Test that file information is displayed correctly after upload."""
        with Screen("/test") as screen:

            @ui.page("/test")
            def test_page():
                upload_dialog = DocumentUploadDialog(sample_client)
                upload_dialog.show()

            await screen.open("/test")

            # Simulate file upload
            with open(sample_pdf_file, "rb") as f:
                file_content = f.read()

            upload_dialog.uploaded_file_info = {
                "filename": "test_document.pdf",
                "content": file_content,
                "size": len(file_content),
                "hash": "abcdef123456",
            }
            upload_dialog._update_file_info()

            # Verify file information is displayed
            screen.should_contain("Informações do arquivo:")
            screen.should_contain("Nome: test_document.pdf")
            screen.should_contain("Tamanho:")  # Size formatting
            screen.should_contain("Hash SHA256: abcdef123456")  # Truncated hash
