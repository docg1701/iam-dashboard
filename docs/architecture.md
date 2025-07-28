# IAM Dashboard Brownfield Enhancement Architecture

| Data | Versão | Descrição | Autor |
| :--- | :--- | :--- | :--- |
| 27/07/2025 | 1.0 | Migração direta para arquitetura de agentes autônomos | Winston, Architect |

## Introduction

### Scope Verification and Requirements Validation

Based on comprehensive analysis of the existing IAM Dashboard system and the detailed PRD document, this architectural enhancement involves:

**Enhancement Scope:**
- ✅ **Major Feature Modification** (migrating from direct services to agent-based architecture)
- ✅ **Integration with New Systems** (Agno framework integration) 
- ✅ **Technology Stack Upgrade** (adding autonomous agent layer)

**Complexity Verification:**
This is **definitely** a substantial enhancement requiring full architectural planning. The migration from legacy services to Agno-based autonomous agents involves:
- Architectural changes across multiple layers (API, services, UI)
- Complete replacement of Celery workers with autonomous agents
- Plugin system implementation with dependency injection management
- Multiple coordinated development phases spanning 6-8 weeks

**Requirements Validation:**
✅ Completed brownfield-prd.md available at `docs/prd.md`
✅ Existing technical documentation comprehensive
✅ Access to existing project structure confirmed
✅ Team capabilities assessed for Agno framework adoption

### Existing Project Analysis

**Current Project State:**
IAM Dashboard is a fully functional SaaS platform for law firms featuring document processing, questionnaire generation, and user management. The system currently uses FastAPI backend with PostgreSQL/pgvector, Celery+Redis for async processing, and NiceGUI for the frontend.

**Technology Stack Analysis:**
- **Languages:** Python 3.12+
- **Frameworks:** FastAPI (API), NiceGUI (UI), SQLAlchemy 2.0 (ORM)
- **Database:** PostgreSQL with pgvector extension
- **Infrastructure:** Celery + Redis (to be replaced)
- **External Dependencies:** Google Gemini API, Llama-Index RAG
- **Dependency Management:** python-dependency-injector
- **Authentication:** Python-JOSE with 2FA (PyOTP)

**Current Architecture Style:**
- Service-oriented architecture with direct service calls
- Container-based dependency injection
- Async processing via Celery workers
- Modular UI components with NiceGUI

## Enhancement Scope and Integration Strategy

### Integration Approach: Direct Replacement Strategy

**Rationale for Direct Replacement:**
Given that the system is not yet in production, we're implementing a **direct replacement approach** rather than complex brownfield bridge architecture. This eliminates the need for legacy compatibility layers and enables faster, cleaner implementation of the autonomous agent architecture.

**Key Integration Decisions:**
1. **Complete Migration:** Replace Celery workers entirely with Agno agents
2. **Contract Preservation:** Maintain identical API request/response schemas
3. **UI Consistency:** Preserve existing NiceGUI patterns and user experiences
4. **Data Integrity:** Use existing PostgreSQL schema without modifications

### Integration Points Analysis

**Database Integration:**
- **Direct Connection:** Agno agents connect directly to existing PostgreSQL+pgvector
- **Schema Preservation:** Maintain current database schema without compatibility layers
- **Vector Operations:** Agents use existing Llama-Index integration for embeddings

**API Integration:**
- **FastAPI Endpoints:** Replace Celery-based endpoints with direct Agno agent calls
- **Synchronous Processing:** Eliminate async task queues in favor of direct agent execution
- **Response Contracts:** Maintain identical request/response schemas

**Frontend Integration:**
- **NiceGUI Components:** Update existing UI components to call agent APIs directly
- **Real-time Updates:** Implement agent status and progress indicators
- **Configuration Interface:** Add agent management panels to existing settings

### Legacy System Migration Plan

**Phase 1: Infrastructure Setup**
- Implement AgentManager with dependency injection
- Create plugin architecture foundation
- Establish configuration management system

**Phase 2: Agent Implementation**
- Develop PDFProcessorAgent replacing Celery workers
- Implement QuestionnaireAgent replacing direct services
- Create agent-specific tools and utilities

**Phase 3: API Migration**
- Update FastAPI endpoints for direct agent calls
- Ensure response schema compatibility
- Implement synchronous processing patterns

**Phase 4: UI Enhancement**
- Add agent management interfaces
- Implement status monitoring and configuration
- Integrate with existing NiceGUI patterns

**Phase 5: Legacy Cleanup**
- Remove Celery workers and unused services
- Clean up obsolete dependencies
- Complete documentation updates

## Tech Stack Alignment

### Current vs. Target Architecture

**Current Implementation (To Be Replaced):**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NiceGUI UI   │────│   FastAPI       │────│  PostgreSQL     │
│                 │    │   + Services    │    │  + pgvector     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │ Celery Workers  │
                       │ + Redis Queue   │
                       └─────────────────┘
```

**Target Agent Architecture:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NiceGUI UI   │────│   FastAPI       │────│  PostgreSQL     │
│  + Agent Mgmt   │    │  + AgentManager │    │  + pgvector     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │ Agno Agents     │
                       │ + Plugin System │
                       └─────────────────┘
```

### Technology Integration Matrix

| Component | Current | Target (Updated July 2025) | Integration Strategy |
|-----------|---------|------------------------------|---------------------|
| **Framework** | FastAPI>=0.104.0 | FastAPI>=0.116.0 + Agno>=1.7.5 | Direct integration, maintain existing endpoints |
| **Database** | PostgreSQL+pgvector | PostgreSQL+pgvector + asyncpg>=0.30.0 | No changes, direct agent connection |
| **Processing** | Celery+Redis | Agno Agents (1.7.5) | Complete replacement, maintain functionality |
| **DI Container** | dependency-injector>=4.48.0 | dependency-injector>=4.48.1 + Agent plugins | Extend existing container |
| **Frontend** | NiceGUI>=1.4.0 | NiceGUI>=2.21.0 + Agent UI | Add management interfaces |
| **Authentication** | Python-JOSE + 2FA | Python-JOSE + 2FA | No changes |
| **External APIs** | google-generativeai>=0.3.0 | google-genai>=0.1.0 | ⚠️ CRITICAL: Replace deprecated package |
| **RAG Framework** | llama-index>=0.12.0 | llama-index>=0.12.52 | Update to latest stable |
| **PDF Processing** | pymupdf>=1.24.0 | pymupdf>=1.26.0 | Update to latest stable |

### New Technology Components

**Agno Framework Integration (Updated July 2025):**
- **Latest Version:** agno>=1.7.5 (July 17, 2025)
- **Version Requirements:** Python 3.12+ (recommended)
- **Core Installation:** `uv add agno>=1.7.5`
- **Agent Base Classes:** Foundation for autonomous agents
- **Tool Architecture:** Modular tools for PDF processing, OCR, vector storage
- **Plugin System:** Dynamic agent loading and lifecycle management
- **Performance Characteristics (v1.7.5):** 
  - Agent instantiation: ~3μs
  - Memory footprint: ~6.5 KiB per agent
  - Supports 23+ model providers
  - ~10,000x faster than LangGraph
  - ~50x less memory than LangGraph
- **Multi-modal Support:** Text, image, audio, video input/output

**Modern Dependency Management (Updated July 2025):**
```bash
# Using UV (recommended for performance)
uv add agno>=1.7.5
uv add google-genai>=0.1.0      # NEW official Gemini SDK (replaces google-generativeai)
uv add fastapi>=0.116.0         # Latest stable
uv add llama-index>=0.12.52     # Latest RAG framework
uv add nicegui>=2.21.0          # Latest UI framework

# IMPORTANT: Remove deprecated package
uv remove google-generativeai   # DEPRECATED - EOL September 30, 2025

# Environment variables required
export GOOGLE_API_KEY=your-gemini-api-key    # For new google-genai SDK
export AGNO_TELEMETRY=false                  # Disable telemetry in production
```

**Critical Migration Notice:**
```
⚠️ URGENT: google-generativeai package deprecation
- Current: google-generativeai (DEPRECATED - EOL Sept 30, 2025)
- Replace with: google-genai (Official Google SDK, GA ready)
- Benefits: Access to Gemini 2.0, Live API, Veo model
- Code changes required: Update import statements
```

**Agno Compatibility Requirements:**
- **Python Version:** 3.12+ (tested and recommended)
- **Existing Stack Compatibility:** 
  - ✅ FastAPI: Direct integration via pre-built routes
  - ✅ PostgreSQL: Native database connection support
  - ✅ NiceGUI: Compatible UI framework integration
  - ✅ Docker: Container deployment supported
- **Production Considerations:**
  - Monitoring available via agno.com platform
  - Telemetry can be disabled for privacy
  - Resource limits configurable per agent
  - FastAPI route integration for web deployment

**Configuration Management:**
- **YAML Configuration:** Agent-specific settings in version-controlled files
- **UI Configuration:** Runtime parameter adjustments through administrative interface
- **Environment Integration:** Core settings through existing environment variables
- **Telemetry Control:** Can be disabled with `AGNO_TELEMETRY=false`

**Potential Dependency Conflicts:**
- **Risk Level:** LOW - Agno has minimal core dependencies
- **Mitigation:** Use virtual environment isolation with UV
- **Testing Required:** Validate against existing python-dependency-injector
- **Monitoring:** Check for version conflicts during installation

## Data Models and Schema Changes

### Database Schema Strategy: Zero Modification Approach

**Rationale:**
Since agents will integrate directly with existing PostgreSQL infrastructure, we maintain the current schema without modifications. This ensures data integrity and eliminates migration risks.

**Current Schema Preservation:**
```sql
-- Existing tables remain unchanged
users (user_id, email, password_hash, ...)
clients (client_id, user_id, name, ...)
documents (document_id, client_id, content, vectors, ...)
questionnaire_drafts (draft_id, client_id, content, ...)
```

**Agent Metadata Strategy:**
Instead of new tables, agents will use existing metadata patterns:
- Document processing status tracked in existing `documents` table
- Agent execution logs stored in existing logging infrastructure
- Configuration managed through YAML files and environment variables

### Data Flow Integration

**Document Processing Flow:**
```
PDF Upload → PDFProcessorAgent → Existing DB Schema
    ↓              ↓                    ↓
FastAPI      Agno Tools         documents table
Endpoint   (PDF, OCR, Vector)    + metadata
```

**Questionnaire Generation Flow:**
```
Request → QuestionnaireAgent → RAG Retrieval → DB Storage
   ↓           ↓                    ↓             ↓
FastAPI   Llama-Index         Existing Vector   questionnaire_drafts
Endpoint  Integration         Store (pgvector)  table
```

### Vector Store Integration

**Existing Integration Preserved:**
- **Llama-Index Integration:** Agents use existing Llama-Index setup
- **pgvector Extension:** Continue using PostgreSQL vector capabilities
- **Embedding Strategy:** Maintain current embedding generation and storage patterns

## Component Architecture

### Core Agent Components

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

### Agent Implementations

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

### Tool Architecture

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

### Plugin Registration System

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

### Container Integration

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

## API Design and Integration

### API Endpoint Migration Strategy

**Current Celery-based Endpoints (To Be Replaced):**
```python
# Current implementation
@router.post("/documents/process")
async def process_document(file: UploadFile):
    # Queue Celery task
    task = process_document_task.delay(file.filename)
    return {"task_id": task.id, "status": "queued"}

@router.get("/documents/status/{task_id}")
async def get_processing_status(task_id: str):
    # Check Celery task status
    task = AsyncResult(task_id)
    return {"status": task.status, "result": task.result}
```

**New Agent-based Endpoints:**
```python
# New agent implementation
@router.post("/documents/process")
@inject
async def process_document(
    file: UploadFile,
    agent_manager: AgentManager = Provide[Container.agent_manager]
):
    # Direct agent processing
    pdf_agent = await agent_manager.get_agent("pdf_processor")
    result = await pdf_agent.process(DocumentProcessRequest(
        file_path=file.filename,
        client_id=request.client_id
    ))
    
    return DocumentProcessResponse(
        document_id=result.document_id,
        status="completed",
        content_summary=result.summary
    )
```

### Response Schema Preservation

**Maintaining API Contracts:**
```python
# Identical response schemas
class DocumentProcessResponse(BaseModel):
    document_id: str
    status: str
    content_summary: Optional[str] = None
    error_message: Optional[str] = None

class QuestionnaireGenerationResponse(BaseModel):
    questionnaire_id: str
    content: str
    template_used: str
    generated_at: datetime
```

### New Agent Management Endpoints

**Administrative API Endpoints:**
```python
@router.get("/admin/agents/status")
@inject
async def get_agents_status(
    agent_manager: AgentManager = Provide[Container.agent_manager],
    current_user: User = Depends(get_current_admin_user)
):
    """Get status of all registered agents."""
    agents_status = await agent_manager.get_all_status()
    return AgentsStatusResponse(agents=agents_status)

@router.post("/admin/agents/{agent_id}/enable")
@inject
async def enable_agent(
    agent_id: str,
    agent_manager: AgentManager = Provide[Container.agent_manager],
    current_user: User = Depends(get_current_admin_user)
):
    """Enable specific agent."""
    success = await agent_manager.enable_agent(agent_id)
    return {"agent_id": agent_id, "enabled": success}

@router.put("/admin/agents/{agent_id}/config")
@inject
async def update_agent_config(
    agent_id: str,
    config_update: AgentConfigUpdate,
    agent_manager: AgentManager = Provide[Container.agent_manager],
    current_user: User = Depends(get_current_admin_user)
):
    """Update agent configuration."""
    updated_config = await agent_manager.update_config(agent_id, config_update)
    return AgentConfigResponse(agent_id=agent_id, config=updated_config)
```

### Error Handling Integration

**Consistent Error Response Format:**
```python
class APIError(Exception):
    def __init__(self, message: str, error_code: str, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

class AgentError(APIError):
    """Agent-specific errors."""
    pass

@app.exception_handler(AgentError)
async def agent_error_handler(request: Request, exc: AgentError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "type": "agent_error"
            }
        }
    )
```

## Source Tree Integration

### Current Project Structure
```
iam-dashboard/
├── app/
│   ├── main.py                 # Entry point
│   ├── core/                   # Core modules
│   │   ├── auth.py
│   │   └── database.py
│   ├── models/                 # SQLAlchemy models
│   ├── repositories/           # Data access layer
│   ├── services/              # Business logic (TO BE REPLACED)
│   ├── ui_components/         # NiceGUI components
│   ├── api/                   # FastAPI endpoints
│   └── workers/               # Celery workers (TO BE REMOVED)
├── alembic/                   # Database migrations
├── tests/
└── docs/
```

### Target Project Structure with Agents
```
iam-dashboard/
├── app/
│   ├── main.py                 # Entry point (MODIFIED)
│   ├── core/                   # Core modules
│   │   ├── auth.py
│   │   ├── database.py
│   │   └── agent_manager.py    # NEW: Central agent management
│   ├── models/                 # SQLAlchemy models (UNCHANGED)
│   ├── repositories/           # Data access layer (UNCHANGED)
│   ├── agents/                 # NEW: Agno agents
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── pdf_processor_agent.py
│   │   └── questionnaire_agent.py
│   ├── tools/                  # NEW: Agno tools
│   │   ├── __init__.py
│   │   ├── pdf_tools.py
│   │   ├── vector_storage_tools.py
│   │   └── ocr_tools.py
│   ├── plugins/                # NEW: Agent plugins
│   │   ├── __init__.py
│   │   ├── pdf_processor_plugin.py
│   │   └── questionnaire_plugin.py
│   ├── ui_components/         # NiceGUI components (MODIFIED)
│   │   ├── dashboard.py        # Add agent status
│   │   ├── admin_control_panel.py # NEW: Agent management
│   │   └── ...
│   ├── api/                   # FastAPI endpoints (MODIFIED)
│   │   ├── documents.py        # Replace Celery with agents
│   │   ├── questionnaires.py   # Replace services with agents
│   │   └── admin.py           # NEW: Agent management API
│   ├── config/                # NEW: Agent configurations
│   │   └── agents.yaml
│   └── containers.py          # MODIFIED: Add agent providers
├── tests/                     # MODIFIED: Add agent tests
│   ├── unit/
│   │   ├── test_agents/        # NEW: Agent tests
│   │   └── test_tools/         # NEW: Tool tests
│   └── integration/
│       └── test_agent_workflows.py # NEW: Full workflow tests
└── docs/                      # UPDATED: Add agent documentation
    ├── architecture.md         # THIS FILE
    └── agent-development-guide.md # NEW
```

### File Integration Details

**Modified Files:**

1. **app/main.py** - Initialize agent manager
```python
# Add agent initialization
from app.core.agent_manager import AgentManager

@app.on_event("startup")
async def startup_event():
    # Existing initialization
    await init_database()
    
    # NEW: Initialize agent manager
    agent_manager = app.state.container.agent_manager()
    await agent_manager.initialize()
```

2. **app/containers.py** - Extended dependency injection
```python
# Add agent-related providers
agent_manager = providers.Singleton(AgentManager, container=providers.Self())
pdf_processor_plugin = providers.Factory(PDFProcessorPlugin, container=providers.Self())
questionnaire_plugin = providers.Factory(QuestionnairePlugin, container=providers.Self())
```

3. **app/ui_components/dashboard.py** - Add agent status
```python
# Add agent status cards
@inject
def agent_status_section(agent_manager: AgentManager = Provide[Container.agent_manager]):
    with ui.card().classes("w-full"):
        ui.label("Agent Status").classes("text-lg font-bold")
        # Agent status indicators
```

**New Files:**

1. **app/agents/** - All agent implementations
2. **app/tools/** - Modular tool components
3. **app/plugins/** - Plugin system implementation
4. **app/config/agents.yaml** - Agent configuration
5. **app/ui_components/admin_control_panel.py** - Agent management UI
6. **app/api/admin.py** - Agent management API

**Removed Files:**

1. **app/services/** - Replaced with agents
2. **app/workers/** - Replaced with agents

### Import Path Strategy

**Consistent Import Patterns:**
```python
# Agent imports
from app.agents.pdf_processor_agent import PDFProcessorAgent
from app.tools.pdf_tools import PDFReaderTool
from app.plugins.pdf_processor_plugin import PDFProcessorPlugin

# Existing imports (unchanged)
from app.models.user import User
from app.repositories.client_repository import ClientRepository
from app.core.database import get_db_session
```

## Infrastructure and Deployment Integration

### Deployment Strategy

**Current Deployment (VPS + Docker):**
```yaml
# docker-compose.yml (existing)
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: iam_dashboard
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
  
  redis:
    image: redis:7-alpine
  
  celery_worker:  # TO BE REMOVED
    build: .
    command: celery -A app.workers.celery_app worker
    depends_on:
      - redis
      - postgres
```

**Target Deployment (Agent-based):**
```yaml
# docker-compose.yml (updated)
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AGNO_CONFIG_PATH=/app/config/agents.yaml
      - AGENT_MANAGEMENT_ENABLED=true
    volumes:
      - ./app/config:/app/config
    depends_on:
      - postgres
      - redis  # Still used for caching
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: iam_dashboard
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
  
  redis:
    image: redis:7-alpine
    # Still used for caching and session storage
```

### Environment Configuration

**Agent-specific Environment Variables:**
```bash
# .env additions
# Agent Configuration
AGNO_CONFIG_PATH="/app/config/agents.yaml"
AGENT_MANAGEMENT_ENABLED=true
AGENT_LOG_LEVEL="INFO"
AGENT_HEALTH_CHECK_INTERVAL=30

# Agent Resources
MAX_CONCURRENT_AGENTS=5
AGENT_MEMORY_LIMIT="512MB"
AGENT_TIMEOUT_SECONDS=300

# Tool Configuration
OCR_ENGINE="tesseract"  # or "gemini"
PDF_PROCESSING_TIMEOUT=120
VECTOR_BATCH_SIZE=100
```

### Resource Requirements

**Updated Resource Requirements:**
```yaml
# Previous: 4 vCPUs, 4GB RAM
# Updated for agents: 4 vCPUs, 6GB RAM

# Memory allocation:
# - FastAPI + NiceGUI: 1.5GB
# - PostgreSQL: 1GB
# - Redis: 256MB
# - Agent Manager + Active Agents: 2GB
# - PDF/OCR Processing: 1GB
# - System overhead: 256MB
```

### Monitoring and Health Checks

**Agent Health Monitoring:**
```python
class AgentHealthCheck:
    async def check_agent_health(self, agent_id: str) -> HealthStatus:
        agent = await self.agent_manager.get_agent(agent_id)
        
        return HealthStatus(
            agent_id=agent_id,
            status=agent.status,
            last_activity=agent.last_activity,
            memory_usage=agent.memory_usage,
            response_time=await self._measure_response_time(agent)
        )
```

**Prometheus Metrics (if monitoring available):**
```python
# app/monitoring/agent_metrics.py
from prometheus_client import Counter, Histogram, Gauge

agent_processing_total = Counter('agent_processing_total', 'Total agent processing requests', ['agent_id'])
agent_processing_duration = Histogram('agent_processing_duration_seconds', 'Agent processing duration', ['agent_id'])
agent_active_count = Gauge('agent_active_count', 'Number of active agents')
```

### Backup and Recovery

**Agent Configuration Backup:**
- **YAML Files:** Version controlled in repository
- **Runtime Configuration:** Backed up with regular database backups
- **Agent State:** Stateless agents, no persistent state backup needed

**Recovery Procedures:**
1. **Agent Failure:** Automatic restart via AgentManager
2. **Configuration Corruption:** Rollback to previous YAML configuration
3. **System Failure:** Standard database recovery + agent reinitialization

## Rollback Procedures Documentation

### Critical Rollback Overview

This section provides detailed step-by-step rollback procedures for each integration point during the brownfield migration from Celery-based architecture to Agno agent-based architecture. All procedures are designed to restore system functionality to the last known working state with minimal data loss.

### 1. Agent Manager Integration Rollback

**When to Execute:**
- AgentManager fails to initialize during startup
- Plugin registration system corruption
- Dependency injection container conflicts
- Agent lifecycle management failures

**Pre-Rollback Assessment:**
```bash
# Check system status
curl -f http://localhost:8000/health || echo "System down"
docker ps | grep iam-dashboard
tail -n 50 /var/log/iam-dashboard/app.log | grep -i error
```

**Step-by-Step Rollback Procedure:**

1. **Stop Current Services**
```bash
# Stop main application
docker-compose stop web
# Or if running directly
pkill -f "python app/main.py"
```

2. **Backup Current State**
```bash
# Backup current configuration
cp app/config/agents.yaml app/config/agents.yaml.failed.$(date +%Y%m%d_%H%M%S)
# Backup container configuration
cp app/containers.py app/containers.py.failed.$(date +%Y%m%d_%H%M%S)
```

3. **Restore Legacy Service Architecture**
```bash
# Restore previous containers.py (without agent providers)
git checkout HEAD~1 -- app/containers.py
# Remove agent manager imports from main.py
git checkout HEAD~1 -- app/main.py
```

4. **Remove Agent-specific Files**
```bash
# Remove agent directories (preserve as backup)
mv app/agents app/agents.backup.$(date +%Y%m%d_%H%M%S)
mv app/tools app/tools.backup.$(date +%Y%m%d_%H%M%S)
mv app/plugins app/plugins.backup.$(date +%Y%m%d_%H%M%S)
mv app/config app/config.backup.$(date +%Y%m%d_%H%M%S)
```

5. **Restore Celery Workers**
```bash
# Restore Celery worker files
git checkout HEAD~1 -- app/workers/
# Restore service files
git checkout HEAD~1 -- app/services/
```

6. **Update Docker Compose**
```bash
# Restore Celery worker service
git checkout HEAD~1 -- docker-compose.yml
```

7. **Restart System**
```bash
# Restart with legacy architecture
docker-compose up -d
# Verify system health
curl -f http://localhost:8000/health
```

8. **Verify Functionality**
```bash
# Test document processing
curl -X POST -F "file=@test.pdf" http://localhost:8000/documents/process
# Test questionnaire generation
curl -X POST -H "Content-Type: application/json" -d '{"client_id":"test","case_type":"trabalhista"}' http://localhost:8000/questionnaires/generate
```

**Post-Rollback Actions:**
- Notify development team of rollback completion
- Schedule investigation meeting within 24 hours
- Document failure cause in rollback-incidents.md
- Plan remediation strategy

### 2. Database Integration Rollback

**When to Execute:**
- Agent database connections failing
- Vector storage corruption
- Schema migration issues
- PostgreSQL+pgvector integration problems

**Pre-Rollback Assessment:**
```bash
# Check database connectivity
psql -h localhost -U $DB_USER -d iam_dashboard -c "SELECT 1;"
# Check vector extension
psql -h localhost -U $DB_USER -d iam_dashboard -c "SELECT * FROM pg_extension WHERE extname='vector';"
# Check recent agent transactions
psql -h localhost -U $DB_USER -d iam_dashboard -c "SELECT * FROM documents WHERE created_at > NOW() - INTERVAL '1 hour';"
```

**Step-by-Step Rollback Procedure:**

1. **Stop All Database-Writing Processes**
```bash
# Stop web application
docker-compose stop web
# Stop any running Celery workers
docker-compose stop celery_worker
```

2. **Create Emergency Database Backup**
```bash
# Full database backup
pg_dump -h localhost -U $DB_USER iam_dashboard > emergency_backup_$(date +%Y%m%d_%H%M%S).sql
# Backup specific tables if corruption detected
pg_dump -h localhost -U $DB_USER -t documents -t questionnaire_drafts iam_dashboard > critical_tables_backup_$(date +%Y%m%d_%H%M%S).sql
```

3. **Assess Database Integrity**
```bash
# Check for corruption
psql -h localhost -U $DB_USER -d iam_dashboard -c "SELECT pg_size_pretty(pg_database_size('iam_dashboard'));"
# Verify vector extension
psql -h localhost -U $DB_USER -d iam_dashboard -c "SELECT COUNT(*) FROM documents WHERE vectors IS NOT NULL;"
```

4. **Rollback Database Schema (if needed)**
```bash
# Check migration history
uv run alembic history
# Rollback to previous working migration
uv run alembic downgrade -1
# Verify rollback success
uv run alembic current
```

5. **Restore Agent Database Connections**
```bash
# Update database configuration to remove agent-specific settings
sed -i 's/AGENT_DB_POOL_SIZE=.*/AGENT_DB_POOL_SIZE=10/' .env
sed -i 's/AGENT_DB_TIMEOUT=.*/AGENT_DB_TIMEOUT=30/' .env
```

6. **Test Database Recovery**
```bash
# Start minimal application
docker-compose up -d postgres redis
# Test basic connectivity
python -c "
from app.core.database import get_db_session
with get_db_session() as db:
    result = db.execute('SELECT COUNT(*) FROM users').scalar()
    print(f'User count: {result}')
"
```

7. **Gradual Service Restoration**
```bash
# Start web application
docker-compose up -d web
# Test API endpoints
curl -f http://localhost:8000/health
# Test database-dependent endpoints
curl -f http://localhost:8000/users/me -H "Authorization: Bearer $TEST_TOKEN"
```

**Post-Rollback Validation:**
- Verify all critical data intact
- Test document upload and retrieval
- Validate user authentication
- Check questionnaire generation functionality

### 3. API Endpoint Migration Rollback

**When to Execute:**
- Agent-based endpoints returning errors
- Response schema incompatibility
- FastAPI route registration failures
- Authentication/authorization issues with new endpoints

**Pre-Rollback Assessment:**
```bash
# Test critical API endpoints
curl -f http://localhost:8000/documents/process || echo "Document processing API failed"
curl -f http://localhost:8000/questionnaires/generate || echo "Questionnaire API failed"
curl -f http://localhost:8000/admin/agents/status || echo "Agent management API failed"
# Check API response schemas
curl -s http://localhost:8000/documents/process | jq . || echo "Invalid JSON response"
```

**Step-by-Step Rollback Procedure:**

1. **Immediate API Isolation**
```bash
# Stop web application
docker-compose stop web
# Backup current API files
cp -r app/api app/api.backup.$(date +%Y%m%d_%H%M%S)
```

2. **Restore Legacy API Endpoints**
```bash
# Restore previous API implementations
git checkout HEAD~1 -- app/api/documents.py
git checkout HEAD~1 -- app/api/questionnaires.py
# Remove new agent management endpoints
rm -f app/api/admin.py
```

3. **Update FastAPI Route Registration**
```bash
# Restore previous main.py routing
git checkout HEAD~1 -- app/main.py
# Verify no agent-specific imports remain
grep -r "agent" app/api/ && echo "WARNING: Agent imports found"
```

4. **Restore Service Dependencies**
```bash
# Restore service layer files
git checkout HEAD~1 -- app/services/
# Update import statements in API files
find app/api/ -name "*.py" -exec sed -i 's/from app\.agents\./from app.services./g' {} \;
```

5. **Update Request/Response Models**
```bash
# Restore previous Pydantic models if modified
git checkout HEAD~1 -- app/models/requests.py
git checkout HEAD~1 -- app/models/responses.py
```

6. **Restart API Services**
```bash
# Start application with restored APIs
docker-compose up -d web
# Wait for startup
sleep 10
```

7. **Comprehensive API Testing**
```bash
# Test document upload
curl -X POST -F "file=@tests/fixtures/sample.pdf" \
  -H "Authorization: Bearer $TEST_TOKEN" \
  http://localhost:8000/documents/process
  
# Test questionnaire generation
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TEST_TOKEN" \
  -d '{"client_id":"test","case_type":"trabalhista"}' \
  http://localhost:8000/questionnaires/generate
  
# Test user management
curl -H "Authorization: Bearer $TEST_TOKEN" \
  http://localhost:8000/users/me
```

**API Rollback Validation:**
- All previous API endpoints functional
- Response schemas unchanged
- Authentication/authorization working
- Performance within acceptable limits

### 4. UI Component Integration Rollback

**When to Execute:**
- NiceGUI components failing to render
- Agent management interfaces causing crashes
- Frontend/backend communication errors
- User experience degradation

**Pre-Rollback Assessment:**
```bash
# Check UI accessibility
curl -f http://localhost:8000/ || echo "UI not accessible"
# Check JavaScript console for errors (if applicable)
# Test critical UI workflows
curl -f http://localhost:8000/dashboard || echo "Dashboard failed"
```

**Step-by-Step Rollback Procedure:**

1. **Backup Current UI State**
```bash
# Backup current UI components
cp -r app/ui_components app/ui_components.backup.$(date +%Y%m%d_%H%M%S)
```

2. **Restore Previous UI Components**
```bash
# Restore dashboard without agent status
git checkout HEAD~1 -- app/ui_components/dashboard.py
# Remove agent management panel
rm -f app/ui_components/admin_control_panel.py
# Restore document processing UI
git checkout HEAD~1 -- app/ui_components/document_summary.py
```

3. **Update UI Route Registration**
```bash
# Restore previous route definitions
git checkout HEAD~1 -- app/main.py
# Remove agent-specific UI routes
grep -v "admin_control_panel" app/main.py > temp && mv temp app/main.py
```

4. **Remove Agent-specific Static Assets**
```bash
# Remove agent management CSS/JS if any
find static/ -name "*agent*" -delete
# Restore previous static assets
git checkout HEAD~1 -- static/
```

5. **Update UI Dependencies**
```bash
# Restore previous UI service dependencies
find app/ui_components/ -name "*.py" -exec sed -i 's/agent_manager/document_service/g' {} \;
find app/ui_components/ -name "*.py" -exec sed -i 's/from app\.core\.agent_manager/from app.services.document_service/g' {} \;
```

6. **Restart UI Services**
```bash
# Restart web application
docker-compose restart web
# Verify UI startup
curl -f http://localhost:8000/health
```

7. **UI Functionality Testing**
```bash
# Test critical UI flows
# Note: Use Playwright MCP for comprehensive UI testing
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:8000')
        title = await page.title()
        print(f'Page title: {title}')
        await browser.close()

asyncio.run(test_ui())
"
```

**UI Rollback Validation:**
- Dashboard loads correctly
- Document upload interface functional
- User authentication UI working
- No JavaScript errors in console

### 5. Complete System Rollback

**When to Execute:**
- Multiple integration points failing
- System-wide instability
- Critical data integrity issues
- Emergency production rollback required

**Emergency Rollback Procedure:**

1. **Immediate System Shutdown**
```bash
# Stop all services
docker-compose down
# Kill any remaining processes
pkill -f "iam-dashboard"
```

2. **Restore Complete Previous State**
```bash
# Restore entire codebase to previous working commit
git log --oneline -5  # Find last working commit
git reset --hard <PREVIOUS_WORKING_COMMIT>
```

3. **Database Emergency Restore**
```bash
# Restore from backup if database issues detected
pg_restore -h localhost -U $DB_USER -d iam_dashboard latest_working_backup.sql
```

4. **Restart Legacy System**
```bash
# Start with previous working configuration
docker-compose up -d
```

5. **Comprehensive System Validation**
```bash
# Full system health check
./scripts/health_check.sh
# Critical function testing
./scripts/integration_test.sh
```

### Rollback Communication Protocol

**Immediate Actions (0-15 minutes):**
1. Execute appropriate rollback procedure
2. Notify system administrator
3. Update status page/monitoring

**Short-term Actions (15-60 minutes):**
1. Complete rollback validation
2. Notify stakeholders
3. Begin preliminary failure analysis

**Medium-term Actions (1-24 hours):**
1. Conduct post-mortem meeting
2. Document lessons learned
3. Plan remediation strategy

**Communication Templates:**

**Immediate Notification:**
```
URGENT: IAM Dashboard System Rollback Initiated
Time: [TIMESTAMP]
Procedure: [ROLLBACK_TYPE]
Estimated Recovery: [TIME_ESTIMATE]
Contact: [ADMIN_CONTACT]
```

**Completion Notification:**
```
IAM Dashboard System Rollback Completed
Time: [TIMESTAMP]
System Status: OPERATIONAL
Validation: COMPLETE
Next Steps: Post-mortem scheduled for [TIME]
```

### Rollback Prevention Measures

**Pre-deployment Validation:**
- Comprehensive staging environment testing
- Database migration dry runs
- API contract validation
- UI regression testing

**Monitoring and Early Detection:**
- Real-time agent health monitoring
- API response time alerts
- Database performance monitoring
- User experience tracking

**Automated Rollback Triggers:**
- Error rate thresholds (>5% in 10 minutes)
- Response time degradation (>200% baseline)
- Database connection failures
- Agent initialization failures

### Rollback Testing and Validation

**Monthly Rollback Drills:**
- Agent manager rollback simulation
- Database recovery testing
- API endpoint restoration
- UI component rollback

**Documentation Maintenance:**
- Update procedures after each deployment
- Validate rollback scripts quarterly
- Train team on rollback procedures
- Maintain emergency contact lists

## Coding Standards and Conventions

### Agent Development Standards

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

### Configuration Management Standards

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

### Testing Standards

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

## Security Integration

### Agent Security Framework

**Authentication and Authorization:**
```python
class AgentSecurityManager:
    """Security manager for agent operations."""
    
    async def authorize_agent_operation(
        self, 
        user: User, 
        agent_id: str, 
        operation: str
    ) -> bool:
        """Authorize user to perform agent operations."""
        # Check user roles
        if not user.is_admin and operation in ["enable", "disable", "configure"]:
            return False
        
        # Check agent-specific permissions
        agent_permissions = await self._get_agent_permissions(user, agent_id)
        return operation in agent_permissions
    
    async def audit_agent_operation(
        self, 
        user: User, 
        agent_id: str, 
        operation: str, 
        success: bool
    ) -> None:
        """Audit log for agent operations."""
        await self._log_security_event(
            event_type="agent_operation",
            user_id=user.id,
            agent_id=agent_id,
            operation=operation,
            success=success,
            timestamp=datetime.utcnow()
        )
```

**Data Protection:**
```python
class AgentDataProtection:
    """Data protection for agent processing."""
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data before agent processing."""
        # Remove sensitive information
        # Validate input format
        # Apply data protection rules
        return sanitized_data
    
    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data in agent processing."""
        sensitive_fields = ["cpf", "rg", "credit_card", "bank_account"]
        
        for field in sensitive_fields:
            if field in data:
                data[field] = self._encrypt_field(data[field])
        
        return data
```

**API Security:**
```python
# Secure agent management endpoints
@router.post("/admin/agents/{agent_id}/enable")
@require_admin_role
@rate_limit("5/minute")
async def enable_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    security_manager: AgentSecurityManager = Depends(get_security_manager)
):
    # Authorize operation
    authorized = await security_manager.authorize_agent_operation(
        current_user, agent_id, "enable"
    )
    
    if not authorized:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Perform operation
    success = await agent_manager.enable_agent(agent_id)
    
    # Audit log
    await security_manager.audit_agent_operation(
        current_user, agent_id, "enable", success
    )
    
    return {"agent_id": agent_id, "enabled": success}
```

### Configuration Security

**Secure Configuration Management:**
```python
class SecureConfigManager:
    """Secure configuration management for agents."""
    
    def validate_config_change(self, config_update: Dict[str, Any]) -> bool:
        """Validate configuration changes for security."""
        # Check for dangerous configurations
        dangerous_patterns = [
            r"eval\(",
            r"exec\(",
            r"__import__",
            r"subprocess",
        ]
        
        config_str = json.dumps(config_update)
        for pattern in dangerous_patterns:
            if re.search(pattern, config_str):
                raise SecurityError(f"Dangerous configuration pattern detected: {pattern}")
        
        return True
    
    def encrypt_config_secrets(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt secrets in configuration."""
        secret_fields = ["api_key", "password", "secret", "token"]
        
        for key, value in config.items():
            if any(secret_field in key.lower() for secret_field in secret_fields):
                config[key] = self._encrypt_secret(value)
        
        return config
```

## Testing Strategy

### Testing Approach Overview

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

### Unit Testing Strategy

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

### Integration Testing Strategy

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

### End-to-End Testing Strategy

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

### Performance Testing

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

### Test Data Management

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

## Next Steps

### Implementation Roadmap

**Phase 1: Foundation (Week 1-2)**
1. ✅ **Agent Infrastructure Setup**
   - Implement AgentManager with dependency injection
   - Create plugin architecture foundation
   - Establish configuration management system
   - Set up comprehensive logging and monitoring

2. ✅ **Container Integration**
   - Extend existing Container class with agent providers
   - Implement plugin registration system
   - Configure YAML-based agent configuration
   - Test dependency injection with existing services

**Phase 2: Core Agent Implementation (Week 3-4)**
1. ✅ **PDF Processor Agent**
   - Implement PDFProcessorAgent using Agno framework
   - Create modular tools (PDFReaderTool, OCRProcessorTool, VectorStorageTool)
   - Replace existing Celery worker functionality
   - Ensure database integration with existing schema

2. ✅ **Questionnaire Writer Agent**
   - Implement QuestionnaireAgent with RAG integration
   - Replace QuestionnaireDraftService with agent calls
   - Maintain template compatibility and quality standards
   - Test LLM integration and content generation

**Phase 3: API Migration (Week 5)**
1. ✅ **API Endpoint Updates**
   - Replace Celery-based endpoints with direct agent calls
   - Ensure response schema preservation for frontend compatibility
   - Implement comprehensive error handling and status reporting
   - Add new agent management API endpoints

2. ✅ **Testing and Validation**
   - Unit tests for all agents and tools
   - Integration tests for complete workflows
   - API contract validation
   - Performance benchmarking against baseline

**Phase 4: UI Enhancement (Week 6)**
1. ✅ **Agent Management Interface**
   - Implement administrative dashboard with NiceGUI
   - Add agent status monitoring and configuration panels
   - Integrate with existing UI patterns and access controls
   - Real-time agent health and performance indicators

2. ✅ **User Experience Updates**
   - Enhanced processing status indicators
   - Agent-powered workflow feedback
   - Configuration management interface
   - Help and documentation integration

**Phase 5: Legacy Cleanup and Deployment (Week 7-8)**
1. ✅ **Legacy System Removal**
   - Remove Celery workers and service classes
   - Clean up unused dependencies and configuration
   - Update deployment configuration for agent architecture
   - Final performance validation and optimization

2. ✅ **Production Deployment**
   - Staging environment deployment and testing
   - Production deployment with monitoring
   - User training and documentation updates
   - Post-deployment monitoring and support

### Handoff to Development Team

**Required Deliverables:**
1. **Architectural Documentation** ✅
   - This comprehensive brownfield architecture document
   - Agent development standards and conventions
   - API integration specifications
   - Security and testing guidelines

2. **Technical Specifications** (Next Phase)
   - Detailed agent implementation specifications
   - Tool interface definitions
   - Configuration schema documentation
   - Database integration patterns

3. **Implementation Guidelines** (Next Phase)
   - Step-by-step implementation roadmap
   - Code templates and examples
   - Testing strategies and templates
   - Deployment and operational procedures

**Development Team Preparation:**
1. **Team Training Requirements**
   - Agno framework introduction and hands-on training
   - Agent-based architecture principles
   - Plugin development patterns
   - Configuration management best practices

2. **Environment Setup**
   - Development environment with Agno framework
   - Testing infrastructure for agent development
   - Staging environment for integration testing
   - Monitoring and logging setup

3. **Quality Assurance**
   - Code review processes for agent development
   - Testing protocols for agent functionality
   - Performance monitoring and optimization
   - Security validation procedures

### Risk Mitigation and Success Metrics

**Success Metrics:**
- **Functional Parity:** 100% feature compatibility with existing system
- **Performance:** Agent processing within 110% of current baseline times
- **Reliability:** 99.9% successful agent processing rate
- **User Experience:** No degradation in UI responsiveness or functionality
- **System Stability:** Zero production issues during migration period

**Risk Mitigation:**
- **Gradual Migration:** Phased implementation with rollback capabilities
- **Comprehensive Testing:** Full test coverage at unit, integration, and E2E levels
- **Performance Monitoring:** Real-time agent performance tracking
- **Configuration Validation:** Schema validation for all agent configurations
- **Team Support:** Comprehensive training and documentation for development team

## Infrastructure & Deployment Requirements (PO Specifications)

### Production Deployment Requirements [HIGH PRIORITY]

**User Story:** As a DevOps Engineer, I need automated production deployment scripts so that I can deploy the IAM Dashboard reliably and consistently.

**Requirements:**

**REQ-DEPLOY-001: Production Deployment Automation**
- **Description:** Automated deployment script supporting production, staging, and development environments
- **Functional Requirements:**
  - Support for multiple environments (production, staging, development)
  - Environment-specific configuration loading (.env.production, .env.staging)
  - Pre-deployment validation (requirements check, environment variables)
  - Database backup before deployment
  - Rolling deployment with health checks
  - Automatic rollback on failure
  - Post-deployment validation and reporting

**REQ-DEPLOY-002: Docker Production Configuration**
- **Description:** Production-optimized Docker configuration separate from development
- **Functional Requirements:**
  - Multi-stage Dockerfile for production optimization
  - Resource limits and reservations
  - Health checks for all services
  - Security hardening (non-root user, minimal base image)
  - Proper logging configuration
  - Environment-specific compose files

**Acceptance Criteria:**
- [ ] Deployment script supports all three environments
- [ ] Zero-downtime deployment capability
- [ ] Automatic rollback on health check failure
- [ ] Complete deployment logs and reporting
- [ ] Environment variable validation before deployment
- [ ] Database backup creation before each deployment

**Definition of Done:**
- [ ] Script tested in staging environment
- [ ] Documentation includes deployment guide
- [ ] Error handling covers all failure scenarios
- [ ] Performance baseline maintained post-deployment

---

### Automated Backup Strategy Requirements [HIGH PRIORITY]

**User Story:** As a System Administrator, I need automated backup solutions so that I can ensure data integrity and disaster recovery capabilities.

**Requirements:**

**REQ-BACKUP-001: Database Backup Automation**
- **Description:** Automated PostgreSQL backup with retention and cloud storage
- **Functional Requirements:**
  - Daily automated database backups
  - Configurable retention policy (default: 7 days local, 30 days cloud)
  - Backup integrity verification
  - Compression and encryption
  - Cloud storage integration (S3-compatible)
  - Backup monitoring and alerting

**REQ-BACKUP-002: Application Data Backup**
- **Description:** Backup of application uploads, logs, and configuration
- **Functional Requirements:**
  - Backup of uploads directory
  - Log file archival
  - Configuration file backup
  - Incremental backup support
  - Metadata tracking for restore operations

**Acceptance Criteria:**
- [ ] Automated daily backups running successfully
- [ ] Backup integrity verification passes
- [ ] Retention policy correctly removes old backups
- [ ] Cloud storage synchronization working
- [ ] Restore process tested and documented
- [ ] Monitoring alerts for backup failures

**Definition of Done:**
- [ ] Backup tested with full restore scenario
- [ ] Monitoring dashboard shows backup status
- [ ] Documentation includes restore procedures
- [ ] Disaster recovery plan updated

---

### Health Check Endpoints Requirements [HIGH PRIORITY]

**User Story:** As a Site Reliability Engineer, I need comprehensive health check endpoints so that I can monitor system health and configure load balancers.

**Requirements:**

**REQ-HEALTH-001: Basic Health Check**
- **Description:** Simple endpoint for load balancer health checks
- **API Contract:**
  ```
  GET /health
  Response: 200 OK
  {
    "status": "healthy",
    "timestamp": "2025-01-28T10:00:00Z",
    "version": "1.0.0",
    "environment": "production",
    "uptime_seconds": 3600
  }
  ```

**REQ-HEALTH-002: Component Health Checks**
- **Description:** Detailed health checks for all system components
- **API Contracts:**
  ```
  GET /health/detailed - Complete system health
  GET /health/db - Database connectivity and performance
  GET /health/redis - Redis connectivity and status
  GET /health/celery - Worker status and queue health
  ```

**REQ-HEALTH-003: Kubernetes Probes**
- **Description:** Kubernetes-compatible readiness and liveness probes
- **API Contracts:**
  ```
  GET /health/readiness - Ready to receive traffic
  GET /health/liveness - Process alive check
  ```

**Acceptance Criteria:**
- [ ] All endpoints return appropriate HTTP status codes
- [ ] Response times under 100ms for basic checks
- [ ] Failed components return 503 status
- [ ] Load balancer integration tested
- [ ] Kubernetes probe compatibility verified

**Definition of Done:**
- [ ] All health endpoints implemented and tested
- [ ] Load balancer configuration updated
- [ ] Monitoring alerts configured
- [ ] Documentation includes endpoint specifications

---

### Structured Logging Requirements [MEDIUM PRIORITY]

**User Story:** As a DevOps Engineer, I need structured logging so that I can effectively monitor, debug, and analyze application behavior.

**Requirements:**

**REQ-LOG-001: Structured Log Format**
- **Description:** JSON-structured logs with consistent formatting
- **Functional Requirements:**
  - JSON log format for all application logs
  - Consistent log levels (DEBUG, INFO, WARN, ERROR, CRITICAL)
  - Correlation IDs for request tracing
  - Structured fields (timestamp, level, message, context)
  - Security: No sensitive data in logs

**REQ-LOG-002: Centralized Log Collection**
- **Description:** Centralized logging infrastructure for production
- **Functional Requirements:**
  - Log aggregation system compatible
  - Log retention policy (30 days default)
  - Log rotation and compression
  - Search and filtering capabilities
  - Real-time log streaming

**Acceptance Criteria:**
- [ ] All logs in JSON format
- [ ] No sensitive data exposure in logs
- [ ] Correlation IDs present in related log entries
- [ ] Log aggregation system integration working
- [ ] Log retention policy implemented

**Definition of Done:**
- [ ] Logging tested across all application components
- [ ] Log analysis dashboard configured
- [ ] Documentation includes logging standards
- [ ] Security review completed for log content

---

### Security Hardening Requirements [HIGH PRIORITY]

**User Story:** As a Security Engineer, I need production security hardening so that the application meets enterprise security standards.

**Requirements:**

**REQ-SEC-001: Container Security**
- **Description:** Security hardening for production containers
- **Functional Requirements:**
  - Non-root user execution
  - Minimal base images (distroless/alpine)
  - No unnecessary packages or tools
  - Read-only file systems where possible
  - Security scanning integration
  - Resource limits enforcement

**REQ-SEC-002: Network Security**
- **Description:** Network-level security configurations
- **Functional Requirements:**
  - TLS/SSL termination at reverse proxy
  - Security headers (HSTS, CSP, X-Frame-Options)
  - Rate limiting configuration
  - IP whitelisting capability
  - DDoS protection measures

**REQ-SEC-003: Application Security**
- **Description:** Application-level security hardening
- **Functional Requirements:**
  - Environment variable security (no secrets in images)
  - Input validation and sanitization
  - Authentication token security
  - CORS configuration
  - SQL injection prevention

**Acceptance Criteria:**
- [ ] Security scan passes with no high-severity issues
- [ ] Containers run as non-root user
- [ ] All HTTP traffic redirected to HTTPS
- [ ] Security headers properly configured
- [ ] Rate limiting prevents abuse
- [ ] No secrets exposed in container images

**Definition of Done:**
- [ ] Security audit completed and passed
- [ ] Penetration testing completed
- [ ] Security documentation updated
- [ ] Compliance requirements verified

## Security Enhancement Requirements (PO Specifications - Section 3 Gaps)

### Rate Limiting Requirements [HIGH PRIORITY - CRITICAL GAP]

**User Story:** As a Security Engineer, I need comprehensive rate limiting to protect the IAM Dashboard from abuse, brute force attacks, and ensure fair API usage for all users.

**Requirements:**

**REQ-RATE-001: Authentication Rate Limiting**
- **Description:** Protection against brute force authentication attacks
- **Functional Requirements:**
  - Login endpoint: 5 attempts per minute per IP
  - 2FA verification: 3 attempts per minute per user
  - Password reset: 3 attempts per hour per email
  - Account lockout: 15 minutes after 5 failed attempts
  - Progressive delays on repeated failures
  - Whitelist capability for trusted IPs

**REQ-RATE-002: API Endpoint Rate Limiting**
- **Description:** General API protection and fair usage enforcement
- **Functional Requirements:**
  - General API endpoints: 100 requests per minute per authenticated user
  - File upload endpoints: 10 requests per minute per user
  - Heavy operations (document processing): 5 requests per minute per user
  - Public endpoints: 20 requests per minute per IP
  - Admin endpoints: 50 requests per minute per admin user
  - Rate limit headers in responses (X-RateLimit-Limit, X-RateLimit-Remaining)

**REQ-RATE-003: Implementation Strategy**
- **Description:** Technical implementation using proven libraries and Redis backend
- **Technical Requirements:**
  - **Primary Library:** FastAPI-Limiter with Redis backend for production scalability
  - **Alternative:** SlowAPI for simpler deployments
  - **Storage:** Redis for distributed rate limiting state
  - **Algorithms:** Token bucket algorithm for smooth rate limiting
  - **Response Codes:** HTTP 429 (Too Many Requests) with Retry-After header
  - **Monitoring:** Rate limiting metrics and alerts

**Acceptance Criteria:**
- [ ] Authentication endpoints protected against brute force (≤5 attempts/minute)
- [ ] API endpoints have appropriate rate limits based on operation cost
- [ ] Rate limiting state persisted in Redis for cluster scalability
- [ ] Rate limit headers included in all API responses
- [ ] HTTP 429 responses with proper Retry-After headers
- [ ] Monitoring dashboard shows rate limiting metrics
- [ ] Load testing confirms rate limiting effectiveness

**Definition of Done:**
- [ ] Rate limiting tested with automated security scans
- [ ] Performance impact measurement (≤5ms additional latency)
- [ ] Documentation includes rate limiting policies
- [ ] Monitoring alerts configured for rate limiting anomalies

---

### Security Headers Requirements [HIGH PRIORITY - CRITICAL GAP]

**User Story:** As a Security Engineer, I need comprehensive security headers implemented to protect against XSS, clickjacking, MIME attacks, and enforce secure communication standards.

**Requirements:**

**REQ-HEADERS-001: Content Security Policy (CSP)**
- **Description:** Comprehensive CSP implementation following OWASP 2025 guidelines
- **Functional Requirements:**
  - **Strict CSP Policy:** Protection against XSS attacks
  - **Nonce-based approach:** Dynamic nonce generation for inline scripts
  - **Report-Only mode:** Initial deployment for policy testing
  - **Form Action Control:** Prevent form hijacking attacks
  - **Frame Ancestors:** Prevent clickjacking attacks
  - **CSP Reporting:** Violation reporting endpoint for monitoring

**CSP Policy Specification:**
```
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' 'nonce-{random}';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' data:;
  connect-src 'self';
  frame-src 'none';
  frame-ancestors 'none';
  form-action 'self';
  base-uri 'self';
  object-src 'none';
  upgrade-insecure-requests;
  report-uri /api/security/csp-report
```

**REQ-HEADERS-002: HTTP Strict Transport Security (HSTS)**
- **Description:** Enforce HTTPS connections and prevent protocol downgrade attacks
- **Functional Requirements:**
  - **HSTS Header:** Mandatory HTTPS for all connections
  - **Subdomain Inclusion:** Include all subdomains in HSTS policy
  - **Preload Consideration:** Evaluate HSTS preload list inclusion
  - **Long-term Policy:** Minimum 1 year max-age for production

**HSTS Policy Specification:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

**REQ-HEADERS-003: Additional Security Headers**
- **Description:** Comprehensive set of security headers following OWASP recommendations
- **Functional Requirements:**
  - **X-Content-Type-Options:** Prevent MIME type sniffing
  - **X-Frame-Options:** Backup protection against clickjacking
  - **Referrer-Policy:** Control referrer information leakage
  - **Permissions-Policy:** Restrict browser features
  - **Cross-Origin-Embedder-Policy:** Isolate cross-origin resources

**Additional Headers Specification:**
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
```

**Acceptance Criteria:**
- [ ] CSP policy blocks XSS attempts in security testing
- [ ] HSTS enforces HTTPS connections with 1-year duration
- [ ] All recommended security headers present in HTTP responses
- [ ] CSP violations properly logged and monitored
- [ ] Security headers score A+ on security testing tools
- [ ] No MIME type sniffing vulnerabilities detected

**Definition of Done:**
- [ ] Security headers tested with OWASP ZAP scan
- [ ] CSP policy refined based on violation reports
- [ ] Headers validated with online security scanners
- [ ] Documentation includes security headers configuration

---

### Input Validation Requirements [MEDIUM PRIORITY]

**User Story:** As a Security Engineer, I need comprehensive input validation to prevent injection attacks and ensure data integrity across all API endpoints.

**Requirements:**

**REQ-VALIDATION-001: Server-Side Input Validation**
- **Description:** Comprehensive server-side validation for all user inputs
- **Functional Requirements:**
  - **Pydantic Models:** Strict data validation using Pydantic schemas
  - **Sanitization:** Input sanitization for all text fields
  - **File Upload Validation:** MIME type, size, and content validation
  - **SQL Injection Prevention:** Parameterized queries via SQLAlchemy ORM
  - **Path Traversal Prevention:** Secure file path handling
  - **Email Format Validation:** RFC-compliant email validation

**REQ-VALIDATION-002: API Endpoint Validation**
- **Description:** Validation requirements for each API endpoint category
- **Functional Requirements:**
  - **Authentication Endpoints:** Email format, password complexity, 2FA code format
  - **Document Endpoints:** File type validation, size limits, virus scanning
  - **Client Management:** Business data validation, phone numbers, addresses
  - **Questionnaire Endpoints:** Text length limits, HTML sanitization
  - **Admin Endpoints:** Privilege validation, audit logging

**REQ-VALIDATION-003: Error Handling and Logging**
- **Description:** Secure error handling that doesn't leak sensitive information
- **Functional Requirements:**
  - **Generic Error Messages:** No sensitive data in error responses
  - **Validation Logging:** Log validation failures for security monitoring
  - **Rate Limiting:** Prevent validation endpoint abuse
  - **Input Length Limits:** Prevent buffer overflow and DoS attacks

**Acceptance Criteria:**
- [ ] All API endpoints validate inputs using Pydantic models
- [ ] File uploads restricted to allowed MIME types and sizes
- [ ] SQL injection testing passes with no vulnerabilities
- [ ] XSS attempts blocked by input sanitization
- [ ] Error messages don't expose internal system details
- [ ] Validation failures logged for security monitoring

---

### Security Monitoring Requirements [MEDIUM PRIORITY]

**User Story:** As a Security Engineer, I need comprehensive security monitoring to detect threats, track security events, and maintain audit trails for compliance.

**Requirements:**

**REQ-MONITOR-001: Security Event Logging**
- **Description:** Comprehensive logging of security-relevant events
- **Functional Requirements:**
  - **Authentication Events:** Login attempts, failures, 2FA usage, logouts
  - **Authorization Events:** Access denials, privilege escalations, admin actions
  - **Rate Limiting Events:** Rate limit violations, blocked requests
  - **Validation Events:** Input validation failures, suspicious patterns
  - **Security Header Violations:** CSP violations, protocol downgrades
  - **File Operations:** Upload attempts, download access, virus detections

**REQ-MONITOR-002: Threat Detection**
- **Description:** Automated threat detection and alerting capabilities
- **Functional Requirements:**
  - **Brute Force Detection:** Multiple failed login attempts
  - **Anomaly Detection:** Unusual access patterns, geographic anomalies
  - **Attack Pattern Recognition:** Common attack signatures, bot detection
  - **Real-time Alerts:** Immediate notification of critical security events
  - **Dashboard Integration:** Security metrics visualization
  - **Incident Response:** Automated blocking of malicious IPs

**REQ-MONITOR-003: Audit Trail Requirements**
- **Description:** Comprehensive audit trails for compliance and forensic analysis
- **Functional Requirements:**
  - **User Activity Tracking:** Complete user action history
  - **Data Access Logs:** Who accessed what data when
  - **Configuration Changes:** All system configuration modifications
  - **Security Policy Changes:** Rate limits, security headers, access controls
  - **Log Integrity:** Tamper-evident logging with checksums
  - **Retention Policy:** 1 year retention for audit logs

**Acceptance Criteria:**
- [ ] All security events logged with complete context information
- [ ] Threat detection rules trigger alerts within 5 minutes
- [ ] Audit logs tamper-evident with integrity verification
- [ ] Security dashboard provides real-time threat visibility
- [ ] Compliance reports generated automatically
- [ ] Log retention meets regulatory requirements

**Definition of Done:**
- [ ] Security monitoring tested with simulated attacks
- [ ] Alert thresholds tuned to minimize false positives
- [ ] Audit trail validated with compliance requirements
- [ ] Security team trained on monitoring tools

---

### Implementation Priority and Timeline

**SECURITY ENHANCEMENT SPRINTS (Priority: CRITICAL)**

**Sprint S1 (Week 1 - Security Focus):** 
1. **CRITICAL:** Rate Limiting Implementation (REQ-RATE-001, REQ-RATE-002, REQ-RATE-003)
2. **CRITICAL:** Security Headers Implementation (REQ-HEADERS-001, REQ-HEADERS-002, REQ-HEADERS-003)
3. Health Check Endpoints (REQ-HEALTH-001, REQ-HEALTH-002, REQ-HEALTH-003)

**Sprint S2 (Week 2 - Infrastructure & Security):**
1. Production Docker Configuration (REQ-DEPLOY-002)
2. Input Validation Enhancement (REQ-VALIDATION-001, REQ-VALIDATION-002, REQ-VALIDATION-003)
3. Container Security Hardening (REQ-SEC-001)

**Sprint S3 (Week 3 - Deployment & Monitoring):**
1. Deployment Automation (REQ-DEPLOY-001)
2. Security Monitoring Implementation (REQ-MONITOR-001, REQ-MONITOR-002, REQ-MONITOR-003)
3. Network Security (REQ-SEC-002)

**Sprint S4 (Week 4 - Backup & Observability):**
1. Backup Automation (REQ-BACKUP-001, REQ-BACKUP-002)
2. Structured Logging (REQ-LOG-001, REQ-LOG-002)
3. Application Security Final Hardening (REQ-SEC-003)

**RATIONALE FOR SPRINT REORDERING:**
- **Security gaps are CRITICAL** and must be addressed immediately
- Rate limiting protects against active threats (brute force, DoS)
- Security headers provide essential browser-level protection
- Infrastructure improvements can follow once security baseline is established

### Dependencies and Blockers

**Dependencies:**
- Cloud storage credentials for backup (S3/compatible)
- Production domain and SSL certificates
- Monitoring infrastructure setup
- Security scanning tools integration

**Potential Blockers:**
- Environment provisioning delays
- Security policy approval process
- Third-party service integration delays
- Performance testing environment availability

## API Security Enhancement Requirements (PO Specifications - Section 5 Critical Gap)

### API Authentication Gap Resolution [CRITICAL PRIORITY]

**CRITICAL FINDING:** During Section 5 (API Design & Integration) validation, a critical security gap was identified where API endpoints lack authentication middleware, exposing business-critical functionality without access control.

**ADDITIONAL CRITICAL FINDING:** Gap Analysis revealed that the authentication infrastructure for FastAPI is completely missing, requiring foundational implementation before endpoint protection can be achieved.

**User Story:** As a Security Engineer, I need all API endpoints protected with proper authentication and authorization so that only authenticated users can access sensitive business data and operations.

**Requirements:**

**REQ-API-AUTH-000: Authentication Infrastructure Foundation [PREREQUISITE]**
- **Description:** Build complete authentication infrastructure required for FastAPI integration
- **Current State:** AuthManager exists for NiceGUI only, no FastAPI authentication infrastructure
- **Critical Gaps Identified:**
  - No `fastapi.security.HTTPBearer` implementation
  - No authentication dependency functions
  - No bridge between AuthManager and User database model
  - No role-based authorization infrastructure
  - Missing `app/api/dependencies/` directory structure
- **Technical Requirements:**
  ```python
  # app/api/dependencies/auth.py (MISSING FILE)
  from fastapi import Depends, HTTPException, status
  from fastapi.security import HTTPBearer
  from sqlalchemy.ext.asyncio import AsyncSession
  from app.core.auth import AuthManager
  from app.models.user import User
  from app.repositories.user_repository import UserRepository
  
  oauth2_scheme = HTTPBearer()
  
  async def get_current_authenticated_user(
      token: str = Depends(oauth2_scheme),
      db: AsyncSession = Depends(get_async_db)
  ) -> User:
      """Extract and validate JWT token, return User model from database."""
      
  async def get_current_admin_user(
      current_user: User = Depends(get_current_authenticated_user)
  ) -> User:
      """Validate user has admin privileges."""
      
  async def authorize_client_access(
      client_id: uuid.UUID,
      current_user: User = Depends(get_current_authenticated_user),
      db: AsyncSession = Depends(get_async_db)
  ) -> Client:
      """Verify user can access specified client."""
  ```

**Acceptance Criteria:**
- [ ] `app/api/dependencies/auth.py` created with complete infrastructure
- [ ] `HTTPBearer` oauth2_scheme properly configured
- [ ] JWT token extraction and validation functions implemented
- [ ] User model lookup from database integrated with token validation
- [ ] Role-based authorization functions implemented
- [ ] Client-level authorization logic implemented
- [ ] Authentication exception classes defined
- [ ] Integration tested with existing AuthManager

**REQ-API-AUTH-001: Authentication Middleware Implementation [UPDATED]**
- **Description:** Implement comprehensive authentication middleware for all API endpoints
- **Prerequisite:** REQ-API-AUTH-000 must be completed first
- **Current State:** APIs exist but lack authentication dependencies and infrastructure
- **Target State:** All endpoints protected with JWT-based authentication using new infrastructure
- **Technical Requirements:**
  - **Depends on:** Authentication infrastructure from REQ-API-AUTH-000
  - Integration with existing AuthManager (`app/core/auth.py`) via dependency bridge
  - JWT token validation on all protected endpoints using `oauth2_scheme`
  - Proper error responses for unauthenticated requests (401 Unauthorized)
  - Database-backed user validation for each API request
  - Integration with existing user session management for web UI compatibility

**REQ-API-AUTH-002: Endpoint Protection Strategy**
- **Description:** Define authentication requirements per endpoint category
- **Functional Requirements:**

**Document Endpoints (HIGH SECURITY):**
```python
# CURRENT (INSECURE):
@router.get("/v1/documents/{document_id}")
async def get_document(document_id: uuid.UUID):

# REQUIRED (SECURE):
@router.get("/v1/documents/{document_id}")
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_authenticated_user)
):
```

**Client Endpoints (HIGH SECURITY + AUTHORIZATION):**
```python
# REQUIRED: Authentication + Client Access Authorization
@router.get("/v1/clients/{client_id}")
async def get_client(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_authenticated_user),
    authorized_client: Client = Depends(authorize_client_access)
):
```

**Questionnaire Endpoints (HIGH SECURITY):**
```python
# REQUIRED: Authentication + Business Logic Protection
@router.post("/v1/questionnaire/generate")
async def generate_questionnaire(
    request: QuestionnaireGenerateRequest,
    current_user: User = Depends(get_current_authenticated_user)
):
```

**REQ-API-AUTH-003: Authorization Layer Implementation**
- **Description:** Role-based access control for API endpoints
- **Functional Requirements:**
  - **SYSADMIN Role:** Full access to all endpoints including admin operations
  - **ADMIN_USER Role:** Access to client management and document operations
  - **COMMON_USER Role:** Access only to own client data and authorized operations
  - **Client-level Authorization:** Users can only access clients they own/manage
  - **Document-level Authorization:** Users can only access documents from authorized clients

**REQ-API-AUTH-004: Authentication Dependency Functions**
- **Description:** Reusable authentication and authorization dependencies
- **Technical Implementation:**

```python
# app/api/dependencies/auth.py
from app.core.auth import AuthManager

async def get_current_authenticated_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """Validate JWT token and return authenticated user."""
    
async def get_current_admin_user(
    current_user: User = Depends(get_current_authenticated_user)
) -> User:
    """Ensure user has admin privileges."""
    
async def authorize_client_access(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_authenticated_user),
    db: AsyncSession = Depends(get_async_db)
) -> Client:
    """Verify user can access specified client."""
```

**REQ-API-AUTH-005: Error Handling and Security**
- **Description:** Secure error handling for authentication failures
- **Functional Requirements:**
  - **401 Unauthorized:** Invalid or missing authentication token
  - **403 Forbidden:** Valid authentication but insufficient permissions
  - **Security:** No information leakage in error responses
  - **Logging:** All authentication failures logged for security monitoring
  - **Rate Limiting:** Protection against brute force authentication attempts

**Acceptance Criteria:**
- [ ] All API endpoints require valid JWT authentication
- [ ] Role-based authorization enforced per endpoint category
- [ ] Client-level authorization prevents cross-client data access
- [ ] Authentication failures return appropriate HTTP status codes
- [ ] No sensitive information exposed in error responses
- [ ] Authentication events logged for security monitoring
- [ ] Existing web UI authentication integration preserved
- [ ] API documentation updated with authentication requirements

**Definition of Done:**
- [ ] Authentication middleware implemented and tested
- [ ] All endpoints protected with appropriate authentication dependencies
- [ ] Authorization logic tested with different user roles
- [ ] Security testing confirms no unauthorized access possible
- [ ] Performance impact measurement (≤10ms additional latency)
- [ ] Documentation includes API authentication guide
- [ ] Integration tested with existing web UI authentication

**REQ-API-AUTH-006: Backward Compatibility and Migration**
- **Description:** Ensure smooth migration without breaking existing functionality
- **Functional Requirements:**
  - **Web UI Integration:** Existing NiceGUI authentication continues to work
  - **Session Sharing:** API authentication uses same JWT tokens as web UI
  - **Gradual Rollout:** Option to enable authentication per endpoint group
  - **Development Mode:** Option to disable authentication for local development
  - **Testing:** Comprehensive test coverage for authentication scenarios

**Acceptance Criteria:**
- [ ] Existing web UI login/logout functionality unaffected
- [ ] Same JWT tokens work for both web UI and API access
- [ ] Development environment authentication can be disabled via config
- [ ] All authentication scenarios covered by automated tests
- [ ] Migration can be performed without downtime

---

### API Performance Enhancement Requirements [HIGH PRIORITY]

**User Story:** As a System Administrator, I need API performance optimizations including rate limiting and caching so that the system can handle production load efficiently and prevent abuse.

**Requirements:**

**REQ-API-PERF-001: API Rate Limiting Integration**
- **Description:** Integrate rate limiting with API authentication for comprehensive protection
- **Functional Requirements:**
  - **Authenticated Users:** 200 requests per minute per user
  - **Document Upload:** 20 uploads per hour per user
  - **Questionnaire Generation:** 10 generations per hour per user
  - **Admin Operations:** 500 requests per minute for admin users
  - **Rate Limit Headers:** Include rate limit information in responses
  - **Override Capability:** Admin users can temporarily increase limits

**REQ-API-PERF-002: Response Caching Strategy**
- **Description:** Implement intelligent caching for frequently accessed API data
- **Functional Requirements:**
  - **Document Metadata:** Cache document lists and metadata (TTL: 5 minutes)
  - **Client Information:** Cache client details (TTL: 15 minutes)
  - **Questionnaire Templates:** Cache generated content (TTL: 1 hour)
  - **Cache Invalidation:** Smart invalidation on data updates
  - **Cache Headers:** Proper ETag and Last-Modified headers

**REQ-API-PERF-003: API Monitoring and Performance Metrics**
- **Description:** Comprehensive API performance monitoring and alerting
- **Functional Requirements:**
  - **Response Time Monitoring:** Track API endpoint performance
  - **Authentication Metrics:** Monitor authentication success/failure rates
  - **Rate Limiting Metrics:** Track rate limit violations and patterns
  - **Error Rate Monitoring:** Alert on elevated error rates
  - **Usage Analytics:** Track API usage patterns per user/endpoint

**REVISED Implementation Priority (Post Gap Analysis):**

**Phase 1: Infrastructure Foundation (Week 1)**
1. **CRITICAL:** Authentication Infrastructure Foundation (REQ-API-AUTH-000)
   - Create authentication dependency system
   - Implement OAuth2 scheme and JWT validation
   - Build User model integration bridge
   - Develop role-based authorization infrastructure

**Phase 2: Endpoint Protection (Week 2)**
1. **CRITICAL:** Authentication Middleware Implementation (REQ-API-AUTH-001)
2. **CRITICAL:** Endpoint Protection Strategy (REQ-API-AUTH-002)
3. **CRITICAL:** Authorization Layer Implementation (REQ-API-AUTH-003)

**Phase 3: Advanced Security (Week 3)**
1. **HIGH:** Error Handling and Security (REQ-API-AUTH-005)
2. **HIGH:** Backward Compatibility and Migration (REQ-API-AUTH-006)
3. **HIGH:** Rate limiting integration (REQ-API-PERF-001)

**Phase 4: Performance & Monitoring (Week 4)**
1. **MEDIUM:** Caching strategy implementation (REQ-API-PERF-002)
2. **MEDIUM:** Performance monitoring setup (REQ-API-PERF-003)

**COMPLEXITY UPDATE:**
- **Original Estimate:** 1 week for authentication
- **Revised Estimate:** 3 weeks for complete implementation
- **Reason:** Missing foundational infrastructure discovered in gap analysis

### Critical Gaps Summary (Gap Analysis Results)

**🚨 INFRASTRUCTURE GAPS IDENTIFIED:**

1. **Authentication Infrastructure Missing (100% Gap)**
   - No `fastapi.security.HTTPBearer` implementation
   - No authentication dependency functions
   - No `app/api/dependencies/` directory structure
   - No bridge between AuthManager and database User model

2. **Authorization Infrastructure Missing (100% Gap)**
   - No role-based authorization logic
   - No client-level authorization functions
   - No admin privilege validation system
   - No authorization exception handling

3. **Integration Infrastructure Missing (75% Gap)**
   - AuthManager isolated from FastAPI ecosystem
   - No User repository integration with JWT validation
   - No session-to-API token bridge for web UI compatibility
   - Missing authentication exception classes

**📊 DEPENDENCY ASSESSMENT:**

| Component | Status | Impact | Priority |
|-----------|---------|---------|----------|
| OAuth2 Scheme | ❌ Missing | Critical | P0 |
| Auth Dependencies | ❌ Missing | Critical | P0 |
| User Model Bridge | ❌ Missing | Critical | P0 |
| Role Authorization | ❌ Missing | High | P1 |
| Client Authorization | ❌ Missing | High | P1 |
| Error Handling | ❌ Missing | Medium | P2 |

**🔄 IMPLEMENTATION RISK ASSESSMENT:**
- **High Risk:** Complete infrastructure rebuild required
- **Medium Risk:** Integration complexity with existing AuthManager
- **Low Risk:** Endpoint protection once infrastructure exists

**📋 PREREQUISITES FOR SUCCESS:**
1. Complete REQ-API-AUTH-000 before any endpoint protection
2. Thorough testing of AuthManager integration
3. Comprehensive role and client authorization testing
4. Performance validation of new authentication flow

## Additional Requirements Integration (HIGH & MEDIUM Priority Adjustments)

### Testing Strategy Integration Requirements [HIGH PRIORITY]

**User Story:** As a QA Engineer, I need comprehensive testing strategies for authentication, security, and API integration so that all security measures are thoroughly validated before production deployment.

**Requirements:**

**REQ-TEST-001: Authentication Flow Testing Strategy**
- **Description:** Comprehensive testing approach for all authentication scenarios
- **Functional Requirements:**
  - **Unit Testing:** All authentication dependency functions isolated testing
  - **Integration Testing:** AuthManager ↔ FastAPI bridge validation
  - **End-to-End Testing:** Complete authentication flows (login → API call → logout)
  - **Security Testing:** Authentication bypass attempts, token manipulation
  - **Performance Testing:** Authentication overhead measurement (≤10ms target)
  - **Load Testing:** Concurrent authentication requests handling

**Testing Scenarios:**
```python
# Unit Tests
test_oauth2_scheme_token_extraction()
test_jwt_token_validation_success()
test_jwt_token_validation_expired()
test_user_model_lookup_from_token()
test_role_authorization_logic()
test_client_authorization_logic()

# Integration Tests  
test_web_ui_to_api_token_sharing()
test_authentication_dependency_injection()
test_authorization_cascade_logic()

# Security Tests
test_invalid_token_rejection()
test_expired_token_handling()
test_role_privilege_enforcement()
test_client_access_boundary_enforcement()
test_sql_injection_in_auth_queries()

# Performance Tests
test_authentication_latency_under_load()
test_concurrent_authentication_requests()
test_database_connection_pooling_with_auth()
```

**REQ-TEST-002: Security Requirements Testing Integration**
- **Description:** Coordinate security testing across rate limiting, headers, and authentication
- **Functional Requirements:**
  - **Rate Limiting Testing:** Validate authentication rate limits work with general API limits
  - **Security Headers Testing:** CSP policy compatibility with authentication endpoints
  - **Input Validation Testing:** Authentication data validation comprehensive testing
  - **Cross-System Security Testing:** Web UI + API authentication security validation

**REQ-TEST-003: Agent Authentication Testing Strategy**
- **Description:** Testing strategy for agent-specific authentication requirements  
- **Functional Requirements:**
  - **Agent Identity Testing:** How agents authenticate with the system
  - **Agent Authorization Testing:** What agents can access vs. users
  - **Agent Security Context Testing:** Agent operations security boundaries
  - **Agent API Integration Testing:** Agent calls to protected endpoints

**Acceptance Criteria:**
- [ ] 100% test coverage for all authentication dependency functions
- [ ] Security testing covers all attack vectors identified
- [ ] Performance testing validates <10ms authentication overhead
- [ ] Integration testing covers web UI + API authentication flows
- [ ] Agent authentication testing covers autonomous operations
- [ ] Load testing validates production authentication capacity

---

### Agent Authentication Integration Requirements [HIGH PRIORITY]

**User Story:** As a System Architect, I need clear authentication requirements for autonomous agents so that agents can securely access APIs and database resources without compromising security.

**Requirements:**

**REQ-AGENT-AUTH-001: Agent Identity and Authentication**
- **Description:** Define how autonomous agents authenticate with the system
- **Current Gap:** Agents planned but authentication method undefined
- **Functional Requirements:**
  - **Agent Service Accounts:** Dedicated user accounts for agent operations
  - **Agent API Keys:** Long-term authentication tokens for agent use
  - **Agent Scope Limitation:** Agents restricted to specific operations and data
  - **Agent Audit Trail:** All agent operations logged with agent identity

**Technical Implementation:**
```python
# Agent Authentication Strategy
class AgentAuthManager:
    """Authentication manager for autonomous agents."""
    
    async def authenticate_agent(self, agent_id: str, api_key: str) -> AgentUser:
        """Authenticate agent using service account credentials."""
        
    async def validate_agent_scope(self, agent: AgentUser, operation: str) -> bool:
        """Validate agent has permission for specific operation."""
        
    async def create_agent_context(self, agent: AgentUser) -> AgentContext:
        """Create security context for agent operations."""
```

**REQ-AGENT-AUTH-002: Agent Authorization Matrix**
- **Description:** Define what each agent type can access and perform
- **Functional Requirements:**

**PDFProcessorAgent Authorization:**
- ✅ **Can Access:** Document upload endpoints, document processing APIs
- ✅ **Can Modify:** Document status, processing metadata, document chunks
- ❌ **Cannot Access:** User management, client management, questionnaire generation
- ❌ **Cannot Modify:** User data, client information, authentication settings

**QuestionnaireAgent Authorization:**
- ✅ **Can Access:** Client documents, RAG retrieval, questionnaire endpoints
- ✅ **Can Modify:** Questionnaire drafts, generation metadata
- ❌ **Cannot Access:** Document upload, user management, system configuration
- ❌ **Cannot Modify:** Document content, user data, client information

**REQ-AGENT-AUTH-003: Agent Security Context**
- **Description:** Security boundaries and isolation for agent operations
- **Functional Requirements:**
  - **Data Isolation:** Agents can only access data they're authorized for
  - **Operation Logging:** All agent operations logged for audit
  - **Rate Limiting:** Agents subject to specific rate limits
  - **Error Isolation:** Agent errors don't expose system internals
  - **Resource Limits:** Agents have memory/CPU/database connection limits

**Acceptance Criteria:**
- [ ] Agent service accounts created and managed
- [ ] Agent API key system implemented and tested
- [ ] Agent authorization matrix enforced in code
- [ ] Agent operations fully auditable
- [ ] Agent security context prevents privilege escalation
- [ ] Agent rate limiting prevents resource abuse

---

### Enhanced Monitoring & Observability Requirements [MEDIUM PRIORITY]

**User Story:** As a DevOps Engineer, I need comprehensive monitoring for authentication, security, and agent operations so that I can detect issues, track performance, and maintain system health.

**Requirements:**

**REQ-MONITOR-ENHANCE-001: Authentication & Security Metrics**
- **Description:** Comprehensive monitoring for all authentication and security systems
- **Functional Requirements:**
  - **Authentication Metrics:** Login success/failure rates, token validation performance
  - **Authorization Metrics:** Role/client authorization success/failure tracking
  - **Security Event Metrics:** Rate limiting violations, CSP violations, authentication attempts
  - **Agent Authentication Metrics:** Agent login success, API key usage, agent operations
  - **Performance Metrics:** Authentication latency, database query performance, API response times

**Key Metrics to Track:**
```yaml
# Authentication Metrics
auth.login.success_rate: percentage
auth.login.failure_rate: percentage  
auth.token.validation_time: milliseconds
auth.api.requests_per_minute: count

# Security Metrics
security.rate_limit.violations: count
security.csp.violations: count
security.auth.brute_force_attempts: count

# Agent Metrics
agent.authentication.success_rate: percentage
agent.operations.per_minute: count
agent.errors.count: count

# Performance Metrics
api.response_time.p95: milliseconds
database.connection_pool.usage: percentage
```

**REQ-MONITOR-ENHANCE-002: Integrated Security Dashboard**
- **Description:** Unified dashboard for all security and authentication monitoring
- **Functional Requirements:**
  - **Real-time Security Status:** Current threat level, active incidents
  - **Authentication Overview:** Login patterns, failure spikes, geographic anomalies
  - **Agent Activity Dashboard:** Agent operations, performance, errors
  - **API Security Status:** Rate limiting status, endpoint health, authentication metrics
  - **Alert Management:** Escalation rules, notification channels, incident tracking

**REQ-MONITOR-ENHANCE-003: Advanced Threat Detection**
- **Description:** AI-enhanced threat detection for authentication and API security
- **Functional Requirements:**
  - **Anomaly Detection:** Unusual login patterns, API usage spikes, geographic anomalies
  - **Attack Pattern Recognition:** Brute force detection, credential stuffing, API abuse
  - **Agent Behavior Analysis:** Unusual agent activity, performance degradation
  - **Automated Response:** Automatic IP blocking, rate limit adjustment, alert generation

**Acceptance Criteria:**
- [ ] All authentication and security metrics collected and displayed
- [ ] Real-time dashboard provides comprehensive security overview
- [ ] Anomaly detection accurately identifies threats with <5% false positives
- [ ] Automated responses contain threats within 5 minutes
- [ ] Performance metrics track authentication overhead
- [ ] Agent monitoring provides complete operational visibility

---

### Infrastructure-Authentication Integration Requirements [MEDIUM PRIORITY]

**User Story:** As a Platform Engineer, I need coordinated integration between infrastructure components and authentication systems so that deployment, backup, and operational procedures account for authentication requirements.

**Requirements:**

**REQ-INFRA-AUTH-001: Deployment Integration**
- **Description:** Coordinate deployment procedures with authentication infrastructure
- **Integration Requirements:**
  - **Health Checks:** Authentication endpoints included in health check monitoring
  - **Database Migrations:** User/role schema changes coordinated with auth updates
  - **Environment Separation:** Authentication configs properly isolated per environment
  - **Rollback Procedures:** Authentication rollback included in deployment rollback

**Updated Health Check Requirements:**
```python
# Enhanced health checks including authentication
@router.get("/health/auth")
async def authentication_health_check():
    """Comprehensive authentication system health check."""
    - JWT token validation performance
    - Database user lookup performance  
    - Role authorization system status
    - Agent authentication system status
```

**REQ-INFRA-AUTH-002: Backup Strategy Integration**
- **Description:** Include authentication data in backup and recovery procedures
- **Integration Requirements:**
  - **User Session Backup:** Strategy for active user sessions during backup
  - **Token Invalidation:** Coordinated token refresh during system maintenance
  - **Agent Credential Backup:** Secure backup of agent authentication credentials
  - **Recovery Testing:** Authentication system included in disaster recovery testing

**REQ-INFRA-AUTH-003: Security Hardening Coordination**
- **Description:** Coordinate container security with authentication requirements
- **Integration Requirements:**
  - **Secret Management:** Secure storage of JWT keys, agent credentials
  - **Network Security:** Authentication traffic protection, TLS termination
  - **Container Isolation:** Authentication components properly isolated
  - **Security Scanning:** Authentication code included in security scanning

**Acceptance Criteria:**
- [ ] Health checks validate complete authentication system
- [ ] Backup procedures include all authentication data
- [ ] Deployment scripts handle authentication infrastructure
- [ ] Security hardening protects authentication components
- [ ] Recovery procedures restore complete authentication capability

### Security Requirements Coordination [MEDIUM PRIORITY]

**User Story:** As a Security Engineer, I need coordinated security requirements across all system components so that security measures work together cohesively without conflicts.

**Requirements:**

**REQ-SECURITY-COORD-001: Cross-System Security Integration**
- **Description:** Coordinate security measures across authentication, rate limiting, headers, and monitoring
- **Integration Requirements:**
  - **Rate Limiting Coordination:** Authentication rate limits + API rate limits + Security header rate limits
  - **CSP Policy Integration:** Authentication endpoints included in Content Security Policy
  - **Security Headers Coordination:** Authentication responses include all required security headers
  - **Monitoring Integration:** Authentication events feed into security monitoring system

**Security Integration Matrix:**
```yaml
# Authentication + Rate Limiting
auth_endpoints:
  rate_limits:
    - authentication: 5 attempts/minute/IP
    - api_general: 100 requests/minute/user
    - coordination: authentication failures trigger API rate limit increase

# Authentication + Security Headers  
auth_responses:
  security_headers:
    - CSP: include authentication endpoints in policy
    - HSTS: enforce on authentication endpoints
    - coordination: authentication cookies require Secure flag

# Authentication + Monitoring
auth_monitoring:
  security_events:
    - login_attempts: feed to threat detection
    - token_validation: performance monitoring
    - coordination: authentication anomalies trigger security alerts
```

**REQ-SECURITY-COORD-002: Unified Security Policy**
- **Description:** Single security policy covering all system components
- **Policy Components:**
  - **Authentication Policy:** JWT duration, 2FA requirements, session management
  - **Authorization Policy:** Role definitions, client access rules, agent permissions
  - **Rate Limiting Policy:** Limits per endpoint category, escalation rules
  - **Security Headers Policy:** CSP directives, HSTS settings, additional headers
  - **Monitoring Policy:** Event logging, alert thresholds, incident response

**REQ-SECURITY-COORD-003: Security Configuration Management**
- **Description:** Centralized management of all security configurations
- **Configuration Areas:**
  - **Environment-based Security:** Production vs staging vs development security levels
  - **Dynamic Security Updates:** Ability to update security policies without deployment
  - **Security Validation:** Automated validation of security configuration consistency
  - **Audit and Compliance:** Security configuration change tracking and approval

**Acceptance Criteria:**
- [ ] All security systems work together without conflicts
- [ ] Unified security policy implemented and enforced
- [ ] Security configuration centrally managed and validated
- [ ] Cross-system security monitoring provides complete visibility
- [ ] Security policy updates can be deployed without system downtime

---

### FINAL INTEGRATED IMPLEMENTATION TIMELINE

**REVISED COMPLETE IMPLEMENTATION SCHEDULE (Post All Adjustments):**

**Phase 1: Foundation & Infrastructure (Weeks 1-2)**
1. **Week 1:** Authentication Infrastructure (REQ-API-AUTH-000)
2. **Week 2:** Infrastructure Integration (REQ-INFRA-AUTH-001,002,003)

**Phase 2: Security Implementation (Weeks 3-4)**  
1. **Week 3:** API Authentication & Authorization (REQ-API-AUTH-001,002,003)
2. **Week 4:** Security Coordination & Headers (REQ-SECURITY-COORD-001,002,003)

**Phase 3: Agent & Advanced Features (Weeks 5-6)**
1. **Week 5:** Agent Authentication Integration (REQ-AGENT-AUTH-001,002,003)
2. **Week 6:** Rate Limiting & Performance (REQ-API-PERF-001,002,003)

**Phase 4: Testing & Monitoring (Weeks 7-8)**
1. **Week 7:** Testing Strategy Implementation (REQ-TEST-001,002,003)
2. **Week 8:** Enhanced Monitoring & Observability (REQ-MONITOR-ENHANCE-001,002,003)

**TOTAL IMPLEMENTATION:** 8 weeks (vs original 1 week estimate)

**CRITICAL PATH DEPENDENCIES:**
- REQ-API-AUTH-000 → REQ-API-AUTH-001,002,003
- REQ-API-AUTH-003 → REQ-AGENT-AUTH-001,002,003
- All Security Requirements → REQ-SECURITY-COORD-001,002,003
- All Implementation → REQ-TEST-001,002,003

**FINAL COMPLEXITY ASSESSMENT:**
- **Infrastructure Gap:** 2 weeks to build foundation
- **Security Integration:** 2 weeks for comprehensive security
- **Agent Integration:** 2 weeks for autonomous agent authentication
- **Testing & Monitoring:** 2 weeks for complete validation

---

**Change Log**

| Change | Date | Version | Description | Author |
|--------|------|---------|-------------|--------|
| Initial creation | 27/07/2025 | 1.0 | Complete brownfield architecture for agent migration | Winston, Architect |
| Added PO Requirements | 28/07/2025 | 1.1 | Infrastructure & Deployment requirements specification | Sarah, PO |
| Added Security Enhancement | 28/07/2025 | 1.2 | Security gaps resolution requirements | Sarah, PO |
| Added API Security Gap | 28/07/2025 | 1.3 | Critical API authentication gap resolution | Sarah, PO |

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>