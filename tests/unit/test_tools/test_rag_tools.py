"""Unit tests for RAG retrieval tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.tools.rag_tools import RAGRetrieverTool


class TestRAGRetrieverTool:
    """Test suite for RAGRetrieverTool."""

    @pytest.fixture
    def mock_llama_config(self):
        """Mock LlamaIndex configuration."""
        mock_config = MagicMock()
        mock_config.setup_global_settings = MagicMock()
        mock_config.get_vector_store = MagicMock()
        return mock_config

    @pytest.fixture
    def rag_tool(self, mock_llama_config):
        """Create RAGRetrieverTool instance for testing."""
        with patch('app.tools.rag_tools.get_llama_index_config', return_value=mock_llama_config):
            return RAGRetrieverTool()

    @patch('app.tools.rag_tools.VectorStoreIndex')
    @patch('app.tools.rag_tools.VectorIndexRetriever')
    @patch('app.tools.rag_tools.QueryBundle')
    def test_retrieve_client_context_success(self, mock_query_bundle, mock_retriever_class,
                                           mock_index_class, rag_tool):
        """Test successful client context retrieval."""
        # Mock retrieval results
        mock_node1 = MagicMock()
        mock_node1.text = "Medical report shows back injury"
        mock_node1.score = 0.9
        mock_node1.metadata = {"client_id": "test-client-id"}

        mock_node2 = MagicMock()
        mock_node2.text = "X-ray results indicate herniated disc"
        mock_node2.score = 0.8
        mock_node2.metadata = {"client_id": "test-client-id"}

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [mock_node1, mock_node2]
        mock_retriever_class.return_value = mock_retriever

        mock_index = MagicMock()
        mock_index_class.from_vector_store.return_value = mock_index

        # Test context retrieval
        result = rag_tool.retrieve_client_context(
            client_id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
            profession="Engineer",
            disease="Back pain",
            incident_date="01/01/2023"
        )

        assert result["success"] is True
        assert len(result["context_chunks"]) == 2
        assert result["context_chunks"][0]["text"] == "Medical report shows back injury"
        assert result["context_chunks"][0]["score"] == 0.9
        assert result["total_chunks"] == 2

    @patch('app.tools.rag_tools.VectorStoreIndex')
    def test_retrieve_client_context_no_results(self, mock_index_class, rag_tool):
        """Test context retrieval with no results."""
        # Mock empty retrieval results
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []

        mock_index = MagicMock()
        mock_index_class.from_vector_store.return_value = mock_index

        with patch('app.tools.rag_tools.VectorIndexRetriever', return_value=mock_retriever):
            result = rag_tool.retrieve_client_context(
                client_id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
                profession="Engineer",
                disease="Back pain",
                incident_date="01/01/2023"
            )

        assert result["success"] is True
        assert len(result["context_chunks"]) == 0
        assert result["total_chunks"] == 0

    @patch('app.tools.rag_tools.VectorStoreIndex')
    def test_retrieve_client_context_filter_other_clients(self, mock_index_class, rag_tool):
        """Test context retrieval filters out other clients."""
        # Mock retrieval results with mixed client IDs
        mock_node1 = MagicMock()
        mock_node1.text = "Client A medical report"
        mock_node1.score = 0.9
        mock_node1.metadata = {"client_id": "test-client-id"}

        mock_node2 = MagicMock()
        mock_node2.text = "Client B medical report"
        mock_node2.score = 0.8
        mock_node2.metadata = {"client_id": "other-client-id"}

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [mock_node1, mock_node2]

        mock_index = MagicMock()
        mock_index_class.from_vector_store.return_value = mock_index

        with patch('app.tools.rag_tools.VectorIndexRetriever', return_value=mock_retriever):
            result = rag_tool.retrieve_client_context(
                client_id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
                profession="Engineer",
                disease="Back pain",
                incident_date="01/01/2023"
            )

        # Should only include the matching client
        assert result["success"] is True
        assert len(result["context_chunks"]) == 1
        assert result["context_chunks"][0]["text"] == "Client A medical report"

    def test_retrieve_client_context_exception(self, rag_tool):
        """Test context retrieval with exception."""
        with patch('app.tools.rag_tools.VectorStoreIndex') as mock_index_class:
            mock_index_class.from_vector_store.side_effect = Exception("Vector store error")

            result = rag_tool.retrieve_client_context(
                client_id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
                profession="Engineer",
                disease="Back pain",
                incident_date="01/01/2023"
            )

        assert result["success"] is False
        assert "error" in result
        assert result["context_chunks"] == []

    @patch('app.tools.rag_tools.VectorStoreIndex')
    @patch('app.tools.rag_tools.VectorIndexRetriever')
    @patch('app.tools.rag_tools.QueryBundle')
    def test_search_documents_by_query_success(self, mock_query_bundle, mock_retriever_class,
                                             mock_index_class, rag_tool):
        """Test successful document search by query."""
        # Mock search results
        mock_node1 = MagicMock()
        mock_node1.text = "Relevant document content"
        mock_node1.score = 0.9
        mock_node1.metadata = {"client_id": "test-client-id", "document_type": "medical"}

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [mock_node1]
        mock_retriever_class.return_value = mock_retriever

        mock_index = MagicMock()
        mock_index_class.from_vector_store.return_value = mock_index

        # Test document search
        result = rag_tool.search_documents_by_query(
            query_text="medical examination results",
            client_id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
            similarity_top_k=5
        )

        assert result["success"] is True
        assert len(result["search_results"]) == 1
        assert result["search_results"][0]["text"] == "Relevant document content"
        assert result["search_results"][0]["score"] == 0.9
        assert result["total_results"] == 1

    @patch('app.tools.rag_tools.VectorStoreIndex')
    @patch('app.tools.rag_tools.VectorIndexRetriever')
    def test_search_documents_by_query_no_client_filter(self, mock_retriever_class,
                                                       mock_index_class, rag_tool):
        """Test document search without client filtering."""
        # Mock search results from multiple clients
        mock_node1 = MagicMock()
        mock_node1.text = "Client A content"
        mock_node1.score = 0.9
        mock_node1.metadata = {"client_id": "client-a"}

        mock_node2 = MagicMock()
        mock_node2.text = "Client B content"
        mock_node2.score = 0.8
        mock_node2.metadata = {"client_id": "client-b"}

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [mock_node1, mock_node2]
        mock_retriever_class.return_value = mock_retriever

        mock_index = MagicMock()
        mock_index_class.from_vector_store.return_value = mock_index

        # Test document search without client filter
        result = rag_tool.search_documents_by_query(
            query_text="medical examination results",
            client_id=None,
            similarity_top_k=5
        )

        assert result["success"] is True
        assert len(result["search_results"]) == 2
        assert result["total_results"] == 2

    def test_search_documents_by_query_exception(self, rag_tool):
        """Test document search with exception."""
        with patch('app.tools.rag_tools.VectorStoreIndex') as mock_index_class:
            mock_index_class.from_vector_store.side_effect = Exception("Search error")

            result = rag_tool.search_documents_by_query(
                query_text="test query"
            )

        assert result["success"] is False
        assert "error" in result
        assert result["search_results"] == []
        assert result["total_results"] == 0

    def test_initialization_with_repository(self):
        """Test tool initialization with document repository."""
        mock_repository = MagicMock()

        with patch('app.tools.rag_tools.get_llama_index_config'):
            tool = RAGRetrieverTool(chunk_repository=mock_repository)

            assert tool.chunk_repository == mock_repository

    def test_query_text_generation(self, rag_tool):
        """Test query text generation for context retrieval."""
        # This tests the internal query formatting
        with patch.object(rag_tool, 'config') as mock_config:
            mock_vector_store = MagicMock()
            mock_config.get_vector_store.return_value = mock_vector_store

            with patch('app.tools.rag_tools.VectorStoreIndex'), \
                 patch('app.tools.rag_tools.VectorIndexRetriever') as mock_retriever_class:

                mock_retriever = MagicMock()
                mock_retriever.retrieve.return_value = []
                mock_retriever_class.return_value = mock_retriever

                result = rag_tool.retrieve_client_context(
                    client_id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
                    profession="Software Engineer",
                    disease="Carpal Tunnel Syndrome",
                    incident_date="15/03/2023"
                )

                # Verify query was created
                assert result["success"] is True
                assert "Software Engineer" in result["query_text"]
                assert "Carpal Tunnel Syndrome" in result["query_text"]
                assert "15/03/2023" in result["query_text"]
