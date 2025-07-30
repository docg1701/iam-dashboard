# Unified Project Structure

This document defines the standardized project structure for the IAM Dashboard autonomous agent platform. This structure accommodates the Python-based FastAPI backend, NiceGUI web interface, and Agno autonomous agents system.

## Project Structure Overview

```
iam-dashboard/
├── .github/                    # CI/CD workflows and GitHub configuration
│   └── workflows/
│       ├── ci.yml             # Continuous integration pipeline
│       └── deploy.yml         # Deployment pipeline
├── app/                       # Main application package
│   ├── main.py               # FastAPI application entry point
│   ├── containers.py         # Dependency injection setup
│   │
│   ├── core/                 # Core infrastructure components
│   │   ├── __init__.py
│   │   ├── auth.py          # JWT authentication & 2FA
│   │   ├── database.py      # Database configuration & connection
│   │   ├── agent_manager.py # Central agent lifecycle management
│   │   ├── agent_registry.py# Agent discovery and registration
│   │   └── agent_config.py  # Agent configuration management
│   │
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py         # Base model with common fields
│   │   ├── user.py         # User authentication model
│   │   ├── client.py       # Client management model
│   │   ├── document.py     # Document metadata model
│   │   ├── agent.py        # Agent configuration model
│   │   └── questionnaire_draft.py # Generated questionnaire model
│   │
│   ├── repositories/        # Data access layer (Repository pattern)
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── client_repository.py
│   │   ├── document_repository.py
│   │   └── document_chunk_repository.py
│   │
│   ├── services/            # Business logic layer
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── client_service.py
│   │   ├── document_service.py
│   │   ├── document_preprocessing.py
│   │   └── questionnaire_draft_service.py
│   │
│   ├── agents/              # Agno autonomous agents
│   │   ├── __init__.py
│   │   ├── base_agent.py    # Base agent class with common functionality
│   │   ├── pdf_processor_agent.py # PDF processing and analysis
│   │   ├── questionnaire_agent.py  # Legal questionnaire generation
│   │   └── plugin_discovery.py     # Dynamic plugin loading
│   │
│   ├── tools/               # Agent tools and utilities
│   │   ├── __init__.py
│   │   ├── pdf_tools.py     # PDF processing utilities
│   │   ├── ocr_tools.py     # OCR processing tools
│   │   ├── llm_tools.py     # LLM interaction tools
│   │   ├── rag_tools.py     # RAG (Retrieval Augmented Generation)
│   │   ├── template_tools.py# Document template management
│   │   └── vector_storage_tools.py # Vector database operations
│   │
│   ├── plugins/             # Agent plugins for extensibility
│   │   ├── __init__.py
│   │   ├── pdf_processor_plugin.py
│   │   └── questionnaire_plugin.py
│   │
│   ├── api/                 # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── clients.py       # Client management endpoints
│   │   ├── documents.py     # Document upload/processing endpoints
│   │   ├── questionnaire.py # Questionnaire generation endpoints
│   │   ├── admin.py         # Administrative endpoints
│   │   └── middleware/      # Custom middleware
│   │       ├── agent_error_handler.py
│   │       └── performance_middleware.py
│   │
│   ├── ui_components/       # NiceGUI user interface components
│   │   ├── __init__.py
│   │   ├── login.py         # Authentication UI
│   │   ├── register.py      # User registration UI
│   │   ├── dashboard.py     # Main dashboard
│   │   ├── clients_area.py  # Client management UI
│   │   ├── client_details.py# Individual client view
│   │   ├── document_upload.py  # Document upload interface
│   │   ├── document_list.py    # Document listing and management
│   │   ├── document_summary.py # Document analysis display
│   │   ├── questionnaire_writer.py # Questionnaire generation UI
│   │   ├── admin_dashboard.py  # Admin interface
│   │   ├── admin_control_panel.py # System administration
│   │   ├── agent_config_manager.py # Agent configuration UI
│   │   ├── agent_status_monitor.py # Agent monitoring
│   │   ├── plugin_manager.py   # Plugin management UI
│   │   └── settings_2fa.py     # 2FA settings
│   │
│   ├── config/              # Configuration files
│   │   ├── __init__.py
│   │   ├── agents.yaml      # Agent configuration
│   │   ├── agents.py        # Agent settings
│   │   └── llama_index_config.py # LlamaIndex configuration
│   │
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── security_validators.py # Security validation utilities
│
├── tests/                   # Test suites (co-located with code)
│   ├── __init__.py
│   ├── unit/               # Unit tests
│   │   ├── test_agents/
│   │   ├── test_services/
│   │   └── test_repositories/
│   ├── integration/        # Integration tests
│   │   ├── test_agent_workflows/
│   │   └── test_api_endpoints/
│   ├── e2e/               # End-to-end tests (MCP Playwright)
│   │   └── test_user_workflows/
│   └── performance/       # Performance benchmarking
│       └── test_load/
│
├── alembic/               # Database migration scripts
│   ├── versions/          # Migration versions
│   ├── env.py            # Alembic environment configuration
│   └── script.py.mako    # Migration template
│
├── scripts/               # Utility and maintenance scripts
│   ├── setup_dev.py      # Development environment setup
│   ├── backup_db.py      # Database backup utilities
│   └── deploy.py         # Deployment scripts
│
├── uploads/               # File upload storage
│   ├── documents/         # PDF and document uploads
│   └── temp/             # Temporary processing files
│
├── docs/                  # Comprehensive project documentation
│   ├── architecture/      # Architecture decisions & design
│   │   ├── index.md
│   │   ├── tech-stack.md
│   │   ├── coding-standards.md
│   │   ├── source-tree.md
│   │   └── unified-project-structure.md
│   ├── prd/              # Product requirements documents
│   │   └── index.md
│   └── reference/        # Technical reference materials
│
├── .bmad-core/           # BMad Method configuration and resources
│   ├── core-config.yaml # BMad configuration
│   ├── tasks/           # BMad tasks
│   ├── templates/       # BMad templates
│   └── checklists/      # BMad checklists
│
├── docker-compose.yml    # Docker container orchestration
├── Dockerfile           # Container definition
├── pyproject.toml       # Python project configuration (UV)
├── uv.lock             # UV dependency lock file
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore patterns
├── .ruff.toml          # Ruff linting configuration
├── mypy.ini            # MyPy type checking configuration
├── pytest.ini         # Pytest configuration
└── README.md           # Project overview and setup instructions
```

## Key Directories and Their Purpose

### Application Core (`app/`)

**Core Infrastructure (`app/core/`)**
- Central system components including authentication, database, and agent management
- Agent lifecycle management and registry services
- Dependency injection configuration

**Business Logic (`app/services/`)**
- Domain-specific business logic implementation
- Service layer that orchestrates between repositories and agents
- Stateless services following single responsibility principle

**Data Access (`app/repositories/`)**
- Repository pattern implementation for data access abstraction
- Each repository handles one entity type
- Async SQLAlchemy operations with proper error handling

**Autonomous Agents (`app/agents/`)**
- Agno-based autonomous agents for specialized tasks
- Plugin-based architecture for extensibility
- Agent tools and utilities for common operations

**API Layer (`app/api/`)**
- FastAPI route handlers organized by functional areas
- Custom middleware for cross-cutting concerns
- RESTful endpoints with proper HTTP status codes

**User Interface (`app/ui_components/`)**
- NiceGUI components for web-based user interface
- Component-based architecture with clear separation of concerns
- Real-time updates using WebSocket integration

### Testing Strategy (`tests/`)

**Unit Tests (`tests/unit/`)**
- Individual component testing with mocking
- Fast execution with minimal dependencies
- 80% minimum code coverage requirement

**Integration Tests (`tests/integration/`)**
- Multi-component workflow testing
- Real database connections for data layer testing
- Agent workflow testing with actual Agno instances

**E2E Tests (`tests/e2e/`)**
- Full user workflow testing using MCP Playwright
- Real browser automation (no mocked browser interactions)
- Critical user journey validation

**Performance Tests (`tests/performance/`)**
- Load testing with 100+ concurrent users
- Agent performance benchmarking
- Memory and resource usage validation

### Documentation Structure (`docs/`)

**Architecture Documentation (`docs/architecture/`)**
- Complete system architecture documentation
- Technology stack specifications
- Coding standards and conventions
- Project structure guidelines

**Product Requirements (`docs/prd/`)**
- Business requirements and user stories
- Epic and story definitions
- Success criteria and acceptance criteria

### Development Support

**Migration Management (`alembic/`)**
- Database schema versioning and migration
- Rollback procedures for safe deployments
- Environment-specific migration configurations

**Utility Scripts (`scripts/`)**
- Development environment setup automation
- Database backup and restore procedures
- Deployment and maintenance utilities

**BMad Method Integration (`.bmad-core/`)**
- BMad Method configuration and resources
- Task templates and checklists
- Project methodology documentation

## File Naming Conventions

### Python Files
- **Modules**: `snake_case.py` (e.g., `user_service.py`)
- **Classes**: `PascalCase` (e.g., `UserService`, `PDFProcessorAgent`)
- **Functions**: `snake_case` (e.g., `process_document`, `get_user_by_id`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_FILE_SIZE`, `DEFAULT_TIMEOUT`)

### Configuration Files
- **Environment**: `.env`, `.env.example`, `.env.local`
- **Python Config**: `pyproject.toml`, `setup.cfg`
- **Docker**: `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`
- **CI/CD**: `.github/workflows/*.yml`

### Documentation Files
- **Markdown**: `kebab-case.md` (e.g., `tech-stack.md`, `coding-standards.md`)
- **Architecture**: Organized by section with clear hierarchical structure
- **README**: Each major directory should have a README.md explaining its purpose

## Development Workflow Integration

### Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd iam-dashboard

# Install dependencies
uv sync

# Setup database
docker compose up -d postgres redis
uv run alembic upgrade head

# Start application
uv run python -m app.main
```

### Agent Development Workflow
```bash
# Create new agent
mkdir app/agents/new_agent
touch app/agents/new_agent/{__init__.py,new_agent.py}

# Register agent in config
# Edit app/config/agents.yaml

# Create agent tests
mkdir tests/unit/test_agents/test_new_agent
touch tests/unit/test_agents/test_new_agent/test_agent.py

# Run agent tests
uv run pytest tests/unit/test_agents/test_new_agent/
```

### UI Component Development
```bash
# Create new UI component
touch app/ui_components/new_component.py

# Import in main UI router
# Edit app/main.py to include new route

# Create integration test
touch tests/integration/test_ui/test_new_component.py

# Test with real browser
uv run pytest tests/e2e/ -k new_component
```

## Project Structure Guidelines

### Vertical Slice Organization
Each major feature spans multiple layers:
- `models/{feature}.py` - Data model
- `repositories/{feature}_repository.py` - Data access
- `services/{feature}_service.py` - Business logic
- `api/{feature}.py` - HTTP endpoints
- `ui_components/{feature}_*.py` - UI components
- `agents/{feature}_agent.py` - Autonomous agent (if applicable)

### Agent Architecture Pattern
- `agents/` - Core agent implementations
- `tools/` - Reusable agent tools
- `plugins/` - Extension points
- `config/agents.yaml` - Agent configuration

### Cross-Cutting Concerns
- Authentication: Centralized in `app/core/auth.py`
- Logging: Configured in `app/core/config.py`
- Error Handling: Middleware in `app/api/middleware/`
- Database: Connection management in `app/core/database.py`

## Navigation and File Discovery

### Quick Navigation Patterns
- **Find Model**: `app/models/{entity}.py`
- **Find Service**: `app/services/{entity}_service.py`
- **Find API**: `app/api/{entity}.py`
- **Find UI**: `app/ui_components/{entity}_*.py`
- **Find Tests**: `tests/unit/test_{category}/test_{entity}.py`
- **Find Agent**: `app/agents/{entity}_agent.py`

### Import Patterns
```python
# Core imports
from app.core.database import get_async_db
from app.core.auth import require_auth

# Service layer imports
from app.services.user_service import UserService

# Model imports
from app.models.user import User

# Agent imports
from app.agents.pdf_processor_agent import PDFProcessorAgent
```

This unified project structure ensures consistency, maintainability, and clear separation of concerns while supporting the autonomous agent architecture and modern Python development practices.