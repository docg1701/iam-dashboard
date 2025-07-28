# Component Architecture

## Core Agent Components

**AgentManager (Central Orchestrator):**
```python
class AgentManager:
    """Central management for all autonomous agents."""
    
    def __init__(self, container: Container):
        self.container = container
        self.agents: Dict[str, AgentPlugin] = {}
        self.config = container.config()
    
    async def load_agent(self, agent_id: str) -> AgentPlugin
    async def enable_agent(self, agent_id: str) -> bool
    async def disable_agent(self, agent_id: str) -> bool
    async def get_agent_status(self, agent_id: str) -> AgentStatus
```

**AgentPlugin Interface:**
```python
from abc import ABC, abstractmethod

class AgentPlugin(ABC):
    """Base interface for all agent plugins."""
    
    @abstractmethod
    async def initialize(self) -> bool
    
    @abstractmethod
    async def process(self, request: Any) -> Any
    
    @abstractmethod
    async def health_check(self) -> HealthStatus
    
    @abstractmethod
    def get_capabilities(self) -> List[str]
```

## Agent Implementations

**PDFProcessorAgent:**
```python
from agno import Agent
from app.tools.pdf_tools import PDFReaderTool, OCRProcessorTool
from app.tools.vector_storage_tools import VectorStorageTool

class PDFProcessorAgent(Agent):
    """Autonomous agent for PDF document processing."""
    
    def __init__(self, name: str = "pdf_processor"):
        super().__init__(name)
        self.pdf_reader = PDFReaderTool()
        self.ocr_processor = OCRProcessorTool()
        self.vector_storage = VectorStorageTool()
    
    async def process_document(self, document_path: str) -> ProcessingResult:
        """Process PDF document with full pipeline."""
        # Extract text and metadata
        content = await self.pdf_reader.extract_text(document_path)
        
        # OCR processing if needed
        if content.needs_ocr:
            content = await self.ocr_processor.process(document_path)
        
        # Generate and store embeddings
        vectors = await self.vector_storage.embed_content(content)
        
        return ProcessingResult(
            content=content,
            vectors=vectors,
            metadata=content.metadata
        )
```

**QuestionnaireAgent:**
```python
class QuestionnaireAgent(Agent):
    """Autonomous agent for questionnaire generation."""
    
    def __init__(self, name: str = "questionnaire_writer"):
        super().__init__(name)
        self.rag_retriever = RAGRetrieverTool()
        self.llm_processor = LLMProcessorTool()
        self.template_manager = TemplateManagerTool()
    
    async def generate_questionnaire(self, request: QuestionnaireRequest) -> Questionnaire:
        """Generate legal questionnaire using RAG and LLM."""
        # Retrieve relevant context
        context = await self.rag_retriever.get_context(request.client_id, request.case_type)
        
        # Apply template
        template = await self.template_manager.get_template(request.questionnaire_type)
        
        # Generate content
        content = await self.llm_processor.generate(
            template=template,
            context=context,
            requirements=request.requirements
        )
        
        return Questionnaire(
            content=content,
            template_id=template.id,
            metadata=request.metadata
        )
```

## Tool Architecture

**Modular Tool System:**
```python
# PDF Processing Tools
class PDFReaderTool:
    async def extract_text(self, path: str) -> DocumentContent
    async def extract_metadata(self, path: str) -> DocumentMetadata

class OCRProcessorTool:
    async def process(self, path: str) -> DocumentContent
    async def detect_language(self, content: str) -> str

# Vector Storage Tools
class VectorStorageTool:
    async def embed_content(self, content: DocumentContent) -> List[float]
    async def store_vectors(self, vectors: List[float], metadata: dict) -> str
    async def search_similar(self, query_vector: List[float]) -> List[SearchResult]

# LLM Integration Tools
class LLMProcessorTool:
    async def generate(self, template: str, context: str, **kwargs) -> str
    async def summarize(self, content: str) -> str
    async def extract_entities(self, content: str) -> List[Entity]
```

## Plugin Registration System

**Plugin Registration:**
```python
class PDFProcessorPlugin(AgentPlugin):
    """Plugin wrapper for PDF Processor Agent."""
    
    def __init__(self, container: Container):
        self.agent = PDFProcessorAgent()
        self.db_session = container.db_session()
        self.config = container.config.agents.pdf_processor()
    
    async def initialize(self) -> bool:
        """Initialize agent with configuration."""
        return await self.agent.setup(self.config)
    
    async def process(self, request: DocumentProcessRequest) -> DocumentProcessResult:
        """Process document through agent."""
        result = await self.agent.process_document(request.file_path)
        
        # Save to existing database schema
        await self._save_to_database(result, request)
        
        return DocumentProcessResult(
            document_id=result.document_id,
            content=result.content,
            vectors=result.vectors
        )
```

## Container Integration

**Extended Container Configuration:**
```python
# app/containers.py
from dependency_injector import containers, providers
from app.agents.pdf_processor_agent import PDFProcessorPlugin
from app.agents.questionnaire_agent import QuestionnairePlugin
from app.core.agent_manager import AgentManager

class Container(containers.DeclarativeContainer):
    # Existing providers
    config = providers.Configuration()
    db_session = providers.Resource(create_db_session)
    client_service = providers.Factory(ClientService, db_session=db_session)
    user_service = providers.Factory(UserService, db_session=db_session)
    
    # New agent providers
    agent_manager = providers.Singleton(
        AgentManager,
        container=providers.Self()
    )
    
    pdf_processor_plugin = providers.Factory(
        PDFProcessorPlugin,
        container=providers.Self()
    )
    
    questionnaire_plugin = providers.Factory(
        QuestionnairePlugin,
        container=providers.Self()
    )
```