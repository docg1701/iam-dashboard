"""Client API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.repositories.client_repository import ClientRepository
from app.repositories.document_repository import DocumentRepository
from app.services.client_service import ClientService
from app.services.document_service import DocumentService

router = APIRouter(prefix="/v1/clients", tags=["clients"])


@router.get("/{client_id}", response_model=dict)
async def get_client(
    client_id: str, db: AsyncSession = Depends(get_async_db)
) -> dict[str, str | None]:
    """Get a specific client by ID."""
    try:
        client_uuid = uuid.UUID(client_id)

        client_repository = ClientRepository(db)
        client_service = ClientService(client_repository)

        client = await client_service.get_client_by_id(client_uuid)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )

        return {
            "id": str(client.id),
            "name": client.name,
            "cpf": client.cpf,
            "formatted_cpf": client.formatted_cpf,
            "birth_date": client.birth_date.isoformat() if client.birth_date else None,
            "created_at": client.created_at.isoformat() if client.created_at else None,
            "updated_at": client.updated_at.isoformat() if client.updated_at else None,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client ID format"
        ) from e
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without modification
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving client: {str(e)}",
        ) from e


@router.get("/{client_id}/documents", response_model=list[dict])
async def get_client_documents(
    client_id: str, db: AsyncSession = Depends(get_async_db)
) -> list[dict[str, str | None | int]]:
    """Get all documents for a specific client."""
    try:
        client_uuid = uuid.UUID(client_id)

        # First verify client exists
        client_repository = ClientRepository(db)
        client_service = ClientService(client_repository)
        client = await client_service.get_client_by_id(client_uuid)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )

        # Get client documents
        document_repository = DocumentRepository(db)
        document_service = DocumentService(document_repository)
        documents = await document_service.get_documents_by_client(client_uuid)

        return [
            {
                "id": str(doc.id),
                "filename": doc.filename,
                "document_type": doc.document_type,
                "status": doc.status,
                "file_size": doc.file_size,
                "formatted_file_size": doc.formatted_file_size,
                "task_id": doc.task_id,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "processed_at": (
                    doc.processed_at.isoformat() if doc.processed_at else None
                ),
                "error_message": doc.error_message,
                "content_hash": doc.content_hash,
            }
            for doc in documents
        ]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client ID format"
        ) from e
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without modification
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving client documents: {str(e)}",
        ) from e


@router.get("/{client_id}/documents/summary", response_model=dict)
async def get_client_documents_summary(
    client_id: str, db: AsyncSession = Depends(get_async_db)
) -> dict[str, dict[str, str | int | float]]:
    """Get summary statistics for all documents of a client."""
    try:
        client_uuid = uuid.UUID(client_id)

        # First verify client exists
        client_repository = ClientRepository(db)
        client_service = ClientService(client_repository)
        client = await client_service.get_client_by_id(client_uuid)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )

        # Get client documents
        document_repository = DocumentRepository(db)
        document_service = DocumentService(document_repository)
        documents = await document_service.get_documents_by_client(client_uuid)

        # Calculate statistics
        total_documents = len(documents)
        status_counts: dict[str, int] = {}
        total_size = 0
        processing_count = 0
        processed_count = 0
        failed_count = 0

        for doc in documents:
            # Count by status
            status_counts[doc.status] = status_counts.get(doc.status, 0) + 1
            total_size += doc.file_size

            # Specific status counts
            if doc.status == "processing":
                processing_count += 1
            elif doc.status == "processed":
                processed_count += 1
            elif doc.status == "failed":
                failed_count += 1

        # Format total size
        if total_size < 1024:
            total_size_formatted = f"{total_size} B"
        elif total_size < 1024 * 1024:
            total_size_formatted = f"{total_size / 1024:.1f} KB"
        else:
            total_size_formatted = f"{total_size / (1024 * 1024):.1f} MB"

        return {
            "client": {
                "id": str(client.id),
                "name": client.name,
            },
            "summary": {
                "total_documents": total_documents,
                "total_size": total_size,
                "total_size_formatted": total_size_formatted,
                "processing_count": processing_count,
                "processed_count": processed_count,
                "failed_count": failed_count,
                "status_counts": status_counts,
                "completion_rate": (
                    (processed_count / total_documents * 100)
                    if total_documents > 0
                    else 0
                ),
            },
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client ID format"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving client documents summary: {str(e)}",
        ) from e
