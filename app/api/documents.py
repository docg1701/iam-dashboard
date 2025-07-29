"""Document API endpoints."""

import uuid
from pathlib import Path
from typing import Any

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.agent_error_handler import (
    AgentNotActiveError,
    AgentNotFoundError,
)
from app.containers import Container
from app.core.agent_manager import AgentManager
from app.core.database import get_async_db
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.get("/client/{client_id}", response_model=list[dict[str, Any]])
async def get_client_documents(
    client_id: str, db: AsyncSession = Depends(get_async_db)
) -> list[dict[str, Any]]:
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


@router.get("/{document_id}", response_model=dict[str, Any])
async def get_document(
    document_id: str, db: AsyncSession = Depends(get_async_db)
) -> dict[str, Any]:
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


@router.get("/{document_id}/summary", response_model=dict[str, Any])
async def get_document_summary(
    document_id: str, db: AsyncSession = Depends(get_async_db)
) -> dict[str, Any]:
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
                detail="Document summary only available for processed documents",
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
            chunk_data.append(
                {
                    "index": i + 1,
                    "node_id": chunk.node_id,
                    "text": chunk.text,
                    "text_length": len(chunk.text) if chunk.text else 0,
                    "metadata": chunk.metadata or {},
                }
            )

        return {
            "document": {
                "id": str(document.id),
                "filename": document.filename,
                "document_type": document.document_type,
                "status": document.status,
                "file_size": document.formatted_file_size,
                "client_id": str(document.client_id),
                "created_at": document.created_at.isoformat(),
                "processed_at": (
                    document.processed_at.isoformat() if document.processed_at else None
                ),
            },
            "statistics": {
                "total_chunks": len(chunks),
                "total_characters": total_chars,
                "total_words": total_words,
                "average_chunk_size": avg_chunk_size,
            },
            "chunks": chunk_data,
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


@router.post("/upload", response_model=dict[str, Any])
@inject
async def upload_document(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    perform_ocr: bool = Form(True),
    db: AsyncSession = Depends(get_async_db),
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> dict[str, Any]:
    """Upload and process a PDF document using the PDF Processor Agent."""
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported",
            )

        # Save uploaded file temporarily
        upload_dir = Path("/tmp/pdf_uploads")
        upload_dir.mkdir(exist_ok=True)

        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Get PDF processor agent instance from AgentManager
        pdf_agent_instance = agent_manager.get_agent("pdf_processor")

        if not pdf_agent_instance:
            raise AgentNotFoundError(
                "PDF Processor Agent not found", agent_id="pdf_processor"
            )

        if not agent_manager.is_agent_active("pdf_processor"):
            raise AgentNotActiveError(
                "PDF Processor Agent is not active", agent_id="pdf_processor"
            )

        # Process document using the agent
        processing_result = await pdf_agent_instance.process_document(
            file_path=str(file_path), user_id=user_id, perform_ocr=perform_ocr
        )

        # Clean up temporary file
        try:
            file_path.unlink()
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up temporary file: {str(cleanup_error)}")

        if processing_result["success"]:
            return {
                "success": True,
                "document_id": processing_result["document_id"],
                "filename": processing_result["filename"],
                "processing_summary": processing_result["processing_summary"],
                "message": "Document processed successfully using PDF Processor Agent",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Document processing failed: "
                    f"{processing_result.get('error', 'Unknown error')}"
                ),
            )

    except HTTPException:
        raise
    except Exception as e:
        # Clean up temporary file if it exists
        if "file_path" in locals():
            try:
                file_path.unlink()
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}",
        ) from e


@router.get("/agents/status", response_model=dict[str, Any])
@inject
async def get_agent_status(
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> dict[str, Any]:
    """Get status of all document processing agents."""
    try:
        agents_metadata = agent_manager.get_all_agents_metadata()

        return {
            "agents": {
                agent_id: {
                    "name": metadata.name,
                    "description": metadata.description,
                    "status": metadata.status.value,
                    "capabilities": metadata.capabilities,
                    "health_status": metadata.health_status,
                    "last_health_check": (
                        metadata.last_health_check.isoformat()
                        if metadata.last_health_check
                        else None
                    ),
                    "error_message": metadata.error_message,
                }
                for agent_id, metadata in agents_metadata.items()
            },
            "total_agents": len(agents_metadata),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving agent status: {str(e)}",
        ) from e


@router.post("/agents/{agent_id}/enable", response_model=dict[str, Any])
@inject
async def enable_agent(
    agent_id: str,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> dict[str, Any]:
    """Enable a specific agent."""
    try:
        success = await agent_manager.enable_agent(agent_id)

        if success:
            return {
                "success": True,
                "message": f"Agent {agent_id} enabled successfully",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to enable agent {agent_id}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enabling agent: {str(e)}",
        ) from e


@router.post("/agents/{agent_id}/disable", response_model=dict[str, Any])
@inject
async def disable_agent(
    agent_id: str,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> dict[str, Any]:
    """Disable a specific agent."""
    try:
        success = await agent_manager.disable_agent(agent_id)

        if success:
            return {
                "success": True,
                "message": f"Agent {agent_id} disabled successfully",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to disable agent {agent_id}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disabling agent: {str(e)}",
        ) from e


@router.get("/agents/{agent_id}/health", response_model=dict[str, Any])
@inject
async def check_agent_health(
    agent_id: str,
    agent_manager: AgentManager = Depends(Provide[Container.agent_manager]),
) -> dict[str, Any]:
    """Perform health check on a specific agent."""
    try:
        is_healthy = await agent_manager.health_check(agent_id)
        metadata = agent_manager.get_agent_metadata(agent_id)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        return {
            "agent_id": agent_id,
            "is_healthy": is_healthy,
            "health_status": metadata.health_status,
            "last_health_check": (
                metadata.last_health_check.isoformat()
                if metadata.last_health_check
                else None
            ),
            "status": metadata.status.value,
            "error_message": metadata.error_message,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking agent health: {str(e)}",
        ) from e
