"""Document chunk model for storing vectorized text chunks."""

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import TimestampedModel


class DocumentChunk(TimestampedModel):
    """Model for storing document text chunks with vector embeddings.

    This model is designed to be compatible with Llama-Index's PGVectorStore
    and stores the vectorized text chunks for RAG operations.
    """

    __tablename__ = "document_chunks"

    # Node ID from Llama-Index (unique identifier for each chunk)
    node_id = Column(String(255), nullable=False, unique=True, index=True)

    # Vector embedding (768 dimensions for Gemini embeddings)
    embedding = Column(Vector(768), nullable=False)

    # The actual text content of the chunk
    text = Column(Text, nullable=False)

    # Metadata as JSON (includes chunk position, page numbers, etc.)
    chunk_metadata = Column(JSONB, nullable=False, default=dict)

    # Reference to the source document
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        """String representation of DocumentChunk."""
        return f"<DocumentChunk(id={self.id}, node_id='{self.node_id}', document_id={self.document_id})>"

    @property
    def preview_text(self) -> str:
        """Get a preview of the chunk text (first 100 characters)."""
        text_str = str(self.text)
        return text_str[:100] + "..." if len(text_str) > 100 else text_str

    @property
    def word_count(self) -> int:
        """Get the word count of the chunk."""
        return len(self.text.split())

    @property
    def chunk_position(self) -> int:
        """Get the chunk position from metadata."""
        return self.chunk_metadata.get("chunk_position", 0)

    @property
    def page_numbers(self) -> list[int]:
        """Get the page numbers this chunk spans from metadata."""
        return self.chunk_metadata.get("page_numbers", [])
