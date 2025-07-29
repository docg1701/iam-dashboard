"""Unit tests for vector storage tools."""

from unittest.mock import Mock, patch

import pytest

from app.tools.vector_storage_tools import VectorStorageTool


class TestVectorStorageTool:
    """Test VectorStorageTool functionality."""

    @pytest.fixture
    def vector_tool(self) -> VectorStorageTool:
        """Create a test VectorStorageTool instance."""
        return VectorStorageTool(
            embedding_model="gemini-embedding-001",
            chunk_size=500,
            chunk_overlap=50,
            max_chunks_per_document=100,
        )

    def test_tool_initialization(self, vector_tool: VectorStorageTool) -> None:
        """Test tool initialization."""
        assert vector_tool.embedding_model == "gemini-embedding-001"
        assert vector_tool.chunk_size == 500
        assert vector_tool.chunk_overlap == 50
        assert vector_tool.max_chunks_per_document == 100

    @patch("app.core.database.get_db")
    def test_validate_pgvector_setup_success(
        self, mock_get_db: Mock, vector_tool: VectorStorageTool
    ) -> None:
        """Test successful pgvector validation."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value.__next__ = Mock(return_value=mock_db)

        # Mock extension check
        mock_result = Mock()
        mock_result.fetchone.return_value = ("vector",)
        mock_db.execute.return_value = mock_result

        result = vector_tool.validate_pgvector_setup()

        assert result["valid"] is True
        assert result["pgvector_available"] is True

    @patch("app.core.database.get_db")
    def test_validate_pgvector_setup_extension_missing(
        self, mock_get_db: Mock, vector_tool: VectorStorageTool
    ) -> None:
        """Test pgvector validation when extension is missing."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value.__next__ = Mock(return_value=mock_db)

        # Mock extension check - no result
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        result = vector_tool.validate_pgvector_setup()

        assert result["valid"] is False
        assert "pgvector extension not installed" in result["error"]

    @patch("app.core.database.get_db", side_effect=Exception("DB connection failed"))
    def test_validate_pgvector_setup_failure(
        self, mock_get_db: Mock, vector_tool: VectorStorageTool
    ) -> None:
        """Test pgvector validation failure."""
        result = vector_tool.validate_pgvector_setup()

        assert result["valid"] is False
        assert "pgvector validation failed" in result["error"]

    def test_chunk_text_simple(self, vector_tool: VectorStorageTool) -> None:
        """Test simple text chunking."""
        text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
        metadata = {"source": "test"}

        chunks = vector_tool.chunk_text(text, metadata)

        assert len(chunks) > 0
        assert all("chunk_id" in chunk for chunk in chunks)
        assert all("text" in chunk for chunk in chunks)
        assert all(
            "metadata" in chunk and chunk["metadata"] == metadata for chunk in chunks
        )

        # Verify chunks have appropriate sizes (considering chunk_size=500)
        for chunk in chunks:
            assert len(chunk["text"]) <= vector_tool.chunk_size

    def test_chunk_text_empty(self, vector_tool: VectorStorageTool) -> None:
        """Test chunking empty text."""
        chunks = vector_tool.chunk_text("")
        assert chunks == []

        chunks = vector_tool.chunk_text("   ")  # Only whitespace
        assert chunks == []

    def test_chunk_text_large_document(self, vector_tool: VectorStorageTool) -> None:
        """Test chunking large document."""
        # Create text larger than chunk_size
        large_text = "This is a sentence. " * 100  # ~2000 characters

        chunks = vector_tool.chunk_text(large_text)

        assert len(chunks) > 1  # Should be split into multiple chunks
        assert len(chunks) <= vector_tool.max_chunks_per_document

        # Verify overlap between consecutive chunks
        if len(chunks) > 1:
            # Check that there's some overlap (though exact overlap depends on sentence boundaries)
            assert (
                chunks[0]["end_pos"]
                > chunks[1]["start_pos"] - vector_tool.chunk_overlap
            )

    @patch("google.generativeai.embed_content")
    def test_generate_embedding_success(
        self, mock_embed_content: Mock, vector_tool: VectorStorageTool
    ) -> None:
        """Test successful embedding generation."""
        mock_embed_content.return_value = {"embedding": [0.1, 0.2, 0.3, 0.4, 0.5]}

        result = vector_tool.generate_embedding("Sample text for embedding")

        assert result["success"] is True
        assert result["embedding"] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert result["dimension"] == 5
        assert result["model"] == "gemini-embedding-001"

    def test_generate_embedding_empty_text(
        self, vector_tool: VectorStorageTool
    ) -> None:
        """Test embedding generation with empty text."""
        result = vector_tool.generate_embedding("")

        assert result["success"] is False
        assert "Empty text provided" in result["error"]

    @patch("google.generativeai.embed_content", side_effect=Exception("API error"))
    def test_generate_embedding_failure(
        self, mock_embed_content: Mock, vector_tool: VectorStorageTool
    ) -> None:
        """Test embedding generation failure."""
        result = vector_tool.generate_embedding("Sample text")

        assert result["success"] is False
        assert "Failed to generate embedding" in result["error"]

    def test_generate_embeddings_batch_success(
        self, vector_tool: VectorStorageTool
    ) -> None:
        """Test successful batch embedding generation."""
        text_chunks = [
            {"chunk_id": 0, "text": "First chunk", "metadata": {}},
            {"chunk_id": 1, "text": "Second chunk", "metadata": {}},
        ]

        with patch.object(vector_tool, "generate_embedding") as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "embedding": [0.1, 0.2, 0.3],
                "dimension": 3,
            }

            result = vector_tool.generate_embeddings_batch(text_chunks)

            assert result["success"] is True
            assert result["total_chunks"] == 2
            assert result["successful_embeddings"] == 2
            assert len(result["embeddings"]) == 2
            assert result["embedding_dimension"] == 3

    def test_generate_embeddings_batch_partial_failure(
        self, vector_tool: VectorStorageTool
    ) -> None:
        """Test batch embedding generation with partial failures."""
        text_chunks = [
            {"chunk_id": 0, "text": "First chunk", "metadata": {}},
            {"chunk_id": 1, "text": "Second chunk", "metadata": {}},
        ]

        with patch.object(vector_tool, "generate_embedding") as mock_generate:

            def side_effect(text, task_type="retrieval_document"):
                if "First" in text:
                    return {
                        "success": True,
                        "embedding": [0.1, 0.2, 0.3],
                        "dimension": 3,
                    }
                else:
                    return {"success": False, "error": "Embedding failed"}

            mock_generate.side_effect = side_effect

            result = vector_tool.generate_embeddings_batch(text_chunks)

            assert result["success"] is True
            assert result["total_chunks"] == 2
            assert result["successful_embeddings"] == 1
            assert len(result["failed_chunks"]) == 1

    @patch("app.core.database.get_db")
    def test_store_document_embeddings_success(
        self, mock_get_db: Mock, vector_tool: VectorStorageTool
    ) -> None:
        """Test successful document embeddings storage."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value.__next__ = Mock(return_value=mock_db)

        embeddings_data = [
            {
                "chunk_id": 0,
                "text": "First chunk",
                "embedding": [0.1, 0.2, 0.3],
                "start_pos": 0,
                "end_pos": 11,
                "char_count": 11,
                "metadata": {"source": "test"},
            }
        ]

        result = vector_tool.store_document_embeddings(123, embeddings_data)

        assert result["success"] is True
        assert result["document_id"] == 123
        assert result["stored_embeddings"] == 1
        assert result["total_embeddings"] == 1

        # Verify database operations were called
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    @patch("app.core.database.get_db")
    def test_store_document_embeddings_failure(
        self, mock_get_db: Mock, vector_tool: VectorStorageTool
    ) -> None:
        """Test document embeddings storage failure."""
        # Mock database session that raises exception
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Database error")
        mock_get_db.return_value.__next__ = Mock(return_value=mock_db)

        embeddings_data = [{"chunk_id": 0, "text": "Test", "embedding": [0.1]}]

        result = vector_tool.store_document_embeddings(123, embeddings_data)

        assert result["success"] is False
        assert "Failed to store embeddings" in result["error"]

    @patch("app.core.database.get_db")
    def test_search_similar_content_success(
        self, mock_get_db: Mock, vector_tool: VectorStorageTool
    ) -> None:
        """Test successful similarity search."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value.__next__ = Mock(return_value=mock_db)

        # Mock query embedding generation
        with patch.object(vector_tool, "generate_embedding") as mock_generate:
            mock_generate.return_value = {"success": True, "embedding": [0.1, 0.2, 0.3]}

            # Mock search results
            mock_row = Mock()
            mock_row.id = 1
            mock_row.document_id = 123
            mock_row.chunk_id = 0
            mock_row.filename = "test.pdf"
            mock_row.text_content = "Similar content"
            mock_row.start_pos = 0
            mock_row.end_pos = 15
            mock_row.char_count = 15
            mock_row.metadata = '{"source": "test"}'
            mock_row.similarity_score = 0.85
            mock_row.created_at = None

            mock_db.execute.return_value.fetchall.return_value = [mock_row]

            result = vector_tool.search_similar_content("query text", limit=5)

            assert result["success"] is True
            assert result["total_results"] == 1
            assert len(result["results"]) == 1
            assert result["results"][0]["similarity_score"] == 0.85
            assert result["results"][0]["text_content"] == "Similar content"

    def test_search_similar_content_embedding_failure(
        self, vector_tool: VectorStorageTool
    ) -> None:
        """Test similarity search with embedding generation failure."""
        with patch.object(vector_tool, "generate_embedding") as mock_generate:
            mock_generate.return_value = {"success": False, "error": "Embedding failed"}

            result = vector_tool.search_similar_content("query text")

            assert result["success"] is False
            assert "Embedding failed" in result["error"]

    def test_process_document_text_success(
        self, vector_tool: VectorStorageTool
    ) -> None:
        """Test successful document text processing."""
        document_text = "This is a sample document. It has multiple sentences. This should be processed into chunks and embeddings."

        with (
            patch.object(vector_tool, "chunk_text") as mock_chunk,
            patch.object(vector_tool, "generate_embeddings_batch") as mock_embed,
            patch.object(vector_tool, "store_document_embeddings") as mock_store,
        ):
            # Mock chunking
            mock_chunks = [{"chunk_id": 0, "text": "Sample chunk"}]
            mock_chunk.return_value = mock_chunks

            # Mock embedding generation
            mock_embed.return_value = {
                "success": True,
                "embeddings": [{"chunk_id": 0, "embedding": [0.1, 0.2]}],
            }

            # Mock storage
            mock_store.return_value = {"success": True, "stored_embeddings": 1}

            result = vector_tool.process_document_text(123, document_text)

            assert result["success"] is True
            assert result["document_id"] == 123
            assert "processing_summary" in result

    def test_process_document_text_no_chunks(
        self, vector_tool: VectorStorageTool
    ) -> None:
        """Test document text processing with no chunks generated."""
        with patch.object(vector_tool, "chunk_text", return_value=[]):
            result = vector_tool.process_document_text(123, "")

            assert result["success"] is False
            assert "No text chunks generated" in result["error"]

    def test_process_document_text_embedding_failure(
        self, vector_tool: VectorStorageTool
    ) -> None:
        """Test document text processing with embedding failure."""
        with (
            patch.object(vector_tool, "chunk_text") as mock_chunk,
            patch.object(vector_tool, "generate_embeddings_batch") as mock_embed,
        ):
            mock_chunk.return_value = [{"chunk_id": 0, "text": "Sample"}]
            mock_embed.return_value = {
                "success": False,
                "error": "Embedding generation failed",
            }

            result = vector_tool.process_document_text(123, "Sample text")

            assert result["success"] is False
            assert "Embedding generation failed" in result["error"]

    def test_process_document_text_storage_failure(
        self, vector_tool: VectorStorageTool
    ) -> None:
        """Test document text processing with storage failure."""
        with (
            patch.object(vector_tool, "chunk_text") as mock_chunk,
            patch.object(vector_tool, "generate_embeddings_batch") as mock_embed,
            patch.object(vector_tool, "store_document_embeddings") as mock_store,
        ):
            mock_chunk.return_value = [{"chunk_id": 0, "text": "Sample"}]
            mock_embed.return_value = {"success": True, "embeddings": [{"chunk_id": 0}]}
            mock_store.return_value = {"success": False, "error": "Storage failed"}

            result = vector_tool.process_document_text(123, "Sample text")

            assert result["success"] is False
            assert "Storage failed" in result["error"]
