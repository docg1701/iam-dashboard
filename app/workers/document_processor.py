"""Document processing worker for asynchronous document processing."""

import asyncio
import uuid
from datetime import datetime

# Load environment variables first (required for Celery workers)
from dotenv import load_dotenv
load_dotenv()

from celery import Celery
from celery.utils.log import get_task_logger

from app.core.database import get_async_db
from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService
from app.utils.security_validators import get_security_validator
from app.workers.llama_index_processor import get_llama_index_processor

# Initialize Celery
celery_app = Celery(
    "document_processor",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
)

logger = get_task_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str) -> dict[str, any]:
    """Process a document asynchronously.

    Args:
        document_id: UUID string of the document to process

    Returns:
        Dict with processing results
    """
    try:
        # Convert string back to UUID
        doc_uuid = uuid.UUID(document_id)

        # Run the async processing function with new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_process_document_async(doc_uuid, self.request.id))
            return result
        finally:
            loop.close()

    except Exception as exc:
        logger.error(f"Error processing document {document_id}: {str(exc)}")

        # Update document status to failed
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    _update_document_status(
                        uuid.UUID(document_id), DocumentStatus.FAILED, str(exc)
                    )
                )
            finally:
                loop.close()
        except Exception as update_exc:
            logger.error(f"Error updating document status: {str(update_exc)}")

        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying document processing for {document_id}. Attempt {self.request.retries + 1}"
            )
            raise self.retry(countdown=60, exc=exc) from None

        return {"success": False, "error": str(exc), "document_id": document_id}


async def _process_document_async(
    document_id: uuid.UUID, task_id: str
) -> dict[str, any]:
    """Async function to process a document."""
    logger.info(f"Starting document processing for {document_id}")

    # Create a new database session for this task
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db_session:
        document_repository = DocumentRepository(db_session)
        document_service = DocumentService(document_repository)

        try:
            # Get the document
            document = await document_service.get_document_by_id(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Update status to processing
            await document_service.update_document_status(
                document_id, DocumentStatus.PROCESSING
            )

            # Update task ID
            await document_repository.update_task_id(document_id, task_id)

            logger.info(
                f"Processing document: {document.filename} (Type: {document.document_type})"
            )

            # Get the actual file path for processing
            file_path = document_service.get_file_path(document)
            if not file_path.exists():
                raise FileNotFoundError(f"Document file not found: {file_path}")

            logger.info(f"Processing file: {file_path}")

            # Initialize processors and validators
            llama_processor = get_llama_index_processor()
            security_validator = get_security_validator()

            # Step 1: Ensure document type is set by user
            if not document.document_type:
                raise ValueError(f"Document {document.filename} must have type set by user (simple or complex)")

            logger.info(f"Processing document {document.filename} as {document.document_type} (user selected)")

            # Step 2: Process document through Llama-Index RAG pipeline
            try:
                document_chunks = await llama_processor.process_document(document, file_path)

                # Step 3: Save document chunks to database
                for chunk in document_chunks:
                    await document_repository.save_document_chunk(chunk)

                logger.info(f"Successfully processed {len(document_chunks)} chunks for {document.filename}")

            except Exception as processing_error:
                logger.error(f"Llama-Index processing failed for {document.filename}: {str(processing_error)}")
                raise

            # Update processed timestamp
            document.processed_at = datetime.utcnow()

            # Mark as completed (Concluído)
            await document_service.update_document_status(
                document_id, DocumentStatus.PROCESSED
            )

            # Secure cleanup of any temporary files (if any were created)
            # Note: The current implementation doesn't create temp files,
            # but this is here for future enhancement and best practices
            temp_files = []  # Add any temp file paths here if created
            if temp_files:
                cleanup_results = security_validator.secure_file_cleanup(temp_files)
                logger.info(f"Secure cleanup completed: {cleanup_results}")

            logger.info(f"Document processing completed successfully for {document_id}")

            return {
                "success": True,
                "document_id": str(document_id),
                "filename": document.filename,
                "chunks_created": len(document_chunks) if 'document_chunks' in locals() else 0,
                "message": "Document processed successfully",
            }

        except Exception as e:
            logger.error(f"Error during document processing: {str(e)}")
            await document_service.update_document_status(
                document_id, DocumentStatus.FAILED, str(e)
            )
            raise


async def _update_document_status(
    document_id: uuid.UUID, status: DocumentStatus, error_message: str | None = None
) -> None:
    """Helper function to update document status."""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db_session:
        document_repository = DocumentRepository(db_session)
        document_service = DocumentService(document_repository)
        await document_service.update_document_status(
            document_id, status, error_message
        )


# Task to check document processing status
@celery_app.task
def get_task_status(task_id: str) -> dict[str, any]:
    """Get the status of a processing task."""
    try:
        task_result = celery_app.AsyncResult(task_id)

        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None,
            "traceback": task_result.traceback if task_result.failed() else None,
        }

    except Exception as e:
        return {"task_id": task_id, "status": "ERROR", "error": str(e)}


# Periodic task to clean up old results (optional)
@celery_app.task
def cleanup_old_results():
    """Clean up old task results to prevent Redis from growing too large."""
    try:
        # This would implement cleanup logic for old results
        logger.info("Cleaning up old task results")
        return {"cleaned": True}
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return {"cleaned": False, "error": str(e)}


if __name__ == "__main__":
    # Start the worker with: celery -A app.workers.document_processor worker --loglevel=info
    celery_app.start()
