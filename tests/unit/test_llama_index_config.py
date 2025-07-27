"""Unit tests for Llama-Index pipeline configuration."""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.config.llama_index_config import LlamaIndexConfig, get_llama_index_config


class TestLlamaIndexConfig:
    """Unit tests for Llama-Index configuration."""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test_gemini_key',
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/test_db'
        }):
            yield

    def test_config_initialization_success(self, mock_env_vars):
        """Test successful configuration initialization."""
        # Act
        config = LlamaIndexConfig()
        
        # Assert
        assert config.embedding_dimension == 768
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50
        assert config.gemini_api_key == 'test_gemini_key'
        assert config.database_url == 'postgresql://user:pass@localhost:5432/test_db'

    def test_config_missing_gemini_key(self):
        """Test configuration fails when GEMINI_API_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
                LlamaIndexConfig()

    def test_config_missing_database_url(self):
        """Test configuration fails when DATABASE_URL is missing."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'}, clear=True):
            with pytest.raises(ValueError, match="DATABASE_URL environment variable is required"):
                LlamaIndexConfig()

    @patch('app.config.llama_index_config.genai.configure')
    def test_gemini_api_configuration(self, mock_configure, mock_env_vars):
        """Test that Gemini API is configured correctly."""
        # Act
        config = LlamaIndexConfig()
        
        # Assert
        mock_configure.assert_called_once_with(api_key='test_gemini_key')

    @patch('app.config.llama_index_config.GeminiEmbedding')
    def test_get_embedding_model(self, mock_gemini_embedding, mock_env_vars):
        """Test embedding model creation."""
        # Arrange
        config = LlamaIndexConfig()
        mock_embedding = MagicMock()
        mock_gemini_embedding.return_value = mock_embedding
        
        # Act
        result = config.get_embedding_model()
        
        # Assert
        mock_gemini_embedding.assert_called_once_with(
            model_name="models/embedding-001",
            api_key='test_gemini_key',
            title="Legal Document Embeddings"
        )
        assert result == mock_embedding

    @patch('app.config.llama_index_config.SentenceSplitter')
    def test_get_text_splitter(self, mock_sentence_splitter, mock_env_vars):
        """Test text splitter creation with legal document optimization."""
        # Arrange
        config = LlamaIndexConfig()
        mock_splitter = MagicMock()
        mock_sentence_splitter.return_value = mock_splitter
        
        # Act
        result = config.get_text_splitter()
        
        # Assert
        mock_sentence_splitter.assert_called_once_with(
            chunk_size=512,
            chunk_overlap=50,
            paragraph_separator="\n\n",
            secondary_chunking_regex="[.!?]+",
            include_metadata=True,
            include_prev_next_rel=True
        )
        assert result == mock_splitter

    @patch('app.config.llama_index_config.create_engine')
    @patch('app.config.llama_index_config.PGVectorStore.from_params')
    def test_get_vector_store(self, mock_pg_vector_store, mock_create_engine, mock_env_vars):
        """Test vector store creation with proper HNSW configuration."""
        # Arrange
        config = LlamaIndexConfig()
        mock_engine = MagicMock()
        mock_engine.url.database = 'test_db'
        mock_engine.url.host = 'localhost'
        mock_engine.url.password = 'pass'
        mock_engine.url.port = 5432
        mock_engine.url.username = 'user'
        mock_create_engine.return_value = mock_engine
        
        mock_vector_store = MagicMock()
        mock_pg_vector_store.return_value = mock_vector_store
        
        # Act
        result = config.get_vector_store()
        
        # Assert
        mock_create_engine.assert_called_once_with('postgresql://user:pass@localhost:5432/test_db')
        mock_pg_vector_store.assert_called_once_with(
            database='test_db',
            host='localhost',
            password='pass',
            port=5432,
            user='user',
            table_name="document_chunks",
            embed_dim=768,
            hnsw_kwargs={
                "hnsw_m": 16,
                "hnsw_ef_construction": 64,
                "hnsw_ef_search": 40,
            }
        )
        assert result == mock_vector_store

    @patch('app.config.llama_index_config.Settings')
    def test_setup_global_settings(self, mock_settings, mock_env_vars):
        """Test global settings setup (replaces deprecated ServiceContext)."""
        # Arrange
        config = LlamaIndexConfig()
        
        with patch.object(config, 'get_embedding_model') as mock_get_embed:
            with patch.object(config, 'get_text_splitter') as mock_get_splitter:
                mock_embed_model = MagicMock()
                mock_text_splitter = MagicMock()
                mock_get_embed.return_value = mock_embed_model
                mock_get_splitter.return_value = mock_text_splitter
                
                # Act
                config.setup_global_settings()
                
                # Assert
                assert mock_settings.embed_model == mock_embed_model
                assert mock_settings.text_splitter == mock_text_splitter
                assert mock_settings.chunk_size == 512
                assert mock_settings.chunk_overlap == 50

    def test_factory_function(self, mock_env_vars):
        """Test factory function returns LlamaIndexConfig instance."""
        # Act
        result = get_llama_index_config()
        
        # Assert
        assert isinstance(result, LlamaIndexConfig)

    def test_chunk_size_configuration(self, mock_env_vars):
        """Test that chunk size is optimized for legal documents."""
        # Act
        config = LlamaIndexConfig()
        
        # Assert
        assert config.chunk_size == 512  # Optimized for legal document density
        assert config.chunk_overlap == 50  # 10% overlap for context preservation

    def test_embedding_dimension_configuration(self, mock_env_vars):
        """Test embedding dimension matches Gemini model specifications."""
        # Act
        config = LlamaIndexConfig()
        
        # Assert
        assert config.embedding_dimension == 768  # Gemini embedding dimension