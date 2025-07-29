"""Vector storage tools for embedding generation and pgvector database operations."""

import json
import logging
from typing import Any

import google.generativeai as genai
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_sync_db

logger = logging.getLogger(__name__)


class VectorStorageTool:
    """Tool for generating embeddings and storing them in PostgreSQL with pgvector."""

    def __init__(
        self,
        embedding_model: str = "gemini-embedding-001",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        max_chunks_per_document: int = 1000,
    ) -> None:
        """Initialize the vector storage tool.

        Args:
            embedding_model: Gemini embedding model to use
            chunk_size: Size of text chunks for embedding generation
            chunk_overlap: Overlap between consecutive chunks
            max_chunks_per_document: Maximum number of chunks per document
        """
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunks_per_document = max_chunks_per_document

    def validate_pgvector_setup(self) -> dict[str, Any]:
        """Validate that pgvector extension is available in the database.

        Returns:
            Dictionary containing validation results
        """
        try:
            db: Session = next(get_sync_db())

            try:
                # Check if pgvector extension is installed
                result = db.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                )
                extension_exists = result.fetchone() is not None

                if not extension_exists:
                    return {
                        "valid": False,
                        "error": "pgvector extension not installed in database",
                    }

                # Check if we can create a simple vector
                test_query = text("SELECT ARRAY[1,2,3]::vector(3) as test_vector")
                result = db.execute(test_query)
                test_result = result.fetchone()

                return {
                    "valid": True,
                    "pgvector_available": True,
                    "test_vector": str(test_result[0]) if test_result else None,
                }

            finally:
                db.close()

        except Exception as e:
            return {"valid": False, "error": f"pgvector validation failed: {str(e)}"}

    def chunk_text(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Split text into chunks for embedding generation.

        Args:
            text: Text content to chunk
            metadata: Optional metadata to include with each chunk

        Returns:
            List of text chunks with metadata
        """
        if not text or not text.strip():
            return []

        chunks = []
        text = text.strip()

        # Simple chunking strategy - split by sentences when possible
        sentences = text.split(". ")
        current_chunk = ""
        chunk_id = 0

        for sentence in sentences:
            # Add sentence to current chunk
            test_chunk = current_chunk + ". " + sentence if current_chunk else sentence

            # If chunk would exceed size limit, save current chunk and start new one
            if len(test_chunk) > self.chunk_size and current_chunk:
                # Add overlap from end of current chunk
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                overlap_text = current_chunk[overlap_start:]

                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "text": current_chunk,
                        "start_pos": len(chunks) * self.chunk_size,  # Approximate
                        "end_pos": len(chunks) * self.chunk_size + len(current_chunk),
                        "char_count": len(current_chunk),
                        "metadata": metadata or {},
                    }
                )

                current_chunk = (
                    overlap_text + ". " + sentence if overlap_text else sentence
                )
                chunk_id += 1

                # Prevent too many chunks
                if len(chunks) >= self.max_chunks_per_document:
                    logger.warning(
                        f"Reached maximum chunks limit ({self.max_chunks_per_document})"
                    )
                    break
            else:
                current_chunk = test_chunk

        # Add the last chunk if it exists
        if current_chunk and len(chunks) < self.max_chunks_per_document:
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": current_chunk,
                    "start_pos": len(chunks) * self.chunk_size,
                    "end_pos": len(chunks) * self.chunk_size + len(current_chunk),
                    "char_count": len(current_chunk),
                    "metadata": metadata or {},
                }
            )

        logger.info(
            f"Text chunked into {len(chunks)} chunks (avg {sum(c['char_count'] for c in chunks) / len(chunks):.0f} chars/chunk)"
        )
        return chunks

    def generate_embedding(
        self, text: str, task_type: str = "retrieval_document"
    ) -> dict[str, Any]:
        """Generate embedding for a single text using Gemini.

        Args:
            text: Text to generate embedding for
            task_type: Type of task for embedding optimization

        Returns:
            Dictionary containing embedding and metadata
        """
        try:
            if not text or not text.strip():
                return {"success": False, "error": "Empty text provided for embedding"}

            # Generate embedding using Gemini
            result = genai.embed_content(
                model=self.embedding_model, content=text, task_type=task_type
            )

            embedding_vector = result["embedding"]

            return {
                "success": True,
                "embedding": embedding_vector,
                "dimension": len(embedding_vector),
                "model": self.embedding_model,
                "task_type": task_type,
                "text_length": len(text),
            }

        except Exception as e:
            error_msg = f"Failed to generate embedding: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def generate_embeddings_batch(
        self, text_chunks: list[dict[str, Any]], task_type: str = "retrieval_document"
    ) -> dict[str, Any]:
        """Generate embeddings for multiple text chunks.

        Args:
            text_chunks: List of text chunks with metadata
            task_type: Type of task for embedding optimization

        Returns:
            Dictionary containing batch embedding results
        """
        try:
            embeddings = []
            failed_chunks = []

            for chunk in text_chunks:
                chunk_text = chunk.get("text", "")
                chunk_id = chunk.get("chunk_id", 0)

                embedding_result = self.generate_embedding(chunk_text, task_type)

                if embedding_result["success"]:
                    embedding_data = {
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "embedding": embedding_result["embedding"],
                        "dimension": embedding_result["dimension"],
                        "start_pos": chunk.get("start_pos", 0),
                        "end_pos": chunk.get("end_pos", 0),
                        "char_count": chunk.get("char_count", len(chunk_text)),
                        "metadata": chunk.get("metadata", {}),
                    }
                    embeddings.append(embedding_data)
                else:
                    failed_chunks.append(
                        {"chunk_id": chunk_id, "error": embedding_result["error"]}
                    )
                    logger.warning(
                        f"Failed to generate embedding for chunk {chunk_id}: {embedding_result['error']}"
                    )

            result = {
                "success": True,
                "embeddings": embeddings,
                "total_chunks": len(text_chunks),
                "successful_embeddings": len(embeddings),
                "failed_chunks": failed_chunks,
                "embedding_dimension": embeddings[0]["dimension"] if embeddings else 0,
                "model_used": self.embedding_model,
            }

            logger.info(
                f"Generated {len(embeddings)}/{len(text_chunks)} embeddings successfully"
            )
            return result

        except Exception as e:
            error_msg = f"Batch embedding generation failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def store_document_embeddings(
        self, document_id: int, embeddings_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Store document embeddings in the database.

        Args:
            document_id: ID of the document
            embeddings_data: List of embedding data dictionaries

        Returns:
            Dictionary containing storage results
        """
        try:
            db: Session = next(get_sync_db())

            try:
                stored_embeddings = 0

                # Create table if it doesn't exist (for development)
                create_table_query = text("""
                    CREATE TABLE IF NOT EXISTS document_embeddings (
                        id SERIAL PRIMARY KEY,
                        document_id INTEGER NOT NULL,
                        chunk_id INTEGER NOT NULL,
                        text_content TEXT NOT NULL,
                        embedding VECTOR(768),
                        start_pos INTEGER,
                        end_pos INTEGER,
                        char_count INTEGER,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents(document_id)
                    )
                """)
                db.execute(create_table_query)

                # Create index on embeddings for similarity search
                index_query = text("""
                    CREATE INDEX IF NOT EXISTS idx_document_embeddings_vector
                    ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
                """)
                db.execute(index_query)

                # Insert embeddings
                for embedding_data in embeddings_data:
                    try:
                        # Convert embedding to PostgreSQL vector format
                        embedding_vector = embedding_data["embedding"]
                        vector_str = f"[{','.join(map(str, embedding_vector))}]"

                        insert_query = text("""
                            INSERT INTO document_embeddings
                            (document_id, chunk_id, text_content, embedding, start_pos, end_pos, char_count, metadata)
                            VALUES (:document_id, :chunk_id, :text_content, :embedding::vector,
                                   :start_pos, :end_pos, :char_count, :metadata)
                        """)

                        db.execute(
                            insert_query,
                            {
                                "document_id": document_id,
                                "chunk_id": embedding_data["chunk_id"],
                                "text_content": embedding_data["text"],
                                "embedding": vector_str,
                                "start_pos": embedding_data.get("start_pos"),
                                "end_pos": embedding_data.get("end_pos"),
                                "char_count": embedding_data.get("char_count"),
                                "metadata": json.dumps(
                                    embedding_data.get("metadata", {})
                                ),
                            },
                        )

                        stored_embeddings += 1

                    except Exception as chunk_error:
                        logger.error(
                            f"Failed to store embedding for chunk {embedding_data.get('chunk_id')}: {str(chunk_error)}"
                        )
                        continue

                db.commit()

                result = {
                    "success": True,
                    "document_id": document_id,
                    "stored_embeddings": stored_embeddings,
                    "total_embeddings": len(embeddings_data),
                    "failed_embeddings": len(embeddings_data) - stored_embeddings,
                }

                logger.info(
                    f"Stored {stored_embeddings}/{len(embeddings_data)} embeddings for document {document_id}"
                )
                return result

            finally:
                db.close()

        except Exception as e:
            error_msg = (
                f"Failed to store embeddings for document {document_id}: {str(e)}"
            )
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "document_id": document_id}

    def search_similar_content(
        self,
        query_text: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        document_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Search for similar content using vector similarity.

        Args:
            query_text: Text to search for
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score
            document_ids: Optional list of document IDs to search within

        Returns:
            Dictionary containing search results
        """
        try:
            # Generate embedding for query
            query_embedding_result = self.generate_embedding(
                query_text, "retrieval_query"
            )

            if not query_embedding_result["success"]:
                return query_embedding_result

            query_embedding = query_embedding_result["embedding"]
            vector_str = f"[{','.join(map(str, query_embedding))}]"

            db: Session = next(get_sync_db())

            try:
                # Build search query
                where_clause = ""
                params = {
                    "query_vector": vector_str,
                    "limit": limit,
                    "threshold": similarity_threshold,
                }

                if document_ids:
                    where_clause = "AND de.document_id = ANY(:document_ids)"
                    params["document_ids"] = document_ids

                search_query = text(f"""
                    SELECT
                        de.id,
                        de.document_id,
                        de.chunk_id,
                        de.text_content,
                        de.start_pos,
                        de.end_pos,
                        de.char_count,
                        de.metadata,
                        de.created_at,
                        d.filename,
                        1 - (de.embedding <=> :query_vector::vector) as similarity_score
                    FROM document_embeddings de
                    JOIN documents d ON de.document_id = d.document_id
                    WHERE 1 - (de.embedding <=> :query_vector::vector) > :threshold
                    {where_clause}
                    ORDER BY de.embedding <=> :query_vector::vector
                    LIMIT :limit
                """)

                results = db.execute(search_query, params).fetchall()

                search_results = []
                for row in results:
                    search_results.append(
                        {
                            "embedding_id": row.id,
                            "document_id": row.document_id,
                            "chunk_id": row.chunk_id,
                            "filename": row.filename,
                            "text_content": row.text_content,
                            "start_pos": row.start_pos,
                            "end_pos": row.end_pos,
                            "char_count": row.char_count,
                            "metadata": json.loads(row.metadata)
                            if row.metadata
                            else {},
                            "similarity_score": float(row.similarity_score),
                            "created_at": row.created_at.isoformat()
                            if row.created_at
                            else None,
                        }
                    )

                result = {
                    "success": True,
                    "query_text": query_text,
                    "results": search_results,
                    "total_results": len(search_results),
                    "similarity_threshold": similarity_threshold,
                    "query_embedding_dimension": len(query_embedding),
                }

                logger.info(
                    f"Found {len(search_results)} similar content chunks for query"
                )
                return result

            finally:
                db.close()

        except Exception as e:
            error_msg = f"Vector similarity search failed: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def process_document_text(
        self,
        document_id: int,
        text_content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Complete workflow for processing document text into vector embeddings.

        Args:
            document_id: ID of the document
            text_content: Full text content of the document
            metadata: Optional metadata to include

        Returns:
            Dictionary containing complete processing results
        """
        logger.info(f"Starting vector processing for document {document_id}")

        try:
            # Step 1: Chunk the text
            chunks = self.chunk_text(text_content, metadata)

            if not chunks:
                return {
                    "success": False,
                    "error": "No text chunks generated from document",
                    "document_id": document_id,
                }

            # Step 2: Generate embeddings
            embeddings_result = self.generate_embeddings_batch(chunks)

            if not embeddings_result["success"]:
                return embeddings_result

            # Step 3: Store embeddings in database
            storage_result = self.store_document_embeddings(
                document_id, embeddings_result["embeddings"]
            )

            # Combine results
            final_result = {
                "success": storage_result["success"],
                "document_id": document_id,
                "processing_summary": {
                    "text_length": len(text_content),
                    "chunks_generated": len(chunks),
                    "embeddings_generated": embeddings_result["successful_embeddings"],
                    "embeddings_stored": storage_result.get("stored_embeddings", 0),
                    "embedding_dimension": embeddings_result.get(
                        "embedding_dimension", 0
                    ),
                    "model_used": self.embedding_model,
                },
            }

            if not storage_result["success"]:
                final_result["error"] = storage_result["error"]

            logger.info(f"Vector processing completed for document {document_id}")
            return final_result

        except Exception as e:
            error_msg = f"Document vector processing failed for document {document_id}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "document_id": document_id}
