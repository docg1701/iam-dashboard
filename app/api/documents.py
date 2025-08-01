"""Document API endpoints."""

import asyncio
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
    """Upload and process a PDF document using the PDF Processor Agent with comprehensive validation."""
    import logging

    logger = logging.getLogger(__name__)
    file_path = None
    start_time = asyncio.get_event_loop().time()

    try:
        # Enhanced file validation
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided",
            )

        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported. Uploaded file must have .pdf extension.",
            )

        # Read file content for size validation
        content = await file.read()
        await file.seek(0)  # Reset file pointer

        # Validate file size (50MB limit)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {max_size / (1024 * 1024):.1f}MB, got {len(content) / (1024 * 1024):.1f}MB",
            )

        # Validate file is not empty
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file not allowed",
            )

        # Basic PDF header validation
        if not content.startswith(b'%PDF-'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file. File does not have valid PDF header.",
            )

        logger.info(f"Processing PDF upload: {file.filename} ({len(content)} bytes) for user {user_id}")

        # Save uploaded file temporarily with secure naming
        upload_dir = Path("/tmp/pdf_uploads")
        upload_dir.mkdir(exist_ok=True, mode=0o700)  # Secure directory permissions

        # Create secure temporary filename
        secure_filename = f"{uuid.uuid4()}_{Path(file.filename).stem}.pdf"
        file_path = upload_dir / secure_filename

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Set secure file permissions
        file_path.chmod(0o600)

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

        logger.info(f"Starting PDF processing for {file.filename} using agent")

        # Create progress callback for WebSocket updates
        processing_id = str(uuid.uuid4())

        async def progress_callback(step: str, progress: int, message: str, status: str = "processing"):
            """Send progress updates via WebSocket."""
            try:
                from datetime import UTC, datetime

                from app.api.websockets import get_document_websocket_manager

                ws_manager = get_document_websocket_manager()

                progress_data = {
                    "processing_id": processing_id,
                    "filename": file.filename,
                    "step": step,
                    "progress": progress,
                    "message": message,
                    "status": status,
                    "timestamp": datetime.now(UTC).isoformat()
                }

                await ws_manager.broadcast_progress(processing_id, progress_data)

            except Exception as e:
                logger.warning(f"Failed to send progress update: {str(e)}")

        # Process document using the agent with timeout protection and progress tracking
        try:
            processing_result = await asyncio.wait_for(
                pdf_agent_instance.process_document(
                    file_path=str(file_path),
                    user_id=user_id,
                    perform_ocr=perform_ocr,
                    progress_callback=progress_callback
                ),
                timeout=300.0  # 5 minute timeout
            )
        except TimeoutError as timeout_error:
            logger.error(f"PDF processing timeout for {file.filename}")
            # Send timeout update via WebSocket
            await progress_callback("storage", 0, "Timeout - processamento excedeu 5 minutos", "error")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Document processing timed out. Please try with a smaller file or contact support.",
            ) from timeout_error

        # Calculate processing time
        processing_time = asyncio.get_event_loop().time() - start_time

        # Clean up temporary file
        try:
            if file_path and file_path.exists():
                file_path.unlink()
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up temporary file {file_path}: {str(cleanup_error)}")

        if processing_result["success"]:
            logger.info(
                f"Successfully processed PDF {file.filename} in {processing_time:.2f}s "
                f"(document_id: {processing_result.get('document_id')})"
            )

            return {
                "success": True,
                "document_id": processing_result["document_id"],
                "filename": processing_result["filename"],
                "processing_id": processing_id,
                "processing_summary": {
                    **processing_result["processing_summary"],
                    "processing_time_seconds": round(processing_time, 2),
                    "file_size_mb": round(len(content) / (1024 * 1024), 2),
                },
                "message": "Document processed successfully using PDF Processor Agent",
            }
        else:
            logger.error(f"PDF processing failed for {file.filename}: {processing_result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Document processing failed: "
                    f"{processing_result.get('error', 'Unknown processing error')}"
                ),
            )

    except HTTPException:
        raise
    except (AgentNotFoundError, AgentNotActiveError):
        # Let agent errors bubble up to middleware for proper handling
        # Clean up temporary file if it exists
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        raise
    except Exception as e:
        logger.error(f"Document upload error for {file.filename if file else 'unknown'}: {str(e)}")

        # Clean up temporary file if it exists
        if file_path and file_path.exists():
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


@router.post("/search/similarity", response_model=dict[str, Any])
async def search_similar_documents(
    query: dict[str, Any],
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Search for similar documents using vector similarity search."""
    try:
        query_text = query.get("query")
        if not query_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query text is required",
            )

        limit = query.get("limit", 10)
        similarity_threshold = query.get("similarity_threshold", 0.7)
        document_ids = query.get("document_ids")  # Optional filter by document IDs

        # Validate parameters
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100",
            )

        if similarity_threshold < 0.0 or similarity_threshold > 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Similarity threshold must be between 0.0 and 1.0",
            )

        # Import vector storage tool
        from app.tools.vector_storage_tools import VectorStorageTool

        # Initialize vector storage tool
        vector_tool = VectorStorageTool()

        # Perform similarity search
        search_result = vector_tool.search_similar_content(
            query_text=query_text,
            limit=limit,
            similarity_threshold=similarity_threshold,
            document_ids=document_ids
        )

        if search_result["success"]:
            return {
                "success": True,
                "query": query_text,
                "results": search_result["results"],
                "total_results": search_result["total_results"],
                "similarity_threshold": similarity_threshold,
                "message": f"Found {search_result['total_results']} similar content chunks"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Similarity search failed: {search_result.get('error', 'Unknown error')}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similarity search error: {str(e)}",
        ) from e


@router.get("/search/validate", response_model=dict[str, Any])
async def validate_vector_search_setup() -> dict[str, Any]:
    """Validate that vector search capabilities are properly configured."""
    try:
        from app.tools.vector_storage_tools import VectorStorageTool

        vector_tool = VectorStorageTool()

        # Validate pgvector setup
        validation_result = vector_tool.validate_pgvector_setup()

        if validation_result["valid"]:
            return {
                "success": True,
                "message": "Vector search is properly configured",
                "pgvector_available": validation_result.get("pgvector_available", False),
                "embedding_model": vector_tool.embedding_model,
                "chunk_size": vector_tool.chunk_size,
            }
        else:
            return {
                "success": False,
                "error": validation_result.get("error", "Unknown validation error"),
                "message": "Vector search is not properly configured",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Validation failed: {str(e)}",
            "message": "Unable to validate vector search setup",
        }
