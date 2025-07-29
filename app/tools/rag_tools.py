"""RAG retrieval tools for document context retrieval using Llama-Index infrastructure."""

import logging
import uuid
from typing import Any

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import QueryBundle

from app.config.llama_index_config import get_llama_index_config
from app.repositories.document_chunk_repository import DocumentChunkRepository

logger = logging.getLogger(__name__)


class RAGRetrieverTool:
    """Tool for retrieving relevant document chunks using RAG."""

    def __init__(self, chunk_repository: DocumentChunkRepository | None = None):
        """Initialize the RAG retriever tool.

        Args:
            chunk_repository: Document chunk repository for database operations
        """
        self.chunk_repository = chunk_repository
        self.config = get_llama_index_config()
        self.config.setup_global_settings()

    def retrieve_client_context(
        self,
        client_id: uuid.UUID,
        profession: str,
        disease: str,
        incident_date: str,
        similarity_top_k: int = 10,
    ) -> dict[str, Any]:
        """Retrieve relevant document chunks for the client using RAG.

        Args:
            client_id: Client UUID
            profession: Client's profession
            disease: Disease/condition
            incident_date: Date of incident
            similarity_top_k: Number of top chunks to retrieve

        Returns:
            Dictionary containing retrieved context and metadata
        """
        try:
            logger.info(f"Retrieving context for client {client_id}")

            # Note: Repository operations would need to be handled differently in sync context
            # For now, we'll continue with vector store search

            # Create query combining the form data
            query_text = f"""
            Profissão: {profession}
            Condição médica: {disease}
            Data do incidente: {incident_date}

            Buscar informações sobre diagnósticos, tratamentos, incapacidade laboral,
            relação com atividade profissional e evidências médicas.
            """

            # Use vector store for similarity search
            vector_store = self.config.get_vector_store()
            index = VectorStoreIndex.from_vector_store(vector_store)

            # Create retriever with client filtering
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=similarity_top_k,
            )

            # Perform retrieval
            query_bundle = QueryBundle(query_text)
            retrieved_nodes = retriever.retrieve(query_bundle)

            # Filter nodes by client_id and extract text
            relevant_texts = []
            for node in retrieved_nodes:
                # Check if this chunk belongs to our client
                node_client_id = None
                if hasattr(node, "metadata") and node.metadata.get("client_id"):
                    node_client_id = node.metadata.get("client_id")
                elif hasattr(node, "node") and hasattr(node.node, "metadata"):
                    node_client_id = node.node.metadata.get("client_id")

                if node_client_id == str(client_id):
                    chunk_text = (
                        node.text
                        if hasattr(node, "text")
                        else (
                            node.node.text
                            if hasattr(node, "node") and hasattr(node.node, "text")
                            else ""
                        )
                    )
                    if chunk_text:
                        relevant_texts.append(
                            {
                                "text": chunk_text,
                                "score": node.score if hasattr(node, "score") else 0.0,
                                "metadata": node.metadata
                                if hasattr(node, "metadata")
                                else {},
                            }
                        )

            result = {
                "success": True,
                "context_chunks": relevant_texts,
                "total_chunks": len(relevant_texts),
                "query_text": query_text.strip(),
                "client_id": str(client_id),
                "similarity_top_k": similarity_top_k,
            }

            logger.info(
                f"Retrieved {len(relevant_texts)} relevant chunks for client {client_id}"
            )
            return result

        except Exception as e:
            error_msg = f"Error retrieving context for client {client_id}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "context_chunks": [],
                "total_chunks": 0,
                "client_id": str(client_id),
            }

    def search_documents_by_query(
        self,
        query_text: str,
        client_id: uuid.UUID | None = None,
        similarity_top_k: int = 10,
    ) -> dict[str, Any]:
        """Search documents by free-form query text.

        Args:
            query_text: Query text to search for
            client_id: Optional client ID to filter results
            similarity_top_k: Number of top chunks to retrieve

        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.info(f"Searching documents with query: {query_text[:100]}...")

            # Use vector store for similarity search
            vector_store = self.config.get_vector_store()
            index = VectorStoreIndex.from_vector_store(vector_store)

            # Create retriever
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=similarity_top_k,
            )

            # Perform retrieval
            query_bundle = QueryBundle(query_text)
            retrieved_nodes = retriever.retrieve(query_bundle)

            # Extract results with optional client filtering
            search_results = []
            for node in retrieved_nodes:
                # Get node metadata and text
                node_client_id = None
                node_text = ""
                node_metadata = {}
                score = 0.0

                if hasattr(node, "metadata"):
                    node_metadata = node.metadata
                    node_client_id = node_metadata.get("client_id")
                if hasattr(node, "text"):
                    node_text = node.text
                if hasattr(node, "score"):
                    score = node.score

                # Alternative node structure
                if hasattr(node, "node"):
                    if hasattr(node.node, "metadata"):
                        node_metadata = node.node.metadata
                        node_client_id = node_metadata.get("client_id")
                    if hasattr(node.node, "text"):
                        node_text = node.node.text

                # Apply client filter if specified
                if client_id and node_client_id != str(client_id):
                    continue

                if node_text:
                    search_results.append(
                        {
                            "text": node_text,
                            "score": score,
                            "metadata": node_metadata,
                            "client_id": node_client_id,
                        }
                    )

            result = {
                "success": True,
                "search_results": search_results,
                "total_results": len(search_results),
                "query_text": query_text,
                "client_filter": str(client_id) if client_id else None,
                "similarity_top_k": similarity_top_k,
            }

            logger.info(f"Found {len(search_results)} relevant chunks for query")
            return result

        except Exception as e:
            error_msg = f"Error searching documents: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "search_results": [],
                "total_results": 0,
            }
