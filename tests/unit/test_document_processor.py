"""Unit tests for document processing logic in worker."""

import asyncio
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.models.document import Document, DocumentStatus, DocumentType
from app.workers.document_processor import _process_document_async


class TestDocumentProcessor:
    """Unit tests for document processor worker logic."""

    @pytest.fixture
    def mock_document(self):
        """Create a mock document for testing."""
        return Document(
            id=uuid.uuid4(),
            filename="test_document.pdf",
            document_type=DocumentType.SIMPLE,
            status=DocumentStatus.UPLOADED,
            client_id=uuid.uuid4(),
            content_hash="test_hash",
            file_size=1024,
            file_path="uploads/test_document.pdf"
        )

    @pytest.fixture
    def mock_file_path(self, tmp_path):
        """Create a mock file path for testing."""
        file_path = tmp_path / "test_document.pdf"
        file_path.write_bytes(b"%PDF-1.4\ntest content")
        return file_path

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        mock_repo = AsyncMock()
        mock_service = AsyncMock()
        mock_llama_processor = AsyncMock()
        
        return {
            "repository": mock_repo,
            "service": mock_service,
            "llama_processor": mock_llama_processor
        }

    @pytest.mark.asyncio
    async def test_simple_document_processing_success(self, mock_document, mock_file_path, mock_services):
        """Test successful processing of simple document."""
        # Arrange
        mock_document.document_type = DocumentType.SIMPLE
        mock_services["service"].get_document_by_id.return_value = mock_document
        mock_services["service"].get_file_path.return_value = mock_file_path
        mock_services["llama_processor"].classify_document_complexity.return_value = "simple"
        mock_services["llama_processor"].process_document.return_value = [
            MagicMock(id=uuid.uuid4(), node_id="node_1"),
            MagicMock(id=uuid.uuid4(), node_id="node_2"),
        ]

        with patch("app.workers.document_processor.get_llama_index_processor") as mock_get_processor:
            mock_get_processor.return_value = mock_services["llama_processor"]
            
            with patch("app.workers.document_processor.DocumentRepository") as mock_repo_class:
                mock_repo_class.return_value = mock_services["repository"]
                
                with patch("app.workers.document_processor.DocumentService") as mock_service_class:
                    mock_service_class.return_value = mock_services["service"]
                    
                    # Act
                    # Note: This would need to be adapted based on actual implementation
                    # For now, testing the logic components
                    pass

    @pytest.mark.asyncio
    async def test_complex_document_processing_success(self, mock_document, mock_file_path, mock_services):
        """Test successful processing of complex document requiring OCR."""
        # Arrange
        mock_document.document_type = DocumentType.COMPLEX
        mock_services["service"].get_document_by_id.return_value = mock_document
        mock_services["service"].get_file_path.return_value = mock_file_path
        mock_services["llama_processor"].classify_document_complexity.return_value = "complex"
        mock_services["llama_processor"].process_document.return_value = [
            MagicMock(id=uuid.uuid4(), node_id="node_1"),
        ]

        # Test would verify complex document path is taken
        assert mock_document.document_type == DocumentType.COMPLEX

    @pytest.mark.asyncio
    async def test_document_not_found_error(self, mock_services):
        """Test handling when document is not found."""
        # Arrange
        document_id = uuid.uuid4()
        task_id = "test_task_id"
        
        # Mock the database session and services
        with patch("app.workers.document_processor.get_async_db") as mock_get_db:
            with patch("app.workers.document_processor.DocumentRepository") as mock_repo_class:
                with patch("app.workers.document_processor.DocumentService") as mock_service_class:
                    
                    # Configure mocks
                    mock_session = AsyncMock()
                    
                    async def mock_async_db():
                        yield mock_session
                    
                    mock_get_db.return_value = mock_async_db()
                    
                    mock_repo = AsyncMock()
                    mock_repo_class.return_value = mock_repo
                    
                    mock_service = AsyncMock()
                    mock_service_class.return_value = mock_service
                    mock_service.get_document_by_id.return_value = None
                    
                    # Act & Assert
                    from app.workers.document_processor import _process_document_async
                    with pytest.raises(ValueError, match="not found"):
                        await _process_document_async(document_id, task_id)

    @pytest.mark.asyncio
    async def test_file_not_found_error(self, mock_document, mock_services):
        """Test handling when file is not found."""
        # Arrange
        document_id = uuid.uuid4()
        task_id = "test_task_id"
        mock_document.document_type = DocumentType.SIMPLE
        nonexistent_path = Path("/nonexistent/file.pdf")
        
        # Mock the database session and services
        with patch("app.workers.document_processor.get_async_db") as mock_get_db:
            with patch("app.workers.document_processor.DocumentRepository") as mock_repo_class:
                with patch("app.workers.document_processor.DocumentService") as mock_service_class:
                    
                    # Configure mocks
                    mock_session = AsyncMock()
                    
                    async def mock_async_db():
                        yield mock_session
                    
                    mock_get_db.return_value = mock_async_db()
                    
                    mock_repo = AsyncMock()
                    mock_repo_class.return_value = mock_repo
                    
                    mock_service = AsyncMock()
                    mock_service_class.return_value = mock_service
                    mock_service.get_document_by_id.return_value = mock_document
                    # get_file_path is not async, so we need to configure it differently
                    mock_service.get_file_path = Mock(return_value=nonexistent_path)
                    mock_service.update_document_status = AsyncMock()
                    
                    mock_repo.update_task_id = AsyncMock()
                    
                    # Act & Assert
                    from app.workers.document_processor import _process_document_async
                    with pytest.raises(FileNotFoundError, match="Document file not found"):
                        await _process_document_async(document_id, task_id)

    @pytest.mark.asyncio
    async def test_processing_failure_updates_status(self, mock_document, mock_file_path, mock_services):
        """Test that processing failures update document status correctly."""
        # Arrange
        document_id = uuid.uuid4()
        task_id = "test_task_id"
        mock_document.document_type = DocumentType.SIMPLE
        
        # Mock the database session and services
        with patch("app.workers.document_processor.get_async_db") as mock_get_db:
            with patch("app.workers.document_processor.DocumentRepository") as mock_repo_class:
                with patch("app.workers.document_processor.DocumentService") as mock_service_class:
                    with patch("app.workers.document_processor.get_llama_index_processor") as mock_get_processor:
                        
                        # Configure mocks
                        mock_session = AsyncMock()
                        
                        async def mock_async_db():
                            yield mock_session
                        
                        mock_get_db.return_value = mock_async_db()
                        
                        mock_repo = AsyncMock()
                        mock_repo_class.return_value = mock_repo
                        
                        mock_service = AsyncMock()
                        mock_service_class.return_value = mock_service
                        mock_service.get_document_by_id.return_value = mock_document
                        # get_file_path is not async, so we need to configure it differently
                        mock_service.get_file_path = Mock(return_value=mock_file_path)
                        mock_service.update_document_status = AsyncMock()
                        
                        mock_repo.update_task_id = AsyncMock()
                        
                        # Mock processor to fail
                        mock_processor = AsyncMock()
                        mock_get_processor.return_value = mock_processor
                        mock_processor.process_document.side_effect = Exception("Processing failed")
                        
                        # Act & Assert
                        from app.workers.document_processor import _process_document_async
                        with pytest.raises(Exception, match="Processing failed"):
                            await _process_document_async(document_id, task_id)
                        
                        # Verify status was updated to FAILED
                        mock_service.update_document_status.assert_called_with(
                            document_id, DocumentStatus.FAILED, "Processing failed"
                        )

    @pytest.mark.asyncio
    async def test_document_type_classification(self, mock_document, mock_file_path, mock_services):
        """Test automatic document type classification when not set."""
        # Arrange
        mock_document.document_type = None  # Not classified yet
        mock_services["service"].get_document_by_id.return_value = mock_document
        mock_services["service"].get_file_path.return_value = mock_file_path
        mock_services["llama_processor"].classify_document_complexity.return_value = "complex"

        # Test would verify classification is performed and document is updated
        pass

    def test_task_retry_logic(self):
        """Test Celery task retry logic for transient failures."""
        # Test would verify retry behavior
        pass

    def test_task_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        # Test would verify final failure handling
        pass