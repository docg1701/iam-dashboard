"""Unit tests for DocumentService."""

import hashlib
import uuid
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from app.models.document import Document, DocumentStatus, DocumentType
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService


@pytest.fixture
def mock_document_repository():
    """Mock document repository."""
    return AsyncMock(spec=DocumentRepository)


@pytest.fixture
def document_service(mock_document_repository):
    """Document service with mocked repository."""
    return DocumentService(mock_document_repository, upload_dir="test_uploads")


@pytest.fixture
def sample_file_content():
    """Sample PDF file content."""
    return b"PDF file content for testing"


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    client_id = uuid.uuid4()
    return Document(
        id=uuid.uuid4(),
        filename="test.pdf",
        content_hash="abc123",
        file_size=1024,
        document_type=DocumentType.SIMPLE,
        status=DocumentStatus.UPLOADED,
        client_id=client_id,
        file_path="uploads/test.pdf",
    )


class TestDocumentService:
    """Test cases for DocumentService."""

    def test_calculate_file_hash(self, document_service, sample_file_content):
        """Test file hash calculation."""
        # Act
        result = document_service.calculate_file_hash(sample_file_content)

        # Assert
        expected_hash = hashlib.sha256(sample_file_content).hexdigest()
        assert result == expected_hash

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_check_duplicate_found(
        self, document_service, mock_document_repository, sample_document
    ):
        """Test duplicate check when duplicate found."""
        # Arrange
        client_id = uuid.uuid4()
        content_hash = "abc123"
        mock_document_repository.check_duplicate_by_hash.return_value = sample_document

        # Act
        result = await document_service.check_duplicate(client_id, content_hash)

        # Assert
        assert result == sample_document
        mock_document_repository.check_duplicate_by_hash.assert_called_once_with(
            client_id, content_hash
        )

    @pytest.mark.asyncio
    async def test_check_duplicate_not_found(
        self, document_service, mock_document_repository
    ):
        """Test duplicate check when no duplicate found."""
        # Arrange
        client_id = uuid.uuid4()
        content_hash = "abc123"
        mock_document_repository.check_duplicate_by_hash.return_value = None

        # Act
        result = await document_service.check_duplicate(client_id, content_hash)

        # Assert
        assert result is None
        mock_document_repository.check_duplicate_by_hash.assert_called_once_with(
            client_id, content_hash
        )

    @pytest.mark.asyncio
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("app.workers.document_processor.process_document")
    @pytest.mark.asyncio
    async def test_create_document_success(
        self,
        mock_process_document,
        mock_file_open,
        mock_mkdir,
        document_service,
        mock_document_repository,
        sample_file_content,
        sample_document,
    ):
        """Test successful document creation."""
        # Arrange
        client_id = uuid.uuid4()
        filename = "test.pdf"
        document_type = DocumentType.SIMPLE

        mock_document_repository.check_duplicate_by_hash.return_value = None
        mock_document_repository.create.return_value = sample_document
        mock_document_repository.update_task_id = AsyncMock()

        # Mock Celery task
        mock_task_result = Mock()
        mock_task_result.id = "task_123"
        mock_process_document.delay.return_value = mock_task_result

        # Act
        result = await document_service.create_document(
            client_id, filename, sample_file_content, document_type
        )

        # Assert
        assert result["success"] is True
        assert "document_id" in result
        assert "task_id" in result
        mock_document_repository.create.assert_called_once()
        mock_file_open.assert_called_once()
        mock_process_document.delay.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_duplicate_found(
        self,
        document_service,
        mock_document_repository,
        sample_file_content,
        sample_document,
    ):
        """Test document creation when duplicate exists."""
        # Arrange
        client_id = uuid.uuid4()
        filename = "test.pdf"
        document_type = DocumentType.SIMPLE

        mock_document_repository.check_duplicate_by_hash.return_value = sample_document

        # Act
        result = await document_service.create_document(
            client_id, filename, sample_file_content, document_type
        )

        # Assert
        assert result["success"] is False
        assert "duplicado" in result["error"]
        mock_document_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_document_by_id(
        self, document_service, mock_document_repository, sample_document
    ):
        """Test getting document by ID."""
        # Arrange
        document_id = uuid.uuid4()
        mock_document_repository.get_by_id.return_value = sample_document

        # Act
        result = await document_service.get_document_by_id(document_id)

        # Assert
        assert result == sample_document
        mock_document_repository.get_by_id.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_documents_by_client(
        self, document_service, mock_document_repository, sample_document
    ):
        """Test getting documents by client."""
        # Arrange
        client_id = uuid.uuid4()
        mock_document_repository.get_by_client_id.return_value = [sample_document]

        # Act
        result = await document_service.get_documents_by_client(client_id)

        # Assert
        assert result == [sample_document]
        mock_document_repository.get_by_client_id.assert_called_once_with(client_id)

    @pytest.mark.asyncio
    async def test_update_document_status_success(
        self, document_service, mock_document_repository
    ):
        """Test successful document status update."""
        # Arrange
        document_id = uuid.uuid4()
        status = DocumentStatus.PROCESSED
        mock_document_repository.update_status.return_value = True

        # Act
        result = await document_service.update_document_status(document_id, status)

        # Assert
        assert result is True
        mock_document_repository.update_status.assert_called_once_with(
            document_id, status, None
        )

    @pytest.mark.asyncio
    async def test_update_document_status_with_error(
        self, document_service, mock_document_repository
    ):
        """Test document status update with error message."""
        # Arrange
        document_id = uuid.uuid4()
        status = DocumentStatus.FAILED
        error_message = "Processing failed"
        mock_document_repository.update_status.return_value = True

        # Act
        result = await document_service.update_document_status(
            document_id, status, error_message
        )

        # Assert
        assert result is True
        mock_document_repository.update_status.assert_called_once_with(
            document_id, status, error_message
        )

    @pytest.mark.asyncio
    async def test_get_document_by_task_id(
        self, document_service, mock_document_repository, sample_document
    ):
        """Test getting document by task ID."""
        # Arrange
        task_id = "task_123"
        mock_document_repository.get_by_task_id.return_value = sample_document

        # Act
        result = await document_service.get_document_by_task_id(task_id)

        # Assert
        assert result == sample_document
        mock_document_repository.get_by_task_id.assert_called_once_with(task_id)

    @pytest.mark.asyncio
    async def test_get_processing_documents(
        self, document_service, mock_document_repository, sample_document
    ):
        """Test getting processing documents."""
        # Arrange
        mock_document_repository.get_by_status.return_value = [sample_document]

        # Act
        result = await document_service.get_processing_documents()

        # Assert
        assert result == [sample_document]
        mock_document_repository.get_by_status.assert_called_once_with(
            DocumentStatus.PROCESSING
        )

    @pytest.mark.asyncio
    async def test_get_failed_documents(
        self, document_service, mock_document_repository, sample_document
    ):
        """Test getting failed documents."""
        # Arrange
        mock_document_repository.get_by_status.return_value = [sample_document]

        # Act
        result = await document_service.get_failed_documents()

        # Assert
        assert result == [sample_document]
        mock_document_repository.get_by_status.assert_called_once_with(
            DocumentStatus.FAILED
        )

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    @pytest.mark.asyncio
    async def test_delete_document_success(
        self,
        mock_unlink,
        mock_exists,
        document_service,
        mock_document_repository,
        sample_document,
    ):
        """Test successful document deletion."""
        # Arrange
        document_id = uuid.uuid4()
        mock_document_repository.get_by_id.return_value = sample_document
        mock_document_repository.delete.return_value = True
        mock_exists.return_value = True

        # Act
        result = await document_service.delete_document(document_id)

        # Assert
        assert result is True
        mock_unlink.assert_called_once()
        mock_document_repository.delete.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_delete_document_not_found(
        self, document_service, mock_document_repository
    ):
        """Test document deletion when document not found."""
        # Arrange
        document_id = uuid.uuid4()
        mock_document_repository.get_by_id.return_value = None

        # Act
        result = await document_service.delete_document(document_id)

        # Assert
        assert result is False
        mock_document_repository.delete.assert_not_called()

    def test_get_file_path(self, document_service, sample_document):
        """Test getting file path for document."""
        # Act
        result = document_service.get_file_path(sample_document)

        # Assert
        expected_path = document_service.upload_dir / sample_document.file_path
        assert result == expected_path
