"""Document API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService
from app.workers.document_processor import get_task_status

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.get("/tasks/{task_id}", response_model=dict)
async def get_document_task_status(task_id: str) -> dict:
    """Get the status of a document processing task."""
    try:
        # Get task status from Celery
        task_status = get_task_status(task_id)

        return {
            "task_id": task_id,
            "status": task_status.get("status", "UNKNOWN"),
            "result": task_status.get("result"),
            "error": task_status.get("traceback") or task_status.get("error"),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving task status: {str(e)}",
        ) from e


@router.get("/client/{client_id}", response_model=list[dict])
async def get_client_documents(
    client_id: str, db: AsyncSession = Depends(get_async_db)
) -> list[dict]:
    """Get all documents for a specific client."""
    try:
        client_uuid = uuid.UUID(client_id)

        document_repository = DocumentRepository(db)
        document_service = DocumentService(document_repository)

        documents = await document_service.get_documents_by_client(client_uuid)

        return [
            {
                "id": str(doc.id),
                "filename": doc.filename,
                "document_type": doc.document_type,
                "status": doc.status,
                "file_size": doc.formatted_file_size,
                "task_id": doc.task_id,
                "created_at": doc.created_at.isoformat(),
                "processed_at": (
                    doc.processed_at.isoformat() if doc.processed_at else None
                ),
                "error_message": doc.error_message,
            }
            for doc in documents
        ]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client ID format"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}",
        ) from e


@router.get("/{document_id}", response_model=dict)
async def get_document(
    document_id: str, db: AsyncSession = Depends(get_async_db)
) -> dict:
    """Get a specific document by ID."""
    try:
        doc_uuid = uuid.UUID(document_id)

        document_repository = DocumentRepository(db)
        document_service = DocumentService(document_repository)

        document = await document_service.get_document_by_id(doc_uuid)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        return {
            "id": str(document.id),
            "filename": document.filename,
            "document_type": document.document_type,
            "status": document.status,
            "file_size": document.formatted_file_size,
            "task_id": document.task_id,
            "client_id": str(document.client_id),
            "created_at": document.created_at.isoformat(),
            "processed_at": (
                document.processed_at.isoformat() if document.processed_at else None
            ),
            "error_message": document.error_message,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}",
        ) from e


@router.get("/{document_id}/summary", response_model=dict)
async def get_document_summary(
    document_id: str, db: AsyncSession = Depends(get_async_db)
) -> dict:
    """Get document summary with extracted content and chunks."""
    try:
        doc_uuid = uuid.UUID(document_id)

        document_repository = DocumentRepository(db)
        document_service = DocumentService(document_repository)
        chunk_repository = DocumentChunkRepository(db)

        # Get document
        document = await document_service.get_document_by_id(doc_uuid)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # Check if document is processed
        if document.status != "processed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document summary only available for processed documents"
            )

        # Get document chunks
        chunks = await chunk_repository.get_by_document_id(doc_uuid)

        # Calculate statistics
        total_chars = sum(len(chunk.text) for chunk in chunks if chunk.text)
        total_words = sum(len(chunk.text.split()) for chunk in chunks if chunk.text)
        avg_chunk_size = total_chars // len(chunks) if chunks else 0

        # Prepare chunk data
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_data.append({
                "index": i + 1,
                "node_id": chunk.node_id,
                "text": chunk.text,
                "text_length": len(chunk.text) if chunk.text else 0,
                "metadata": chunk.metadata or {}
            })

        return {
            "document": {
                "id": str(document.id),
                "filename": document.filename,
                "document_type": document.document_type,
                "status": document.status,
                "file_size": document.formatted_file_size,
                "client_id": str(document.client_id),
                "created_at": document.created_at.isoformat(),
                "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            },
            "statistics": {
                "total_chunks": len(chunks),
                "total_characters": total_chars,
                "total_words": total_words,
                "average_chunk_size": avg_chunk_size
            },
            "chunks": chunk_data
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID format"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document summary: {str(e)}",
        ) from e
