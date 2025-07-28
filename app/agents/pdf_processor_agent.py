"""PDF Processor Agent for autonomous document processing."""

import logging
from pathlib import Path
from typing import Any

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools import tool

from app.agents.base_agent import AgentPlugin
from app.tools.ocr_tools import OCRProcessorTool
from app.tools.pdf_tools import PDFReaderTool
from app.tools.vector_storage_tools import VectorStorageTool

logger = logging.getLogger(__name__)


class PDFProcessorAgent(Agent):
    """Autonomous agent for PDF document processing with OCR and vector storage."""

    def __init__(
        self,
        model: str = "gemini-2.5-pro",
        instructions: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the PDF Processor Agent.

        Args:
            model: The LLM model to use for document analysis
            instructions: Custom instructions for the agent
            **kwargs: Additional agent configuration
        """
        default_instructions = """You are a PDF processing agent specialized in:
        1. Extracting text and metadata from PDF documents
        2. Performing OCR on image-based PDFs
        3. Generating vector embeddings for semantic search
        4. Storing processed documents in PostgreSQL with pgvector

        Always provide detailed logging for document processing operations.
        Ensure data integrity and handle errors gracefully.
        """

        # Extract tool-specific config before passing to parent
        tool_config = {
            'max_file_size_mb': kwargs.pop('max_file_size_mb', 50),
            'embedding_model': kwargs.pop('embedding_model', 'gemini-embedding-001'),
            'chunk_size': kwargs.pop('chunk_size', 1000),
            'ocr_confidence': kwargs.pop('ocr_confidence', 50.0),
            'ocr_preprocessing': kwargs.pop('ocr_preprocessing', True),
        }

        # Convert model string to Gemini model object
        model_instance = Gemini(id=model) if isinstance(model, str) else model

        super().__init__(
            model=model_instance,
            instructions=instructions or default_instructions,
            **kwargs,
        )

        # Initialize tools
        self.pdf_reader = PDFReaderTool(
            max_file_size_mb=tool_config["max_file_size_mb"]
        )
        self.ocr_processor = OCRProcessorTool(
            min_confidence=tool_config["ocr_confidence"],
            preprocessing=tool_config["ocr_preprocessing"],
        )
        self.vector_storage = VectorStorageTool(
            embedding_model=tool_config["embedding_model"],
            chunk_size=tool_config["chunk_size"],
        )

        self.add_tool(self.extract_pdf_text)
        self.add_tool(self.process_ocr)
        self.add_tool(self.generate_embeddings)
        self.add_tool(self.store_document)

        logger.info(f"Initialized PDFProcessorAgent with model: {model}")

    @tool
    def extract_pdf_text(self, file_path: str) -> dict[str, Any]:
        """Extract text and metadata from PDF document.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing extracted text, metadata, and page count
        """
        try:
            result = self.pdf_reader.process_document(file_path)

            if result["success"]:
                # Reformat for agent compatibility
                formatted_result = {
                    "success": True,
                    "text_content": result["text_content"],
                    "metadata": result["metadata"],
                    "page_count": result["text_summary"]["total_pages"],
                    "total_chars": result["text_summary"]["total_chars"],
                    "file_path": file_path,
                    "document_info": result["document_info"],
                    "images_info": result["images_info"],
                }

                logger.info(
                    f"Successfully extracted text from PDF: {file_path} ({formatted_result['page_count']} pages)"
                )
                return formatted_result
            else:
                return result

        except Exception as e:
            error_msg = f"Failed to extract PDF text from {file_path}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "file_path": file_path}

    @tool
    def process_ocr(
        self, file_path: str, pages_with_images: list[int] | None = None
    ) -> dict[str, Any]:
        """Process OCR on image-based PDF pages.

        Args:
            file_path: Path to the PDF file
            pages_with_images: List of page numbers that need OCR (1-indexed)

        Returns:
            Dictionary containing OCR results
        """
        try:
            if pages_with_images:
                result = self.ocr_processor.process_pdf_pages(
                    file_path, pages_with_images
                )
            else:
                result = self.ocr_processor.process_pdf_pages(file_path)

            if result["success"]:
                # Reformat for agent compatibility
                formatted_result = {
                    "success": True,
                    "ocr_results": [
                        {
                            "page_number": ocr_data["page_number"],
                            "ocr_text": ocr_data["ocr_text"],
                            "confidence": ocr_data["average_confidence"],
                            "char_count": ocr_data["char_count"],
                        }
                        for ocr_data in result["ocr_results"]
                        if ocr_data.get("success", True)
                    ],
                    "pages_processed": result["successful_pages"],
                    "total_ocr_chars": result["summary"]["total_ocr_chars"],
                    "file_path": file_path,
                }

                logger.info(
                    f"Successfully processed OCR for PDF: {file_path} ({formatted_result['pages_processed']} pages)"
                )
                return formatted_result
            else:
                return result

        except Exception as e:
            error_msg = f"Failed to process OCR for {file_path}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "file_path": file_path}

    @tool
    def generate_embeddings(
        self, text_content: str, chunk_size: int = 1000
    ) -> dict[str, Any]:
        """Generate vector embeddings for document text.

        Args:
            text_content: Text content to generate embeddings for
            chunk_size: Size of text chunks for embedding generation

        Returns:
            Dictionary containing embedding vectors and metadata
        """
        try:
            # Create chunks using the vector storage tool
            chunks = self.vector_storage.chunk_text(text_content)

            if not chunks:
                return {
                    "success": False,
                    "error": "No chunks generated from text content",
                }

            # Generate embeddings using the vector storage tool
            result = self.vector_storage.generate_embeddings_batch(chunks)

            if result["success"]:
                # Reformat for agent compatibility
                formatted_result = {
                    "success": True,
                    "embeddings": [
                        {
                            "chunk_id": emb_data["chunk_id"],
                            "text": emb_data["text"],
                            "embedding": emb_data["embedding"],
                            "start_pos": emb_data["start_pos"],
                            "end_pos": emb_data["end_pos"],
                        }
                        for emb_data in result["embeddings"]
                    ],
                    "total_chunks": result["total_chunks"],
                    "successful_embeddings": result["successful_embeddings"],
                    "embedding_dimension": result["embedding_dimension"],
                }

                logger.info(
                    f"Successfully generated embeddings: {formatted_result['successful_embeddings']}/{formatted_result['total_chunks']} chunks"
                )
                return formatted_result
            else:
                return result

        except Exception as e:
            error_msg = f"Failed to generate embeddings: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    @tool
    def store_document(
        self, document_data: dict[str, Any], user_id: int
    ) -> dict[str, Any]:
        """Store processed document data in PostgreSQL database.

        Args:
            document_data: Processed document data including text, metadata, and embeddings
            user_id: ID of the user who uploaded the document

        Returns:
            Dictionary containing storage results and document ID
        """
        try:
            import json
            from datetime import datetime

            from sqlalchemy.orm import Session

            from app.core.database import get_sync_db
            from app.models.document import Document

            # This would typically be injected, but for the agent we'll get it directly
            db_gen = get_sync_db()
            db: Session = next(db_gen)

            try:
                # Create document record
                document = Document(
                    user_id=user_id,
                    filename=Path(document_data.get("file_path", "")).name,
                    content_type="application/pdf",
                    file_size=document_data.get("file_size", 0),
                    content=document_data.get("extracted_text", ""),
                    metadata_=json.dumps(
                        {
                            "page_count": document_data.get("page_count", 0),
                            "pdf_metadata": document_data.get("pdf_metadata", {}),
                            "ocr_results": document_data.get("ocr_results", []),
                            "processing_timestamp": datetime.utcnow().isoformat(),
                            "agent_processed": True,
                        }
                    ),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                db.add(document)
                db.commit()
                db.refresh(document)

                # Generate and store embeddings using vector storage tool
                extracted_text = document_data.get("extracted_text", "")
                stored_embeddings = 0

                if extracted_text.strip():
                    try:
                        vector_result = self.vector_storage.process_document_text(
                            document.document_id,
                            extracted_text,
                            metadata={
                                "filename": document.filename,
                                "page_count": document_data.get("page_count", 0),
                                "file_size": document_data.get("file_size", 0),
                            },
                        )

                        if vector_result["success"]:
                            stored_embeddings = vector_result["processing_summary"][
                                "embeddings_stored"
                            ]
                        else:
                            logger.warning(
                                f"Failed to process embeddings: {vector_result.get('error', 'Unknown error')}"
                            )
                    except Exception as emb_error:
                        logger.warning(
                            f"Failed to process embeddings: {str(emb_error)}"
                        )
                        pass

                result = {
                    "success": True,
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "stored_embeddings": stored_embeddings,
                    "text_length": len(extracted_text),
                }

                logger.info(
                    f"Successfully stored document: {document.filename} (ID: {document.document_id})"
                )
                return result

            finally:
                db.close()

        except Exception as e:
            error_msg = f"Failed to store document: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def process_document(
        self, file_path: str, user_id: int, perform_ocr: bool = True
    ) -> dict[str, Any]:
        """Main workflow for processing a PDF document.

        Args:
            file_path: Path to the PDF file to process
            user_id: ID of the user who uploaded the document
            perform_ocr: Whether to perform OCR on the document

        Returns:
            Dictionary containing complete processing results
        """
        logger.info(f"Starting document processing workflow for: {file_path}")

        try:
            # Step 1: Extract PDF text
            text_result = self.extract_pdf_text(file_path)
            if not text_result["success"]:
                return text_result

            all_text = " ".join([page["text"] for page in text_result["text_content"]])

            # Step 2: Perform OCR if needed
            ocr_result = None
            if perform_ocr:
                # Identify pages that might need OCR (pages with very little text)
                pages_needing_ocr = [
                    page["page_number"]
                    for page in text_result["text_content"]
                    if page["char_count"] < 100  # Threshold for "low text" pages
                ]

                if pages_needing_ocr:
                    ocr_result = self.process_ocr(file_path, pages_needing_ocr)
                    if ocr_result["success"]:
                        # Combine OCR text with extracted text
                        ocr_text = " ".join(
                            [page["ocr_text"] for page in ocr_result["ocr_results"]]
                        )
                        all_text += " " + ocr_text

            # Step 3: Generate and store embeddings using integrated workflow
            document_data = {
                "file_path": file_path,
                "extracted_text": all_text,
                "page_count": text_result["page_count"],
                "pdf_metadata": text_result["metadata"],
                "ocr_results": ocr_result["ocr_results"]
                if ocr_result and ocr_result["success"]
                else [],
                "file_size": Path(file_path).stat().st_size,
            }

            # Step 4: Store document and generate embeddings
            storage_result = self.store_document(document_data, user_id)

            # Compile final result
            final_result = {
                "success": storage_result["success"],
                "document_id": storage_result.get("document_id"),
                "filename": storage_result.get("filename"),
                "processing_summary": {
                    "pages_processed": text_result["page_count"],
                    "text_chars_extracted": len(all_text),
                    "ocr_pages": len(ocr_result["ocr_results"])
                    if ocr_result and ocr_result["success"]
                    else 0,
                    "embeddings_stored": storage_result.get("stored_embeddings", 0),
                    "storage_success": storage_result["success"],
                },
            }

            if not storage_result["success"]:
                final_result["error"] = storage_result["error"]

            logger.info(f"Document processing completed for: {file_path}")
            return final_result

        except Exception as e:
            error_msg = f"Document processing workflow failed for {file_path}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "file_path": file_path}


class PDFProcessorPlugin(AgentPlugin):
    """Plugin wrapper for PDFProcessorAgent."""

    PLUGIN_NAME = "PDFProcessorPlugin"
    VERSION = "1.0.0"
    DEPENDENCIES: list[str] = []

    def __init__(self, agent_id: str, config: dict[str, Any]):
        super().__init__(agent_id, config)
        self._agent_instance: PDFProcessorAgent | None = None

    async def initialize(self) -> bool:
        """Initialize the PDF processor agent."""
        try:
            model = self.config.get("model", "gemini-2.5-pro")
            instructions = self.config.get("instructions")

            self._agent_instance = PDFProcessorAgent(
                model=model,
                instructions=instructions,
                name=self.name,
                description=self.description,
            )

            self._initialized = True
            logger.info(f"Initialized PDFProcessorPlugin: {self.agent_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to initialize PDFProcessorPlugin {self.agent_id}: {str(e)}"
            )
            return False

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process a document through the PDF processor agent."""
        if not self._initialized or not self._agent_instance:
            return {"success": False, "error": "Agent not initialized"}

        try:
            file_path = data.get("file_path")
            user_id = data.get("user_id")
            perform_ocr = data.get("perform_ocr", True)

            if not file_path or not user_id:
                return {
                    "success": False,
                    "error": "Missing required parameters: file_path and user_id",
                }

            result = await self._agent_instance.process_document(
                file_path=file_path, user_id=user_id, perform_ocr=perform_ocr
            )

            return result

        except Exception as e:
            error_msg = f"Processing failed in PDFProcessorPlugin: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def health_check(self) -> bool:
        """Perform health check on the PDF processor agent."""
        if not self._initialized or not self._agent_instance:
            return False

        try:
            # Simple health check - verify agent tools are available
            return hasattr(self._agent_instance, "extract_pdf_text")
        except Exception:
            return False

    def get_capabilities(self) -> list[str]:
        """Get the capabilities of the PDF processor agent."""
        return [
            "pdf_text_extraction",
            "ocr_processing",
            "vector_embedding_generation",
            "document_storage",
            "metadata_extraction",
        ]
