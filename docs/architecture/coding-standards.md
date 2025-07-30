# Coding Standards

This document defines MINIMAL but CRITICAL standards for AI agents and developers working on the IAM Dashboard project. These rules prevent common mistakes and ensure consistent, maintainable code.

## Critical Project-Specific Rules

### Agent Integration Rules
- **Agent Service Pattern**: Always use `BaseAgentService` for agent integration - never call agents directly
- **Agent Error Handling**: All agent operations must use try/catch with `AgentExecutionError` hierarchy
- **Agent State Management**: Never access agent internal state directly - use manager interface
- **Hot-Swap Safety**: Agent replacements must preserve session state and gracefully handle in-flight requests

### API and Service Layer Rules
- **Repository Pattern**: Never access database models directly from UI or API - always use repository layer
- **Service Layer Isolation**: Business logic MUST reside in service layer, not in API endpoints or UI components
- **Async Consistency**: All database operations and external API calls must be async
- **Error Response Format**: All API endpoints must use standardized error response format

### Authentication and Security Rules
- **JWT Token Validation**: Never skip token validation in protected endpoints
- **Role-Based Access**: Always check user roles before agent operations or admin functions
- **Input Sanitization**: All user inputs must be validated and sanitized before processing
- **Secret Management**: Never hardcode secrets - use environment variables with validation

### Agent Development Rules
- **Plugin Interface**: All agents must implement the standard plugin interface for hot-swap capability
- **Health Check Implementation**: Every agent must implement health_check() method with meaningful status
- **Execution Tracking**: All agent operations must be tracked with execution_id for debugging
- **Resource Cleanup**: Agents must properly clean up resources (files, connections) after processing

## Python Code Style Standards

### Code Formatting
- **Line Length**: 88 characters (Black/Ruff standard)
- **Formatter**: Use `ruff format` (replaces Black)
- **Linting**: Use `ruff check` with strict configuration
- **Auto-fixes**: Run `ruff check --fix` before commits

### Type Hints (MANDATORY)
```python
# Required for ALL functions and class attributes
def process_document(doc_id: str, user_id: int, client_id: int) -> DocumentResult:
    """Process document with full type annotations."""
    pass

class AgentManager:
    """Agent manager with typed attributes."""
    agents: dict[str, AgentPlugin]
    health_monitor: HealthMonitor
    
    async def create_agent(self, agent_type: str, agent_id: str) -> AgentPlugin:
        """Create agent with proper return type."""
        pass
```

### Documentation Standards
```python
def create_agent(agent_type: str, config: dict | None = None) -> Agent:
    """Create a new agent instance with configuration.
    
    Args:
        agent_type: Type of agent to create (e.g., 'pdf_processor', 'questionnaire_writer')
        config: Optional agent configuration dictionary
        
    Returns:
        Configured agent instance ready for processing
        
    Throws:
        AgentConfigError: If agent type is invalid or configuration is malformed
        AgentCreationError: If agent instantiation fails
        
    Example:
        >>> agent = create_agent('pdf_processor', {'timeout': 30})
        >>> await agent.process({'file_data': pdf_bytes})
    """
```

### Code Organization Limits
- **Files**: Maximum 500 lines (split if larger)
- **Functions**: Maximum 50 lines, single responsibility
- **Classes**: Maximum 100 lines (use composition over inheritance)
- **Function Parameters**: Maximum 5 parameters (use dataclasses for more)

## Naming Conventions

| Element | Convention | Example | Notes |
|---------|------------|---------|-------|
| **Modules** | snake_case | `user_service.py` | Descriptive, avoid abbreviations |
| **Classes** | PascalCase | `UserService`, `PDFProcessorAgent` | Clear business domain names |
| **Functions** | snake_case | `process_document()`, `get_user_by_id()` | Verb + noun pattern |
| **Variables** | snake_case | `user_id`, `processed_count` | Descriptive, avoid single letters |
| **Constants** | UPPER_SNAKE_CASE | `MAX_FILE_SIZE`, `DEFAULT_TIMEOUT` | Module-level constants |
| **Private Methods** | _snake_case | `_validate_input()`, `_cleanup_temp_files()` | Leading underscore |
| **Agent IDs** | snake_case | `pdf_processor`, `questionnaire_writer` | Used in configuration |

### Database Naming Conventions

| Element | Convention | Example | Rationale |
|---------|------------|---------|-----------|
| **Tables** | snake_case (plural) | `users`, `client_documents` | Standard SQL convention |
| **Primary Keys** | `{entity}_id` | `user_id`, `client_id` | Entity-specific identification |
| **Foreign Keys** | `{referenced_entity}_id` | `user_id`, `document_id` | Clear relationship naming |
| **Timestamps** | `{action}_at` | `created_at`, `updated_at` | Action-based naming |
| **Booleans** | `is_{state}` | `is_active`, `is_processed` | Boolean state indicators |
| **Indexes** | `idx_{table}_{column}` | `idx_users_email` | Consistent index naming |

### Agent and Service Naming

```python
# Service Classes
class DocumentProcessingService:    # Business domain + Service
class UserAuthenticationService:    # Business domain + Service
class AgentOrchestrationService:    # Business domain + Service

# Agent Classes  
class PDFProcessorAgent:           # Function + Agent
class QuestionnaireWriterAgent:    # Function + Agent
class ClientManagementAgent:       # Function + Agent

# Repository Classes
class UserRepository:              # Entity + Repository
class DocumentRepository:          # Entity + Repository
class AgentExecutionRepository:    # Entity + Repository
```

## Architecture Pattern Standards

### Dependency Injection Pattern
```python
# ALWAYS use dependency injection for services
class DocumentService:
    def __init__(
        self, 
        doc_repo: DocumentRepository = Depends(DocumentRepository),
        agent_manager: AgentManager = Depends(AgentManager)
    ):
        self.doc_repo = doc_repo
        self.agent_manager = agent_manager
```

### Repository Pattern Implementation
```python
# Standard repository interface
class BaseRepository:
    async def create(self, data: dict) -> BaseModel:
        """Create new entity."""
        pass
    
    async def get_by_id(self, entity_id: int) -> BaseModel | None:
        """Get entity by primary key."""
        pass
    
    async def update(self, entity_id: int, data: dict) -> BaseModel:
        """Update existing entity."""
        pass
    
    async def delete(self, entity_id: int) -> bool:
        """Delete entity by primary key."""
        pass
```

### Service Layer Pattern
```python
# Business logic in service layer only
class DocumentProcessingService:
    async def process_document(
        self, 
        file_data: bytes, 
        filename: str, 
        user_context: UserContext
    ) -> ProcessingResult:
        """Complete document processing workflow."""
        
        # Validation
        self._validate_file_data(file_data, filename)
        
        # Authorization
        await self._check_processing_permissions(user_context)
        
        # Business logic
        agent = await self.agent_manager.get_agent('pdf_processor')
        result = await agent.process({'file_data': file_data, 'filename': filename})
        
        # Persistence
        document = await self.doc_repo.create({
            'filename': filename,
            'user_id': user_context.user_id,
            'processing_result': result
        })
        
        return ProcessingResult(success=True, document_id=document.id)
```

## Critical Security Rules

### Authentication and Authorization
- **Token Validation**: ALWAYS validate JWT tokens in protected endpoints
- **Role Checking**: Verify user roles before sensitive operations
- **Session Management**: Use secure session handling with proper expiration
- **2FA Enforcement**: Require 2FA for administrative operations

### Input Validation and Sanitization
- **File Upload Validation**: Check file types, sizes, and content before processing
- **SQL Injection Prevention**: Use parameterized queries only (SQLAlchemy ORM)
- **XSS Prevention**: Sanitize all user inputs displayed in UI
- **Path Traversal Prevention**: Validate file paths and restrict access

### Secrets and Configuration Management
- **Environment Variables**: Store all secrets in environment variables
- **Secret Validation**: Validate required environment variables at startup
- **Configuration Security**: Never commit secrets to version control
- **Key Rotation**: Support key rotation for JWT and encryption keys

## Error Handling Standards

### Exception Hierarchy
```python
# Project-specific exception hierarchy
class IAMDashboardError(Exception):
    """Base exception for all project errors."""
    pass

class AgentExecutionError(IAMDashboardError):
    """Agent execution failures."""
    def __init__(self, agent_id: str, message: str, execution_id: str = None):
        self.agent_id = agent_id
        self.execution_id = execution_id
        super().__init__(f"Agent {agent_id}: {message}")

class ValidationError(IAMDashboardError):
    """Input validation failures."""
    pass

class AuthenticationError(IAMDashboardError):
    """Authentication and authorization failures."""
    pass

class DocumentProcessingError(IAMDashboardError):
    """Document processing failures."""
    pass
```

### Error Response Format
```python
# Standardized API error responses
class ErrorResponse:
    error_code: str
    message: str
    details: dict | None = None
    timestamp: datetime
    request_id: str

# Usage in FastAPI endpoints
@router.post("/documents/process")
async def process_document(file: UploadFile):
    try:
        result = await document_service.process_document(file)
        return result
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error_code="VALIDATION_ERROR",
                message=str(e),
                timestamp=datetime.now(UTC),
                request_id=request.state.request_id
            ).dict()
        )
```

## Testing Standards

### Test Organization and Coverage
- **Minimum Coverage**: 80% code coverage required
- **Test Co-location**: Place tests near the code they test
- **Test Naming**: `test_{function_name}_{scenario}` pattern
- **Fixture Usage**: Use pytest fixtures for common setup

### Testing Categories
```python
# Unit Tests - Fast, isolated
class TestUserService:
    async def test_create_user_success(self):
        """Test successful user creation."""
        # Mock dependencies
        # Test single unit of functionality
        pass
    
    async def test_create_user_duplicate_email_raises_error(self):
        """Test error handling for duplicate email."""
        pass

# Integration Tests - Real database, external services mocked  
class TestDocumentProcessingWorkflow:
    async def test_pdf_processing_end_to_end(self):
        """Test complete PDF processing workflow."""
        # Use real database
        # Mock external APIs (Gemini)
        # Test multiple components working together
        pass

# E2E Tests - Real browser, real workflows
class TestUserDocumentUpload:
    async def test_user_uploads_pdf_and_sees_results(self):
        """Test complete user workflow from login to results."""
        # Use MCP Playwright for real browser testing
        # Test complete user journey
        pass
```

### Agent Testing Patterns
```python
# Agent testing with proper isolation
class TestPDFProcessorAgent:
    async def test_process_pdf_success(self):
        """Test PDF processing with valid input."""
        agent = PDFProcessorAgent()
        
        # Use test file data
        test_data = {'file_data': sample_pdf_bytes, 'filename': 'test.pdf'}
        
        result = await agent.process(test_data)
        
        assert result['success'] is True
        assert result['extracted_text'] is not None
        assert result['metadata']['page_count'] > 0
    
    async def test_agent_health_check(self):
        """Test agent health check functionality."""
        agent = PDFProcessorAgent()
        
        health_status = await agent.health_check()
        
        assert health_status is True
```

## Performance and Scalability Standards

### Async Programming
- **Async All I/O**: Use async/await for all database and external API calls
- **Connection Pooling**: Use connection pools for database and HTTP clients
- **Resource Management**: Properly close connections and clean up resources
- **Timeout Handling**: Set appropriate timeouts for all external calls

### Memory Management
- **Large File Handling**: Stream large files, don't load entirely in memory
- **Agent Resource Limits**: Implement memory limits for agent processing
- **Garbage Collection**: Explicitly clean up large objects after processing
- **Memory Monitoring**: Monitor memory usage in production

## Development Workflow Standards

### Pre-commit Requirements
```bash
# Required pre-commit checks
ruff format .                    # Code formatting
ruff check .                     # Linting
mypy app/                       # Type checking
pytest tests/unit/              # Unit tests
pytest --cov=app tests/         # Coverage check
```

### Version Control Standards
- **Commit Messages**: Use conventional commit format
- **Branch Naming**: `feature/description`, `fix/description`, `hotfix/description`
- **Pull Request Requirements**: All checks pass, code review approved
- **No Direct Main**: Always use pull requests for main branch

### Environment Management
- **Environment Variables**: Document all required environment variables
- **Development Setup**: Maintain up-to-date development setup instructions
- **Docker Consistency**: Ensure Docker environments match production
- **Dependency Management**: Keep dependencies up-to-date and secure

## Tool Configuration

### Ruff Configuration (.ruff.toml)
```toml
line-length = 88
target-version = "py312"
exclude = ["migrations/", "venv/", ".venv/"]

[lint]
select = ["E", "F", "I", "N", "W", "UP", "S", "B", "A", "C4", "T20"]
ignore = ["E501", "S101"]  # Line length handled by formatter, allow assert

[lint.per-file-ignores]
"tests/*" = ["S101"]  # Allow assert in tests
```

### MyPy Configuration (mypy.ini)
```ini
[mypy]
python_version = 3.12
strict = True
warn_return_any = True
warn_unused_configs = True
exclude = venv/,migrations/

[mypy-tests.*]
disallow_untyped_defs = False
```

These coding standards ensure consistency, maintainability, and quality across the IAM Dashboard codebase while supporting the autonomous agent architecture and modern Python development practices.