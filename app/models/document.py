"""Document model for storing uploaded PDF documents and their metadata."""

from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import TimestampedModel


class DocumentType(str, Enum):
    """Document classification types."""

    SIMPLE = "simple"  # Digital PDF, good quality text
    COMPLEX = "complex"  # Scanned PDF, requires OCR


class DocumentStatus(str, Enum):
    """Document processing status."""

    UPLOADED = "uploaded"  # Just uploaded, waiting for processing
    PROCESSING = "processing"  # Being processed by worker
    PROCESSED = "processed"  # Successfully processed
    FAILED = "failed"  # Processing failed


class Document(TimestampedModel):
    """Document model for storing uploaded PDF documents and their metadata."""

    __tablename__ = "documents"

    # Basic document info
    filename = Column(String(255), nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False, default="application/pdf")

    # Classification and status
    document_type = Column(String(20), nullable=False)  # Store enum as string
    status = Column(String(20), nullable=False, default=DocumentStatus.UPLOADED.value)

    # Client association
    client_id = Column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )

    # Processing information
    task_id = Column(String(255), nullable=True)  # Celery task ID
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # File storage path (relative to upload directory)
    file_path = Column(String(500), nullable=False)

    # Relationships
    client = relationship("Client", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of Document."""
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}', client_id={self.client_id})>"

    @property
    def formatted_file_size(self) -> str:
        """Format file size for display."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    @property
    def is_processing(self) -> bool:
        """Check if document is currently being processed."""
        return self.status == DocumentStatus.PROCESSING

    @property
    def is_processed(self) -> bool:
        """Check if document has been successfully processed."""
        return self.status == DocumentStatus.PROCESSED

    @property
    def has_failed(self) -> bool:
        """Check if document processing has failed."""
        return self.status == DocumentStatus.FAILED
