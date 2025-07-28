# Coding Standards and Conventions

## Agent Development Standards

**Naming Conventions:**
- **Agents:** `{Purpose}Agent` (e.g., `PDFProcessorAgent`, `QuestionnaireAgent`)
- **Tools:** `{Function}Tool` (e.g., `PDFReaderTool`, `OCRProcessorTool`)
- **Plugins:** `{Agent}Plugin` (e.g., `PDFProcessorPlugin`)
- **Configuration:** `{agent_name}_config.yaml`

**Code Structure Standards:**
```python
# Agent implementation template
from agno import Agent
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()

class ExampleAgent(Agent):
    """
    Agent responsible for [specific functionality].
    
    Capabilities:
    - Capability 1
    - Capability 2
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name)
        self.config = config
        self._initialize_tools()
    
    def _initialize_tools(self) -> None:
        """Initialize agent-specific tools."""
        # Tool setup
    
    async def process(self, request: Any) -> Any:
        """Main processing method with comprehensive error handling."""
        try:
            logger.info("Starting processing", agent=self.name, request_id=request.id)
            
            # Implementation
            result = await self._execute_processing(request)
            
            logger.info("Processing completed", agent=self.name, request_id=request.id)
            return result
            
        except Exception as e:
            logger.error("Processing failed", agent=self.name, error=str(e))
            raise AgentProcessingError(f"Agent {self.name} failed: {str(e)}")
    
    async def health_check(self) -> HealthStatus:
        """Comprehensive health check implementation."""
        # Health check logic
        return HealthStatus(healthy=True, details={})
```

**Error Handling Standards:**
```python
# Hierarchical exception structure
class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass

class AgentInitializationError(AgentError):
    """Agent failed to initialize properly."""
    pass

class AgentProcessingError(AgentError):
    """Agent processing failed."""
    pass

class AgentConfigurationError(AgentError):
    """Invalid agent configuration."""
    pass
```

**Logging Standards:**
```python
# Structured logging with context
logger.info(
    "Document processed successfully",
    agent_id=self.name,
    document_id=request.document_id,
    processing_time=elapsed_time,
    file_size=file_stats.size,
    pages_processed=result.page_count
)

logger.error(
    "OCR processing failed",
    agent_id=self.name,
    document_id=request.document_id,
    error_type=type(e).__name__,
    error_message=str(e),
    file_path=request.file_path
)
```

## Configuration Management Standards

**YAML Configuration Schema:**
```yaml
# app/config/agents.yaml
agents:
  pdf_processor:
    enabled: true
    max_concurrent_jobs: 3
    timeout_seconds: 300
    tools:
      ocr:
        engine: "tesseract"
        language: "por"
        dpi: 300
      pdf_reader:
        extract_images: false
        preserve_layout: true
      vector_storage:
        batch_size: 100
        embedding_model: "gemini"
    
  questionnaire_writer:
    enabled: true
    max_concurrent_jobs: 2
    timeout_seconds: 180
    tools:
      llm:
        model: "gemini-2.5-pro"
        temperature: 0.7
        max_tokens: 4000
      rag:
        similarity_threshold: 0.8
        max_context_length: 8000
```

**Configuration Validation:**
```python
from pydantic import BaseModel, validator
from typing import Dict, Any

class AgentConfig(BaseModel):
    enabled: bool = True
    max_concurrent_jobs: int = 1
    timeout_seconds: int = 300
    tools: Dict[str, Any] = {}
    
    @validator('max_concurrent_jobs')
    def validate_concurrent_jobs(cls, v):
        if v < 1 or v > 10:
            raise ValueError('max_concurrent_jobs must be between 1 and 10')
        return v
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        if v < 30 or v > 600:
            raise ValueError('timeout_seconds must be between 30 and 600')
        return v
```

## Testing Standards

**Agent Unit Test Template:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.pdf_processor_agent import PDFProcessorAgent
from app.models.document import Document

class TestPDFProcessorAgent:
    """Test suite for PDF Processor Agent."""
    
    @pytest.fixture
    def agent_config(self):
        return {
            "timeout_seconds": 300,
            "max_concurrent_jobs": 3,
            "tools": {
                "ocr": {"engine": "tesseract"},
                "pdf_reader": {"extract_images": False}
            }
        }
    
    @pytest.fixture
    def pdf_agent(self, agent_config):
        return PDFProcessorAgent("test_pdf_processor", agent_config)
    
    async def test_process_document_success(self, pdf_agent):
        # Arrange
        mock_request = MagicMock()
        mock_request.file_path = "/path/to/test.pdf"
        mock_request.document_id = "test-doc-123"
        
        # Mock tool responses
        pdf_agent.pdf_reader.extract_text = AsyncMock(return_value="Extracted text")
        pdf_agent.vector_storage.embed_content = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        # Act
        result = await pdf_agent.process(mock_request)
        
        # Assert
        assert result.content == "Extracted text"
        assert result.vectors == [0.1, 0.2, 0.3]
        assert result.document_id == "test-doc-123"
    
    async def test_process_document_failure(self, pdf_agent):
        # Test error handling
        mock_request = MagicMock()
        pdf_agent.pdf_reader.extract_text = AsyncMock(side_effect=Exception("PDF corrupted"))
        
        with pytest.raises(AgentProcessingError):
            await pdf_agent.process(mock_request)
    
    async def test_health_check(self, pdf_agent):
        # Test health check functionality
        health_status = await pdf_agent.health_check()
        assert health_status.healthy is True
```

**Integration Test Template:**
```python
class TestAgentWorkflow:
    """Integration tests for complete agent workflows."""
    
    async def test_document_processing_workflow(self, test_db, test_client):
        # Upload document
        with open("test_files/sample.pdf", "rb") as f:
            response = test_client.post("/documents/process", files={"file": f})
        
        assert response.status_code == 200
        document_id = response.json()["document_id"]
        
        # Verify database storage
        document = test_db.query(Document).filter_by(id=document_id).first()
        assert document is not None
        assert document.content is not None
        assert document.vectors is not None
```