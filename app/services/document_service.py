"""Document service for business logic and file handling."""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path

from app.models.document import Document, DocumentStatus, DocumentType
from app.repositories.document_repository import DocumentRepository


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

            # Create Celery task for processing
            try:
                from app.workers.document_processor import process_document

                task_result = process_document.delay(str(saved_document.id))
                await self.repository.update_task_id(saved_document.id, task_result.id)

                return {
                    "success": True,
                    "document_id": str(saved_document.id),
                    "task_id": task_result.id,
                    "message": "Documento criado e processamento iniciado",
                }
            except Exception as task_error:
                # If task creation fails, still return success for document creation
                # but note the task error
                return {
                    "success": True,
                    "document_id": str(saved_document.id),
                    "task_id": None,
                    "message": f"Documento criado, mas erro ao iniciar processamento: {str(task_error)}",
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
        """Get a document by Celery task ID."""
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
