"""Tests for PDF processor agent integration and functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.pdf_processor_agent import PDFProcessorAgent, PDFProcessorPlugin


class TestPDFProcessorAgent:
    """Test PDF processor agent functionality."""

    @pytest.fixture
    def mock_pdf_data(self):
        """Mock PDF processing data."""
        return {
            "success": True,
            "text_content": [
                {"page_number": 1, "text": "Sample PDF text", "char_count": 15}
            ],
            "metadata": {"title": "Test Document", "author": "Test Author"},
            "page_count": 1,
            "document_info": {"encryption": False, "page_count": 1}
        }

    @pytest.fixture
    def mock_ocr_data(self):
        """Mock OCR processing data."""
        return {
            "success": True,
            "ocr_results": [
                {
                    "page_number": 1,
                    "ocr_text": "OCR extracted text",
                    "average_confidence": 85.5,
                    "char_count": 18
                }
            ],
            "successful_pages": 1,
            "summary": {"total_ocr_chars": 18}
        }

    @pytest.fixture
    def mock_embedding_data(self):
        """Mock embedding generation data."""
        return {
            "success": True,
            "embeddings": [
                {
                    "chunk_id": "chunk_1",
                    "text": "Sample text chunk",
                    "embedding": [0.1, 0.2, 0.3],
                    "start_pos": 0,
                    "end_pos": 17
                }
            ],
            "total_chunks": 1,
            "successful_embeddings": 1,
            "embedding_dimension": 768
        }

    @pytest.fixture
    def pdf_agent(self):
        """Create a PDF processor agent for testing."""
        with patch('app.agents.pdf_processor_agent.Gemini') as mock_gemini:
            mock_model = MagicMock()
            mock_gemini.return_value = mock_model

            agent = PDFProcessorAgent(model="gemini-2.5-pro")
            return agent

    def test_pdf_agent_initialization(self):
        """Test PDF processor agent initialization."""
        with patch('app.agents.pdf_processor_agent.Gemini') as mock_gemini:
            mock_model = MagicMock()
            mock_gemini.return_value = mock_model

            agent = PDFProcessorAgent(
                model="gemini-2.5-pro",
                max_file_size_mb=25,
                chunk_size=500
            )

            assert agent is not None
            assert hasattr(agent, 'extract_pdf_text')
            assert hasattr(agent, 'process_ocr')
            assert hasattr(agent, 'generate_embeddings')
            assert hasattr(agent, 'store_document')

    def test_extract_pdf_text_success(self, pdf_agent, mock_pdf_data):
        """Test successful PDF text extraction."""
        with patch.object(pdf_agent.pdf_reader, 'process_document', return_value=mock_pdf_data):
            result = pdf_agent.extract_pdf_text("/fake/path/test.pdf")

            assert result["success"] is True
            assert "text_content" in result
            assert result["page_count"] == 1
            assert "metadata" in result

    def test_extract_pdf_text_failure(self, pdf_agent):
        """Test PDF text extraction failure."""
        with patch.object(pdf_agent.pdf_reader, 'process_document', side_effect=Exception("PDF read error")):
            result = pdf_agent.extract_pdf_text("/fake/path/test.pdf")

            assert result["success"] is False
            assert "error" in result
            assert "PDF read error" in result["error"]

    def test_process_ocr_success(self, pdf_agent, mock_ocr_data):
        """Test successful OCR processing."""
        with patch.object(pdf_agent.ocr_processor, 'process_pdf_pages', return_value=mock_ocr_data):
            result = pdf_agent.process_ocr("/fake/path/test.pdf", [1])

            assert result["success"] is True
            assert "ocr_results" in result
            assert result["pages_processed"] == 1

    def test_process_ocr_failure(self, pdf_agent):
        """Test OCR processing failure."""
        with patch.object(pdf_agent.ocr_processor, 'process_pdf_pages', side_effect=Exception("OCR error")):
            result = pdf_agent.process_ocr("/fake/path/test.pdf")

            assert result["success"] is False
            assert "error" in result
            assert "OCR error" in result["error"]

    def test_generate_embeddings_success(self, pdf_agent, mock_embedding_data):
        """Test successful embedding generation."""
        with patch.object(pdf_agent.vector_storage, 'chunk_text', return_value=["Sample text chunk"]):
            with patch.object(pdf_agent.vector_storage, 'generate_embeddings_batch', return_value=mock_embedding_data):
                result = pdf_agent.generate_embeddings("Sample text content")

                assert result["success"] is True
                assert "embeddings" in result
                assert result["successful_embeddings"] == 1

    def test_generate_embeddings_no_chunks(self, pdf_agent):
        """Test embedding generation with no chunks."""
        with patch.object(pdf_agent.vector_storage, 'chunk_text', return_value=[]):
            result = pdf_agent.generate_embeddings("Sample text content")

            assert result["success"] is False
            assert "No chunks generated" in result["error"]

    def test_store_document_success(self, pdf_agent):
        """Test successful document storage."""
        mock_document_data = {
            "file_path": "/fake/path/test.pdf",
            "extracted_text": "Sample extracted text",
            "page_count": 1,
            "pdf_metadata": {"title": "Test"},
            "ocr_results": [],
            "file_size": 1024
        }

        with patch('app.agents.pdf_processor_agent.get_sync_db') as mock_db:
            mock_db_session = MagicMock()
            mock_db.return_value = iter([mock_db_session])

            mock_document = MagicMock()
            mock_document.document_id = "test-doc-id"
            mock_document.filename = "test.pdf"

            mock_db_session.add = MagicMock()
            mock_db_session.commit = MagicMock()
            mock_db_session.refresh = MagicMock()
            mock_db_session.close = MagicMock()

            with patch('app.models.document.Document', return_value=mock_document):
                with patch.object(pdf_agent.vector_storage, 'process_document_text', return_value={
                    "success": True,
                    "processing_summary": {"embeddings_stored": 5}
                }):
                    result = pdf_agent.store_document(mock_document_data, 1)

                    assert result["success"] is True
                    assert result["document_id"] == "test-doc-id"
                    assert result["stored_embeddings"] == 5

    @pytest.mark.asyncio
    async def test_process_document_workflow_success(self, pdf_agent, mock_pdf_data, mock_ocr_data):
        """Test complete document processing workflow."""
        with patch.object(pdf_agent, 'extract_pdf_text', return_value=mock_pdf_data):
            with patch.object(pdf_agent, 'process_ocr', return_value=mock_ocr_data):
                with patch.object(pdf_agent, 'store_document', return_value={
                    "success": True,
                    "document_id": "test-doc-id",
                    "stored_embeddings": 3
                }):
                    with patch('pathlib.Path.stat') as mock_stat:
                        mock_stat.return_value.st_size = 1024

                        result = await pdf_agent.process_document(
                            "/fake/path/test.pdf",
                            user_id=1,
                            perform_ocr=True
                        )

                        assert result["success"] is True
                        assert result["document_id"] == "test-doc-id"
                        assert "processing_summary" in result

    @pytest.mark.asyncio
    async def test_process_document_workflow_failure(self, pdf_agent):
        """Test document processing workflow failure."""
        with patch.object(pdf_agent, 'extract_pdf_text', return_value={"success": False, "error": "Extract failed"}):
            result = await pdf_agent.process_document("/fake/path/test.pdf", user_id=1)

            assert result["success"] is False
            assert "Extract failed" in result["error"]


class TestPDFProcessorPlugin:
    """Test PDF processor plugin functionality."""

    @pytest.fixture
    def plugin_config(self):
        """Plugin configuration for testing."""
        return {
            "name": "Test PDF Processor",
            "description": "Test plugin",
            "model": "gemini-2.5-pro"
        }

    def test_plugin_initialization(self, plugin_config):
        """Test plugin initialization."""
        plugin = PDFProcessorPlugin("test_pdf_processor", plugin_config)

        assert plugin.agent_id == "test_pdf_processor"
        assert plugin.config == plugin_config
        assert plugin.PLUGIN_NAME == "PDFProcessorPlugin"

    @pytest.mark.asyncio
    async def test_plugin_initialize_success(self, plugin_config):
        """Test successful plugin initialization."""
        plugin = PDFProcessorPlugin("test_pdf_processor", plugin_config)

        with patch('app.agents.pdf_processor_agent.PDFProcessorAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            result = await plugin.initialize()

            assert result is True
            assert plugin._initialized is True
            assert plugin._agent_instance == mock_agent

    @pytest.mark.asyncio
    async def test_plugin_initialize_failure(self, plugin_config):
        """Test plugin initialization failure."""
        plugin = PDFProcessorPlugin("test_pdf_processor", plugin_config)

        with patch('app.agents.pdf_processor_agent.PDFProcessorAgent', side_effect=Exception("Init failed")):
            result = await plugin.initialize()

            assert result is False
            assert plugin._initialized is False

    @pytest.mark.asyncio
    async def test_plugin_process_success(self, plugin_config):
        """Test successful plugin processing."""
        plugin = PDFProcessorPlugin("test_pdf_processor", plugin_config)
        plugin._initialized = True

        mock_agent = AsyncMock()
        mock_agent.process_document.return_value = {"success": True, "result": "processed"}
        plugin._agent_instance = mock_agent

        data = {
            "file_path": "/fake/path/test.pdf",
            "user_id": 1,
            "perform_ocr": True
        }

        result = await plugin.process(data)

        assert result["success"] is True
        mock_agent.process_document.assert_called_once_with(
            file_path="/fake/path/test.pdf",
            user_id=1,
            perform_ocr=True
        )

    @pytest.mark.asyncio
    async def test_plugin_process_not_initialized(self, plugin_config):
        """Test plugin processing when not initialized."""
        plugin = PDFProcessorPlugin("test_pdf_processor", plugin_config)
        plugin._initialized = False

        data = {"file_path": "/fake/path/test.pdf", "user_id": 1}
        result = await plugin.process(data)

        assert result["success"] is False
        assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_plugin_process_missing_params(self, plugin_config):
        """Test plugin processing with missing parameters."""
        plugin = PDFProcessorPlugin("test_pdf_processor", plugin_config)
        plugin._initialized = True
        plugin._agent_instance = MagicMock()

        data = {"file_path": "/fake/path/test.pdf"}  # Missing user_id
        result = await plugin.process(data)

        assert result["success"] is False
        assert "Missing required parameters" in result["error"]

    @pytest.mark.asyncio
    async def test_plugin_health_check_success(self, plugin_config):
        """Test successful plugin health check."""
        plugin = PDFProcessorPlugin("test_pdf_processor", plugin_config)
        plugin._initialized = True

        mock_agent = MagicMock()
        mock_agent.extract_pdf_text = MagicMock()
        plugin._agent_instance = mock_agent

        result = await plugin.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_plugin_health_check_not_initialized(self, plugin_config):
        """Test plugin health check when not initialized."""
        plugin = PDFProcessorPlugin("test_pdf_processor", plugin_config)
        plugin._initialized = False

        result = await plugin.health_check()

        assert result is False

    def test_plugin_get_capabilities(self, plugin_config):
        """Test getting plugin capabilities."""
        plugin = PDFProcessorPlugin("test_pdf_processor", plugin_config)

        capabilities = plugin.get_capabilities()

        assert "pdf_text_extraction" in capabilities
        assert "ocr_processing" in capabilities
        assert "vector_embedding_generation" in capabilities
        assert "document_storage" in capabilities
        assert "metadata_extraction" in capabilities
