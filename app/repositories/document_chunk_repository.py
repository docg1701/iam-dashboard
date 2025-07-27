"""Repository for DocumentChunk model."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk


class DocumentChunkRepository:
    """Repository for document chunk operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize the repository."""
        self.db_session = db_session

    async def get_by_document_id(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        """Get all chunks for a specific document."""
        query = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, chunk_id: str) -> DocumentChunk | None:
        """Get a chunk by node_id."""
        query = select(DocumentChunk).where(DocumentChunk.node_id == chunk_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, chunk: DocumentChunk) -> DocumentChunk:
        """Create a new document chunk."""
        self.db_session.add(chunk)
        await self.db_session.commit()
        await self.db_session.refresh(chunk)
        return chunk

    async def create_multiple(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Create multiple document chunks."""
        self.db_session.add_all(chunks)
        await self.db_session.commit()
        for chunk in chunks:
            await self.db_session.refresh(chunk)
        return chunks

    async def delete_by_document_id(self, document_id: uuid.UUID) -> bool:
        """Delete all chunks for a specific document."""
        query = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await self.db_session.execute(query)
        chunks = result.scalars().all()

        for chunk in chunks:
            await self.db_session.delete(chunk)

        await self.db_session.commit()
        return True

    async def count_by_document_id(self, document_id: uuid.UUID) -> int:
        """Count chunks for a specific document."""
        query = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await self.db_session.execute(query)
        chunks = result.scalars().all()
        return len(chunks)
