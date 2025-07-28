"""Unit tests for QuestionnaireWriterPage UI component."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.client import Client
from app.ui_components.questionnaire_writer import QuestionnaireWriterPage


class TestQuestionnaireWriterPage:
    """Test suite for QuestionnaireWriterPage UI component."""

    @pytest.fixture
    def mock_client(self):
        """Mock Client instance."""
        client = MagicMock(spec=Client)
        client.id = uuid.uuid4()
        client.name = "Maria Santos"
        client.formatted_cpf = "987.654.321-00"
        return client

    @pytest.fixture
    def page_instance(self):
        """QuestionnaireWriterPage instance."""
        return QuestionnaireWriterPage()

    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user."""
        return {
            "username": "test_user",
            "role": "common_user",
            "is_active": True
        }

    def test_page_initialization(self, page_instance):
        """Test page initialization with default values."""
        assert page_instance.clients == []
        assert page_instance.selected_client is None
        assert page_instance.client_select is None
        assert page_instance.profession_input is None
        assert page_instance.disease_input is None
        assert page_instance.incident_date_input is None
        assert page_instance.medical_date_input is None
        assert page_instance.result_area is None

    @patch('app.ui_components.questionnaire_writer.AuthManager.require_auth')
    @patch('app.ui_components.questionnaire_writer.AuthManager.get_current_user')
    def test_create_requires_authentication(self, mock_get_user, mock_require_auth, page_instance, mock_auth_user):
        """Test that page creation requires authentication."""
        # Arrange
        mock_require_auth.return_value = False

        # Act
        page_instance.create()

        # Assert
        mock_require_auth.assert_called_once()
        mock_get_user.assert_not_called()

    @patch('app.ui_components.questionnaire_writer.AuthManager.require_auth')
    @patch('app.ui_components.questionnaire_writer.AuthManager.get_current_user')
    @patch('app.ui_components.questionnaire_writer.ui')
    def test_create_with_authentication(self, mock_ui, mock_get_user, mock_require_auth, page_instance, mock_auth_user):
        """Test page creation with proper authentication."""
        # Arrange
        mock_require_auth.return_value = True
        mock_get_user.return_value = mock_auth_user

        # Act
        page_instance.create()

        # Assert
        mock_require_auth.assert_called_once()
        mock_get_user.assert_called_once()

    def test_on_client_selected_with_valid_client(self, page_instance, mock_client):
        """Test client selection with valid client."""
        # Arrange
        page_instance.clients = [mock_client]
        mock_event = MagicMock()
        mock_event.value = str(mock_client.id)

        with patch('app.ui_components.questionnaire_writer.ui.notify') as mock_notify:
            # Act
            page_instance._on_client_selected(mock_event)

            # Assert
            assert page_instance.selected_client == mock_client
            mock_notify.assert_called_once_with(f"Cliente selecionado: {mock_client.name}", type="positive")

    def test_on_client_selected_with_empty_value(self, page_instance):
        """Test client selection with empty value."""
        # Arrange
        mock_event = MagicMock()
        mock_event.value = None

        # Act
        page_instance._on_client_selected(mock_event)

        # Assert
        assert page_instance.selected_client is None

    def test_on_client_selected_with_invalid_client(self, page_instance, mock_client):
        """Test client selection with invalid client ID."""
        # Arrange
        page_instance.clients = [mock_client]
        mock_event = MagicMock()
        mock_event.value = str(uuid.uuid4())  # Different ID

        # Act
        page_instance._on_client_selected(mock_event)

        # Assert
        assert page_instance.selected_client is None

    @patch('app.ui_components.questionnaire_writer.get_async_db')
    async def test_load_clients_with_documents_success(self, mock_get_db, page_instance, mock_client):
        """Test successful loading of clients with documents."""
        # Arrange
        mock_db_session = AsyncMock()
        mock_get_db.return_value.__aiter__.return_value = [mock_db_session]

        mock_client_service = AsyncMock()
        mock_client_service.get_all_clients.return_value = [mock_client]

        page_instance.client_select = MagicMock()
        page_instance.client_select.options = {}

        with patch('app.ui_components.questionnaire_writer.ClientRepository'):
            with patch('app.ui_components.questionnaire_writer.ClientService') as mock_service:
                with patch('app.ui_components.questionnaire_writer.ui.notify') as mock_notify:
                    mock_service.return_value = mock_client_service

                    # Act
                    await page_instance._load_clients_with_documents()

                    # Assert
                    mock_client_service.get_all_clients.assert_called_once()
                    assert page_instance.clients == [mock_client]
                    expected_option = f"{mock_client.name} - {mock_client.formatted_cpf}"
                    assert page_instance.client_select.options[str(mock_client.id)] == expected_option
                    mock_notify.assert_called_once_with("1 cliente(s) carregado(s)", type="positive")

    @patch('app.ui_components.questionnaire_writer.get_async_db')
    async def test_load_clients_with_documents_no_clients(self, mock_get_db, page_instance):
        """Test loading clients when no clients exist."""
        # Arrange
        mock_db_session = AsyncMock()
        mock_get_db.return_value.__aiter__.return_value = [mock_db_session]

        mock_client_service = AsyncMock()
        mock_client_service.get_all_clients.return_value = []

        page_instance.client_select = MagicMock()
        page_instance.client_select.options = {}

        with patch('app.ui_components.questionnaire_writer.ClientRepository'):
            with patch('app.ui_components.questionnaire_writer.ClientService') as mock_service:
                with patch('app.ui_components.questionnaire_writer.ui.notify') as mock_notify:
                    mock_service.return_value = mock_client_service

                    # Act
                    await page_instance._load_clients_with_documents()

                    # Assert
                    assert page_instance.clients == []
                    assert page_instance.client_select.options == {}
                    mock_notify.assert_called_once_with("Nenhum cliente encontrado", type="warning")

    @patch('app.ui_components.questionnaire_writer.get_async_db')
    async def test_load_clients_with_documents_exception(self, mock_get_db, page_instance):
        """Test exception handling in client loading."""
        # Arrange
        mock_get_db.side_effect = Exception("Database error")

        with patch('app.ui_components.questionnaire_writer.ui.notify') as mock_notify:
            # Act
            await page_instance._load_clients_with_documents()

            # Assert
            mock_notify.assert_called_once_with("Erro ao carregar clientes: Database error", type="negative")

    def test_copy_result_with_content(self, page_instance):
        """Test copying result when content is available."""
        # Arrange
        page_instance.result_area = MagicMock()
        page_instance.result_area.value = "Test questionnaire content"

        with patch('app.ui_components.questionnaire_writer.ui.run_javascript') as mock_js:
            with patch('app.ui_components.questionnaire_writer.ui.notify') as mock_notify:
                # Act
                page_instance._copy_result()

                # Assert
                mock_js.assert_called_once()
                mock_notify.assert_called_once_with("Texto copiado para a área de transferência!", type="positive")

    def test_copy_result_without_content(self, page_instance):
        """Test copying result when no content is available."""
        # Arrange
        page_instance.result_area = MagicMock()
        page_instance.result_area.value = ""

        with patch('app.ui_components.questionnaire_writer.ui.notify') as mock_notify:
            # Act
            page_instance._copy_result()

            # Assert
            mock_notify.assert_called_once_with("Nenhum conteúdo para copiar", type="warning")

    async def test_generate_questionnaire_no_client_selected(self, page_instance):
        """Test questionnaire generation when no client is selected."""
        # Arrange
        page_instance.selected_client = None

        with patch('app.ui_components.questionnaire_writer.ui.notify') as mock_notify:
            # Act
            await page_instance._generate_questionnaire()

            # Assert
            mock_notify.assert_called_once_with("Por favor, selecione um cliente", type="warning")

    async def test_generate_questionnaire_missing_fields(self, page_instance, mock_client):
        """Test questionnaire generation with missing required fields."""
        # Arrange
        page_instance.selected_client = mock_client
        page_instance.profession_input = MagicMock()
        page_instance.profession_input.value = ""  # Empty profession
        page_instance.disease_input = MagicMock()
        page_instance.disease_input.value = "Test disease"
        page_instance.incident_date_input = MagicMock()
        page_instance.incident_date_input.value = "01/01/2024"
        page_instance.medical_date_input = MagicMock()
        page_instance.medical_date_input.value = "02/01/2024"

        with patch('app.ui_components.questionnaire_writer.ui.notify') as mock_notify:
            # Act
            await page_instance._generate_questionnaire()

            # Assert
            mock_notify.assert_called_once_with("Por favor, preencha todos os campos obrigatórios", type="warning")

    @patch('app.ui_components.questionnaire_writer.get_async_db')
    async def test_generate_questionnaire_success(self, mock_get_db, page_instance, mock_client):
        """Test successful questionnaire generation."""
        # Arrange
        page_instance.selected_client = mock_client
        page_instance.profession_input = MagicMock()
        page_instance.profession_input.value = "Enfermeiro"
        page_instance.disease_input = MagicMock()
        page_instance.disease_input.value = "LER/DORT"
        page_instance.incident_date_input = MagicMock()
        page_instance.incident_date_input.value = "01/01/2024"
        page_instance.medical_date_input = MagicMock()
        page_instance.medical_date_input.value = "02/01/2024"
        page_instance.result_area = MagicMock()

        mock_db_session = AsyncMock()
        mock_get_db.return_value.__aiter__.return_value = [mock_db_session]

        mock_service = AsyncMock()
        mock_service.generate_questionnaire.return_value = {
            "success": True,
            "questionnaire": "Generated questionnaire",
            "context_chunks": 5,
            "client_name": "Test Client"
        }

        with patch('app.ui_components.questionnaire_writer.DocumentChunkRepository'):
            with patch('app.ui_components.questionnaire_writer.get_questionnaire_draft_service') as mock_get_service:
                with patch('app.ui_components.questionnaire_writer.ui.notify') as mock_notify:
                    mock_get_service.return_value = mock_service

                    # Act
                    await page_instance._generate_questionnaire()

                    # Assert
                    assert page_instance.result_area.value == "Generated questionnaire"
                    mock_notify.assert_any_call("Gerando quesitos... Aguarde.", type="info")
                    mock_notify.assert_any_call("Quesitos gerados com sucesso (baseado em 5 documento(s))!", type="positive")

    @patch('app.ui_components.questionnaire_writer.get_async_db')
    async def test_generate_questionnaire_service_failure(self, mock_get_db, page_instance, mock_client):
        """Test questionnaire generation when service fails."""
        # Arrange
        page_instance.selected_client = mock_client
        page_instance.profession_input = MagicMock()
        page_instance.profession_input.value = "Médico"
        page_instance.disease_input = MagicMock()
        page_instance.disease_input.value = "Burnout"
        page_instance.incident_date_input = MagicMock()
        page_instance.incident_date_input.value = "01/01/2024"
        page_instance.medical_date_input = MagicMock()
        page_instance.medical_date_input.value = "02/01/2024"

        mock_db_session = AsyncMock()
        mock_get_db.return_value.__aiter__.return_value = [mock_db_session]

        mock_service = AsyncMock()
        mock_service.generate_questionnaire.return_value = {
            "success": False,
            "error": "Service error",
            "questionnaire": "",
            "context_chunks": 0
        }

        with patch('app.ui_components.questionnaire_writer.DocumentChunkRepository'):
            with patch('app.ui_components.questionnaire_writer.get_questionnaire_draft_service') as mock_get_service:
                with patch('app.ui_components.questionnaire_writer.ui.notify') as mock_notify:
                    mock_get_service.return_value = mock_service

                    # Act
                    await page_instance._generate_questionnaire()

                    # Assert
                    mock_notify.assert_any_call("Erro ao gerar quesitos: Service error", type="negative")
