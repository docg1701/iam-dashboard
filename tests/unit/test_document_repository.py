"""Unit tests for DocumentRepository."""

import pytest
from unittest.mock import AsyncMock, Mock
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus, DocumentType
from app.repositories.document_repository import DocumentRepository


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def document_repository(mock_db_session):
    """Document repository with mocked session."""
    return DocumentRepository(mock_db_session)


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
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestDocumentRepository:
    """Test cases for DocumentRepository."""

    @pytest.mark.asyncio
    async def test_create_document_success(self, document_repository, mock_db_session, sample_document):
        """Test successful document creation."""
        # Arrange
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Act
        result = await document_repository.create(sample_document)
        
        # Assert
        assert result == sample_document
        mock_db_session.add.assert_called_once_with(sample_document)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(sample_document)

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, document_repository, mock_db_session, sample_document):
        """Test getting document by ID when found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_document
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await document_repository.get_by_id(sample_document.id)
        
        # Assert
        assert result == sample_document
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, document_repository, mock_db_session):
        """Test getting document by ID when not found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await document_repository.get_by_id(uuid.uuid4())
        
        # Assert
        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_client_id(self, document_repository, mock_db_session, sample_document):
        """Test getting documents by client ID."""
        # Arrange
        client_id = uuid.uuid4()
        mock_result = Mock()
        mock_result.scalars.return_value = [sample_document]
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await document_repository.get_by_client_id(client_id)
        
        # Assert
        assert result == [sample_document]
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_duplicate_by_hash_found(self, document_repository, mock_db_session, sample_document):
        """Test checking for duplicate document when found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_document
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await document_repository.check_duplicate_by_hash(
            sample_document.client_id, 
            sample_document.content_hash
        )
        
        # Assert
        assert result == sample_document
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_duplicate_by_hash_not_found(self, document_repository, mock_db_session):
        """Test checking for duplicate document when not found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await document_repository.check_duplicate_by_hash(uuid.uuid4(), "hash123")
        
        # Assert
        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_success(self, document_repository, mock_db_session, sample_document):
        """Test successful status update."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_document
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        
        # Act
        result = await document_repository.update_status(
            sample_document.id, 
            DocumentStatus.PROCESSED, 
            None
        )
        
        # Assert
        assert result is True
        assert sample_document.status == DocumentStatus.PROCESSED
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_document_not_found(self, document_repository, mock_db_session):
        """Test status update when document not found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await document_repository.update_status(uuid.uuid4(), DocumentStatus.PROCESSED)
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_update_task_id_success(self, document_repository, mock_db_session, sample_document):
        """Test successful task ID update."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_document
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        task_id = "task_123"
        
        # Act
        result = await document_repository.update_task_id(sample_document.id, task_id)
        
        # Assert
        assert result is True
        assert sample_document.task_id == task_id
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_status(self, document_repository, mock_db_session, sample_document):
        """Test getting documents by status."""
        # Arrange
        mock_result = Mock()
        mock_result.scalars.return_value = [sample_document]
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await document_repository.get_by_status(DocumentStatus.UPLOADED)
        
        # Assert
        assert result == [sample_document]
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(self, document_repository, mock_db_session, sample_document):
        """Test successful document deletion."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_document
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.delete = AsyncMock()
        mock_db_session.commit = AsyncMock()
        
        # Act
        result = await document_repository.delete(sample_document.id)
        
        # Assert
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_document)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, document_repository, mock_db_session):
        """Test deletion when document not found."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await document_repository.delete(uuid.uuid4())
        
        # Assert
        assert result is False