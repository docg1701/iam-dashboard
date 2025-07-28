# Testing Strategy

## Testing Approach Overview

**Testing Pyramid for Agent Architecture:**
```
                    E2E Tests
                 (Full UI Workflows)
                /                 \
         Integration Tests        
      (Agent + API + Database)    
     /                           \
Unit Tests                  Unit Tests
(Agents + Tools)         (API + UI Components)
```

## Unit Testing Strategy

**Agent Unit Tests:**
```python
# Test framework: pytest + pytest-asyncio
# Mock framework: unittest.mock for external dependencies

class TestPDFProcessorAgent:
    """Comprehensive unit tests for PDF Processor Agent."""
    
    @pytest.fixture
    def mock_tools(self):
        return {
            "pdf_reader": AsyncMock(),
            "ocr_processor": AsyncMock(),
            "vector_storage": AsyncMock()
        }
    
    @pytest.fixture
    def pdf_agent(self, mock_tools):
        agent = PDFProcessorAgent("test_pdf_processor", {})
        agent.pdf_reader = mock_tools["pdf_reader"]
        agent.ocr_processor = mock_tools["ocr_processor"]
        agent.vector_storage = mock_tools["vector_storage"]
        return agent
    
    async def test_successful_processing(self, pdf_agent, mock_tools):
        # Arrange
        mock_tools["pdf_reader"].extract_text.return_value = DocumentContent(
            text="Sample text", needs_ocr=False
        )
        mock_tools["vector_storage"].embed_content.return_value = [0.1, 0.2, 0.3]
        
        # Act
        result = await pdf_agent.process_document("/path/to/test.pdf")
        
        # Assert
        assert result.content.text == "Sample text"
        assert result.vectors == [0.1, 0.2, 0.3]
        mock_tools["pdf_reader"].extract_text.assert_called_once()
    
    async def test_ocr_fallback(self, pdf_agent, mock_tools):
        # Test OCR processing when PDF extraction fails
        mock_tools["pdf_reader"].extract_text.return_value = DocumentContent(
            text="", needs_ocr=True
        )
        mock_tools["ocr_processor"].process.return_value = DocumentContent(
            text="OCR extracted text", needs_ocr=False
        )
        
        result = await pdf_agent.process_document("/path/to/scanned.pdf")
        
        assert result.content.text == "OCR extracted text"
        mock_tools["ocr_processor"].process.assert_called_once()
    
    async def test_error_handling(self, pdf_agent, mock_tools):
        # Test error handling and logging
        mock_tools["pdf_reader"].extract_text.side_effect = Exception("PDF corrupted")
        
        with pytest.raises(AgentProcessingError) as exc_info:
            await pdf_agent.process_document("/path/to/corrupted.pdf")
        
        assert "PDF corrupted" in str(exc_info.value)
```

**Tool Unit Tests:**
```python
class TestPDFReaderTool:
    """Unit tests for PDF reading tool."""
    
    def test_extract_text_from_valid_pdf(self, sample_pdf_path):
        tool = PDFReaderTool()
        result = tool.extract_text(sample_pdf_path)
        
        assert result.text is not None
        assert len(result.text) > 0
        assert result.page_count > 0
    
    def test_extract_metadata(self, sample_pdf_path):
        tool = PDFReaderTool()
        metadata = tool.extract_metadata(sample_pdf_path)
        
        assert metadata.title is not None
        assert metadata.author is not None
        assert metadata.creation_date is not None
    
    def test_invalid_file_handling(self):
        tool = PDFReaderTool()
        
        with pytest.raises(PDFProcessingError):
            tool.extract_text("/path/to/nonexistent.pdf")
```

## Integration Testing Strategy

**Agent Workflow Integration Tests:**
```python
class TestAgentIntegration:
    """Integration tests for complete agent workflows."""
    
    @pytest.fixture
    def test_container(self):
        """Test container with real database and mocked external services."""
        container = Container()
        container.config.from_dict({
            "database": {"url": "postgresql://test:test@localhost/test_db"},
            "gemini": {"api_key": "test_key"},
            "redis": {"url": "redis://localhost:6379/1"}
        })
        container.wire(modules=[])
        return container
    
    async def test_document_processing_integration(self, test_container, test_db):
        # Test complete document processing workflow
        agent_manager = test_container.agent_manager()
        
        # Upload test document
        test_file_path = "tests/fixtures/sample_legal_document.pdf"
        
        pdf_agent = await agent_manager.get_agent("pdf_processor")
        result = await pdf_agent.process_document(test_file_path)
        
        # Verify database storage
        document = test_db.query(Document).filter_by(
            id=result.document_id
        ).first()
        
        assert document is not None
        assert document.content is not None
        assert len(document.vectors) > 0
        assert document.processing_status == "completed"
    
    async def test_questionnaire_generation_integration(self, test_container, test_db):
        # Test questionnaire generation with real RAG pipeline
        agent_manager = test_container.agent_manager()
        
        # Create test client with documents
        client = self._create_test_client_with_documents(test_db)
        
        questionnaire_agent = await agent_manager.get_agent("questionnaire_writer")
        result = await questionnaire_agent.generate_questionnaire(
            QuestionnaireRequest(
                client_id=client.id,
                case_type="trabalhista",
                requirements=["pedido_inicial", "provas_documentais"]
            )
        )
        
        # Verify questionnaire quality
        assert result.content is not None
        assert len(result.content) > 1000  # Minimum content length
        assert "trabalhista" in result.content.lower()
        
        # Verify database storage
        questionnaire = test_db.query(QuestionnaireDraft).filter_by(
            id=result.questionnaire_id
        ).first()
        assert questionnaire is not None
```

**API Integration Tests:**
```python
class TestAPIIntegration:
    """Integration tests for API endpoints with agents."""
    
    async def test_document_upload_api(self, test_client, test_db):
        # Test document upload API with agent processing
        with open("tests/fixtures/sample.pdf", "rb") as f:
            response = test_client.post(
                "/documents/process",
                files={"file": ("sample.pdf", f, "application/pdf")},
                headers={"Authorization": f"Bearer {self.test_token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "document_id" in data
        assert data["status"] == "completed"
        
        # Verify database state
        document = test_db.query(Document).filter_by(
            id=data["document_id"]
        ).first()
        assert document is not None
    
    async def test_agent_management_api(self, admin_client):
        # Test agent management endpoints
        
        # Get agent status
        response = admin_client.get("/admin/agents/status")
        assert response.status_code == 200
        
        agents = response.json()["agents"]
        assert len(agents) > 0
        
        # Enable/disable agent
        agent_id = agents[0]["id"]
        response = admin_client.post(f"/admin/agents/{agent_id}/disable")
        assert response.status_code == 200
        
        response = admin_client.post(f"/admin/agents/{agent_id}/enable")
        assert response.status_code == 200
```

## End-to-End Testing Strategy

**Browser-based E2E Tests (Using Playwright MCP):**
```python
# Using Playwright MCP for complete UI testing
class TestE2EAgentWorkflows:
    """End-to-end tests for agent-powered UI workflows."""
    
    async def test_document_upload_and_processing_ui(self, browser):
        # Navigate to dashboard
        await browser.navigate("http://localhost:8000/dashboard")
        
        # Login
        await browser.type("#email", "test@example.com")
        await browser.type("#password", "testpassword")
        await browser.click("#login-button")
        
        # Upload document
        await browser.file_upload(["tests/fixtures/sample_legal_document.pdf"])
        
        # Wait for processing to complete
        await browser.wait_for("text=Processing completed")
        
        # Verify document appears in list
        snapshot = await browser.snapshot()
        assert "sample_legal_document.pdf" in snapshot
        
        # Verify agent status indicator
        assert "PDF Processor: Active" in snapshot
    
    async def test_questionnaire_generation_ui(self, browser):
        # Navigate to questionnaire generator
        await browser.navigate("http://localhost:8000/questionnaires/new")
        
        # Select client and case type
        await browser.select_option("#client-select", "Test Client")
        await browser.select_option("#case-type", "trabalhista")
        
        # Start generation
        await browser.click("#generate-questionnaire")
        
        # Wait for agent processing
        await browser.wait_for("text=Questionnaire generated successfully")
        
        # Verify questionnaire content
        snapshot = await browser.snapshot()
        assert "questionnaire-content" in snapshot
        
        # Verify agent indicators
        assert "Questionnaire Agent: Active" in snapshot
    
    async def test_admin_agent_management_ui(self, admin_browser):
        # Navigate to admin panel
        await admin_browser.navigate("http://localhost:8000/admin/control-panel")
        
        # Verify agent status display
        snapshot = await admin_browser.snapshot()
        assert "PDF Processor Agent" in snapshot
        assert "Questionnaire Agent" in snapshot
        
        # Test agent disable/enable
        await admin_browser.click("#disable-pdf-processor")
        await admin_browser.wait_for("text=PDF Processor disabled")
        
        await admin_browser.click("#enable-pdf-processor")
        await admin_browser.wait_for("text=PDF Processor enabled")
        
        # Test configuration update
        await admin_browser.click("#configure-pdf-processor")
        await admin_browser.type("#timeout-input", "600")
        await admin_browser.click("#save-config")
        await admin_browser.wait_for("text=Configuration saved")
```

## Performance Testing

**Agent Performance Tests:**
```python
class TestAgentPerformance:
    """Performance tests for agent operations."""
    
    async def test_pdf_processing_performance(self, pdf_agent):
        # Test processing time requirements (≤110% of baseline)
        baseline_time = 30.0  # seconds
        max_acceptable_time = baseline_time * 1.1
        
        start_time = time.time()
        result = await pdf_agent.process_document("tests/fixtures/large_document.pdf")
        processing_time = time.time() - start_time
        
        assert processing_time <= max_acceptable_time
        assert result.document_id is not None
    
    async def test_concurrent_agent_processing(self, agent_manager):
        # Test multiple concurrent agent operations
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                self._process_test_document(agent_manager, f"test_doc_{i}.pdf")
            )
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify all processing completed successfully
        assert len(results) == 5
        assert all(result.success for result in results)
        
        # Verify concurrent processing efficiency
        max_sequential_time = 30.0 * 5  # 5 docs × 30 seconds each
        assert total_time < max_sequential_time * 0.6  # Should be significantly faster
```

## Test Data Management

**Test Fixtures and Data:**
```python
# tests/fixtures/
├── sample_legal_document.pdf      # Standard legal document for testing
├── large_document.pdf             # Large file for performance testing
├── scanned_document.pdf           # OCR testing document
├── corrupted_document.pdf         # Error handling testing
└── multilingual_document.pdf      # Language detection testing

# Test database setup
@pytest.fixture
def test_db():
    # Create test database
    engine = create_engine("postgresql://test:test@localhost/test_iam_dashboard")
    Base.metadata.create_all(engine)
    
    session = Session(engine)
    
    # Create test data
    test_user = User(email="test@example.com", password_hash="hashed_password")
    test_client = Client(name="Test Law Firm", user_id=test_user.id)
    
    session.add_all([test_user, test_client])
    session.commit()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)
```