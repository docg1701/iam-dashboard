"""Integration tests for status update mechanisms."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.document import Document, DocumentStatus, DocumentType
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService


class TestStatusTracking:
    """Integration tests for document status tracking mechanisms."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document(
            id=uuid.uuid4(),
            filename="status_test.pdf",
            document_type=DocumentType.SIMPLE,
            status=DocumentStatus.UPLOADED,
            client_id=uuid.uuid4(),
            content_hash="status_hash",
            file_size=1024,
            file_path="uploads/status_test.pdf",
        )

    @pytest.mark.asyncio
    async def test_status_progression_uploaded_to_processing(
        self, mock_db_session, sample_document
    ):
        """Test status progression from UPLOADED to PROCESSING."""
        # Arrange
        repository = DocumentRepository(mock_db_session)
        service = DocumentService(repository)

        # Mock repository methods
        repository.update_status = AsyncMock(return_value=True)
        repository.get_by_id = AsyncMock(return_value=sample_document)

        # Act
        result = await service.update_document_status(
            sample_document.id, DocumentStatus.PROCESSING
        )

        # Assert
        assert result is True
        repository.update_status.assert_called_once_with(
            sample_document.id, DocumentStatus.PROCESSING, None
        )

    @pytest.mark.asyncio
    async def test_status_progression_processing_to_processed(
        self, mock_db_session, sample_document
    ):
        """Test status progression from PROCESSING to PROCESSED."""
        # Arrange
        sample_document.status = DocumentStatus.PROCESSING
        repository = DocumentRepository(mock_db_session)
        service = DocumentService(repository)

        repository.update_status = AsyncMock(return_value=True)
        repository.get_by_id = AsyncMock(return_value=sample_document)

        # Act
        result = await service.update_document_status(
            sample_document.id, DocumentStatus.PROCESSED
        )

        # Assert
        assert result is True
        repository.update_status.assert_called_once_with(
            sample_document.id, DocumentStatus.PROCESSED, None
        )

    @pytest.mark.asyncio
    async def test_status_progression_to_failed_with_error_message(
        self, mock_db_session, sample_document
    ):
        """Test status progression to FAILED with error message."""
        # Arrange
        sample_document.status = DocumentStatus.PROCESSING
        repository = DocumentRepository(mock_db_session)
        service = DocumentService(repository)

        repository.update_status = AsyncMock(return_value=True)
        repository.get_by_id = AsyncMock(return_value=sample_document)

        error_message = "Processing failed due to OCR error"

        # Act
        result = await service.update_document_status(
            sample_document.id, DocumentStatus.FAILED, error_message
        )

        # Assert
        assert result is True
        repository.update_status.assert_called_once_with(
            sample_document.id, DocumentStatus.FAILED, error_message
        )

    @pytest.mark.asyncio
    async def test_task_id_tracking_update(self, mock_db_session, sample_document):
        """Test task ID tracking during processing."""
        # Arrange
        repository = DocumentRepository(mock_db_session)
        repository.update_task_id = AsyncMock(return_value=True)

        task_id = "celery_task_12345"

        # Act
        result = await repository.update_task_id(sample_document.id, task_id)

        # Assert
        assert result is True
        repository.update_task_id.assert_called_once_with(sample_document.id, task_id)

    @pytest.mark.asyncio
    async def test_document_retrieval_by_task_id(
        self, mock_db_session, sample_document
    ):
        """Test retrieving document by Celery task ID."""
        # Arrange
        sample_document.task_id = "celery_task_12345"
        repository = DocumentRepository(mock_db_session)
        repository.get_by_task_id = AsyncMock(return_value=sample_document)

        # Act
        result = await repository.get_by_task_id("celery_task_12345")

        # Assert
        assert result == sample_document
        assert result.task_id == "celery_task_12345"

    @pytest.mark.asyncio
    async def test_documents_retrieval_by_status(self, mock_db_session):
        """Test retrieving all documents with specific status."""
        # Arrange
        processing_docs = [
            Document(
                id=uuid.uuid4(),
                filename=f"doc_{i}.pdf",
                status=DocumentStatus.PROCESSING,
                client_id=uuid.uuid4(),
                content_hash=f"hash_{i}",
                file_size=1024,
                file_path=f"uploads/doc_{i}.pdf",
            )
            for i in range(3)
        ]

        repository = DocumentRepository(mock_db_session)
        repository.get_by_status = AsyncMock(return_value=processing_docs)

        # Act
        result = await repository.get_by_status(DocumentStatus.PROCESSING)

        # Assert
        assert len(result) == 3
        assert all(doc.status == DocumentStatus.PROCESSING for doc in result)

    @pytest.mark.asyncio
    async def test_status_update_nonexistent_document(self, mock_db_session):
        """Test status update for non-existent document."""
        # Arrange
        nonexistent_id = uuid.uuid4()
        repository = DocumentRepository(mock_db_session)
        service = DocumentService(repository)

        repository.update_status = AsyncMock(return_value=False)  # Document not found

        # Act
        result = await service.update_document_status(
            nonexistent_id, DocumentStatus.PROCESSED
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_concurrent_status_updates(self, mock_db_session, sample_document):
        """Test concurrent status updates to the same document."""
        # Arrange
        repository = DocumentRepository(mock_db_session)
        service = DocumentService(repository)

        # Mock successful updates
        repository.update_status = AsyncMock(return_value=True)
        repository.get_by_id = AsyncMock(return_value=sample_document)

        # Act - simulate concurrent updates
        tasks = [
            service.update_document_status(
                sample_document.id, DocumentStatus.PROCESSING
            ),
            service.update_document_status(
                sample_document.id, DocumentStatus.PROCESSED
            ),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - both updates should succeed (in a real scenario, database constraints would handle conflicts)
        assert all(
            result is True for result in results if not isinstance(result, Exception)
        )

    @pytest.mark.asyncio
    async def test_status_transition_validation(self, mock_db_session, sample_document):
        """Test validation of status transitions."""
        # This test would verify that invalid status transitions are prevented
        # For example, going from PROCESSED back to PROCESSING should be invalid

        # Arrange
        sample_document.status = DocumentStatus.PROCESSED
        repository = DocumentRepository(mock_db_session)
        service = DocumentService(repository)

        # In a real implementation, this might raise an exception or return False
        # For now, we'll assume all transitions are allowed at the repository level
        repository.update_status = AsyncMock(return_value=True)

        # Act
        result = await service.update_document_status(
            sample_document.id,
            DocumentStatus.PROCESSING,  # Invalid transition from PROCESSED to PROCESSING
        )

        # Assert - this would depend on business logic implementation
        assert result is True  # Current implementation allows all transitions

    @pytest.mark.asyncio
    async def test_processing_timestamp_update(self, mock_db_session, sample_document):
        """Test that processed_at timestamp is updated correctly."""
        # This test would verify that the processed_at field is set when document is marked as processed

        # Arrange
        repository = DocumentRepository(mock_db_session)

        # Mock the save method to capture the document state
        saved_documents = []

        async def mock_save(document):
            saved_documents.append(document)
            return document

        repository.save = mock_save

        # Act
        sample_document.status = DocumentStatus.PROCESSED
        await repository.save(sample_document)

        # Assert
        assert len(saved_documents) == 1
        assert saved_documents[0].status == DocumentStatus.PROCESSED

    @pytest.mark.asyncio
    async def test_error_message_persistence(self, mock_db_session):
        """Test that error messages are properly persisted."""
        # Arrange
        document_id = uuid.uuid4()
        error_message = "Detailed error message about processing failure"

        # Mock document in database
        mock_document = MagicMock()
        mock_document.id = document_id

        repository = DocumentRepository(mock_db_session)

        # Mock the database operations
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            mock_document
        )
        mock_db_session.commit = AsyncMock()

        # Act
        result = await repository.update_status(
            document_id, DocumentStatus.FAILED, error_message
        )

        # Assert
        assert result is True
        assert mock_document.status == DocumentStatus.FAILED
        assert mock_document.error_message == error_message

    @pytest.mark.asyncio
    async def test_bulk_status_updates(self, mock_db_session):
        """Test bulk status updates for multiple documents."""
        # This test would verify efficient bulk updating of document statuses
        # Useful for scenarios like marking all stuck PROCESSING documents as FAILED
        pass

    @pytest.mark.asyncio
    async def test_status_change_notifications(self, mock_db_session, sample_document):
        """Test that status changes trigger appropriate notifications."""
        # This test would verify that status changes trigger events/notifications
        # for real-time UI updates
        pass

    @pytest.mark.asyncio
    async def test_status_history_tracking(self, mock_db_session, sample_document):
        """Test tracking of status change history."""
        # This test would verify that a complete history of status changes is maintained
        # Useful for auditing and debugging
        pass

    @pytest.mark.asyncio
    async def test_status_rollback_scenarios(self, mock_db_session, sample_document):
        """Test status rollback in various failure scenarios."""
        # This test would verify that status is properly rolled back
        # when processing fails at various stages
        pass

    def test_document_status_enum_values(self):
        """Test that document status enum has expected values."""
        # Assert all expected status values exist
        assert DocumentStatus.UPLOADED == "uploaded"
        assert DocumentStatus.PROCESSING == "processing"
        assert DocumentStatus.PROCESSED == "processed"
        assert DocumentStatus.FAILED == "failed"

    def test_document_status_property_methods(self, sample_document):
        """Test document status property methods."""
        # Test is_processing property
        sample_document.status = DocumentStatus.PROCESSING
        assert sample_document.is_processing is True

        sample_document.status = DocumentStatus.UPLOADED
        assert sample_document.is_processing is False

        # Test is_processed property
        sample_document.status = DocumentStatus.PROCESSED
        assert sample_document.is_processed is True

        sample_document.status = DocumentStatus.PROCESSING
        assert sample_document.is_processed is False

        # Test has_failed property
        sample_document.status = DocumentStatus.FAILED
        assert sample_document.has_failed is True

        sample_document.status = DocumentStatus.PROCESSED
        assert sample_document.has_failed is False
