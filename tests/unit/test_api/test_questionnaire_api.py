"""Unit tests for questionnaire API endpoints with agent integration."""

import uuid
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
def mock_questionnaire_agent():
    """Mock questionnaire agent."""
    agent = AsyncMock()
    agent.generate_questionnaire.return_value = {
        "success": True,
        "questionnaire": "Generated questionnaire content",
        "context_chunks": 5,
        "client_name": "John Doe",
    }
    return agent


@pytest.fixture
def mock_client():
    """Mock client data."""
    client = MagicMock()
    client.id = uuid.uuid4()
    client.name = "John Doe"
    client.cpf = "123.456.789-00"
    return client


@pytest.fixture
def valid_questionnaire_request():
    """Valid questionnaire generation request data."""
    return {
        "client_id": str(uuid.uuid4()),
        "profession": "Software Developer",
        "disease": "RSI - Repetitive Strain Injury",
        "incident_date": "15/01/2023",
        "medical_date": "20/01/2023",
    }


class TestQuestionnaireGeneration:
    """Test questionnaire generation endpoint."""

    @patch("app.api.questionnaire.Container.agent_manager")
    @patch("app.api.questionnaire.get_async_db")
    def test_generate_questionnaire_success(
        self,
        mock_db,
        mock_container,
        client,
        mock_agent_manager,
        mock_questionnaire_agent,
        mock_client,
        valid_questionnaire_request,
    ):
        """Test successful questionnaire generation."""
        # Setup mocks
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_agent.return_value = mock_questionnaire_agent
        mock_agent_manager.is_agent_active.return_value = True

        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        # Mock client service
        with patch("app.api.questionnaire.ClientService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_client_by_id.return_value = mock_client

            # Make request
            response = client.post(
                "/v1/questionnaire/generate", json=valid_questionnaire_request
            )

            # Assertions
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["questionnaire"] == "Generated questionnaire content"
            assert data["context_chunks"] == 5
            assert data["client_name"] == "John Doe"
            assert data["error"] is None

    @patch("app.api.questionnaire.Container.agent_manager")
    @patch("app.api.questionnaire.get_async_db")
    def test_generate_questionnaire_client_not_found(
        self,
        mock_db,
        mock_container,
        client,
        mock_agent_manager,
        valid_questionnaire_request,
    ):
        """Test questionnaire generation when client is not found."""
        # Setup mocks
        mock_container.return_value = mock_agent_manager
        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        # Mock client service
        with patch("app.api.questionnaire.ClientService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_client_by_id.return_value = None

            # Make request
            response = client.post(
                "/v1/questionnaire/generate", json=valid_questionnaire_request
            )

            # Assertions
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "Client not found" in data["detail"]

    @patch("app.api.questionnaire.Container.agent_manager")
    @patch("app.api.questionnaire.get_async_db")
    def test_generate_questionnaire_agent_not_found(
        self,
        mock_db,
        mock_container,
        client,
        mock_agent_manager,
        mock_client,
        valid_questionnaire_request,
    ):
        """Test questionnaire generation when agent is not found."""
        # Setup mocks
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_agent.return_value = None

        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        # Mock client service
        with patch("app.api.questionnaire.ClientService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_client_by_id.return_value = mock_client

            # Make request
            response = client.post(
                "/v1/questionnaire/generate", json=valid_questionnaire_request
            )

            # Assertions
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] == "agent_not_found"
            assert data["agent_id"] == "questionnaire"

    @patch("app.api.questionnaire.Container.agent_manager")
    @patch("app.api.questionnaire.get_async_db")
    def test_generate_questionnaire_agent_not_active(
        self,
        mock_db,
        mock_container,
        client,
        mock_agent_manager,
        mock_questionnaire_agent,
        mock_client,
        valid_questionnaire_request,
    ):
        """Test questionnaire generation when agent is not active."""
        # Setup mocks
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_agent.return_value = mock_questionnaire_agent
        mock_agent_manager.is_agent_active.return_value = False

        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        # Mock client service
        with patch("app.api.questionnaire.ClientService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_client_by_id.return_value = mock_client

            # Make request
            response = client.post(
                "/v1/questionnaire/generate", json=valid_questionnaire_request
            )

            # Assertions
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert data["error"] == "agent_not_active"
            assert data["agent_id"] == "questionnaire"

    @patch("app.api.questionnaire.Container.agent_manager")
    @patch("app.api.questionnaire.get_async_db")
    def test_generate_questionnaire_processing_failure(
        self,
        mock_db,
        mock_container,
        client,
        mock_agent_manager,
        mock_questionnaire_agent,
        mock_client,
        valid_questionnaire_request,
    ):
        """Test questionnaire generation when processing fails."""
        # Setup mocks
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_agent.return_value = mock_questionnaire_agent
        mock_agent_manager.is_agent_active.return_value = True

        # Agent returns failure
        mock_questionnaire_agent.generate_questionnaire.return_value = {
            "success": False,
            "error": "Processing failed",
        }

        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        # Mock client service
        with patch("app.api.questionnaire.ClientService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_client_by_id.return_value = mock_client

            # Make request
            response = client.post(
                "/v1/questionnaire/generate", json=valid_questionnaire_request
            )

            # Assertions
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is False
            assert data["questionnaire"] == ""
            assert data["context_chunks"] == 0
            assert data["error"] == "Processing failed"

    def test_generate_questionnaire_invalid_request(self, client):
        """Test questionnaire generation with invalid request data."""
        invalid_request = {
            "client_id": "invalid-uuid",
            "profession": "",  # Too short
            "disease": "RSI",
            "incident_date": "invalid-date",  # Invalid format
            "medical_date": "20/01/2023",
        }

        response = client.post("/v1/questionnaire/generate", json=invalid_request)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_questionnaire_missing_fields(self, client):
        """Test questionnaire generation with missing required fields."""
        incomplete_request = {
            "client_id": str(uuid.uuid4()),
            "profession": "Software Developer",
            # Missing disease, incident_date, medical_date
        }

        response = client.post("/v1/questionnaire/generate", json=incomplete_request)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestClientDocumentsCheck:
    """Test client documents check endpoint."""

    @patch("app.api.questionnaire.get_async_db")
    def test_check_client_documents_has_documents(self, mock_db, client, mock_client):
        """Test checking client documents when client has documents."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        # Mock chunks
        mock_chunks = [
            MagicMock(document_id="doc1"),
            MagicMock(document_id="doc1"),  # Same document, different chunk
            MagicMock(document_id="doc2"),
        ]

        # Mock services
        with patch("app.api.questionnaire.ClientService") as mock_client_service:
            with patch(
                "app.api.questionnaire.DocumentChunkRepository"
            ) as mock_chunk_repo:
                mock_client_service.return_value.get_client_by_id.return_value = (
                    mock_client
                )
                mock_chunk_repo.return_value.get_chunks_by_client.return_value = (
                    mock_chunks
                )

                client_id = str(uuid.uuid4())
                response = client.get(
                    f"/v1/questionnaire/clients/{client_id}/has-documents"
                )

                # Assertions
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["has_documents"] is True
                assert data["document_count"] == 2  # Two unique documents
                assert data["chunk_count"] == 3  # Three chunks total

    @patch("app.api.questionnaire.get_async_db")
    def test_check_client_documents_no_documents(self, mock_db, client, mock_client):
        """Test checking client documents when client has no documents."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        # Mock services
        with patch("app.api.questionnaire.ClientService") as mock_client_service:
            with patch(
                "app.api.questionnaire.DocumentChunkRepository"
            ) as mock_chunk_repo:
                mock_client_service.return_value.get_client_by_id.return_value = (
                    mock_client
                )
                mock_chunk_repo.return_value.get_chunks_by_client.return_value = []

                client_id = str(uuid.uuid4())
                response = client.get(
                    f"/v1/questionnaire/clients/{client_id}/has-documents"
                )

                # Assertions
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["has_documents"] is False
                assert data["document_count"] == 0
                assert data["chunk_count"] == 0

    @patch("app.api.questionnaire.get_async_db")
    def test_check_client_documents_client_not_found(self, mock_db, client):
        """Test checking client documents when client is not found."""
        # Setup mocks
        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        # Mock service
        with patch("app.api.questionnaire.ClientService") as mock_client_service:
            mock_client_service.return_value.get_client_by_id.return_value = None

            client_id = str(uuid.uuid4())
            response = client.get(
                f"/v1/questionnaire/clients/{client_id}/has-documents"
            )

            # Assertions
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "Client not found" in data["detail"]

    def test_check_client_documents_invalid_uuid(self, client):
        """Test checking client documents with invalid UUID."""
        response = client.get("/v1/questionnaire/clients/invalid-uuid/has-documents")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRequestValidation:
    """Test request validation for questionnaire endpoints."""

    def test_questionnaire_request_validation_date_format(self, client):
        """Test date format validation."""
        request_data = {
            "client_id": str(uuid.uuid4()),
            "profession": "Software Developer",
            "disease": "RSI - Repetitive Strain Injury",
            "incident_date": "2023-01-15",  # Wrong format, should be dd/mm/yyyy
            "medical_date": "20/01/2023",
        }

        response = client.post("/v1/questionnaire/generate", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_questionnaire_request_validation_string_lengths(self, client):
        """Test string length validation."""
        request_data = {
            "client_id": str(uuid.uuid4()),
            "profession": "A",  # Too short (min 2)
            "disease": "A" * 201,  # Too long (max 200)
            "incident_date": "15/01/2023",
            "medical_date": "20/01/2023",
        }

        response = client.post("/v1/questionnaire/generate", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_questionnaire_request_validation_uuid_format(self, client):
        """Test UUID format validation."""
        request_data = {
            "client_id": "not-a-uuid",
            "profession": "Software Developer",
            "disease": "RSI - Repetitive Strain Injury",
            "incident_date": "15/01/2023",
            "medical_date": "20/01/2023",
        }

        response = client.post("/v1/questionnaire/generate", json=request_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
