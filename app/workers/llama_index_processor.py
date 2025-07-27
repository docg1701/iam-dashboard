"""Llama-Index processor for RAG pipeline orchestration."""

import logging
import uuid
from pathlib import Path

from llama_index.core import Document as LlamaDocument
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import BaseNode
from llama_index.readers.file import PyMuPDFReader

from app.config.llama_index_config import get_llama_index_config
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_preprocessing import get_document_preprocessor
from app.utils.security_validators import SecurityError, get_security_validator

logger = logging.getLogger(__name__)


class LlamaIndexProcessor:
    """Handles document processing using Llama-Index RAG pipeline."""

    def __init__(self):
        """Initialize the Llama-Index processor."""
        self.config = get_llama_index_config()
        self.config.setup_global_settings()  # Configure global settings
        self.vector_store = self.config.get_vector_store()
        self.text_splitter = self.config.get_text_splitter()
        self.embed_model = self.config.get_embedding_model()
        self.preprocessor = get_document_preprocessor()
        self.security_validator = get_security_validator()

    async def process_document(self, document: Document, file_path: Path) -> list[DocumentChunk]:
        """
        Process a document through the complete RAG pipeline.

        Args:
            document: Document model instance
            file_path: Path to the PDF file

        Returns:
            List of created DocumentChunk instances
        """
        try:
            logger.info(f"Starting Llama-Index processing for document {document.id}")

            # Step 0: Security validation
            self.security_validator.create_audit_log_entry(
                "process_start",
                str(document.id),
                {"filename": document.filename, "file_size": document.file_size}
            )

            try:
                validation_result = self.security_validator.validate_pdf_file(file_path)
                if not validation_result["valid"]:
                    raise SecurityError("PDF validation failed")

                logger.info(f"Security validation passed for {document.filename}")

            except SecurityError as sec_error:
                logger.error(f"Security validation failed for {document.filename}: {str(sec_error)}")
                self.security_validator.create_audit_log_entry(
                    "security_failure",
                    str(document.id),
                    {"error": str(sec_error)}
                )
                raise

            # Step 1: Extract text based on user-selected document type
            if document.document_type == "complex":
                logger.info(f"Processing complex document {document.filename} with Gemini OCR API")
                raw_text = self.preprocessor.extract_text_from_complex_document(file_path)
            else:
                logger.info(f"Processing simple document {document.filename} with local OCR/extraction")
                raw_text = self._extract_simple_text_or_local_ocr(file_path)

            if not raw_text or not raw_text.strip():
                raise ValueError(f"No text could be extracted from document {document.filename}")

            # Step 1.5: Sanitize extracted text for security
            sanitized_text = self.security_validator.sanitize_extracted_text(raw_text)

            logger.info(f"Extracted and sanitized {len(sanitized_text)} characters from {document.filename}")

            # Step 2: Create Llama-Index document with metadata
            llama_doc = LlamaDocument(
                text=sanitized_text,
                metadata={
                    "document_id": str(document.id),
                    "filename": document.filename,
                    "document_type": document.document_type,
                    "file_size": document.file_size,
                    "client_id": str(document.client_id)
                }
            )

            # Step 3: Split into chunks using Llama-Index text splitter
            nodes = self.text_splitter.get_nodes_from_documents([llama_doc])
            logger.info(f"Split document into {len(nodes)} chunks")

            # Step 4: Generate embeddings and create DocumentChunk instances
            document_chunks = []

            for i, node in enumerate(nodes):
                try:
                    # Generate embedding for the node
                    embedding = await self._generate_embedding(node.text)

                    # Create chunk metadata
                    chunk_metadata = {
                        "chunk_position": i,
                        "total_chunks": len(nodes),
                        "char_count": len(node.text),
                        "word_count": len(node.text.split()),
                        **node.metadata  # Include original document metadata
                    }

                    # Create DocumentChunk instance
                    chunk = DocumentChunk(
                        id=uuid.uuid4(),
                        node_id=node.node_id or str(uuid.uuid4()),
                        embedding=embedding,
                        text=node.text,
                        chunk_metadata=chunk_metadata,
                        document_id=document.id
                    )

                    document_chunks.append(chunk)

                except Exception as chunk_error:
                    logger.error(f"Error processing chunk {i} of document {document.id}: {str(chunk_error)}")
                    continue

            if not document_chunks:
                raise ValueError(f"No valid chunks could be created from document {document.filename}")

            logger.info(f"Successfully created {len(document_chunks)} chunks for document {document.filename}")

            # Step 5: Store in vector database via PGVectorStore
            await self._store_chunks_in_vector_db(document_chunks, nodes)

            # Step 6: Audit logging for successful processing
            self.security_validator.create_audit_log_entry(
                "process_complete",
                str(document.id),
                {
                    "chunks_created": len(document_chunks),
                    "text_length": len(sanitized_text),
                    "processing_success": True
                }
            )

            return document_chunks

        except Exception as e:
            # Audit logging for processing errors
            self.security_validator.create_audit_log_entry(
                "process_error",
                str(document.id),
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "processing_success": False
                }
            )
            logger.error(f"Error processing document {document.id} with Llama-Index: {str(e)}")
            raise

    def _extract_simple_text(self, file_path: Path) -> str:
        """
        Extract text from simple PDF documents using PyMuPDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text
        """
        try:
            # Use Llama-Index PyMuPDFReader for consistent text extraction
            reader = PyMuPDFReader()
            documents = reader.load_data(file_path)

            # Combine all pages
            text_parts = []
            for i, doc in enumerate(documents):
                if doc.text.strip():
                    text_parts.append(f"--- Página {i + 1} ---\n{doc.text}")

            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"Error extracting simple text from {file_path}: {str(e)}")
            raise

    def _extract_simple_text_or_local_ocr(self, file_path: Path) -> str:
        """
        Extract text from documents marked as 'simple' by user.
        First tries direct text extraction, then falls back to local Tesseract OCR.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text
        """
        try:
            # Step 1: Try direct text extraction first
            logger.debug(f"Attempting direct text extraction from {file_path.name}")
            direct_text = self._extract_simple_text(file_path)

            # Check if we got meaningful text
            if direct_text and len(direct_text.strip()) > 50:
                logger.info(f"Successfully extracted text directly from {file_path.name}")
                return direct_text

            # Step 2: Fall back to local OCR using Tesseract
            logger.info(f"No direct text found in {file_path.name}, using local Tesseract OCR")

            # Use the preprocessor's local OCR method
            local_ocr_text = self._extract_with_local_ocr(file_path)

            if local_ocr_text and len(local_ocr_text.strip()) > 0:
                logger.info(f"Successfully extracted text with local OCR from {file_path.name}")
                return local_ocr_text
            else:
                raise ValueError(f"No text could be extracted from {file_path.name} using local methods")

        except Exception as e:
            logger.error(f"Error extracting text from simple document {file_path}: {str(e)}")
            raise

    def _extract_with_local_ocr(self, file_path: Path) -> str:
        """
        Extract text using local Tesseract OCR (similar to complex document processing but local).

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text using local OCR
        """
        try:
            import io

            import cv2
            import fitz  # PyMuPDF
            import numpy as np
            import pytesseract
            from PIL import Image

            extracted_text = []

            # Open PDF with PyMuPDF
            pdf_document = fitz.open(file_path)

            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]

                # Convert page to image with good quality for OCR
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 2x zoom for better quality
                img_data = pix.tobytes("png")

                # Convert to OpenCV format
                pil_image = Image.open(io.BytesIO(img_data))
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

                # Preprocess image for better OCR
                preprocessed = self.preprocessor.preprocess_image_for_ocr(cv_image)

                # Perform OCR using Tesseract with Portuguese configuration
                try:
                    custom_config = r'--oem 3 --psm 6 -l por'
                    text = pytesseract.image_to_string(
                        preprocessed,
                        config=custom_config
                    )

                    if text.strip():
                        extracted_text.append(f"--- Página {page_num + 1} ---\n{text}")
                        logger.debug(f"Successfully extracted text from page {page_num + 1} using local OCR")
                    else:
                        logger.warning(f"No text extracted from page {page_num + 1} using local OCR")

                except Exception as ocr_error:
                    logger.error(f"Local OCR failed for page {page_num + 1}: {str(ocr_error)}")
                    continue

            pdf_document.close()

            result_text = "\n\n".join(extracted_text)
            logger.info(f"Local OCR completed for {file_path.name}: {len(result_text)} characters extracted")
            return result_text

        except Exception as e:
            logger.error(f"Error in local OCR extraction from {file_path}: {str(e)}")
            raise

    async def _generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text using configured embedding model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        try:
            # Use the configured Gemini embedding model
            embedding = await self.embed_model.aget_text_embedding(text)
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    async def _store_chunks_in_vector_db(self, chunks: list[DocumentChunk], nodes: list[BaseNode]) -> None:
        """
        Store document chunks in the vector database.

        Args:
            chunks: List of DocumentChunk instances
            nodes: Corresponding Llama-Index nodes
        """
        try:
            # Create a VectorStoreIndex with our configured vector store
            VectorStoreIndex(
                nodes=nodes,
                vector_store=self.vector_store
                # Settings are configured globally, no need to pass service_context
            )

            logger.info(f"Successfully stored {len(chunks)} chunks in vector database")

        except Exception as e:
            logger.error(f"Error storing chunks in vector database: {str(e)}")
            raise



def get_llama_index_processor() -> LlamaIndexProcessor:
    """Factory function to get LlamaIndexProcessor instance."""
    return LlamaIndexProcessor()
