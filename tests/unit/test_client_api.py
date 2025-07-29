"""Unit tests for client API endpoints."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.clients import (
    get_client,
    get_client_documents,
    get_client_documents_summary,
)
from app.models.client import Client
from app.models.document import Document, DocumentStatus, DocumentType


class TestClientAPI:
    """Test cases for client API endpoints."""

    @pytest.fixture
    def sample_client(self):
        """Create a sample client for testing."""
        return Client(
            id=uuid.uuid4(),
            name="João Silva",
            cpf="12345678901",
            birth_date=datetime(1990, 1, 15).date(),
            created_at=datetime(2025, 1, 1, 10, 0, 0),
            updated_at=datetime(2025, 1, 1, 10, 0, 0),
        )

    @pytest.fixture
    def sample_documents(self, sample_client):
        """Create sample documents for testing."""
        return [
            Document(
                id=uuid.uuid4(),
                filename="document1.pdf",
                content_hash="hash1",
                file_size=1024000,
                document_type=DocumentType.SIMPLE,
                status=DocumentStatus.PROCESSED,
                client_id=sample_client.id,
                file_path="client1/doc1.pdf",
                created_at=datetime(2025, 1, 1, 11, 0, 0),
                processed_at=datetime(2025, 1, 1, 11, 5, 0),
            ),
            Document(
                id=uuid.uuid4(),
                filename="document2.pdf",
                content_hash="hash2",
                file_size=512000,
                document_type=DocumentType.COMPLEX,
                status=DocumentStatus.PROCESSING,
                client_id=sample_client.id,
                file_path="client1/doc2.pdf",
                created_at=datetime(2025, 1, 1, 12, 0, 0),
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_client_success(self, sample_client):
        """Test successful client retrieval."""
        mock_db = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = sample_client

        with patch("app.api.clients.ClientService", return_value=mock_client_service):
            result = await get_client(str(sample_client.id), mock_db)

            assert result["id"] == str(sample_client.id)
            assert result["name"] == sample_client.name
            assert result["cpf"] == sample_client.cpf
            assert result["formatted_cpf"] == sample_client.formatted_cpf
            assert result["birth_date"] == sample_client.birth_date.isoformat()
            assert result["created_at"] == sample_client.created_at.isoformat()
            assert result["updated_at"] == sample_client.updated_at.isoformat()

    @pytest.mark.asyncio
    async def test_get_client_not_found(self):
        """Test client retrieval when client doesn't exist."""
        mock_db = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = None

        with patch("app.api.clients.ClientService", return_value=mock_client_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_client(str(uuid.uuid4()), mock_db)

            assert exc_info.value.status_code == 404
            assert "Client not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_client_invalid_uuid(self):
        """Test client retrieval with invalid UUID format."""
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_client("invalid-uuid", mock_db)

        assert exc_info.value.status_code == 400
        assert "Invalid client ID format" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_client_documents_success(self, sample_client, sample_documents):
        """Test successful client documents retrieval."""
        mock_db = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = sample_client

        mock_document_service = AsyncMock()
        mock_document_service.get_documents_by_client.return_value = sample_documents

        with (
            patch("app.api.clients.ClientService", return_value=mock_client_service),
            patch(
                "app.api.clients.DocumentService", return_value=mock_document_service
            ),
        ):
            result = await get_client_documents(str(sample_client.id), mock_db)

            assert len(result) == 2

            # Check first document
            doc1 = result[0]
            assert doc1["filename"] == "document1.pdf"
            assert doc1["status"] == DocumentStatus.PROCESSED
            assert doc1["document_type"] == DocumentType.SIMPLE
            assert doc1["file_size"] == 1024000
            assert doc1["formatted_file_size"] == "1000.0 KB"
            assert doc1["processed_at"] is not None

            # Check second document
            doc2 = result[1]
            assert doc2["filename"] == "document2.pdf"
            assert doc2["status"] == DocumentStatus.PROCESSING
            assert doc2["processed_at"] is None

    @pytest.mark.asyncio
    async def test_get_client_documents_client_not_found(self):
        """Test client documents retrieval when client doesn't exist."""
        mock_db = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = None

        with patch("app.api.clients.ClientService", return_value=mock_client_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_client_documents(str(uuid.uuid4()), mock_db)

            assert exc_info.value.status_code == 404
            assert "Client not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_client_documents_empty(self, sample_client):
        """Test client documents retrieval when client has no documents."""
        mock_db = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = sample_client

        mock_document_service = AsyncMock()
        mock_document_service.get_documents_by_client.return_value = []

        with (
            patch("app.api.clients.ClientService", return_value=mock_client_service),
            patch(
                "app.api.clients.DocumentService", return_value=mock_document_service
            ),
        ):
            result = await get_client_documents(str(sample_client.id), mock_db)

            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_client_documents_summary_success(
        self, sample_client, sample_documents
    ):
        """Test successful client documents summary retrieval."""
        mock_db = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = sample_client

        mock_document_service = AsyncMock()
        mock_document_service.get_documents_by_client.return_value = sample_documents

        with (
            patch("app.api.clients.ClientService", return_value=mock_client_service),
            patch(
                "app.api.clients.DocumentService", return_value=mock_document_service
            ),
        ):
            result = await get_client_documents_summary(str(sample_client.id), mock_db)

            assert result["client"]["id"] == str(sample_client.id)
            assert result["client"]["name"] == sample_client.name

            summary = result["summary"]
            assert summary["total_documents"] == 2
            assert summary["total_size"] == 1536000  # 1024000 + 512000
            assert summary["total_size_formatted"] == "1.5 MB"
            assert summary["processing_count"] == 1
            assert summary["processed_count"] == 1
            assert summary["failed_count"] == 0
            assert summary["completion_rate"] == 50.0  # 1 processed out of 2 total

    @pytest.mark.asyncio
    async def test_get_client_documents_summary_empty(self, sample_client):
        """Test client documents summary when client has no documents."""
        mock_db = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = sample_client

        mock_document_service = AsyncMock()
        mock_document_service.get_documents_by_client.return_value = []

        with (
            patch("app.api.clients.ClientService", return_value=mock_client_service),
            patch(
                "app.api.clients.DocumentService", return_value=mock_document_service
            ),
        ):
            result = await get_client_documents_summary(str(sample_client.id), mock_db)

            summary = result["summary"]
            assert summary["total_documents"] == 0
            assert summary["total_size"] == 0
            assert summary["total_size_formatted"] == "0 B"
            assert summary["completion_rate"] == 0

    @pytest.mark.asyncio
    async def test_get_client_documents_summary_with_failed_documents(
        self, sample_client
    ):
        """Test client documents summary with failed documents."""
        failed_document = Document(
            id=uuid.uuid4(),
            filename="failed_doc.pdf",
            content_hash="hash3",
            file_size=256000,
            document_type=DocumentType.SIMPLE,
            status=DocumentStatus.FAILED,
            client_id=sample_client.id,
            file_path="client1/failed_doc.pdf",
            error_message="Processing failed",
            created_at=datetime(2025, 1, 1, 13, 0, 0),
        )

        mock_db = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = sample_client

        mock_document_service = AsyncMock()
        mock_document_service.get_documents_by_client.return_value = [failed_document]

        with (
            patch("app.api.clients.ClientService", return_value=mock_client_service),
            patch(
                "app.api.clients.DocumentService", return_value=mock_document_service
            ),
        ):
            result = await get_client_documents_summary(str(sample_client.id), mock_db)

            summary = result["summary"]
            assert summary["total_documents"] == 1
            assert summary["failed_count"] == 1
            assert summary["processed_count"] == 0
            assert summary["completion_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_client_api_error_handling(self, sample_client):
        """Test API error handling for database exceptions."""
        mock_db = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.side_effect = Exception(
            "Database connection error"
        )

        with patch("app.api.clients.ClientService", return_value=mock_client_service):
            with pytest.raises(HTTPException) as exc_info:
                await get_client(str(sample_client.id), mock_db)

            assert exc_info.value.status_code == 500
            assert "Error retrieving client" in str(exc_info.value.detail)

    def test_document_size_formatting(self):
        """Test document size formatting logic."""
        # Test bytes
        doc_small = Document(
            id=uuid.uuid4(),
            filename="small.pdf",
            content_hash="hash",
            file_size=500,
            document_type=DocumentType.SIMPLE,
            status=DocumentStatus.PROCESSED,
            client_id=uuid.uuid4(),
            file_path="small.pdf",
        )
        assert doc_small.formatted_file_size == "500 B"

        # Test KB
        doc_medium = Document(
            id=uuid.uuid4(),
            filename="medium.pdf",
            content_hash="hash",
            file_size=1536,  # 1.5 KB
            document_type=DocumentType.SIMPLE,
            status=DocumentStatus.PROCESSED,
            client_id=uuid.uuid4(),
            file_path="medium.pdf",
        )
        assert doc_medium.formatted_file_size == "1.5 KB"

        # Test MB
        doc_large = Document(
            id=uuid.uuid4(),
            filename="large.pdf",
            content_hash="hash",
            file_size=1572864,  # 1.5 MB
            document_type=DocumentType.SIMPLE,
            status=DocumentStatus.PROCESSED,
            client_id=uuid.uuid4(),
            file_path="large.pdf",
        )
        assert doc_large.formatted_file_size == "1.5 MB"

    @pytest.mark.asyncio
    async def test_status_counts_calculation(self, sample_client):
        """Test status counts calculation in summary."""
        # Create documents with various statuses
        documents = [
            Document(
                id=uuid.uuid4(),
                filename="doc1.pdf",
                content_hash="hash1",
                file_size=1024,
                document_type=DocumentType.SIMPLE,
                status=DocumentStatus.PROCESSED,
                client_id=sample_client.id,
                file_path="doc1.pdf",
            ),
            Document(
                id=uuid.uuid4(),
                filename="doc2.pdf",
                content_hash="hash2",
                file_size=1024,
                document_type=DocumentType.SIMPLE,
                status=DocumentStatus.PROCESSED,
                client_id=sample_client.id,
                file_path="doc2.pdf",
            ),
            Document(
                id=uuid.uuid4(),
                filename="doc3.pdf",
                content_hash="hash3",
                file_size=1024,
                document_type=DocumentType.SIMPLE,
                status=DocumentStatus.PROCESSING,
                client_id=sample_client.id,
                file_path="doc3.pdf",
            ),
            Document(
                id=uuid.uuid4(),
                filename="doc4.pdf",
                content_hash="hash4",
                file_size=1024,
                document_type=DocumentType.SIMPLE,
                status=DocumentStatus.FAILED,
                client_id=sample_client.id,
                file_path="doc4.pdf",
            ),
        ]

        mock_db = AsyncMock()
        mock_client_service = AsyncMock()
        mock_client_service.get_client_by_id.return_value = sample_client

        mock_document_service = AsyncMock()
        mock_document_service.get_documents_by_client.return_value = documents

        with (
            patch("app.api.clients.ClientService", return_value=mock_client_service),
            patch(
                "app.api.clients.DocumentService", return_value=mock_document_service
            ),
        ):
            result = await get_client_documents_summary(str(sample_client.id), mock_db)

            summary = result["summary"]
            assert summary["total_documents"] == 4
            assert summary["processed_count"] == 2
            assert summary["processing_count"] == 1
            assert summary["failed_count"] == 1
            assert summary["completion_rate"] == 50.0  # 2 processed out of 4 total

            status_counts = summary["status_counts"]
            assert status_counts["processed"] == 2
            assert status_counts["processing"] == 1
            assert status_counts["failed"] == 1
