"""Questionnaire API endpoints for judicial questionnaire generation."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.repositories.client_repository import ClientRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.client_service import ClientService
from app.services.questionnaire_draft_service import get_questionnaire_draft_service

router = APIRouter(prefix="/v1/questionnaire", tags=["questionnaire"])


class QuestionnaireGenerateRequest(BaseModel):
    """Request model for questionnaire generation."""

    client_id: uuid.UUID = Field(..., description="Client UUID")
    profession: str = Field(
        ..., min_length=2, max_length=100, description="Client's profession"
    )
    disease: str = Field(
        ..., min_length=2, max_length=200, description="Disease or condition"
    )
    incident_date: str = Field(
        ..., pattern=r"^\d{2}/\d{2}/\d{4}$", description="Incident date (dd/mm/yyyy)"
    )
    medical_date: str = Field(
        ...,
        pattern=r"^\d{2}/\d{2}/\d{4}$",
        description="First medical attention date (dd/mm/yyyy)",
    )


class QuestionnaireGenerateResponse(BaseModel):
    """Response model for questionnaire generation."""

    success: bool = Field(..., description="Whether generation was successful")
    questionnaire: str = Field(..., description="Generated questionnaire text")
    context_chunks: int = Field(..., description="Number of document chunks used")
    client_name: str = Field(..., description="Client name")
    error: str | None = Field(None, description="Error message if failed")


class ClientDocumentsResponse(BaseModel):
    """Response model for client documents check."""

    has_documents: bool = Field(
        ..., description="Whether client has processed documents"
    )
    document_count: int = Field(..., description="Number of processed documents")
    chunk_count: int = Field(..., description="Number of document chunks available")


@router.post("/generate", response_model=QuestionnaireGenerateResponse)
async def generate_questionnaire(
    request: QuestionnaireGenerateRequest, db: AsyncSession = Depends(get_async_db)
) -> QuestionnaireGenerateResponse:
    """
    Generate judicial questionnaire draft from form data and client documents.

    This endpoint uses RAG (Retrieval-Augmented Generation) to search for relevant
    information in the client's processed documents and combines it with the provided
    form data to generate a contextual judicial questionnaire using Google Gemini API.
    """
    try:
        # Get client
        client_repository = ClientRepository(db)
        client_service = ClientService(client_repository)

        client = await client_service.get_client_by_id(request.client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Generate questionnaire
        chunk_repository = DocumentChunkRepository(db)
        questionnaire_service = get_questionnaire_draft_service(chunk_repository)

        result = await questionnaire_service.generate_questionnaire(
            client=client,
            profession=request.profession,
            disease=request.disease,
            incident_date=request.incident_date,
            medical_date=request.medical_date,
        )

        if result["success"]:
            return QuestionnaireGenerateResponse(
                success=True,
                questionnaire=result["questionnaire"],
                context_chunks=result["context_chunks"],
                client_name=result["client_name"],
            )
        else:
            return QuestionnaireGenerateResponse(
                success=False,
                questionnaire="",
                context_chunks=0,
                client_name=client.name,
                error=result.get("error", "Unknown error"),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get(
    "/clients/{client_id}/has-documents", response_model=ClientDocumentsResponse
)
async def check_client_documents(
    client_id: uuid.UUID, db: AsyncSession = Depends(get_async_db)
) -> ClientDocumentsResponse:
    """
    Check if client has processed documents available for questionnaire generation.

    This endpoint verifies whether a client has documents that have been processed
    and indexed in the vector database, making them available for RAG retrieval
    during questionnaire generation.
    """
    try:
        # Check if client exists
        client_repository = ClientRepository(db)
        client_service = ClientService(client_repository)

        client = await client_service.get_client_by_id(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Check for document chunks
        chunk_repository = DocumentChunkRepository(db)
        chunks = await chunk_repository.get_chunks_by_client(client_id)

        has_documents = len(chunks) > 0

        # Count unique documents (by document_id)
        unique_document_ids = set()
        for chunk in chunks:
            if chunk.document_id:
                unique_document_ids.add(chunk.document_id)

        return ClientDocumentsResponse(
            has_documents=has_documents,
            document_count=len(unique_document_ids),
            chunk_count=len(chunks),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e
