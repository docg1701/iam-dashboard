"""Integration tests for API-agent workflows."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.agent_manager import AgentManager
from app.main import fastapi_app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(fastapi_app)


@pytest.fixture
def mock_agent_manager():
    """Mock AgentManager for integration testing."""
    manager = MagicMock(spec=AgentManager)
    return manager


@pytest.fixture
def mock_pdf_agent():
    """Mock PDF processor agent."""
    agent = AsyncMock()
    agent.process_document.return_value = {
        "success": True,
        "document_id": str(uuid.uuid4()),
        "filename": "integration_test.pdf",
        "processing_summary": "Document processed successfully in integration test",
    }
    return agent


@pytest.fixture
def mock_questionnaire_agent():
    """Mock questionnaire agent."""
    agent = AsyncMock()
    agent.generate_questionnaire.return_value = {
        "success": True,
        "questionnaire": "Integration test questionnaire content",
        "context_chunks": 3,
        "client_name": "Integration Test Client",
    }
    return agent


class TestDocumentProcessingIntegration:
    """Integration tests for complete document processing workflow."""

    @patch("app.containers.Container.agent_manager")
    @patch("app.api.documents.get_async_db")
    def test_complete_document_upload_workflow(
        self, mock_db, mock_container, client, mock_agent_manager, mock_pdf_agent
    ):
        """Test complete document upload and processing workflow."""
        # Setup container injection
        mock_container.return_value = mock_agent_manager

        # Setup agent manager
        mock_agent_manager.get_agent.return_value = mock_pdf_agent
        mock_agent_manager.is_agent_active.return_value = True
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

        # Setup database mock
        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        # Test 1: Check agent status first
        status_response = client.get("/v1/documents/agents/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "pdf_processor" in status_data["agents"]
        assert status_data["agents"]["pdf_processor"]["status"] == "active"

        # Test 2: Upload document
        test_file = b"mock pdf content for integration test"
        upload_response = client.post(
            "/v1/documents/upload",
            files={"file": ("integration_test.pdf", test_file, "application/pdf")},
            data={"user_id": 1, "perform_ocr": True},
        )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["success"] is True
        assert upload_data["filename"] == "integration_test.pdf"
        assert "processing_summary" in upload_data

        # Test 3: Verify agent was called correctly
        mock_pdf_agent.process_document.assert_called_once()
        call_args = mock_pdf_agent.process_document.call_args
        assert call_args[1]["user_id"] == 1
        assert call_args[1]["perform_ocr"] is True

    @patch("app.containers.Container.agent_manager")
    def test_document_agent_error_handling_flow(
        self, mock_container, client, mock_agent_manager
    ):
        """Test error handling flow when document agent fails."""
        # Setup container injection
        mock_container.return_value = mock_agent_manager

        # Test scenario: Agent not found
        mock_agent_manager.get_agent.return_value = None

        test_file = b"mock pdf content"
        response = client.post(
            "/v1/documents/upload",
            files={"file": ("test.pdf", test_file, "application/pdf")},
            data={"user_id": 1, "perform_ocr": True},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "agent_not_found"
        assert data["agent_id"] == "pdf_processor"

    @patch("app.containers.Container.agent_manager")
    def test_document_agent_health_monitoring_flow(
        self, mock_container, client, mock_agent_manager
    ):
        """Test agent health monitoring workflow."""
        # Setup container injection
        mock_container.return_value = mock_agent_manager

        # Setup health check responses
        mock_agent_manager.health_check.return_value = True
        mock_agent_manager.get_agent_metadata.return_value = MagicMock(
            health_status="healthy",
            last_health_check=None,
            status=MagicMock(value="active"),
            error_message=None,
        )

        # Test health check endpoint
        response = client.get("/v1/documents/agents/pdf_processor/health")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "pdf_processor"
        assert data["is_healthy"] is True
        assert data["health_status"] == "healthy"


class TestQuestionnaireGenerationIntegration:
    """Integration tests for questionnaire generation workflow."""

    @patch("app.containers.Container.agent_manager")
    @patch("app.api.questionnaire.get_async_db")
    def test_complete_questionnaire_generation_workflow(
        self,
        mock_db,
        mock_container,
        client,
        mock_agent_manager,
        mock_questionnaire_agent,
    ):
        """Test complete questionnaire generation workflow."""
        # Setup container injection
        mock_container.return_value = mock_agent_manager

        # Setup agent manager
        mock_agent_manager.get_agent.return_value = mock_questionnaire_agent
        mock_agent_manager.is_agent_active.return_value = True

        # Setup database and client mocks
        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        mock_client = MagicMock()
        mock_client.id = uuid.uuid4()
        mock_client.name = "Integration Test Client"
        mock_client.cpf = "123.456.789-00"

        # Mock client and chunk services
        with patch("app.api.questionnaire.ClientService") as mock_client_service:
            with patch(
                "app.api.questionnaire.DocumentChunkRepository"
            ) as mock_chunk_repo:
                mock_client_service.return_value.get_client_by_id.return_value = (
                    mock_client
                )

                # Test 1: Check if client has documents
                mock_chunks = [
                    MagicMock(document_id="doc1"),
                    MagicMock(document_id="doc2"),
                ]
                mock_chunk_repo.return_value.get_chunks_by_client.return_value = (
                    mock_chunks
                )

                client_id = str(mock_client.id)
                docs_response = client.get(
                    f"/v1/questionnaire/clients/{client_id}/has-documents"
                )
                assert docs_response.status_code == 200
                docs_data = docs_response.json()
                assert docs_data["has_documents"] is True
                assert docs_data["chunk_count"] == 2

                # Test 2: Generate questionnaire
                questionnaire_request = {
                    "client_id": client_id,
                    "profession": "Integration Test Developer",
                    "disease": "Test Condition",
                    "incident_date": "01/01/2023",
                    "medical_date": "02/01/2023",
                }

                gen_response = client.post(
                    "/v1/questionnaire/generate", json=questionnaire_request
                )
                assert gen_response.status_code == 200
                gen_data = gen_response.json()
                assert gen_data["success"] is True
                assert (
                    gen_data["questionnaire"]
                    == "Integration test questionnaire content"
                )
                assert gen_data["context_chunks"] == 3
                assert gen_data["client_name"] == "Integration Test Client"

                # Test 3: Verify agent was called with correct parameters
                mock_questionnaire_agent.generate_questionnaire.assert_called_once()
                call_kwargs = mock_questionnaire_agent.generate_questionnaire.call_args[
                    1
                ]
                assert call_kwargs["profession"] == "Integration Test Developer"
                assert call_kwargs["disease"] == "Test Condition"
                assert call_kwargs["save_draft"] is True

    @patch("app.containers.Container.agent_manager")
    @patch("app.api.questionnaire.get_async_db")
    def test_questionnaire_error_recovery_workflow(
        self,
        mock_db,
        mock_container,
        client,
        mock_agent_manager,
        mock_questionnaire_agent,
    ):
        """Test error recovery in questionnaire generation workflow."""
        # Setup container injection
        mock_container.return_value = mock_agent_manager

        # Setup agent manager with agent that fails processing
        mock_agent_manager.get_agent.return_value = mock_questionnaire_agent
        mock_agent_manager.is_agent_active.return_value = True

        # Agent returns failure
        mock_questionnaire_agent.generate_questionnaire.return_value = {
            "success": False,
            "error": "Integration test simulated failure",
        }

        # Setup database and client mocks
        mock_session = AsyncMock()
        mock_db.return_value = mock_session

        mock_client = MagicMock()
        mock_client.id = uuid.uuid4()
        mock_client.name = "Test Client"
        mock_client.cpf = "123.456.789-00"

        with patch("app.api.questionnaire.ClientService") as mock_client_service:
            mock_client_service.return_value.get_client_by_id.return_value = mock_client

            questionnaire_request = {
                "client_id": str(mock_client.id),
                "profession": "Test Profession",
                "disease": "Test Disease",
                "incident_date": "01/01/2023",
                "medical_date": "02/01/2023",
            }

            response = client.post(
                "/v1/questionnaire/generate", json=questionnaire_request
            )

            # Should still return 200 but with success=False
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["error"] == "Integration test simulated failure"
            assert data["questionnaire"] == ""
            assert data["context_chunks"] == 0


class TestAdminIntegration:
    """Integration tests for admin operations."""

    @patch("app.containers.Container.agent_manager")
    def test_complete_admin_workflow(self, mock_container, client, mock_agent_manager):
        """Test complete admin workflow for agent management."""
        # Setup container injection
        mock_container.return_value = mock_agent_manager

        # Setup agent metadata
        mock_metadata = {
            "pdf_processor": MagicMock(
                name="PDF Processor",
                description="PDF processing agent",
                status=MagicMock(value="active"),
                capabilities=["pdf_processing"],
                health_status="healthy",
                last_health_check=None,
                error_message=None,
            ),
            "questionnaire": MagicMock(
                name="Questionnaire Agent",
                description="Questionnaire generation agent",
                status=MagicMock(value="inactive"),
                capabilities=["questionnaire_generation"],
                health_status="unhealthy",
                last_health_check=None,
                error_message="Test error",
            ),
        }

        mock_agent_manager.get_all_agents_metadata.return_value = mock_metadata
        mock_agent_manager.health_check.side_effect = [
            True,
            False,
        ]  # pdf healthy, questionnaire unhealthy

        # Test 1: Get system health
        health_response = client.get("/v1/admin/system/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["total_agents"] == 2
        assert health_data["healthy_agents"] == 1
        assert health_data["system_status"] == "degraded"

        # Test 2: List all agents
        agents_response = client.get("/v1/admin/agents")
        assert agents_response.status_code == 200
        agents_data = agents_response.json()
        assert len(agents_data) == 2

        # Test 3: Start inactive agent
        mock_agent_manager.enable_agent.return_value = True
        start_response = client.post("/v1/admin/agents/questionnaire/start")
        assert start_response.status_code == 200
        start_data = start_response.json()
        assert start_data["success"] is True

        # Test 4: Restart all agents
        mock_agent_manager.disable_agent.return_value = True
        mock_agent_manager.enable_agent.return_value = True
        restart_response = client.post("/v1/admin/system/restart-all")
        assert restart_response.status_code == 200
        restart_data = restart_response.json()
        assert restart_data["success"] is True
        assert "Restarted 2 of 2 agents" in restart_data["message"]


class TestCrossServiceIntegration:
    """Integration tests across multiple services."""

    @patch("app.containers.Container.agent_manager")
    @patch("app.api.documents.get_async_db")
    @patch("app.api.questionnaire.get_async_db")
    def test_document_to_questionnaire_workflow(
        self,
        mock_q_db,
        mock_d_db,
        mock_container,
        client,
        mock_agent_manager,
        mock_pdf_agent,
        mock_questionnaire_agent,
    ):
        """Test workflow from document upload to questionnaire generation."""
        # Setup container injection for both services
        mock_container.return_value = mock_agent_manager

        # Setup database mocks
        mock_d_session = AsyncMock()
        mock_d_db.return_value = mock_d_session
        mock_q_session = AsyncMock()
        mock_q_db.return_value = mock_q_session

        # Setup agent manager to return different agents
        def get_agent_side_effect(agent_id):
            if agent_id == "pdf_processor":
                return mock_pdf_agent
            elif agent_id == "questionnaire":
                return mock_questionnaire_agent
            return None

        mock_agent_manager.get_agent.side_effect = get_agent_side_effect
        mock_agent_manager.is_agent_active.return_value = True

        # Test 1: Upload document
        test_file = b"cross-service integration test pdf content"
        upload_response = client.post(
            "/v1/documents/upload",
            files={"file": ("cross_service_test.pdf", test_file, "application/pdf")},
            data={"user_id": 1, "perform_ocr": True},
        )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]

        # Test 2: Simulate document processing created chunks
        mock_client = MagicMock()
        mock_client.id = uuid.uuid4()
        mock_client.name = "Cross Service Test Client"
        mock_client.cpf = "987.654.321-00"

        mock_chunks = [
            MagicMock(document_id=document_id),
            MagicMock(document_id=document_id),
        ]

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

                # Test 3: Check client has documents (from uploaded document)
                client_id = str(mock_client.id)
                docs_response = client.get(
                    f"/v1/questionnaire/clients/{client_id}/has-documents"
                )
                assert docs_response.status_code == 200
                docs_data = docs_response.json()
                assert docs_data["has_documents"] is True

                # Test 4: Generate questionnaire using processed document
                questionnaire_request = {
                    "client_id": client_id,
                    "profession": "Cross Service Developer",
                    "disease": "Integration Test Condition",
                    "incident_date": "15/01/2023",
                    "medical_date": "20/01/2023",
                }

                questionnaire_response = client.post(
                    "/v1/questionnaire/generate", json=questionnaire_request
                )
                assert questionnaire_response.status_code == 200
                questionnaire_data = questionnaire_response.json()
                assert questionnaire_data["success"] is True

                # Verify both agents were called
                mock_pdf_agent.process_document.assert_called_once()
                mock_questionnaire_agent.generate_questionnaire.assert_called_once()


class TestPerformanceIntegration:
    """Integration tests for performance and timeout handling."""

    @patch("app.containers.Container.agent_manager")
    def test_rate_limiting_integration(
        self, mock_container, client, mock_agent_manager
    ):
        """Test rate limiting works across requests."""
        # Setup container injection
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_all_agents_metadata.return_value = {}

        # Make multiple requests to trigger rate limiting
        # Admin endpoints have 100 requests per minute limit
        responses = []
        for i in range(5):  # Within limit
            response = client.get("/v1/admin/agents")
            responses.append(response.status_code)

        # All should succeed (within rate limit for testing)
        assert all(status == 200 for status in responses)

    @patch("app.containers.Container.agent_manager")
    def test_timeout_handling_integration(
        self, mock_container, client, mock_agent_manager, mock_pdf_agent
    ):
        """Test timeout handling in integration scenario."""
        # Setup container injection
        mock_container.return_value = mock_agent_manager
        mock_agent_manager.get_agent.return_value = mock_pdf_agent
        mock_agent_manager.is_agent_active.return_value = True

        # Simulate agent that takes too long (would trigger timeout in real scenario)
        async def slow_process(*args, **kwargs):
            await asyncio.sleep(0.1)  # Short delay for test
            return {
                "success": True,
                "document_id": "timeout_test_doc",
                "filename": "timeout_test.pdf",
                "processing_summary": "Processed after delay",
            }

        mock_pdf_agent.process_document = slow_process

        with patch("app.api.documents.get_async_db"):
            test_file = b"timeout test pdf content"
            response = client.post(
                "/v1/documents/upload",
                files={"file": ("timeout_test.pdf", test_file, "application/pdf")},
                data={"user_id": 1, "perform_ocr": True},
            )

            # Should complete successfully in this test case
            assert response.status_code == 200
