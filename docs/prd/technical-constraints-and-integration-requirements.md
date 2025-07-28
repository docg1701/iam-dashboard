# Technical Constraints and Integration Requirements

## Direct Agent Migration Approach

Given that the system is not yet in production, the migration strategy will implement a **direct replacement approach** rather than complex brownfield bridge architecture. This eliminates the need for legacy compatibility layers and enables faster, cleaner implementation of the autonomous agent architecture.

## Existing Technology Stack

**Current Implementation (To Be Replaced):**
- **Languages**: Python 3.12+
- **Frameworks**: FastAPI (API), NiceGUI (UI), SQLAlchemy 2.0 (ORM)
- **Database**: PostgreSQL with pgvector extension
- **Infrastructure**: Celery + Redis (to be replaced with Agno agents)
- **External Dependencies**: Google Gemini API, Llama-Index RAG

## Dependency Conflict Analysis and Resolution

**Current Dependency Stack Analysis (Updated July 2025):**
```
Core Dependencies (Current versions verified):
├── fastapi>=0.116.0 (Latest: 0.116.1, July 2025)
├── sqlalchemy>=2.0.0 (Latest: 2.0.41, May 2025)  
├── asyncpg>=0.30.0 (Latest: 0.30.0, current)
├── redis>=5.0.0 (Celery backend - TO BE REPLACED)
├── celery>=5.3.0 (TO BE REPLACED with Agno)
├── nicegui>=2.21.0 (Latest: 2.21.1, current)
├── dependency-injector>=4.48.1 (Latest: 4.48.1, June 2025)
├── pymupdf>=1.26.0 (Latest: 1.26.3, current)
├── pytesseract>=0.3.10 (OCR processing)
├── llama-index>=0.12.52 (Latest: 0.12.52, July 2025)
├── google-genai>=0.1.0 (NEW recommended package, replaces google-generativeai)
└── agno>=1.7.5 (Latest: 1.7.5, July 2025 - ALREADY INCLUDED)
```

**CRITICAL UPDATE - Google Generative AI Migration:**
```
⚠️ IMPORTANT: google-generativeai is DEPRECATED (EOL: September 30, 2025)
├── OLD: google-generativeai>=0.3.0 (DEPRECATED - end of life Sept 2025)
└── NEW: google-genai>=0.1.0 (Official recommended replacement)

Migration Required:
- Replace google-generativeai with google-genai in pyproject.toml
- Update code imports from google.generativeai to google.genai
- google-genai provides access to latest Gemini features (Live API, Veo)
```

**Agent Framework Status (Updated):**
```
✅ Agno Framework - Latest Version Verified:
├── agno>=1.7.5 (Latest: 1.7.5, July 2025 - Performance optimized)
├── llama-index>=0.12.52 (Latest stable - July 2025)
├── google-genai>=0.1.0 (NEW official Gemini SDK - GA ready)
├── dependency-injector>=4.48.1 (Latest stable - June 2025)
└── asyncpg>=0.30.0 (Latest PostgreSQL async driver)
```

**Dependency Conflict Analysis:**

✅ **EXCELLENT NEWS**: Minimal conflicts identified due to modern dependency management

1. **Pydantic Version Compatibility (RESOLVED)**
   - **Current**: FastAPI>=0.104.0 (already pydantic v2 compatible)
   - **Agno**: Compatible with current FastAPI version
   - **Status**: ✅ NO CONFLICT - Current versions already compatible
   - **Impact**: Zero migration effort required

2. **Asyncio Event Loop Management (ARCHITECTURAL)**
   - **Current**: Celery manages its own event loop
   - **Agno**: Uses native asyncio event loops (already installed agno>=1.7.0)
   - **Resolution**: Implement agent-based processing alongside Celery initially, then deprecate Celery
   - **Impact**: Simplified async architecture, better performance

3. **Redis Usage Pattern Evolution (CONFIGURATION)**
   - **Current**: Redis used as Celery message broker
   - **Target**: Redis used for caching and session storage only
   - **Resolution**: Reconfigure Redis usage patterns, maintain Celery configs during transition
   - **Impact**: Reduced Redis load, simplified configuration

4. **Framework Integration (DESIGN)**
   - **Agno Integration**: Already included in pyproject.toml (agno>=1.7.0)
   - **LLaMA-Index**: Already compatible (llama-index>=0.12.0)
   - **Dependency Injection**: Already compatible (dependency-injector>=4.48.0)
   - **Status**: ✅ ALL FRAMEWORKS READY FOR INTEGRATION

## Detailed Impact Assessment on Existing Integrations

**Existing Integration Points Analysis:**

1. **Document Processing Service Impact**
   ```python
   # Current integration (app/services/document_processor.py):
   # OLD: Uses google.generativeai for text analysis
   # IMPACT: Direct import changes required
   
   # Files requiring modification:
   affected_files = [
       'app/services/document_processor.py',      # Main processing logic
       'app/services/questionnaire_service.py',  # LLM integration  
       'app/workers/document_processor.py',      # Celery worker (to be replaced)
       'app/config/llm_config.py',              # LLM configuration
       'tests/integration/test_gemini.py',      # Integration tests
   ]
   
   # Required changes per file:
   changes = {
       'import_statements': 'Replace google.generativeai with google.genai',
       'configuration_calls': 'Update configure() method calls',
       'model_initialization': 'Update GenerativeModel instantiation',
       'response_handling': 'Verify response format compatibility',
       'error_handling': 'Update exception handling patterns'
   }
   ```

2. **Configuration System Impact**
   ```yaml
   # Current environment variables (REMAINS UNCHANGED):
   GOOGLE_API_KEY: "your-api-key"              # ✅ Same variable name
   GEMINI_MODEL: "gemini-1.5-pro"             # ✅ Same model names
   GEMINI_TEMPERATURE: 0.1                    # ✅ Same parameters
   GEMINI_MAX_TOKENS: 4096                    # ✅ Same limits
   
   # Configuration compatibility assessment:
   compatibility_status:
     environment_variables: "✅ FULLY_COMPATIBLE"
     model_parameters: "✅ FULLY_COMPATIBLE" 
     rate_limiting: "✅ IMPROVED (better handling)"
     error_responses: "⚠️ REQUIRES_VALIDATION"
   ```

3. **Database Integration Impact**
   ```sql
   -- Current database schema (NO CHANGES REQUIRED):
   -- Vector embeddings, document metadata, processing logs
   -- all remain compatible with new SDK
   
   SELECT 'NO_IMPACT' as assessment 
   FROM information_schema.tables 
   WHERE table_name IN ('documents', 'embeddings', 'processing_logs');
   
   -- Vector operations compatibility:
   -- ✅ Embedding generation: Same input/output format
   -- ✅ Vector storage: No changes to pgvector operations  
   -- ✅ Similarity search: Identical vector operations
   ```

## Direct Integration Strategy

**Phase-based Integration Approach:**

**Phase 1: Infrastructure Preparation (Week 1)**
- Update pyproject.toml with agent framework dependencies
- Implement AgentManager with dependency injection patterns
- Create plugin architecture foundation
- Establish agent configuration system

**Phase 2: Agent Development (Weeks 2-3)**
- Develop PDFProcessorAgent with tool integration
- Create QuestionnaireAgent with RAG capabilities
- Implement comprehensive testing for both agents
- Validate performance benchmarks

**Phase 3: API Migration (Week 4)**
- Update FastAPI endpoints to call agents directly
- Preserve existing request/response schemas
- Implement comprehensive error handling
- Validate frontend compatibility

**Phase 4: UI Enhancement (Week 5)**
- Create administrative interface for agent management
- Integrate monitoring and configuration capabilities
- Implement role-based access controls
- Validate user experience consistency

**Phase 5: Legacy Cleanup (Week 6)**
- Remove Celery workers and service classes
- Clean up unused dependencies
- Update deployment configurations
- Finalize testing and documentation

## Code Organization and Standards

**Directory Structure Integration:**
```
iam-dashboard/
├── app/
│   ├── agents/                    # NEW: Autonomous agents
│   │   ├── pdf_processor_agent.py
│   │   ├── questionnaire_agent.py
│   │   └── base_agent.py
│   ├── tools/                     # NEW: Agent tools
│   │   ├── pdf_tools.py
│   │   ├── ocr_tools.py
│   │   └── vector_storage_tools.py
│   ├── plugins/                   # NEW: Plugin system
│   │   ├── pdf_processor_plugin.py
│   │   └── questionnaire_plugin.py
│   ├── core/                      # MODIFIED: Add agent management
│   │   ├── agent_manager.py       # NEW
│   │   ├── agent_config.py        # NEW
│   │   └── agent_registry.py      # NEW
│   ├── config/                    # NEW: Agent configurations
│   │   └── agents.yaml
│   ├── containers.py              # MODIFIED: Add agent providers
│   └── main.py                    # MODIFIED: Initialize agents
```

**Coding Standards Compliance:**
- **Python Version**: 3.12+ for optimal Agno framework compatibility
- **Type Hints**: Required for all agent classes and methods
- **Async/Await**: Consistent async patterns throughout agent implementation
- **Error Handling**: Comprehensive exception handling with structured logging
- **Testing**: Minimum 80% code coverage for all agent components

## Deployment and Operations

**Deployment Configuration Updates:**

**Docker Compose Changes:**
```yaml
# docker-compose.yml updates:
version: '3.8'
services:
  web:
    build: .
    environment:
      - AGNO_CONFIG_PATH=/app/config/agents.yaml
      - AGENT_MANAGEMENT_ENABLED=true
    volumes:
      - ./app/config:/app/config
    depends_on:
      - postgres
      - redis  # Still used for caching

  # REMOVE after migration:
  # celery_worker:
  #   build: .
  #   command: celery -A app.workers.celery_app worker
```

**Environment Variables:**
```bash
# Agent-specific configurations:
AGNO_CONFIG_PATH="/app/config/agents.yaml"
AGENT_MANAGEMENT_ENABLED=true
AGENT_LOG_LEVEL="INFO"
AGENT_HEALTH_CHECK_INTERVAL=30

# Performance tuning:
MAX_CONCURRENT_AGENTS=5
AGENT_MEMORY_LIMIT="512MB"
AGENT_TIMEOUT_SECONDS=300
```

## CI/CD Pipeline Configuration

**Updated Pipeline Steps:**
1. **Dependency Installation**: Include Agno framework and agent dependencies
2. **Agent Testing**: Run agent-specific test suites with performance benchmarks
3. **Integration Testing**: Validate agent workflows with database integration
4. **Performance Testing**: Compare agent processing times against baselines
5. **Deployment**: Deploy with agent configuration validation

**Quality Gates:**
- All agent tests passing with 80%+ coverage
- Performance benchmarks within 110% of baseline
- Integration tests validating existing functionality
- Security scans including agent-specific vulnerabilities

## Infrastructure as Code (IaC) Strategy

**Configuration Management:**
- **Agent Configurations**: Version-controlled YAML files in repository
- **Environment Variables**: Managed through deployment pipelines
- **Database Migrations**: No schema changes required for agent integration
- **Monitoring**: Enhanced metrics for agent performance and health

## Zero-Downtime Deployment Strategy

**Deployment Approach:**
1. **Blue-Green Deployment**: Maintain existing system while deploying agent version
2. **Gradual Migration**: Progressively route traffic to agent-based endpoints
3. **Rollback Capability**: Immediate rollback to previous version if issues arise
4. **Health Monitoring**: Continuous monitoring during deployment transition

## Email and Messaging Service Configuration

**Integration Requirements:**
- **No Changes Required**: Existing email/messaging services remain unchanged
- **Agent Notifications**: Optional integration for agent status notifications
- **Error Reporting**: Enhanced error reporting through existing channels

## Risk Assessment and Mitigation

**Technical Risks:**
1. **Agent Performance**: Mitigated through comprehensive benchmarking
2. **Integration Complexity**: Reduced through direct replacement approach
3. **Data Loss**: Prevented through existing schema preservation
4. **Service Disruption**: Minimized through gradual migration strategy

**Business Risks:**
1. **User Experience**: Maintained through identical API contracts
2. **System Reliability**: Enhanced through improved error handling
3. **Development Timeline**: Managed through phased implementation approach

## Regression Testing Methodology for Existing Functionality

**Testing Strategy:**
- **Functional Testing**: Validate all existing features work identically
- **Performance Testing**: Ensure agent processing meets baseline requirements
- **Integration Testing**: Verify database and API compatibility
- **User Acceptance Testing**: Validate end-user workflow preservation

## Test Data Seeding Strategy

**Test Data Requirements:**
- **Document Samples**: Representative PDF files for processing testing
- **Questionnaire Templates**: Existing legal templates for generation testing
- **User Accounts**: Test accounts with various permission levels
- **Performance Baselines**: Historical processing time measurements

## Detailed Rollback Procedures by Integration Point

**Rollback Procedures:**
1. **Agent Infrastructure**: Disable agent management and revert to service calls
2. **API Endpoints**: Restore Celery-based processing endpoints
3. **Database**: No rollback required (schema unchanged)
4. **Configuration**: Revert environment variables and YAML configurations
5. **Dependencies**: Restore previous dependency versions if necessary

**Emergency Procedures:**
- **Immediate Rollback**: Automated rollback triggers for critical failures
- **Partial Rollback**: Component-specific rollback for isolated issues
- **Data Recovery**: Procedures for any data consistency issues
- **Communication Plan**: Stakeholder notification and status updates