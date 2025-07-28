# API Design and Integration

## API Endpoint Migration Strategy

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

## Response Schema Preservation

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

## New Agent Management Endpoints

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

## Error Handling Integration

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

## Performance Considerations

**Response Time Requirements:**
- Document processing: ≤ 30 seconds (same as current)
- Questionnaire generation: ≤ 15 seconds (same as current)
- Agent management operations: ≤ 2 seconds
- Health check endpoints: ≤ 500ms

**Concurrency Handling:**
```python
class AgentLoadBalancer:
    """Load balancing for multiple agent instances."""
    
    async def route_request(self, agent_type: str, request: Any) -> Any:
        # Get least busy agent instance
        agent = await self._get_optimal_agent(agent_type)
        
        # Process with timeout
        try:
            result = await asyncio.wait_for(
                agent.process(request),
                timeout=300  # 5 minutes max
            )
            return result
        except asyncio.TimeoutError:
            raise AgentError("Processing timeout", "AGENT_TIMEOUT", 408)
```

## API Versioning Strategy

**Version Headers:**
```python
@router.get("/api/v1/documents/process")
async def process_document_v1(...):
    # Current implementation preserved for compatibility

@router.get("/api/v2/documents/process")  
async def process_document_v2(...):
    # New agent-based implementation
```

**Deprecation Timeline:**
- Phase 1: Both v1 (Celery) and v2 (Agents) available
- Phase 2: v1 marked deprecated, v2 as default
- Phase 3: v1 removed after 6 months notice

## Rate Limiting Integration

**Agent-specific Rate Limits:**
```python
# Heavy processing endpoints
@limiter.limit("5/minute")
@router.post("/documents/process")
async def process_document(...):
    pass

# Agent management endpoints  
@limiter.limit("10/minute")
@router.get("/admin/agents/status")
async def get_agents_status(...):
    pass

# Standard API endpoints
@limiter.limit("100/minute")
@router.get("/clients")
async def list_clients(...):
    pass
```

## Authentication Integration

**Agent Operation Authorization:**
```python
async def authorize_agent_operation(
    user: User,
    agent_id: str,
    operation: str
) -> bool:
    """Authorize user for agent operations."""
    # Admin users can perform all operations
    if user.is_admin:
        return True
    
    # Regular users can only view status
    if operation in ["status", "health"]:
        return True
        
    # Deny management operations for regular users
    return False

@router.post("/admin/agents/{agent_id}/restart")
async def restart_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    if not await authorize_agent_operation(current_user, agent_id, "restart"):
        raise HTTPException(403, "Insufficient permissions")
    
    # Proceed with restart
    await agent_manager.restart_agent(agent_id)
```

## Migration Testing Strategy

**API Contract Testing:**
```python
class TestAPIMigration:
    """Test API compatibility during migration."""
    
    async def test_response_schema_compatibility(self):
        # Test old vs new endpoint responses
        old_response = await celery_endpoint()
        new_response = await agent_endpoint()
        
        # Schema should be identical
        assert old_response.model_dump() == new_response.model_dump()
    
    async def test_performance_requirements(self):
        # Measure response times
        start_time = time.time()
        await agent_endpoint()
        duration = time.time() - start_time
        
        # Should meet performance requirements
        assert duration <= 30.0  # 30 second max
```

## Documentation Updates

**API Documentation:**
- Swagger/OpenAPI specs updated with agent endpoints
- Authentication requirements documented
- Rate limiting policies specified
- Error response formats documented
- Performance expectations clarified

**Developer Guide:**
- Agent-based workflow examples
- Error handling best practices
- Performance optimization tips
- Migration timeline and compatibility notes