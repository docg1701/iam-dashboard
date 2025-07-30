# Revisão da Arquitetura Técnica para Aprimoramentos de UI

### Agent System Initialization Strategy

**CRITICAL IMPLEMENTATION REQUIREMENT**: Sistema Agno nunca inicializado no startup da aplicação - agentes definidos mas não registrados/inicializados.

#### Startup Sequence Specification
```python
# app/main.py - CRITICAL STARTUP FIXES
async def create_application() -> FastAPI:
    container = ApplicationContainer()
    container.wire(modules=[__name__])
    
    app = FastAPI(title="IAM Dashboard", version="1.0.0")
    
    # CRITICAL FIXES - Missing initialization sequence:
    create_tables()  # Initialize database tables
    await initialize_agent_system()  # START AGENT SYSTEM
    await activate_authentication_system()  # Activate auth
    
    # Include ALL API routers (agent router was missing)
    app.include_router(auth_router, prefix="/api/auth")
    app.include_router(user_router, prefix="/api/users") 
    app.include_router(client_router, prefix="/api/clients")
    app.include_router(agent_router, prefix="/api/agents")  # MISSING
    app.include_router(document_router, prefix="/api/documents")
    
    setup_ui_routes(app)
    return app

async def initialize_agent_system():
    \"\"\"Complete agent system initialization sequence.\"\"\"
    from app.core.agent_manager import agent_manager
    from app.agents.pdf_processor_agent import PDFProcessorAgent
    from app.agents.questionnaire_writer_agent import QuestionnaireWriterAgent
    
    # Agent registration order and dependencies
    await agent_manager.register_agent_type("pdf_processor", PDFProcessorAgent)
    await agent_manager.register_agent_type("questionnaire_writer", QuestionnaireWriterAgent)
    
    # Create default agent instances
    await agent_manager.create_agent("pdf_processor", "default_pdf_processor")
    await agent_manager.create_agent("questionnaire_writer", "default_questionnaire_writer")
    
    # Health check procedures for initialized agents
    for agent_id in ["default_pdf_processor", "default_questionnaire_writer"]:
        agent = await agent_manager.get_agent(agent_id)
        if not await agent.health_check():
            raise AgentInitializationError(f"Agent {agent_id} failed startup health check")
```

#### Agent Lifecycle Management
```python
class AgentLifecycleManager:
    \"\"\"Agent state management (STARTING → RUNNING → STOPPING).\"\"\"
    
    async def setup_health_monitoring(self):
        \"\"\"Health monitoring and automatic restart procedures.\"\"\"
        async def monitor_agents():
            while True:
                for agent_id in agent_manager.get_active_agents():
                    agent = await agent_manager.get_agent(agent_id)
                    if not await agent.health_check():
                        await self._recover_failed_agent(agent_id)
                await asyncio.sleep(30)
        
        asyncio.create_task(monitor_agents())
    
    async def _recover_failed_agent(self, agent_id: str):
        \"\"\"Agent failure isolation and recovery.\"\"\"
        try:
            await agent_manager.stop_agent(agent_id)
            await asyncio.sleep(5)  # Backoff
            await agent_manager.restart_agent(agent_id)
            
            agent = await agent_manager.get_agent(agent_id)
            if await agent.health_check():
                logger.info(f"Successfully recovered agent: {agent_id}")
        except Exception as e:
            logger.error(f"Agent recovery failed for {agent_id}: {str(e)}")
```

#### Error Handling for Agent Startup Failures
- **Graceful Degradation**: Se agentes falham no startup, sistema roda em modo degradado
- **Recovery Procedures**: Restart automático com backoff exponencial
- **User Communication**: Notificações claras sobre agentes indisponíveis
- **Fallback Workflows**: Processamento manual quando agentes não estão disponíveis

### Database Schema Completeness Strategy

**CRITICAL IMPLEMENTATION REQUIREMENT**: Tabela `questionnaire_drafts` inexistente causando crashes no CRUD.

#### Missing Table Resolution
```sql
-- CRITICAL FIX: Create missing questionnaire_drafts table
CREATE TABLE IF NOT EXISTS questionnaire_drafts (
    draft_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_type VARCHAR(100) NOT NULL,
    draft_content JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_questionnaire_drafts_client_id 
ON questionnaire_drafts(client_id);

CREATE INDEX IF NOT EXISTS idx_questionnaire_drafts_user_id 
ON questionnaire_drafts(user_id);
```

#### Startup Database Validation
```python
class StartupDatabaseValidator:
    \"\"\"Automatic schema completeness check and validation.\"\"\"
    
    async def validate_database_startup(self):
        # Detect missing tables
        missing_tables = await self._detect_missing_tables()
        if missing_tables:
            await self._create_missing_tables(missing_tables)
        
        # Validate foreign key constraints
        await self._validate_foreign_keys()
        
        # Verify migration status
        await self._verify_migration_status()
    
    async def _detect_missing_tables(self) -> list[str]:
        expected_tables = [
            "users", "clients", "agent_executions", "processed_documents",
            "questionnaire_drafts", "user_sessions", "audit_logs"
        ]
        
        missing_tables = []
        async with get_async_db() as db:
            for table in expected_tables:
                result = await db.execute(
                    text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table)"),
                    {"table": table}
                )
                if not result.scalar():
                    missing_tables.append(table)
        
        return missing_tables
```

### Arquitetura Atual Validada (Updated)

#### Stack Tecnológico (Verificado via MCP Context7)
- **Backend**: Python 3.12 + FastAPI (dependency injection, WebSockets, async)
- **Frontend**: NiceGUI com Vue/Quasar nativo
- **Database**: PostgreSQL + pgvector (embeddings, índices HNSW/IVFFlat)
- **AI/ML**: Google Gemini API (text generation, embeddings, chat, streaming)
- **Agents**: Agno framework (autonomous agents, reasoning, memory) - **REQUER INICIALIZAÇÃO**

#### Capacidades Nativas Confirmadas

**FastAPI**:
- Dependency injection system nativo
- WebSocket support para real-time updates
- Middleware system para autenticação
- Background tasks para processamento async

**SQLAlchemy 2.0**:
- AsyncSession para operações não-bloqueantes
- ORM patterns modernos com type hints
- Relacionamentos com lazy/eager loading
- Migrations via Alembic

**NiceGUI + Quasar**:
- Material Design components nativos
- Sistema de temas CSS variables
- Classes responsivas (xs, sm, md, lg, xl)
- Dark/light mode nativo
- Eventos de UI reativos

**pgvector**:
- Similarity search com operadores nativos (<->, <#>, <=>)
- Índices de performance (HNSW, IVFFlat)
- Integração nativa com SQLAlchemy

**Google Gemini API**:
- Text generation com streaming
- Content embeddings para vector search
- Chat sessions com histórico
- Multimodal support (text + images)

### Restrições de Implementação (Constraints Nativos)

#### Princípio de Estabilidade
**CRÍTICO**: Todas as customizações devem se manter dentro das capacidades nativas dos frameworks para garantir compatibilidade com updates futuros.

#### Constraints por Framework

**NiceGUI**:
- ✅ Usar apenas componentes `ui.*` nativos
- ✅ CSS customization via classes Quasar nativas
- ❌ NÃO criar componentes JavaScript customizados
- ❌ NÃO modificar comportamentos core do framework

**Quasar**:
- ✅ Temas baseados em CSS variables nativas
- ✅ Classes responsivas q-*, col-*, row-*
- ✅ Componentes q-* com props nativas
- ❌ NÃO modificar SCSS variables do Quasar core

**FastAPI**:
- ✅ Dependency injection system nativo
- ✅ Middleware stack padrão
- ✅ Background tasks e WebSockets nativos
- ❌ NÃO modificar comportamento core do ASGI

**SQLAlchemy**:
- ✅ AsyncSession e ORM patterns padrão
- ✅ Relacionamentos e migrations nativas
- ❌ NÃO criar SQL customizado complexo onde ORM resolve

#### Validação de Feasibilidade

**Qualidade Visual 7-8/10**: ✅ POSSÍVEL
- Material Design nativo oferece aparência profissional
- CSS variables permitem customização suficiente
- Micro-interações via transições CSS nativas

**Performance Requirements**: ✅ ATENDÍVEL
- AsyncSession + background tasks para I/O não-bloqueante
- WebSockets nativos para updates em tempo real
- pgvector índices para searches sub-segundo

**Hot-swappable Agents**: ✅ IMPLEMENTÁVEL
- Agno framework suporta dynamic agent loading
- FastAPI dependency injection para runtime swapping
- PostgreSQL para agent state persistence