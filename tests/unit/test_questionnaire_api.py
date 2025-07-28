"""Unit tests for Questionnaire API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import fastapi_app
from app.models.client import Client
from app.models.document_chunk import DocumentChunk


class TestQuestionnaireAPI:
    """Test suite for Questionnaire API endpoints."""

    @pytest.fixture
    def test_client(self):
        """FastAPI test client."""
        return TestClient(fastapi_app)

    @pytest.fixture
    def mock_client(self):
        """Mock Client instance."""
        client = MagicMock(spec=Client)
        client.id = uuid.uuid4()
        client.name = "Ana Costa"
        client.formatted_cpf = "111.222.333-44"
        return client

    @pytest.fixture
    def mock_chunks(self):
        """Mock DocumentChunk list."""
        chunks = []
        for i in range(2):
            chunk = MagicMock(spec=DocumentChunk)
            chunk.id = uuid.uuid4()
            chunk.document_id = uuid.uuid4()
            chunk.text = f"Document chunk {i+1}"
            chunks.append(chunk)
        return chunks

    @pytest.fixture
    def valid_generate_request(self, mock_client):
        """Valid questionnaire generation request."""
        return {
            "client_id": str(mock_client.id),
            "profession": "Fisioterapeuta",
            "disease": "Tendinite",
            "incident_date": "15/06/2024",
            "medical_date": "16/06/2024"
        }

    def test_generate_questionnaire_success(self, test_client, mock_client, valid_generate_request):
        """Test successful questionnaire generation endpoint."""
        with pytest.MonkeyPatch().context() as mp:
            # Mock dependencies
            mock_client_service = AsyncMock()
            mock_client_service.get_client_by_id.return_value = mock_client

            mock_questionnaire_service = AsyncMock()
            mock_questionnaire_service.generate_questionnaire.return_value = {
                "success": True,
                "questionnaire": "Generated questionnaire content",
                "context_chunks": 3,
                "client_name": "Ana Costa"
            }

            # Mock the dependency injection
            def mock_get_db():
                yield AsyncMock()

            def mock_client_repo(db):
                return AsyncMock()

            def mock_chunk_repo(db):
                return AsyncMock()

            def mock_client_service_factory(repo):
                return mock_client_service

            def mock_questionnaire_service_factory(repo):
                return mock_questionnaire_service

            mp.setattr("app.api.questionnaire.get_async_db", mock_get_db)
            mp.setattr("app.api.questionnaire.ClientRepository", mock_client_repo)
            mp.setattr("app.api.questionnaire.DocumentChunkRepository", mock_chunk_repo)
            mp.setattr("app.api.questionnaire.ClientService", mock_client_service_factory)
            mp.setattr("app.api.questionnaire.get_questionnaire_draft_service", mock_questionnaire_service_factory)

            # Act
            response = test_client.post("/v1/questionnaire/generate", json=valid_generate_request)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["questionnaire"] == "Generated questionnaire content"
            assert data["context_chunks"] == 3
            assert data["client_name"] == "Ana Costa"
            assert "error" not in data or data["error"] is None

    def test_generate_questionnaire_client_not_found(self, test_client, valid_generate_request):
        """Test questionnaire generation when client is not found."""
        with pytest.MonkeyPatch().context() as mp:
            # Mock dependencies
            mock_client_service = AsyncMock()
            mock_client_service.get_client_by_id.return_value = None

            # Mock the dependency injection
            def mock_get_db():
                yield AsyncMock()

            def mock_client_repo(db):
                return AsyncMock()

            def mock_client_service_factory(repo):
                return mock_client_service

            mp.setattr("app.api.questionnaire.get_async_db", mock_get_db)
            mp.setattr("app.api.questionnaire.ClientRepository", mock_client_repo)
            mp.setattr("app.api.questionnaire.ClientService", mock_client_service_factory)

            # Act
            response = test_client.post("/v1/questionnaire/generate", json=valid_generate_request)

            # Assert
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Client not found"

    def test_generate_questionnaire_service_failure(self, test_client, mock_client, valid_generate_request):
        """Test questionnaire generation when service returns failure."""
        with pytest.MonkeyPatch().context() as mp:
            # Mock dependencies
            mock_client_service = AsyncMock()
            mock_client_service.get_client_by_id.return_value = mock_client

            mock_questionnaire_service = AsyncMock()
            mock_questionnaire_service.generate_questionnaire.return_value = {
                "success": False,
                "error": "Service error occurred",
                "questionnaire": "",
                "context_chunks": 0,
                "client_name": "Ana Costa"
            }

            # Mock the dependency injection
            def mock_get_db():
                yield AsyncMock()

            def mock_client_repo(db):
                return AsyncMock()

            def mock_chunk_repo(db):
                return AsyncMock()

            def mock_client_service_factory(repo):
                return mock_client_service

            def mock_questionnaire_service_factory(repo):
                return mock_questionnaire_service

            mp.setattr("app.api.questionnaire.get_async_db", mock_get_db)
            mp.setattr("app.api.questionnaire.ClientRepository", mock_client_repo)
            mp.setattr("app.api.questionnaire.DocumentChunkRepository", mock_chunk_repo)
            mp.setattr("app.api.questionnaire.ClientService", mock_client_service_factory)
            mp.setattr("app.api.questionnaire.get_questionnaire_draft_service", mock_questionnaire_service_factory)

            # Act
            response = test_client.post("/v1/questionnaire/generate", json=valid_generate_request)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["error"] == "Service error occurred"
            assert data["questionnaire"] == ""
            assert data["context_chunks"] == 0

    def test_generate_questionnaire_invalid_request(self, test_client):
        """Test questionnaire generation with invalid request data."""
        invalid_request = {
            "client_id": "invalid-uuid",
            "profession": "",  # Empty profession
            "disease": "Test disease",
            "incident_date": "invalid-date",  # Invalid date format
            "medical_date": "16/06/2024"
        }

        # Act
        response = test_client.post("/v1/questionnaire/generate", json=invalid_request)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_generate_questionnaire_missing_fields(self, test_client):
        """Test questionnaire generation with missing required fields."""
        incomplete_request = {
            "client_id": str(uuid.uuid4()),
            "profession": "Dentista"
            # Missing disease, incident_date, medical_date
        }

        # Act
        response = test_client.post("/v1/questionnaire/generate", json=incomplete_request)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_check_client_documents_success(self, test_client, mock_client, mock_chunks):
        """Test successful client documents check."""
        with pytest.MonkeyPatch().context() as mp:
            # Mock dependencies
            mock_client_service = AsyncMock()
            mock_client_service.get_client_by_id.return_value = mock_client

            mock_chunk_repository = AsyncMock()
            mock_chunk_repository.get_chunks_by_client.return_value = mock_chunks

            # Mock the dependency injection
            def mock_get_db():
                yield AsyncMock()

            def mock_client_repo(db):
                return AsyncMock()

            def mock_chunk_repo(db):
                return mock_chunk_repository

            def mock_client_service_factory(repo):
                return mock_client_service

            mp.setattr("app.api.questionnaire.get_async_db", mock_get_db)
            mp.setattr("app.api.questionnaire.ClientRepository", mock_client_repo)
            mp.setattr("app.api.questionnaire.DocumentChunkRepository", mock_chunk_repo)
            mp.setattr("app.api.questionnaire.ClientService", mock_client_service_factory)

            # Act
            response = test_client.get(f"/v1/questionnaire/clients/{mock_client.id}/has-documents")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["has_documents"] is True
            assert data["document_count"] == 2  # 2 unique document IDs
            assert data["chunk_count"] == 2

    def test_check_client_documents_no_documents(self, test_client, mock_client):
        """Test client documents check when client has no documents."""
        with pytest.MonkeyPatch().context() as mp:
            # Mock dependencies
            mock_client_service = AsyncMock()
            mock_client_service.get_client_by_id.return_value = mock_client

            mock_chunk_repository = AsyncMock()
            mock_chunk_repository.get_chunks_by_client.return_value = []

            # Mock the dependency injection
            def mock_get_db():
                yield AsyncMock()

            def mock_client_repo(db):
                return AsyncMock()

            def mock_chunk_repo(db):
                return mock_chunk_repository

            def mock_client_service_factory(repo):
                return mock_client_service

            mp.setattr("app.api.questionnaire.get_async_db", mock_get_db)
            mp.setattr("app.api.questionnaire.ClientRepository", mock_client_repo)
            mp.setattr("app.api.questionnaire.DocumentChunkRepository", mock_chunk_repo)
            mp.setattr("app.api.questionnaire.ClientService", mock_client_service_factory)

            # Act
            response = test_client.get(f"/v1/questionnaire/clients/{mock_client.id}/has-documents")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["has_documents"] is False
            assert data["document_count"] == 0
            assert data["chunk_count"] == 0

    def test_check_client_documents_client_not_found(self, test_client):
        """Test client documents check when client is not found."""
        with pytest.MonkeyPatch().context() as mp:
            # Mock dependencies
            mock_client_service = AsyncMock()
            mock_client_service.get_client_by_id.return_value = None

            # Mock the dependency injection
            def mock_get_db():
                yield AsyncMock()

            def mock_client_repo(db):
                return AsyncMock()

            def mock_client_service_factory(repo):
                return mock_client_service

            mp.setattr("app.api.questionnaire.get_async_db", mock_get_db)
            mp.setattr("app.api.questionnaire.ClientRepository", mock_client_repo)
            mp.setattr("app.api.questionnaire.ClientService", mock_client_service_factory)

            # Act
            client_id = uuid.uuid4()
            response = test_client.get(f"/v1/questionnaire/clients/{client_id}/has-documents")

            # Assert
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Client not found"

    def test_check_client_documents_invalid_uuid(self, test_client):
        """Test client documents check with invalid UUID."""
        # Act
        response = test_client.get("/v1/questionnaire/clients/invalid-uuid/has-documents")

        # Assert
        assert response.status_code == 422  # Validation error

    def test_date_format_validation(self, test_client, mock_client):
        """Test date format validation in request model."""
        # Valid date formats
        valid_dates = ["01/01/2024", "31/12/2023", "15/06/2024"]
        
        # Invalid date formats
        invalid_dates = ["2024-01-01", "01-01-2024", "1/1/24", "01/1/2024", "1/01/2024"]

        base_request = {
            "client_id": str(mock_client.id),
            "profession": "Médico",
            "disease": "Test disease"
        }

        # Test valid dates
        for valid_date in valid_dates:
            request_data = {
                **base_request,
                "incident_date": valid_date,
                "medical_date": valid_date
            }
            
            with pytest.MonkeyPatch().context() as mp:
                # Mock to avoid actual processing
                def mock_get_db():
                    yield AsyncMock()
                mp.setattr("app.api.questionnaire.get_async_db", mock_get_db)
                
                response = test_client.post("/v1/questionnaire/generate", json=request_data)
                # Should not fail validation (might fail later due to missing client, but not validation)
                assert response.status_code != 422

        # Test invalid dates
        for invalid_date in invalid_dates:
            request_data = {
                **base_request,
                "incident_date": invalid_date,
                "medical_date": "01/01/2024"  # Keep one valid
            }
            
            response = test_client.post("/v1/questionnaire/generate", json=request_data)
            assert response.status_code == 422  # Validation error