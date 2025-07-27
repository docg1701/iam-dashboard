"""Llama-Index configuration for RAG pipeline."""

import os

import google.generativeai as genai
from llama_index.core import Settings
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import create_engine


class LlamaIndexConfig:
    """Configuration class for Llama-Index RAG pipeline."""

    def __init__(self):
        """Initialize Llama-Index configuration."""
        self.embedding_dimension = 768
        self.chunk_size = 512
        self.chunk_overlap = 50
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.database_url = os.getenv("DATABASE_URL")

        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        # Configure Google Gemini API
        genai.configure(api_key=self.gemini_api_key)

    def get_embedding_model(self) -> BaseEmbedding:
        """Get Gemini embedding model for generating embeddings."""
        return GeminiEmbedding(
            model_name="models/embedding-001",
            api_key=self.gemini_api_key,
            title="Legal Document Embeddings"
        )

    def get_text_splitter(self) -> SentenceSplitter:
        """Get sentence splitter optimized for legal documents."""
        return SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            paragraph_separator="\n\n",
            secondary_chunking_regex="[.!?]+",
            include_metadata=True,
            include_prev_next_rel=True
        )

    def get_vector_store(self) -> PGVectorStore:
        """Get PostgreSQL vector store with pgvector extension."""
        engine = create_engine(self.database_url)

        return PGVectorStore.from_params(
            database=engine.url.database,
            host=engine.url.host,
            password=engine.url.password,
            port=engine.url.port or 5432,
            user=engine.url.username,
            table_name="document_chunks",
            embed_dim=self.embedding_dimension,
            hnsw_kwargs={
                "hnsw_m": 16,
                "hnsw_ef_construction": 64,
                "hnsw_ef_search": 40,
            }
        )

    def setup_global_settings(self) -> None:
        """Set up global Settings (replaces deprecated ServiceContext)."""
        embed_model = self.get_embedding_model()
        text_splitter = self.get_text_splitter()

        # Configure global settings
        Settings.embed_model = embed_model
        Settings.text_splitter = text_splitter  # Use text_splitter instead of node_parser
        Settings.chunk_size = self.chunk_size
        Settings.chunk_overlap = self.chunk_overlap


def get_llama_index_config() -> LlamaIndexConfig:
    """Factory function to get LlamaIndex configuration."""
    return LlamaIndexConfig()
