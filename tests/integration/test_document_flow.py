"""Integration tests for document upload and processing flow."""

import pytest
from unittest.mock import patch, AsyncMock, Mock
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.document import Document, DocumentStatus, DocumentType
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService


@pytest.fixture
def mock_db_session():
    """Mock database session for integration tests."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_client():
    """Sample client for testing."""
    return Client(
        id=uuid.uuid4(),
        name="Test Client",
        cpf="12345678901",
        birth_date=datetime(1990, 1, 1).date(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj xref 0 4 0000000000 65535 f 0000000010 00000 n 0000000053 00000 n 0000000100 00000 n trailer<</Size 4/Root 1 0 R>> startxref 150 %%EOF"


class TestDocumentFlow:
    """Integration tests for document upload and processing flow."""

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', create=True)
    @patch('app.workers.document_processor.process_document')
    @pytest.mark.asyncio
    async def test_complete_document_upload_flow(
        self,
        mock_process_document,
        mock_open,
        mock_mkdir,
        mock_db_session,
        sample_client,
        sample_pdf_content
    ):
        """Test complete document upload flow from UI to processing."""
        # Arrange
        document_repository = DocumentRepository(mock_db_session)
        document_service = DocumentService(document_repository, upload_dir="test_uploads")
        
        # Mock database responses
        mock_db_session.execute = AsyncMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Mock no duplicate found
        mock_result_duplicate = Mock()
        mock_result_duplicate.scalar_one_or_none.return_value = None
        
        # Mock successful document creation
        created_document = Document(
            id=uuid.uuid4(),
            filename="test_document.pdf",
            content_hash="hash123",
            file_size=len(sample_pdf_content),
            document_type=DocumentType.SIMPLE,
            status=DocumentStatus.UPLOADED,
            client_id=sample_client.id,
            file_path="uploads/test_document.pdf"
        )
        
        mock_result_create = Mock()
        mock_result_create.scalar_one_or_none.return_value = created_document
        
        # Configure mock responses in order
        mock_db_session.execute.side_effect = [
            mock_result_duplicate,  # Duplicate check
            mock_result_create,     # Document creation
        ]
        
        # Mock Celery task
        mock_task_result = Mock()
        mock_task_result.id = "task_123"
        mock_process_document.delay.return_value = mock_task_result
        
        # Mock file operations
        mock_file_handle = Mock()
        mock_open.return_value.__enter__.return_value = mock_file_handle
        
        # Act
        result = await document_service.create_document(
            client_id=sample_client.id,
            filename="test_document.pdf",
            content=sample_pdf_content,
            document_type=DocumentType.SIMPLE
        )
        
        # Assert
        assert result['success'] is True
        assert 'document_id' in result
        assert 'task_id' in result
        assert result['task_id'] == "task_123"
        
        # Verify file operations
        mock_mkdir.assert_called()
        mock_file_handle.write.assert_called_once_with(sample_pdf_content)
        
        # Verify Celery task creation
        mock_process_document.delay.assert_called_once()
        
        # Verify database operations
        assert mock_db_session.execute.call_count == 2  # Duplicate check + create
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_duplicate_document_detection(
        self,
        mock_db_session,
        sample_client,
        sample_pdf_content
    ):
        """Test duplicate document detection prevents upload."""
        # Arrange
        document_repository = DocumentRepository(mock_db_session)
        document_service = DocumentService(document_repository, upload_dir="test_uploads")
        
        # Mock existing document found
        existing_document = Document(
            id=uuid.uuid4(),
            filename="existing_document.pdf",
            content_hash="hash123",
            file_size=1024,
            document_type=DocumentType.SIMPLE,
            status=DocumentStatus.PROCESSED,
            client_id=sample_client.id,
            file_path="uploads/existing_document.pdf"
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_document
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await document_service.create_document(
            client_id=sample_client.id,
            filename="duplicate_document.pdf",
            content=sample_pdf_content,
            document_type=DocumentType.SIMPLE
        )
        
        # Assert
        assert result['success'] is False
        assert 'duplicado' in result['error']
        assert existing_document.filename in result['error']
        
        # Verify no document was created
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_document_status_updates_during_processing(
        self,
        mock_db_session
    ):
        """Test document status updates during processing lifecycle."""
        # Arrange
        document_repository = DocumentRepository(mock_db_session)
        document_service = DocumentService(document_repository, upload_dir="test_uploads")
        
        document_id = uuid.uuid4()
        document = Document(
            id=document_id,
            filename="processing_document.pdf",
            content_hash="hash123",
            file_size=1024,
            document_type=DocumentType.COMPLEX,
            status=DocumentStatus.UPLOADED,
            client_id=uuid.uuid4(),
            file_path="uploads/processing_document.pdf"
        )
        
        # Mock document retrieval
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = document
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        
        # Act & Assert - Test status progression
        
        # 1. Update to PROCESSING
        success = await document_service.update_document_status(
            document_id, 
            DocumentStatus.PROCESSING
        )
        assert success is True
        assert document.status == DocumentStatus.PROCESSING
        
        # 2. Update to PROCESSED
        success = await document_service.update_document_status(
            document_id, 
            DocumentStatus.PROCESSED
        )
        assert success is True
        assert document.status == DocumentStatus.PROCESSED
        
        # 3. Test failure case
        success = await document_service.update_document_status(
            document_id, 
            DocumentStatus.FAILED, 
            "OCR processing failed"
        )
        assert success is True
        assert document.status == DocumentStatus.FAILED
        assert document.error_message == "OCR processing failed"
        
        # Verify database commits
        # Expected: 3 status updates + 1 extra commit for processed_at timestamp
        assert mock_db_session.commit.call_count == 4

    @pytest.mark.asyncio
    async def test_get_client_documents_with_filtering(
        self,
        mock_db_session,
        sample_client
    ):
        """Test retrieving documents for a specific client."""
        # Arrange
        document_repository = DocumentRepository(mock_db_session)
        document_service = DocumentService(document_repository, upload_dir="test_uploads")
        
        # Create sample documents
        documents = [
            Document(
                id=uuid.uuid4(),
                filename="doc1.pdf",
                content_hash="hash1",
                file_size=1024,
                document_type=DocumentType.SIMPLE,
                status=DocumentStatus.PROCESSED,
                client_id=sample_client.id,
                file_path="uploads/doc1.pdf"
            ),
            Document(
                id=uuid.uuid4(),
                filename="doc2.pdf",
                content_hash="hash2",
                file_size=2048,
                document_type=DocumentType.COMPLEX,
                status=DocumentStatus.PROCESSING,
                client_id=sample_client.id,
                file_path="uploads/doc2.pdf"
            )
        ]
        
        mock_result = Mock()
        mock_result.scalars.return_value = documents
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await document_service.get_documents_by_client(sample_client.id)
        
        # Assert
        assert len(result) == 2
        assert all(doc.client_id == sample_client.id for doc in result)
        assert any(doc.status == DocumentStatus.PROCESSED for doc in result)
        assert any(doc.status == DocumentStatus.PROCESSING for doc in result)
        
        # Verify correct query was made
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_during_file_operations(
        self,
        mock_db_session,
        sample_client,
        sample_pdf_content
    ):
        """Test error handling when file operations fail."""
        # Arrange
        document_repository = DocumentRepository(mock_db_session)
        document_service = DocumentService(document_repository, upload_dir="test_uploads")
        
        # Mock no duplicate found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Mock file operation failure
        with patch('builtins.open', side_effect=OSError("Disk full")):
            # Act
            result = await document_service.create_document(
                client_id=sample_client.id,
                filename="test_document.pdf",
                content=sample_pdf_content,
                document_type=DocumentType.SIMPLE
            )
        
        # Assert
        assert result['success'] is False
        assert "Disk full" in result['error']
        
        # Verify no document was added to database
        mock_db_session.add.assert_not_called()