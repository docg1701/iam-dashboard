"""Document repository for database operations."""

import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk


class DocumentRepository:
    """Repository for document database operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize the document repository."""
        self.db_session = db_session

    async def create(self, document: Document) -> Document:
        """Create a new document in the database."""
        self.db_session.add(document)
        await self.db_session.commit()
        await self.db_session.refresh(document)
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        """Get a document by ID."""
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.client))
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_client_id(self, client_id: uuid.UUID) -> list[Document]:
        """Get all documents for a specific client."""
        stmt = (
            select(Document)
            .where(Document.client_id == client_id)
            .order_by(Document.created_at.desc())
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars())

    async def check_duplicate_by_hash(
        self, client_id: uuid.UUID, content_hash: str
    ) -> Document | None:
        """Check if a document with the same hash already exists for this client."""
        stmt = select(Document).where(
            and_(Document.client_id == client_id, Document.content_hash == content_hash)
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_task_id(self, task_id: str) -> Document | None:
        """Get a document by Celery task ID."""
        stmt = (
            select(Document)
            .where(Document.task_id == task_id)
            .options(selectinload(Document.client))
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> bool:
        """Update document status and optional error message."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db_session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            return False

        document.status = status
        if error_message:
            document.error_message = error_message

        await self.db_session.commit()
        return True

    async def update_task_id(self, document_id: uuid.UUID, task_id: str) -> bool:
        """Update the Celery task ID for a document."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db_session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            return False

        document.task_id = task_id
        await self.db_session.commit()
        return True

    async def get_by_status(self, status: DocumentStatus) -> list[Document]:
        """Get all documents with a specific status."""
        stmt = (
            select(Document)
            .where(Document.status == status)
            .options(selectinload(Document.client))
            .order_by(Document.created_at.desc())
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars())

    async def delete(self, document_id: uuid.UUID) -> bool:
        """Delete a document by ID."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db_session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            return False

        await self.db_session.delete(document)
        await self.db_session.commit()
        return True

    async def save(self, document: Document) -> Document:
        """Save or update a document in the database."""
        if document.id:
            # Update existing document
            await self.db_session.merge(document)
        else:
            # Create new document
            self.db_session.add(document)

        await self.db_session.commit()
        await self.db_session.refresh(document)
        return document

    async def save_document_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """Save a document chunk to the database."""
        self.db_session.add(chunk)
        await self.db_session.commit()
        await self.db_session.refresh(chunk)
        return chunk

    async def get_chunks_by_document_id(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        """Get all chunks for a specific document."""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.created_at)
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars())
