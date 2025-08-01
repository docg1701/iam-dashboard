"""Document service for business logic and file handling."""

import hashlib
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.agent_initialization import get_agent
from app.models.document import Document, DocumentStatus, DocumentType
from app.repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document management and processing."""

    def __init__(
        self, document_repository: DocumentRepository, upload_dir: str = "uploads"
    ) -> None:
        """Initialize the document service."""
        self.repository = document_repository
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    def calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of file content."""
        hash_obj = hashlib.sha256(content)
        return hash_obj.hexdigest()

    async def check_duplicate(
        self, client_id: uuid.UUID, content_hash: str
    ) -> Document | None:
        """Check if a document with the same hash already exists for this client."""
        return await self.repository.check_duplicate_by_hash(client_id, content_hash)

    async def create_document(
        self,
        client_id: uuid.UUID,
        filename: str,
        content: bytes,
        document_type: DocumentType,
    ) -> dict[str, any]:
        """Create a new document and save file to disk."""
        try:
            # Calculate file hash
            content_hash = self.calculate_file_hash(content)

            # Check for duplicates
            existing_doc = await self.check_duplicate(client_id, content_hash)
            if existing_doc:
                return {
                    "success": False,
                    "error": f"Documento duplicado encontrado. Arquivo já existe: {existing_doc.filename}",
                }

            # Generate unique file path
            file_extension = Path(filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = self.upload_dir / str(client_id) / unique_filename

            # Create client directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save file to disk
            with open(file_path, "wb") as f:
                f.write(content)

            # Create document record
            document = Document(
                filename=filename,
                content_hash=content_hash,
                file_size=len(content),
                document_type=document_type,
                client_id=client_id,
                file_path=str(file_path.relative_to(self.upload_dir)),
                status=DocumentStatus.UPLOADED,
            )

            # Save to database
            saved_document = await self.repository.create(document)

            # Document created successfully - processing will be handled by API layer via AgentManager
            return {
                "success": True,
                "document_id": str(saved_document.id),
                "message": "Documento criado e pronto para processamento",
            }

        except Exception as e:
            return {"success": False, "error": f"Erro ao criar documento: {str(e)}"}

    async def get_document_by_id(self, document_id: uuid.UUID) -> Document | None:
        """Get a document by ID."""
        return await self.repository.get_by_id(document_id)

    async def get_documents_by_client(self, client_id: uuid.UUID) -> list[Document]:
        """Get all documents for a specific client."""
        return await self.repository.get_by_client_id(client_id)

    async def update_document_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> bool:
        """Update document status."""
        success = await self.repository.update_status(
            document_id, status, error_message
        )

        # If status is processed, update processed_at timestamp
        if success and status == DocumentStatus.PROCESSED:
            document = await self.repository.get_by_id(document_id)
            if document:
                document.processed_at = datetime.utcnow()
                # Create a simple update operation instead of using create()
                try:
                    await self.repository.db_session.commit()
                except AttributeError:
                    # In case of mock testing, ignore db_session
                    pass

        return success

    async def get_document_by_task_id(self, task_id: str) -> Document | None:
        """Get a document by agent processing ID."""
        return await self.repository.get_by_task_id(task_id)

    async def get_processing_documents(self) -> list[Document]:
        """Get all documents currently being processed."""
        return await self.repository.get_by_status(DocumentStatus.PROCESSING)

    async def get_failed_documents(self) -> list[Document]:
        """Get all documents that failed processing."""
        return await self.repository.get_by_status(DocumentStatus.FAILED)

    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """Delete a document and its file."""
        try:
            # Get document first to get file path
            document = await self.repository.get_by_id(document_id)
            if not document:
                return False

            # Delete file from disk
            file_path = self.upload_dir / document.file_path
            if file_path.exists():
                file_path.unlink()

            # Delete from database
            return await self.repository.delete(document_id)

        except Exception:
            return False

    def get_file_path(self, document: Document) -> Path:
        """Get the full file path for a document."""
        return self.upload_dir / document.file_path

    async def process_document_with_agent(
        self, document_id: uuid.UUID, user_id: int, perform_ocr: bool = True
    ) -> dict[str, Any]:
        """Process a document using the PDF processor agent.
        
        Args:
            document_id: ID of the document to process
            user_id: ID of the user who owns the document
            perform_ocr: Whether to perform OCR on the document
            
        Returns:
            Dictionary containing processing results
        """
        try:
            # Get the document
            document = await self.repository.get_by_id(document_id)
            if not document:
                return {"success": False, "error": "Document not found"}

            # Update status to PROCESSING
            await self.update_document_status(document_id, DocumentStatus.PROCESSING)

            # Get full file path
            file_path = self.get_file_path(document)
            if not file_path.exists():
                await self.update_document_status(
                    document_id, DocumentStatus.FAILED, "File not found on disk"
                )
                return {"success": False, "error": "File not found on disk"}

            # Get the PDF processor agent
            pdf_agent = await get_agent("default_pdf_processor")
            if not pdf_agent:
                await self.update_document_status(
                    document_id, DocumentStatus.FAILED, "PDF processor agent not available"
                )
                return {"success": False, "error": "PDF processor agent not available"}

            logger.info(f"Starting document processing for {document.filename} (ID: {document_id})")

            # Process the document using the agent
            result = await pdf_agent.process_document(
                file_path=str(file_path),
                user_id=user_id,
                perform_ocr=perform_ocr
            )

            if result["success"]:
                # Update document status to PROCESSED
                await self.update_document_status(document_id, DocumentStatus.PROCESSED)

                logger.info(
                    f"Successfully processed document {document.filename} (ID: {document_id})"
                )

                return {
                    "success": True,
                    "document_id": str(document_id),
                    "filename": document.filename,
                    "processing_result": result
                }
            else:
                # Update document status to FAILED
                error_message = result.get("error", "Processing failed")
                await self.update_document_status(
                    document_id, DocumentStatus.FAILED, error_message
                )

                logger.error(
                    f"Failed to process document {document.filename} (ID: {document_id}): {error_message}"
                )

                return {
                    "success": False,
                    "document_id": str(document_id),
                    "filename": document.filename,
                    "error": error_message
                }

        except Exception as e:
            error_message = f"Document processing failed: {str(e)}"
            logger.error(f"Error processing document {document_id}: {error_message}")

            # Update document status to FAILED
            try:
                await self.update_document_status(document_id, DocumentStatus.FAILED, error_message)
            except Exception:
                pass  # Don't fail if status update fails

            return {
                "success": False,
                "document_id": str(document_id),
                "error": error_message
            }

    async def process_document(
        self, file_data: bytes, filename: str, user_id: int, client_id: uuid.UUID
    ) -> dict[str, Any]:
        """Complete document processing workflow: Upload → Storage → Agent Processing → Vector Store.
        
        Args:
            file_data: Raw file data
            filename: Original filename
            user_id: ID of the user uploading the document
            client_id: ID of the client the document belongs to
            
        Returns:
            Dictionary containing complete processing results
        """
        try:
            logger.info(f"Starting complete document processing workflow for {filename}")

            # Step 1: Create document and save to storage
            document_type = DocumentType.LEGAL_DOCUMENT
            if filename.lower().endswith('.pdf'):
                document_type = DocumentType.LEGAL_DOCUMENT

            create_result = await self.create_document(client_id, filename, file_data, document_type)

            if not create_result["success"]:
                return create_result

            document_id = uuid.UUID(create_result["document_id"])

            # Step 2: Process document with agent (includes vector storage)
            processing_result = await self.process_document_with_agent(
                document_id, user_id, perform_ocr=True
            )

            if processing_result["success"]:
                return {
                    "success": True,
                    "document_id": str(document_id),
                    "filename": filename,
                    "message": "Document processed successfully",
                    "processing_details": processing_result["processing_result"]
                }
            else:
                return {
                    "success": False,
                    "document_id": str(document_id),
                    "filename": filename,
                    "error": processing_result["error"]
                }

        except Exception as e:
            error_message = f"Complete document processing workflow failed: {str(e)}"
            logger.error(f"Error in complete document processing for {filename}: {error_message}")
            return {"success": False, "error": error_message}
