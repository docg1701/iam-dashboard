"""Unit tests for QuestionnaireDraftService."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.client import Client
from app.models.document_chunk import DocumentChunk
from app.services.questionnaire_draft_service import QuestionnaireDraftService


class TestQuestionnaireDraftService:
    """Test suite for QuestionnaireDraftService."""

    @pytest.fixture
    def mock_chunk_repository(self):
        """Mock DocumentChunkRepository."""
        return AsyncMock()

    @pytest.fixture
    def mock_client(self):
        """Mock Client instance."""
        client = MagicMock(spec=Client)
        client.id = uuid.uuid4()
        client.name = "João Silva"
        client.formatted_cpf = "123.456.789-00"
        return client

    @pytest.fixture
    def mock_chunks(self):
        """Mock DocumentChunk list."""
        chunks = []
        for i in range(3):
            chunk = MagicMock(spec=DocumentChunk)
            chunk.id = uuid.uuid4()
            chunk.text = f"Medical document text chunk {i+1}"
            chunk.client_id = uuid.uuid4()
            chunks.append(chunk)
        return chunks

    @pytest.fixture
    def service(self, mock_chunk_repository):
        """QuestionnaireDraftService instance with mocked dependencies."""
        with patch('app.services.questionnaire_draft_service.get_llama_index_config') as mock_config:
            mock_config_instance = MagicMock()
            mock_config_instance.gemini_api_key = "test-api-key"
            mock_config.return_value = mock_config_instance

            with patch('app.services.questionnaire_draft_service.genai.configure'):
                with patch('app.services.questionnaire_draft_service.genai.GenerativeModel') as mock_model:
                    mock_model_instance = MagicMock()
                    mock_model.return_value = mock_model_instance

                    service = QuestionnaireDraftService(mock_chunk_repository)
                    service.model = mock_model_instance
                    return service

    @pytest.mark.asyncio
    async def test_generate_questionnaire_success(self, service, mock_client, mock_chunk_repository):
        """Test successful questionnaire generation."""
        # Arrange
        profession = "Enfermeiro"
        disease = "Lesão por esforço repetitivo"
        incident_date = "15/03/2024"
        medical_date = "16/03/2024"

        # Mock context retrieval
        service._retrieve_client_context = AsyncMock(return_value=[
            "Paciente apresenta dor no punho direito",
            "Diagnóstico: LER/DORT",
            "Afastamento recomendado por 30 dias"
        ])

        # Mock Gemini generation
        mock_response = MagicMock()
        mock_response.text = "Generated questionnaire content"
        service.model.generate_content = MagicMock(return_value=mock_response)

        # Act
        result = await service.generate_questionnaire(
            client=mock_client,
            profession=profession,
            disease=disease,
            incident_date=incident_date,
            medical_date=medical_date
        )

        # Assert
        assert result["success"] is True
        assert "Generated questionnaire content" in result["questionnaire"]
        assert result["context_chunks"] == 3
        assert result["client_name"] == "João Silva"
        service._retrieve_client_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_questionnaire_with_empty_context(self, service, mock_client):
        """Test questionnaire generation when no context is available."""
        # Arrange
        profession = "Médico"
        disease = "Burnout"
        incident_date = "01/01/2024"
        medical_date = "02/01/2024"

        # Mock empty context
        service._retrieve_client_context = AsyncMock(return_value=[])

        # Mock Gemini generation
        mock_response = MagicMock()
        mock_response.text = "Questionnaire without context"
        service.model.generate_content = MagicMock(return_value=mock_response)

        # Act
        result = await service.generate_questionnaire(
            client=mock_client,
            profession=profession,
            disease=disease,
            incident_date=incident_date,
            medical_date=medical_date
        )

        # Assert
        assert result["success"] is True
        assert result["context_chunks"] == 0
        assert "Questionnaire without context" in result["questionnaire"]

    @pytest.mark.asyncio
    async def test_generate_questionnaire_gemini_failure(self, service, mock_client):
        """Test questionnaire generation when Gemini API fails."""
        # Arrange
        profession = "Engenheiro"
        disease = "Estresse ocupacional"
        incident_date = "10/05/2024"
        medical_date = "11/05/2024"

        # Mock context retrieval
        service._retrieve_client_context = AsyncMock(return_value=["Some context"])

        # Mock Gemini failure
        service.model.generate_content = MagicMock(side_effect=Exception("API Error"))

        # Act
        result = await service.generate_questionnaire(
            client=mock_client,
            profession=profession,
            disease=disease,
            incident_date=incident_date,
            medical_date=medical_date
        )

        # Assert
        assert result["success"] is True  # Fallback should work
        assert "QUESITOS PARA PERÍCIA MÉDICA" in result["questionnaire"]
        assert "Engenheiro" in result["questionnaire"]
        assert "Estresse ocupacional" in result["questionnaire"]

    @pytest.mark.asyncio
    async def test_retrieve_client_context(self, service, mock_client, mock_chunk_repository, mock_chunks):
        """Test context retrieval from client documents."""
        # Arrange
        mock_chunk_repository.get_chunks_by_client.return_value = mock_chunks

        # Mock vector store and index
        with patch('app.services.questionnaire_draft_service.VectorStoreIndex') as mock_index_class:
            mock_index = MagicMock()
            mock_index_class.from_vector_store.return_value = mock_index

            mock_retriever = MagicMock()
            mock_index.as_retriever.return_value = mock_retriever

            # Mock retrieved nodes
            mock_nodes = []
            for i, _chunk in enumerate(mock_chunks):
                node = MagicMock()
                node.text = f"Retrieved text {i+1}"
                node.metadata = {"client_id": str(mock_client.id)}
                mock_nodes.append(node)

            mock_retriever.retrieve.return_value = mock_nodes

            # Act
            result = await service._retrieve_client_context(
                client_id=mock_client.id,
                profession="Test Profession",
                disease="Test Disease",
                incident_date="01/01/2024"
            )

            # Assert
            assert len(result) > 0
            mock_chunk_repository.get_chunks_by_client.assert_called_once_with(mock_client.id)

    @pytest.mark.asyncio
    async def test_retrieve_client_context_no_chunks(self, service, mock_client, mock_chunk_repository):
        """Test context retrieval when client has no document chunks."""
        # Arrange
        mock_chunk_repository.get_chunks_by_client.return_value = []

        # Act
        result = await service._retrieve_client_context(
            client_id=mock_client.id,
            profession="Test Profession",
            disease="Test Disease",
            incident_date="01/01/2024"
        )

        # Assert
        assert result == []
        mock_chunk_repository.get_chunks_by_client.assert_called_once_with(mock_client.id)

    def test_generate_fallback_questionnaire(self, service, mock_client):
        """Test fallback questionnaire generation."""
        # Arrange
        profession = "Advogado"
        disease = "Ansiedade ocupacional"
        incident_date = "20/02/2024"
        medical_date = "21/02/2024"

        # Act
        result = service._generate_fallback_questionnaire(
            client=mock_client,
            profession=profession,
            disease=disease,
            incident_date=incident_date,
            medical_date=medical_date
        )

        # Assert
        assert "QUESITOS PARA PERÍCIA MÉDICA" in result
        assert mock_client.name in result
        assert mock_client.formatted_cpf in result
        assert profession in result
        assert disease in result
        assert incident_date in result
        assert medical_date in result
        assert "modo de segurança" in result

    @pytest.mark.asyncio
    async def test_generate_questionnaire_exception_handling(self, service, mock_client):
        """Test exception handling in questionnaire generation."""
        # Arrange
        profession = "Professor"
        disease = "Síndrome do pânico"
        incident_date = "05/04/2024"
        medical_date = "06/04/2024"

        # Mock context retrieval to raise exception
        service._retrieve_client_context = AsyncMock(side_effect=Exception("Database error"))

        # Act
        result = await service.generate_questionnaire(
            client=mock_client,
            profession=profession,
            disease=disease,
            incident_date=incident_date,
            medical_date=medical_date
        )

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert result["questionnaire"] == ""
