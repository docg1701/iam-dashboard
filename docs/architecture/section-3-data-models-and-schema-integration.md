# Section 3: Data Models and Schema Integration

### 3.1 Enhanced Entity Relationship Model

**Core Entities with Agent Integration**:

```python
# Core Models with Agent Integration
class User(TimestampedModel):
    username = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    totp_secret = Column(String(32), nullable=True)
    is_2fa_enabled = Column(Boolean, default=False)
    agent_permissions = relationship("UserAgentPermission")
    agent_sessions = relationship("AgentSession")

class AgentExecution(TimestampedModel):
    __tablename__ = "agent_executions"
    execution_id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    status = Column(Enum(ExecutionStatus), nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)

class ProcessedDocument(TimestampedModel):
    __tablename__ = "processed_documents"
    document_id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    original_filename = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    agent_execution_id = Column(String(36), ForeignKey("agent_executions.execution_id"))
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    processing_status = Column(Enum(ProcessingStatus), nullable=False)
    extracted_text = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    embedding_vector = Column(Vector(1536), nullable=True)
```

### 3.2 Database Migration Strategy

**Critical Startup Sequence Fix**:

```python
# app/main.py - Critical startup fixes
async def create_application() -> FastAPI:
    container = ApplicationContainer()
    container.wire(modules=[__name__])
    
    app = FastAPI(title="IAM Dashboard", version="1.0.0")
    
    # CRITICAL FIXES:
    create_tables()  # Initialize database tables
    await initialize_agent_system()  # Start agent system
    
    # Include ALL API routers
    app.include_router(auth_router, prefix="/api/auth")
    app.include_router(user_router, prefix="/api/users")
    app.include_router(client_router, prefix="/api/clients")
    app.include_router(agent_router, prefix="/api/agents")  # MISSING
    app.include_router(document_router, prefix="/api/documents")
    
    setup_ui_routes(app)
    return app
```

### 3.3 Database Schema Completeness Verification

**CRITICAL IMPLEMENTATION REQUIREMENT**: Addresses missing questionnaire_drafts table and foreign key violations.

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