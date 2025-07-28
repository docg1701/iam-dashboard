"""Unit tests for QuestionnaireAgent."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.questionnaire_agent import QuestionnaireAgent, QuestionnairePlugin
from app.models.client import Client


class TestQuestionnaireAgent:
    """Test suite for QuestionnaireAgent."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        return Client(
            id=uuid.uuid4(),
            name="Test Client",
            cpf="12345678901"
        )

    @pytest.fixture
    def agent_config(self):
        """Configuration for test agent."""
        return {
            "model": "gemini-1.5-pro",
            "gemini_api_key": "test_api_key",
            "similarity_top_k": 5,
            "min_context_chunks": 1,
            "max_context_chunks": 10
        }

    @pytest.fixture
    def questionnaire_agent(self, agent_config):
        """Create QuestionnaireAgent instance for testing."""
        with patch('app.agents.questionnaire_agent.get_async_db'), \
             patch('app.tools.rag_tools.get_llama_index_config'), \
             patch('google.generativeai.configure'):
            agent = QuestionnaireAgent(**agent_config)
            return agent

    def test_agent_initialization(self, agent_config):
        """Test agent initialization."""
        with patch('app.agents.questionnaire_agent.get_async_db'), \
             patch('app.tools.rag_tools.get_llama_index_config'), \
             patch('google.generativeai.configure'):
            agent = QuestionnaireAgent(**agent_config)

            assert agent.similarity_top_k == 5
            assert agent.min_context_chunks == 1
            assert agent.max_context_chunks == 10
            assert hasattr(agent, 'rag_retriever')
            assert hasattr(agent, 'llm_processor')
            assert hasattr(agent, 'template_manager')

    @pytest.mark.asyncio
    @patch('app.agents.questionnaire_agent.get_async_db')
    @patch('app.repositories.document_chunk_repository.DocumentChunkRepository')
    async def test_retrieve_client_context_success(self, mock_repo_class, mock_get_db, questionnaire_agent):
        """Test successful context retrieval."""
        # Mock database and repository
        mock_db = MagicMock()
        
        async def mock_async_db_generator():
            yield mock_db
        
        mock_get_db.return_value = mock_async_db_generator()

        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Mock RAG retriever
        mock_rag_result = {
            "success": True,
            "context_chunks": [
                {"text": "Test context 1", "score": 0.9},
                {"text": "Test context 2", "score": 0.8}
            ],
            "total_chunks": 2,
            "query_text": "test query",
            "client_id": "550e8400-e29b-41d4-a716-446655440000"
        }

        questionnaire_agent.rag_retriever.retrieve_client_context = MagicMock(
            return_value=mock_rag_result
        )

        # Test context retrieval
        result = await questionnaire_agent.retrieve_client_context(
            client_id="550e8400-e29b-41d4-a716-446655440000",
            profession="Engineer",
            disease="Back pain",
            incident_date="01/01/2023"
        )

        assert result["success"] is True
        assert len(result["context_chunks"]) == 2
        assert result["total_chunks"] == 2

    @pytest.mark.asyncio
    @patch('app.agents.questionnaire_agent.get_async_db')
    async def test_retrieve_client_context_failure(self, mock_get_db, questionnaire_agent):
        """Test context retrieval failure."""
        # Mock database error
        mock_get_db.side_effect = Exception("Database error")

        # Test context retrieval
        result = await questionnaire_agent.retrieve_client_context(
            client_id="550e8400-e29b-41d4-a716-446655440000",
            profession="Engineer",
            disease="Back pain",
            incident_date="01/01/2023"
        )

        assert result["success"] is False
        assert "error" in result
        assert result["context_chunks"] == []

    def test_generate_questionnaire_content_success(self, questionnaire_agent, mock_client):
        """Test successful questionnaire content generation."""
        # Mock LLM processor
        mock_llm_result = {
            "success": True,
            "questionnaire": "Test questionnaire content",
            "context_chunks_used": 2,
            "model_used": "gemini-1.5-pro",
            "client_name": "Test Client",
            "has_context": True
        }

        questionnaire_agent.llm_processor.generate_questionnaire = MagicMock(
            return_value=mock_llm_result
        )

        # Prepare test data
        client_data = {
            "id": str(mock_client.id),
            "name": mock_client.name,
            "cpf": mock_client.cpf
        }
        case_data = {
            "profession": "Engineer",
            "disease": "Back pain",
            "incident_date": "01/01/2023",
            "medical_date": "02/01/2023"
        }
        context_chunks = [{"text": "Test context", "score": 0.9}]

        # Test content generation
        result = questionnaire_agent.generate_questionnaire_content(
            client_data=client_data,
            case_data=case_data,
            context_chunks=context_chunks
        )

        assert result["success"] is True
        assert result["questionnaire"] == "Test questionnaire content"
        assert result["context_chunks_used"] == 2

    def test_generate_questionnaire_content_failure(self, questionnaire_agent):
        """Test questionnaire content generation failure."""
        # Mock LLM processor failure
        questionnaire_agent.llm_processor.generate_questionnaire = MagicMock(
            side_effect=Exception("LLM error")
        )

        # Prepare test data
        client_data = {
            "id": str(uuid.uuid4()),
            "name": "Test Client",
            "cpf": "12345678901"
        }
        case_data = {
            "profession": "Engineer",
            "disease": "Back pain",
            "incident_date": "01/01/2023",
            "medical_date": "02/01/2023"
        }

        # Test content generation
        result = questionnaire_agent.generate_questionnaire_content(
            client_data=client_data,
            case_data=case_data,
            context_chunks=[]
        )

        assert result["success"] is False
        assert "error" in result
        assert result["questionnaire"] == ""

    def test_apply_legal_formatting_success(self, questionnaire_agent, mock_client):
        """Test successful legal formatting application."""
        # Mock template manager
        mock_template_result = {
            "success": True,
            "template": {"name": "medical_examination", "formatting_rules": []}
        }
        mock_formatting_result = {
            "success": True,
            "formatted_questionnaire": "Formatted questionnaire content",
            "template_applied": "medical_examination"
        }

        questionnaire_agent.template_manager.get_questionnaire_template = MagicMock(
            return_value=mock_template_result
        )
        questionnaire_agent.template_manager.apply_template_formatting = MagicMock(
            return_value=mock_formatting_result
        )

        # Prepare test data
        client_data = {
            "id": str(mock_client.id),
            "name": mock_client.name,
            "cpf": mock_client.cpf
        }
        case_data = {
            "profession": "Engineer",
            "disease": "Back pain",
            "incident_date": "01/01/2023",
            "medical_date": "02/01/2023"
        }

        # Test formatting application
        result = questionnaire_agent.apply_legal_formatting(
            questionnaire_text="Raw questionnaire text",
            client_data=client_data,
            case_data=case_data
        )

        assert result["success"] is True
        assert result["formatted_questionnaire"] == "Formatted questionnaire content"
        assert result["template_applied"] == "medical_examination"

    def test_validate_questionnaire_success(self, questionnaire_agent):
        """Test successful questionnaire validation."""
        # Mock template manager
        mock_template_result = {
            "success": True,
            "template": {"name": "medical_examination", "validation_rules": []}
        }
        mock_validation_result = {
            "success": True,
            "validation_results": {
                "is_valid": True,
                "errors": [],
                "warnings": []
            }
        }

        questionnaire_agent.template_manager.get_questionnaire_template = MagicMock(
            return_value=mock_template_result
        )
        questionnaire_agent.template_manager.validate_questionnaire_format = MagicMock(
            return_value=mock_validation_result
        )

        # Test validation
        result = questionnaire_agent.validate_questionnaire(
            questionnaire_text="Valid questionnaire text"
        )

        assert result["success"] is True
        assert result["validation_results"]["is_valid"] is True

    @pytest.mark.asyncio
    @patch('app.agents.questionnaire_agent.get_async_db')
    @patch('app.models.questionnaire_draft.QuestionnaireDraft')
    async def test_save_questionnaire_draft_success(self, mock_draft_class, mock_get_db, questionnaire_agent):
        """Test successful questionnaire draft saving."""
        # Mock database
        mock_db = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        async def mock_async_db_generator():
            yield mock_db
        
        mock_get_db.return_value = mock_async_db_generator()

        # Mock draft instance
        mock_draft = MagicMock()
        mock_draft.id = 123
        mock_draft.created_at = datetime.now(timezone.utc)
        mock_draft_class.return_value = mock_draft

        # Test draft saving
        result = await questionnaire_agent.save_questionnaire_draft(
            questionnaire_text="Test questionnaire",
            client_id=str(uuid.uuid4()),
            case_data={
                "profession": "Engineer",
                "disease": "Back pain",
                "incident_date": "01/01/2023",
                "medical_date": "02/01/2023"
            },
            metadata={"test": "data"}
        )

        assert result["success"] is True
        assert result["draft_id"] == 123
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_questionnaire_workflow_success(self, questionnaire_agent, mock_client):
        """Test complete questionnaire generation workflow."""
        # Mock all tools (need AsyncMock for async methods)
        questionnaire_agent.retrieve_client_context = AsyncMock(
            return_value={
                "success": True,
                "context_chunks": [{"text": "Test context", "score": 0.9}]
            }
        )

        questionnaire_agent.generate_questionnaire_content = MagicMock(
            return_value={
                "success": True,
                "questionnaire": "Generated questionnaire",
                "model_used": "gemini-1.5-pro"
            }
        )

        questionnaire_agent.apply_legal_formatting = MagicMock(
            return_value={
                "success": True,
                "formatted_questionnaire": "Formatted questionnaire",
                "template_applied": "medical_examination"
            }
        )

        questionnaire_agent.validate_questionnaire = MagicMock(
            return_value={
                "success": True,
                "validation_results": {"is_valid": True}
            }
        )

        questionnaire_agent.save_questionnaire_draft = AsyncMock(
            return_value={
                "success": True,
                "draft_id": 123
            }
        )

        # Test workflow
        result = await questionnaire_agent.generate_questionnaire(
            client=mock_client,
            profession="Engineer",
            disease="Back pain",
            incident_date="01/01/2023",
            medical_date="02/01/2023"
        )

        assert result["success"] is True
        assert result["questionnaire"] == "Formatted questionnaire"
        assert result["client_name"] == mock_client.name
        assert result["processing_summary"]["draft_saved"] is True

    @pytest.mark.asyncio
    async def test_generate_questionnaire_workflow_failure(self, questionnaire_agent, mock_client):
        """Test questionnaire generation workflow with failure."""
        # Mock context retrieval failure
        questionnaire_agent.retrieve_client_context = MagicMock(
            side_effect=Exception("Context retrieval failed")
        )

        # Test workflow
        result = await questionnaire_agent.generate_questionnaire(
            client=mock_client,
            profession="Engineer",
            disease="Back pain",
            incident_date="01/01/2023",
            medical_date="02/01/2023"
        )

        assert result["success"] is False
        assert "error" in result
        assert result["client_name"] == mock_client.name


class TestQuestionnairePlugin:
    """Test suite for QuestionnairePlugin."""

    @pytest.fixture
    def plugin_config(self):
        """Configuration for test plugin."""
        return {
            "name": "Test Questionnaire Agent",
            "description": "Test description",
            "model": "gemini-1.5-pro"
        }

    def test_plugin_initialization(self, plugin_config):
        """Test plugin initialization."""
        plugin = QuestionnairePlugin("test_agent", plugin_config)

        assert plugin.agent_id == "test_agent"
        assert plugin.name == "Test Questionnaire Agent"
        assert plugin.description == "Test description"
        assert not plugin.is_initialized

    @pytest.mark.asyncio
    async def test_plugin_initialize_success(self, plugin_config):
        """Test successful plugin initialization."""
        plugin = QuestionnairePlugin("test_agent", plugin_config)

        with patch('app.agents.questionnaire_agent.QuestionnaireAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            result = await plugin.initialize()

            assert result is True
            assert plugin.is_initialized
            assert plugin._agent_instance == mock_agent

    @pytest.mark.asyncio
    async def test_plugin_initialize_failure(self, plugin_config):
        """Test plugin initialization failure."""
        plugin = QuestionnairePlugin("test_agent", plugin_config)

        with patch('app.agents.questionnaire_agent.QuestionnaireAgent') as mock_agent_class:
            mock_agent_class.side_effect = Exception("Initialization failed")

            result = await plugin.initialize()

            assert result is False
            assert not plugin.is_initialized

    @pytest.mark.asyncio
    async def test_plugin_process_success(self, plugin_config):
        """Test successful plugin processing."""
        plugin = QuestionnairePlugin("test_agent", plugin_config)
        plugin._initialized = True

        # Mock agent instance
        mock_agent = AsyncMock()
        mock_agent.generate_questionnaire.return_value = {
            "success": True,
            "questionnaire": "Generated questionnaire",
            "context_chunks": 2,
            "client_name": "Test Client"
        }
        plugin._agent_instance = mock_agent

        # Test data
        data = {
            "client": {
                "id": str(uuid.uuid4()),
                "name": "Test Client",
                "cpf": "12345678901"
            },
            "profession": "Engineer",
            "disease": "Back pain",
            "incident_date": "01/01/2023",
            "medical_date": "02/01/2023"
        }

        result = await plugin.process(data)

        assert result["success"] is True
        assert result["questionnaire"] == "Generated questionnaire"

    @pytest.mark.asyncio
    async def test_plugin_process_missing_params(self, plugin_config):
        """Test plugin processing with missing parameters."""
        plugin = QuestionnairePlugin("test_agent", plugin_config)
        plugin._initialized = True
        plugin._agent_instance = MagicMock()

        # Missing profession parameter
        data = {
            "client": {
                "id": str(uuid.uuid4()),
                "name": "Test Client",
                "cpf": "12345678901"
            },
            "disease": "Back pain",
            "incident_date": "01/01/2023",
            "medical_date": "02/01/2023"
        }

        result = await plugin.process(data)

        assert result["success"] is False
        assert "Missing required parameters" in result["error"]

    @pytest.mark.asyncio
    async def test_plugin_health_check_success(self, plugin_config):
        """Test successful plugin health check."""
        plugin = QuestionnairePlugin("test_agent", plugin_config)
        plugin._initialized = True

        mock_agent = MagicMock()
        mock_agent.generate_questionnaire_content = MagicMock()
        plugin._agent_instance = mock_agent

        result = await plugin.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_plugin_health_check_failure(self, plugin_config):
        """Test plugin health check failure."""
        plugin = QuestionnairePlugin("test_agent", plugin_config)

        result = await plugin.health_check()

        assert result is False

    def test_plugin_get_capabilities(self, plugin_config):
        """Test plugin capabilities."""
        plugin = QuestionnairePlugin("test_agent", plugin_config)

        capabilities = plugin.get_capabilities()

        assert "questionnaire_generation" in capabilities
        assert "rag_document_retrieval" in capabilities
        assert "legal_template_formatting" in capabilities
        assert "content_validation" in capabilities
        assert "draft_management" in capabilities
