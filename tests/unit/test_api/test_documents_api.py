"""Unit tests for documents API endpoints with agent integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import fastapi_app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(fastapi_app)


@pytest.fixture
def mock_agent_manager():
    """Mock AgentManager for testing."""
    return MagicMock()


@pytest.fixture
def mock_pdf_agent():
    """Mock PDF processor agent."""
    agent = AsyncMock()
    agent.process_document.return_value = {
        "success": True,
        "document_id": "test-doc-id",
        "filename": "test.pdf",
        "processing_summary": "Document processed successfully",
    }
    return agent


class TestDocumentUpload:
    """Test document upload endpoint."""

    @patch("app.api.documents.Container.agent_manager")
    @patch("app.api.documents.get_async_db")
    def test_upload_document_success(
        self, mock_db, mock_container, client, mock_agent_manager, mock_pdf_agent
    ):
        """Test successful document upload."""
        # Setup mocks
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_agent.return_value = mock_pdf_agent
        mock_agent_manager.is_agent_active.return_value = True

        # Create test file
        test_file = b"test pdf content"

        # Make request
        response = client.post(
            "/v1/documents/upload",
            files={"file": ("test.pdf", test_file, "application/pdf")},
            data={"user_id": 1, "perform_ocr": True},
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["document_id"] == "test-doc-id"
        assert data["filename"] == "test.pdf"
        assert "Document processed successfully" in data["message"]

    @patch("app.api.documents.Container.agent_manager")
    def test_upload_document_agent_not_found(
        self, mock_container, client, mock_agent_manager
    ):
        """Test document upload when agent is not found."""
        # Setup mocks
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_agent.return_value = None

        # Create test file
        test_file = b"test pdf content"

        # Make request
        response = client.post(
            "/v1/documents/upload",
            files={"file": ("test.pdf", test_file, "application/pdf")},
            data={"user_id": 1, "perform_ocr": True},
        )

        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"] == "agent_not_found"
        assert data["agent_id"] == "pdf_processor"

    @patch("app.api.documents.Container.agent_manager")
    def test_upload_document_agent_not_active(
        self, mock_container, client, mock_agent_manager, mock_pdf_agent
    ):
        """Test document upload when agent is not active."""
        # Setup mocks
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_agent.return_value = mock_pdf_agent
        mock_agent_manager.is_agent_active.return_value = False

        # Create test file
        test_file = b"test pdf content"

        # Make request
        response = client.post(
            "/v1/documents/upload",
            files={"file": ("test.pdf", test_file, "application/pdf")},
            data={"user_id": 1, "perform_ocr": True},
        )

        # Assertions
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["error"] == "agent_not_active"
        assert data["agent_id"] == "pdf_processor"

    def test_upload_non_pdf_file(self, client):
        """Test upload of non-PDF file returns error."""
        test_file = b"test content"

        response = client.post(
            "/v1/documents/upload",
            files={"file": ("test.txt", test_file, "text/plain")},
            data={"user_id": 1, "perform_ocr": True},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Only PDF files are supported" in data["detail"]

    @patch("app.api.documents.Container.agent_manager")
    def test_upload_document_processing_failure(
        self, mock_container, client, mock_agent_manager, mock_pdf_agent
    ):
        """Test document upload when processing fails."""
        # Setup mocks
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_agent.return_value = mock_pdf_agent
        mock_agent_manager.is_agent_active.return_value = True
        mock_pdf_agent.process_document.return_value = {
            "success": False,
            "error": "Processing failed",
        }

        # Create test file
        test_file = b"test pdf content"

        # Make request
        response = client.post(
            "/v1/documents/upload",
            files={"file": ("test.pdf", test_file, "application/pdf")},
            data={"user_id": 1, "perform_ocr": True},
        )

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Document processing failed" in data["detail"]


class TestAgentManagement:
    """Test agent management endpoints."""

    @patch("app.api.documents.Container.agent_manager")
    def test_get_agent_status(self, mock_container, client, mock_agent_manager):
        """Test getting agent status."""
        # Setup mock
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_all_agents_metadata.return_value = {
            "pdf_processor": MagicMock(
                name="PDF Processor",
                description="PDF processing agent",
                status=MagicMock(value="active"),
                capabilities=["pdf_processing"],
                health_status="healthy",
                last_health_check=None,
                error_message=None,
            )
        }

        # Make request
        response = client.get("/v1/documents/agents/status")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "agents" in data
        assert "pdf_processor" in data["agents"]
        assert data["total_agents"] == 1

    @patch("app.api.documents.Container.agent_manager")
    def test_enable_agent_success(self, mock_container, client, mock_agent_manager):
        """Test enabling an agent successfully."""
        # Setup mock
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.enable_agent.return_value = True

        # Make request
        response = client.post("/v1/documents/agents/pdf_processor/enable")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "enabled successfully" in data["message"]

    @patch("app.api.documents.Container.agent_manager")
    def test_enable_agent_failure(self, mock_container, client, mock_agent_manager):
        """Test enabling an agent failure."""
        # Setup mock
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.enable_agent.return_value = False

        # Make request
        response = client.post("/v1/documents/agents/pdf_processor/enable")

        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Failed to enable" in data["detail"]

    @patch("app.api.documents.Container.agent_manager")
    def test_disable_agent_success(self, mock_container, client, mock_agent_manager):
        """Test disabling an agent successfully."""
        # Setup mock
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.disable_agent.return_value = True

        # Make request
        response = client.post("/v1/documents/agents/pdf_processor/disable")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "disabled successfully" in data["message"]

    @patch("app.api.documents.Container.agent_manager")
    def test_agent_health_check(self, mock_container, client, mock_agent_manager):
        """Test agent health check."""
        # Setup mock
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.health_check.return_value = True
        mock_agent_manager.get_agent_metadata.return_value = MagicMock(
            health_status="healthy",
            last_health_check=None,
            status=MagicMock(value="active"),
            error_message=None,
        )

        # Make request
        response = client.get("/v1/documents/agents/pdf_processor/health")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["agent_id"] == "pdf_processor"
        assert data["is_healthy"] is True
        assert data["health_status"] == "healthy"

    @patch("app.api.documents.Container.agent_manager")
    def test_agent_health_check_not_found(
        self, mock_container, client, mock_agent_manager
    ):
        """Test agent health check for non-existent agent."""
        # Setup mock
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.health_check.return_value = False
        mock_agent_manager.get_agent_metadata.return_value = None

        # Make request
        response = client.get("/v1/documents/agents/nonexistent/health")

        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"]


class TestDocumentRetrieval:
    """Test document retrieval endpoints."""

    @patch("app.api.documents.get_async_db")
    def test_get_client_documents(self, mock_db, client):
        """Test getting documents for a client."""
        # Mock database objects
        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        # Create mock document
        mock_document = MagicMock()
        mock_document.id = "doc-id"
        mock_document.filename = "test.pdf"
        mock_document.document_type = "pdf"
        mock_document.status = "processed"
        mock_document.formatted_file_size = "1.2 MB"
        mock_document.task_id = "task-123"
        mock_document.created_at.isoformat.return_value = "2023-01-01T00:00:00"
        mock_document.processed_at.isoformat.return_value = "2023-01-01T00:05:00"
        mock_document.error_message = None

        # Mock service
        with patch("app.api.documents.DocumentService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_documents_by_client.return_value = [mock_document]

            # Make request
            response = client.get(
                "/v1/documents/client/550e8400-e29b-41d4-a716-446655440000"
            )

            # Assertions
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["filename"] == "test.pdf"

    def test_get_client_documents_invalid_uuid(self, client):
        """Test getting documents with invalid client UUID."""
        response = client.get("/v1/documents/client/invalid-uuid")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid client ID format" in data["detail"]
