"""Unit tests for DocumentChunkRepository."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.document_chunk import DocumentChunk
from app.repositories.document_chunk_repository import DocumentChunkRepository


class TestDocumentChunkRepository:
    """Test cases for DocumentChunkRepository."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self, mock_db_session):
        """Create a DocumentChunkRepository instance."""
        return DocumentChunkRepository(mock_db_session)

    @pytest.fixture
    def sample_chunks(self):
        """Create sample document chunks for testing."""
        document_id = uuid.uuid4()
        return [
            DocumentChunk(
                node_id="chunk1",
                text="First chunk of text content.",
                metadata={"page": 1, "section": "header"},
                document_id=document_id,
            ),
            DocumentChunk(
                node_id="chunk2",
                text="Second chunk of text content with more details.",
                metadata={"page": 1, "section": "body"},
                document_id=document_id,
            ),
            DocumentChunk(
                node_id="chunk3",
                text="Third chunk containing footer information.",
                metadata={"page": 2, "section": "footer"},
                document_id=document_id,
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_by_document_id_success(self, repository, mock_db_session, sample_chunks):
        """Test successful retrieval of chunks by document ID."""
        document_id = sample_chunks[0].document_id

        # Mock query execution
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_chunks
        mock_db_session.execute.return_value = mock_result

        # Execute method
        result = await repository.get_by_document_id(document_id)

        # Verify results
        assert len(result) == 3
        assert all(chunk.document_id == document_id for chunk in result)
        assert result[0].node_id == "chunk1"
        assert result[1].node_id == "chunk2"
        assert result[2].node_id == "chunk3"

        # Verify query was executed
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_document_id_empty(self, repository, mock_db_session):
        """Test retrieval when no chunks exist for document ID."""
        document_id = uuid.uuid4()

        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        # Execute method
        result = await repository.get_by_document_id(document_id)

        # Verify empty result
        assert len(result) == 0
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_db_session, sample_chunks):
        """Test successful retrieval of chunk by node ID."""
        chunk = sample_chunks[0]

        # Mock query execution
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = chunk
        mock_db_session.execute.return_value = mock_result

        # Execute method
        result = await repository.get_by_id(chunk.node_id)

        # Verify result
        assert result == chunk
        assert result.node_id == "chunk1"
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_db_session):
        """Test retrieval when chunk with node ID doesn't exist."""
        node_id = "nonexistent_chunk"

        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute method
        result = await repository.get_by_id(node_id)

        # Verify None result
        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_db_session, sample_chunks):
        """Test successful creation of a document chunk."""
        chunk = sample_chunks[0]

        # Execute method
        result = await repository.create(chunk)

        # Verify operations
        mock_db_session.add.assert_called_once_with(chunk)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(chunk)
        assert result == chunk

    @pytest.mark.asyncio
    async def test_create_multiple_success(self, repository, mock_db_session, sample_chunks):
        """Test successful creation of multiple document chunks."""
        # Execute method
        result = await repository.create_multiple(sample_chunks)

        # Verify operations
        mock_db_session.add_all.assert_called_once_with(sample_chunks)
        mock_db_session.commit.assert_called_once()
        
        # Verify refresh was called for each chunk
        assert mock_db_session.refresh.call_count == len(sample_chunks)
        assert result == sample_chunks

    @pytest.mark.asyncio
    async def test_create_multiple_empty_list(self, repository, mock_db_session):
        """Test creation with empty chunk list."""
        empty_chunks = []

        # Execute method
        result = await repository.create_multiple(empty_chunks)

        # Verify operations
        mock_db_session.add_all.assert_called_once_with(empty_chunks)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_not_called()
        assert result == empty_chunks

    @pytest.mark.asyncio
    async def test_delete_by_document_id_success(self, repository, mock_db_session, sample_chunks):
        """Test successful deletion of chunks by document ID."""
        document_id = sample_chunks[0].document_id

        # Mock query execution to return chunks
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_chunks
        mock_db_session.execute.return_value = mock_result

        # Execute method
        result = await repository.delete_by_document_id(document_id)

        # Verify operations
        assert result is True
        mock_db_session.execute.assert_called_once()
        
        # Verify delete was called for each chunk
        assert mock_db_session.delete.call_count == len(sample_chunks)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_document_id_no_chunks(self, repository, mock_db_session):
        """Test deletion when no chunks exist for document ID."""
        document_id = uuid.uuid4()

        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        # Execute method
        result = await repository.delete_by_document_id(document_id)

        # Verify operations
        assert result is True
        mock_db_session.execute.assert_called_once()
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_by_document_id_success(self, repository, mock_db_session, sample_chunks):
        """Test successful counting of chunks by document ID."""
        document_id = sample_chunks[0].document_id

        # Mock query execution
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_chunks
        mock_db_session.execute.return_value = mock_result

        # Execute method
        result = await repository.count_by_document_id(document_id)

        # Verify result
        assert result == 3
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_by_document_id_zero(self, repository, mock_db_session):
        """Test counting when no chunks exist for document ID."""
        document_id = uuid.uuid4()

        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        # Execute method
        result = await repository.count_by_document_id(document_id)

        # Verify result
        assert result == 0
        mock_db_session.execute.assert_called_once()

    def test_repository_initialization(self, mock_db_session):
        """Test repository initialization."""
        repository = DocumentChunkRepository(mock_db_session)
        
        assert repository.db_session == mock_db_session

    @pytest.mark.asyncio
    async def test_database_error_handling(self, repository, mock_db_session):
        """Test error handling for database exceptions."""
        document_id = uuid.uuid4()

        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database connection failed")

        # Verify exception is propagated
        with pytest.raises(Exception, match="Database connection failed"):
            await repository.get_by_document_id(document_id)

    @pytest.mark.asyncio
    async def test_create_commit_error(self, repository, mock_db_session, sample_chunks):
        """Test error handling during commit in create operation."""
        chunk = sample_chunks[0]

        # Mock commit error
        mock_db_session.commit.side_effect = Exception("Commit failed")

        # Verify exception is propagated
        with pytest.raises(Exception, match="Commit failed"):
            await repository.create(chunk)

        # Verify add was called before the error
        mock_db_session.add.assert_called_once_with(chunk)

    @pytest.mark.asyncio
    async def test_create_multiple_commit_error(self, repository, mock_db_session, sample_chunks):
        """Test error handling during commit in create_multiple operation."""
        # Mock commit error
        mock_db_session.commit.side_effect = Exception("Commit failed")

        # Verify exception is propagated
        with pytest.raises(Exception, match="Commit failed"):
            await repository.create_multiple(sample_chunks)

        # Verify add_all was called before the error
        mock_db_session.add_all.assert_called_once_with(sample_chunks)

    @pytest.mark.asyncio
    async def test_delete_commit_error(self, repository, mock_db_session, sample_chunks):
        """Test error handling during commit in delete operation."""
        document_id = sample_chunks[0].document_id

        # Mock query to return chunks
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_chunks
        mock_db_session.execute.return_value = mock_result

        # Mock commit error
        mock_db_session.commit.side_effect = Exception("Commit failed")

        # Verify exception is propagated
        with pytest.raises(Exception, match="Commit failed"):
            await repository.delete_by_document_id(document_id)

        # Verify deletes were called before the error
        assert mock_db_session.delete.call_count == len(sample_chunks)

    def test_chunk_metadata_handling(self, sample_chunks):
        """Test that chunk metadata is properly structured."""
        chunk = sample_chunks[0]
        
        assert isinstance(chunk.metadata, dict)
        assert "page" in chunk.metadata
        assert "section" in chunk.metadata
        assert chunk.metadata["page"] == 1
        assert chunk.metadata["section"] == "header"

    def test_chunk_text_content(self, sample_chunks):
        """Test that chunk text content is properly stored."""
        chunk1, chunk2, chunk3 = sample_chunks
        
        assert chunk1.text == "First chunk of text content."
        assert chunk2.text == "Second chunk of text content with more details."
        assert chunk3.text == "Third chunk containing footer information."
        
        # Verify text lengths
        assert len(chunk1.text) < len(chunk2.text)
        assert all(len(chunk.text) > 0 for chunk in sample_chunks)

    def test_chunk_node_id_uniqueness(self, sample_chunks):
        """Test that chunk node IDs are unique."""
        node_ids = [chunk.node_id for chunk in sample_chunks]
        
        assert len(node_ids) == len(set(node_ids))  # All unique
        assert all(node_id.startswith("chunk") for node_id in node_ids)

    def test_chunk_document_relationship(self, sample_chunks):
        """Test that all chunks belong to the same document."""
        document_ids = [chunk.document_id for chunk in sample_chunks]
        
        # All chunks should have the same document_id
        assert len(set(document_ids)) == 1
        assert all(isinstance(doc_id, uuid.UUID) for doc_id in document_ids)