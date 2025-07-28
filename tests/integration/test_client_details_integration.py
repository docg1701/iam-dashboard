"""Integration tests for client details functionality."""

import time
import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentStatus, DocumentType
from app.models.document_chunk import DocumentChunk
from app.repositories.client_repository import ClientRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.client_service import ClientService
from app.services.document_service import DocumentService


class TestClientDetailsIntegration:
    """Integration tests for client details workflow."""

    @pytest.mark.asyncio
    async def test_client_details_full_workflow(self, async_session: AsyncSession):
        """Test complete client details workflow with real database operations."""
        # Create repositories and services
        client_repository = ClientRepository(async_session)
        document_repository = DocumentRepository(async_session)
        chunk_repository = DocumentChunkRepository(async_session)

        client_service = ClientService(client_repository)
        document_service = DocumentService(document_repository)

        # Create a test client
        timestamp = int(time.time() * 1000000) % 100000000  # Use timestamp for unique CPF
        cpf = f"{timestamp:011d}"
        f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"

        client = await client_service.create_client(
            name="João Silva",
            cpf="123.456.789-09",  # Use the known working CPF
            birth_date=datetime(1990, 1, 15).date()
        )

        # Create test documents for the client
        doc1_content = b"Test PDF content for document 1"
        doc1 = await document_service.create_document(
            client_id=client.id,
            filename="document1.pdf",
            content=doc1_content,
            document_type=DocumentType.SIMPLE
        )
        assert doc1["success"] is True

        doc2_content = b"Test PDF content for document 2"
        doc2 = await document_service.create_document(
            client_id=client.id,
            filename="document2.pdf",
            content=doc2_content,
            document_type=DocumentType.COMPLEX
        )
        assert doc2["success"] is True

        # Simulate document processing completion
        doc1_id = uuid.UUID(doc1["document_id"])
        doc2_id = uuid.UUID(doc2["document_id"])

        await document_service.update_document_status(
            doc1_id,
            DocumentStatus.PROCESSED
        )
        await document_service.update_document_status(
            doc2_id,
            DocumentStatus.FAILED,
            error_message="OCR processing failed"
        )

        # Create document chunks for processed document with fake embeddings
        doc1_obj = await document_service.get_document_by_id(doc1_id)
        import numpy as np

        # Create fake embeddings (768 dimensions)
        fake_embedding_1 = np.random.random(768).tolist()
        fake_embedding_2 = np.random.random(768).tolist()

        chunks = [
            DocumentChunk(
                node_id="chunk1",
                text="Este é o primeiro bloco de texto extraído.",
                embedding=fake_embedding_1,
                chunk_metadata={"page": 1, "section": "header"},
                document_id=doc1_obj.id,
            ),
            DocumentChunk(
                node_id="chunk2",
                text="Este é o segundo bloco com mais conteúdo.",
                embedding=fake_embedding_2,
                chunk_metadata={"page": 1, "section": "body"},
                document_id=doc1_obj.id,
            ),
        ]
        await chunk_repository.create_multiple(chunks)

        # Test client details retrieval
        retrieved_client = await client_service.get_client_by_id(client.id)
        assert retrieved_client is not None
        assert retrieved_client.name == "João Silva"
        assert retrieved_client.formatted_cpf == "123.456.789-09"

        # Test document listing for client
        documents = await document_service.get_documents_by_client(client.id)
        assert len(documents) == 2

        # Verify document statuses
        processed_docs = [d for d in documents if d.status == DocumentStatus.PROCESSED]
        failed_docs = [d for d in documents if d.status == DocumentStatus.FAILED]

        assert len(processed_docs) == 1
        assert len(failed_docs) == 1
        assert failed_docs[0].error_message == "OCR processing failed"

        # Test document chunks retrieval
        doc1_chunks = await chunk_repository.get_by_document_id(doc1_id)
        assert len(doc1_chunks) == 2
        assert doc1_chunks[0].text == "Este é o primeiro bloco de texto extraído."
        assert doc1_chunks[1].text == "Este é o segundo bloco com mais conteúdo."

        # Test document summary statistics
        total_chars = sum(len(chunk.text) for chunk in doc1_chunks)
        total_words = sum(len(chunk.text.split()) for chunk in doc1_chunks)

        assert total_chars > 0
        assert total_words > 0

    @pytest.mark.asyncio
    async def test_client_with_no_documents(self, async_session: AsyncSession):
        """Test client details when client has no documents."""
        client_repository = ClientRepository(async_session)
        document_repository = DocumentRepository(async_session)

        client_service = ClientService(client_repository)
        document_service = DocumentService(document_repository)

        # Create a client without documents
        client = await client_service.create_client(
            name="Maria Santos",
            cpf="987.654.321-00",
            birth_date=datetime(1985, 5, 20).date()
        )

        # Test document listing returns empty
        documents = await document_service.get_documents_by_client(client.id)
        assert len(documents) == 0

        # Verify client details are still retrievable
        retrieved_client = await client_service.get_client_by_id(client.id)
        assert retrieved_client is not None
        assert retrieved_client.name == "Maria Santos"

    @pytest.mark.asyncio
    async def test_document_status_updates(self, async_session: AsyncSession):
        """Test real-time document status update workflow."""
        client_repository = ClientRepository(async_session)
        document_repository = DocumentRepository(async_session)

        client_service = ClientService(client_repository)
        document_service = DocumentService(document_repository)

        # Create client and document
        client = await client_service.create_client(
            name="Pedro Costa",
            cpf="222.333.444-55",
            birth_date=datetime(1992, 8, 10).date()
        )

        doc_content = b"Test document for status updates"
        doc = await document_service.create_document(
            client_id=client.id,
            filename="status_test.pdf",
            content=doc_content,
            document_type=DocumentType.SIMPLE
        )

        doc_id = uuid.UUID(doc["document_id"])

        # Verify initial status
        document = await document_service.get_document_by_id(doc_id)
        assert document.status == DocumentStatus.UPLOADED

        # Simulate processing start
        await document_service.update_document_status(
            doc_id,
            DocumentStatus.PROCESSING
        )

        # Verify processing status
        document = await document_service.get_document_by_id(doc_id)
        assert document.status == DocumentStatus.PROCESSING
        assert document.is_processing is True

        # Simulate processing completion
        await document_service.update_document_status(
            doc_id,
            DocumentStatus.PROCESSED
        )

        # Verify completed status
        document = await document_service.get_document_by_id(doc_id)
        assert document.status == DocumentStatus.PROCESSED
        assert document.is_processed is True
        assert document.processed_at is not None

    @pytest.mark.asyncio
    async def test_duplicate_document_handling(self, async_session: AsyncSession):
        """Test duplicate document detection in client details."""
        client_repository = ClientRepository(async_session)
        document_repository = DocumentRepository(async_session)

        client_service = ClientService(client_repository)
        document_service = DocumentService(document_repository)

        # Create client
        client = await client_service.create_client(
            name="Ana Lima",
            cpf="111.444.777-35",
            birth_date=datetime(1988, 3, 25).date()
        )

        # Create first document
        doc_content = b"Identical document content"
        doc1 = await document_service.create_document(
            client_id=client.id,
            filename="original.pdf",
            content=doc_content,
            document_type=DocumentType.SIMPLE
        )
        assert doc1["success"] is True

        # Attempt to create duplicate document
        doc2 = await document_service.create_document(
            client_id=client.id,
            filename="duplicate.pdf",
            content=doc_content,  # Same content
            document_type=DocumentType.SIMPLE
        )
        assert doc2["success"] is False
        assert "duplicado" in doc2["error"].lower()

        # Verify only one document exists
        documents = await document_service.get_documents_by_client(client.id)
        assert len(documents) == 1

    @pytest.mark.asyncio
    async def test_large_document_chunks(self, async_session: AsyncSession):
        """Test handling of documents with many chunks."""
        client_repository = ClientRepository(async_session)
        document_repository = DocumentRepository(async_session)
        chunk_repository = DocumentChunkRepository(async_session)

        client_service = ClientService(client_repository)
        document_service = DocumentService(document_repository)

        # Create client and document
        client = await client_service.create_client(
            name="Carlos Ferreira",
            cpf="333.333.333-33",
            birth_date=datetime(1975, 12, 5).date()
        )

        doc_content = b"Large document content"
        doc = await document_service.create_document(
            client_id=client.id,
            filename="large_document.pdf",
            content=doc_content,
            document_type=DocumentType.COMPLEX
        )

        doc_id = uuid.UUID(doc["document_id"])
        await document_service.update_document_status(doc_id, DocumentStatus.PROCESSED)

        # Create many chunks to simulate large document
        chunks = []
        for i in range(20):  # Create 20 chunks
            chunks.append(
                DocumentChunk(
                    node_id=f"chunk_{i}",
                    text=f"Este é o bloco de texto número {i + 1} com conteúdo simulado.",
                    metadata={"page": (i // 5) + 1, "section": f"section_{i}"},
                    document_id=doc_id,
                )
            )

        await chunk_repository.create_multiple(chunks)

        # Test chunk retrieval
        retrieved_chunks = await chunk_repository.get_by_document_id(doc_id)
        assert len(retrieved_chunks) == 20

        # Test statistics calculation
        total_chars = sum(len(chunk.text) for chunk in retrieved_chunks)
        total_words = sum(len(chunk.text.split()) for chunk in retrieved_chunks)
        avg_chunk_size = total_chars // len(retrieved_chunks)

        assert total_chars > 1000  # Should have substantial content
        assert total_words > 200   # Should have many words
        assert avg_chunk_size > 0  # Average should be calculated

    @pytest.mark.asyncio
    async def test_client_not_found_handling(self, async_session: AsyncSession):
        """Test handling of non-existent client IDs."""
        client_repository = ClientRepository(async_session)
        document_repository = DocumentRepository(async_session)

        client_service = ClientService(client_repository)
        document_service = DocumentService(document_repository)

        # Try to get non-existent client
        fake_client_id = uuid.uuid4()
        client = await client_service.get_client_by_id(fake_client_id)
        assert client is None

        # Try to get documents for non-existent client
        documents = await document_service.get_documents_by_client(fake_client_id)
        assert len(documents) == 0

    @pytest.mark.asyncio
    async def test_document_error_handling(self, async_session: AsyncSession):
        """Test document processing error scenarios."""
        client_repository = ClientRepository(async_session)
        document_repository = DocumentRepository(async_session)

        client_service = ClientService(client_repository)
        document_service = DocumentService(document_repository)

        # Create client and document
        client = await client_service.create_client(
            name="Rita Oliveira",
            cpf="444.444.444-44",
            birth_date=datetime(1995, 7, 18).date()
        )

        doc_content = b"Document that will fail processing"
        doc = await document_service.create_document(
            client_id=client.id,
            filename="error_document.pdf",
            content=doc_content,
            document_type=DocumentType.COMPLEX
        )

        doc_id = uuid.UUID(doc["document_id"])

        # Simulate processing failure
        error_message = "OCR engine failed to process document"
        await document_service.update_document_status(
            doc_id,
            DocumentStatus.FAILED,
            error_message=error_message
        )

        # Verify error status and message
        document = await document_service.get_document_by_id(doc_id)
        assert document.status == DocumentStatus.FAILED
        assert document.has_failed is True
        assert document.error_message == error_message
