"""Unit tests for LLM processing tools."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.models.client import Client
from app.tools.llm_tools import LLMProcessorTool


class TestLLMProcessorTool:
    """Test suite for LLMProcessorTool."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        return Client(id=uuid.uuid4(), name="João Silva", cpf="12345678901")

    @pytest.fixture
    def llm_tool(self):
        """Create LLMProcessorTool instance for testing."""
        with (
            patch("google.generativeai.configure"),
            patch("google.generativeai.GenerativeModel") as mock_model_class,
        ):
            mock_model = MagicMock()
            mock_model_class.return_value = mock_model

            return LLMProcessorTool(model_name="gemini-1.5-pro", api_key="test_key")

    def test_tool_initialization(self):
        """Test tool initialization."""
        with (
            patch("google.generativeai.configure") as mock_configure,
            patch("google.generativeai.GenerativeModel") as mock_model_class,
        ):
            tool = LLMProcessorTool(model_name="gemini-1.5-pro", api_key="test_api_key")

            mock_configure.assert_called_once_with(api_key="test_api_key")
            mock_model_class.assert_called_once_with("gemini-1.5-pro")
            assert tool.model_name == "gemini-1.5-pro"

    def test_tool_initialization_without_api_key(self):
        """Test tool initialization without providing API key."""
        with (
            patch("google.generativeai.configure") as mock_configure,
            patch("google.generativeai.GenerativeModel"),
        ):
            LLMProcessorTool(model_name="gemini-1.5-pro")

            # Should not call configure if no API key provided
            mock_configure.assert_not_called()

    def test_generate_questionnaire_success(self, llm_tool, mock_client):
        """Test successful questionnaire generation."""
        # Mock Gemini API response
        mock_response = MagicMock()
        mock_response.text = """QUESITOS PARA PERÍCIA MÉDICA

DADOS DO EXAMINANDO:
Nome: João Silva
CPF: 123.456.789-01
Profissão: Engenheiro
Condição Relatada: Dor nas costas
Data do Incidente: 01/01/2023
Data do Primeiro Atendimento: 02/01/2023

QUESITOS:

1. O examinando apresenta a condição denominada dor nas costas?

2. A condição apresentada pelo examinando tem relação com sua atividade profissional como Engenheiro?"""

        llm_tool.model.generate_content.return_value = mock_response

        context_chunks = [
            {"text": "Exame médico mostra lesão na coluna", "score": 0.9},
            {"text": "Laudo radiológico indica hérnia de disco", "score": 0.8},
        ]

        result = llm_tool.generate_questionnaire(
            client=mock_client,
            profession="Engenheiro",
            disease="Dor nas costas",
            incident_date="01/01/2023",
            medical_date="02/01/2023",
            context_chunks=context_chunks,
        )

        assert result["success"] is True
        assert "QUESITOS PARA PERÍCIA MÉDICA" in result["questionnaire"]
        assert result["context_chunks_used"] == 2
        assert result["model_used"] == "gemini-1.5-pro"
        assert result["client_name"] == "João Silva"
        assert result["has_context"] is True

    def test_generate_questionnaire_empty_response(self, llm_tool, mock_client):
        """Test questionnaire generation with empty API response."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.text = None
        llm_tool.model.generate_content.return_value = mock_response

        result = llm_tool.generate_questionnaire(
            client=mock_client,
            profession="Advogado",
            disease="LER/DORT",
            incident_date="15/03/2023",
            medical_date="20/03/2023",
        )

        # Should return fallback questionnaire
        assert result["success"] is True
        assert "fallback_used" in result
        assert result["fallback_used"] is True
        assert (
            "ATENÇÃO: Quesitos gerados em modo de segurança" in result["questionnaire"]
        )

    def test_generate_questionnaire_api_exception(self, llm_tool, mock_client):
        """Test questionnaire generation with API exception."""
        # Mock API exception
        llm_tool.model.generate_content.side_effect = Exception("API Error")

        result = llm_tool.generate_questionnaire(
            client=mock_client,
            profession="Médico",
            disease="Estresse",
            incident_date="10/05/2023",
            medical_date="12/05/2023",
        )

        # Should return fallback questionnaire
        assert result["success"] is True
        assert "fallback_used" in result
        assert result["fallback_used"] is True
        assert "original_error" in result

    def test_generate_questionnaire_no_context(self, llm_tool, mock_client):
        """Test questionnaire generation without context."""
        mock_response = MagicMock()
        mock_response.text = "Generated questionnaire without context"
        llm_tool.model.generate_content.return_value = mock_response

        result = llm_tool.generate_questionnaire(
            client=mock_client,
            profession="Professor",
            disease="Ansiedade",
            incident_date="05/08/2023",
            medical_date="07/08/2023",
            context_chunks=None,
        )

        assert result["success"] is True
        assert result["context_chunks_used"] == 0
        assert result["has_context"] is False

    def test_generate_with_prompt_success(self, llm_tool):
        """Test successful content generation with custom prompt."""
        mock_response = MagicMock()
        mock_response.text = "Generated content from custom prompt"
        llm_tool.model.generate_content.return_value = mock_response

        result = llm_tool.generate_with_prompt(
            prompt="Generate a legal document about workplace injuries", temperature=0.5
        )

        assert result["success"] is True
        assert result["generated_text"] == "Generated content from custom prompt"
        assert result["model_used"] == "gemini-1.5-pro"

    def test_generate_with_prompt_failure(self, llm_tool):
        """Test content generation failure with custom prompt."""
        llm_tool.model.generate_content.side_effect = Exception("Generation failed")

        result = llm_tool.generate_with_prompt(prompt="Test prompt")

        assert result["success"] is False
        assert "error" in result
        assert result["generated_text"] == ""

    def test_prepare_context_text_with_chunks(self, llm_tool):
        """Test context text preparation with chunks."""
        context_chunks = [
            {
                "text": "Medical report text",
                "score": 0.9,
                "metadata": {"type": "medical"},
            },
            {"text": "X-ray analysis", "score": 0.8, "metadata": {"type": "radiology"}},
            {"text": "Doctor's notes", "score": 0.7, "metadata": {}},
        ]

        context_text = llm_tool._prepare_context_text(context_chunks)

        assert "Medical report text" in context_text
        assert "X-ray analysis" in context_text
        assert "Doctor's notes" in context_text
        assert "Relevância: 0.90" in context_text
        assert "Relevância: 0.80" in context_text

    def test_prepare_context_text_empty(self, llm_tool):
        """Test context text preparation with empty chunks."""
        context_text = llm_tool._prepare_context_text(None)

        assert context_text == "Nenhum documento disponível para análise."

        context_text = llm_tool._prepare_context_text([])

        assert context_text == "Nenhum documento disponível para análise."

    def test_create_questionnaire_prompt(self, llm_tool, mock_client):
        """Test questionnaire prompt creation."""
        context_text = "Contexto médico relevante"

        prompt = llm_tool._create_questionnaire_prompt(
            client=mock_client,
            profession="Engenheiro Civil",
            disease="Síndrome do Túnel do Carpo",
            incident_date="12/06/2023",
            medical_date="15/06/2023",
            context_text=context_text,
        )

        assert "João Silva" in prompt
        assert "123.456.789-01" in prompt
        assert "Engenheiro Civil" in prompt
        assert "Síndrome do Túnel do Carpo" in prompt
        assert "12/06/2023" in prompt
        assert "15/06/2023" in prompt
        assert "Contexto médico relevante" in prompt
        assert "QUESITOS PARA PERÍCIA MÉDICA" in prompt

    def test_generate_fallback_questionnaire(self, llm_tool, mock_client):
        """Test fallback questionnaire generation."""
        fallback = llm_tool._generate_fallback_questionnaire(
            client=mock_client,
            profession="Contador",
            disease="Depressão",
            incident_date="20/09/2023",
            medical_date="25/09/2023",
        )

        assert "QUESITOS PARA PERÍCIA MÉDICA" in fallback
        assert "João Silva" in fallback
        assert "123.456.789-01" in fallback
        assert "Contador" in fallback
        assert "Depressão" in fallback
        assert "20/09/2023" in fallback
        assert "25/09/2023" in fallback
        assert "ATENÇÃO: Quesitos gerados em modo de segurança" in fallback

    def test_formatted_cpf_in_prompt(self, llm_tool):
        """Test that CPF is properly formatted in generated content."""
        # Create client with specific CPF
        client = Client(id=uuid.uuid4(), name="Maria Santos", cpf="98765432100")

        mock_response = MagicMock()
        mock_response.text = "Test questionnaire"
        llm_tool.model.generate_content.return_value = mock_response

        llm_tool.generate_questionnaire(
            client=client,
            profession="Professora",
            disease="Estresse",
            incident_date="01/01/2023",
            medical_date="02/01/2023",
        )

        # Verify that generate_content was called
        llm_tool.model.generate_content.assert_called_once()

        # Get the prompt that was passed to generate_content
        call_args = llm_tool.model.generate_content.call_args[0]
        prompt = call_args[0]

        # Check that formatted CPF is in the prompt
        assert "987.654.321-00" in prompt

    def test_questionnaire_structure_validation(self, llm_tool, mock_client):
        """Test that generated questionnaire has expected structure."""
        mock_response = MagicMock()
        mock_response.text = """QUESITOS PARA PERÍCIA MÉDICA

DADOS DO EXAMINANDO:
Nome: João Silva
CPF: 123.456.789-01

QUESITOS:

1. Primeiro quesito
2. Segundo quesito
3. Terceiro quesito"""

        llm_tool.model.generate_content.return_value = mock_response

        result = llm_tool.generate_questionnaire(
            client=mock_client,
            profession="Engenheiro",
            disease="Lesão",
            incident_date="01/01/2023",
            medical_date="02/01/2023",
        )

        questionnaire = result["questionnaire"]

        # Check structure
        assert "QUESITOS PARA PERÍCIA MÉDICA" in questionnaire
        assert "DADOS DO EXAMINANDO:" in questionnaire
        assert "QUESITOS:" in questionnaire
        assert "1." in questionnaire
        assert "2." in questionnaire
        assert "3." in questionnaire
