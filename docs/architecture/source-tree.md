# Source Tree Structure

This document provides a comprehensive overview of the IAM Dashboard project structure, including all directories, key files, and organizational patterns that guide development.

## Complete Project Structure

```
iam-dashboard/
├── .github/                           # GitHub configuration and workflows
│   ├── workflows/
│   │   ├── ci.yml                    # Continuous integration pipeline
│   │   ├── deploy.yml                # Deployment automation  
│   │   └── security-scan.yml         # Security scanning workflow
│   ├── ISSUE_TEMPLATE/               # Issue templates
│   └── pull_request_template.md      # PR template
│
├── .bmad-core/                       # BMad Method configuration and resources
│   ├── core-config.yaml             # BMad project configuration
│   ├── tasks/                        # BMad task definitions
│   │   ├── create-next-story.md
│   │   ├── document-project.md
│   │   └── execute-checklist.md
│   ├── templates/                    # BMad document templates
│   │   ├── story-tmpl.yaml
│   │   ├── architecture-tmpl.yaml
│   │   └── fullstack-architecture-tmpl.yaml
│   ├── checklists/                   # BMad quality checklists
│   │   ├── story-draft-checklist.md
│   │   └── architect-checklist.md
│   └── data/                         # BMad knowledge base
│       └── bmad-kb.md
│
├── app/                              # Main application package
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   ├── containers.py                 # Dependency injection container setup
│   │
│   ├── core/                         # Core infrastructure components
│   │   ├── __init__.py
│   │   ├── auth.py                   # JWT authentication & 2FA implementation
│   │   ├── database.py               # Database configuration & async connection
│   │   ├── config.py                 # Application configuration management
│   │   ├── agent_manager.py          # Central agent lifecycle management
│   │   ├── agent_registry.py         # Agent discovery and registration
│   │   └── agent_config.py           # Agent configuration management
│   │
│   ├── models/                       # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py                   # Base model with common fields and methods
│   │   ├── user.py                   # User authentication and profile model
│   │   ├── client.py                 # Client management and metadata model
│   │   ├── document.py               # Document metadata and processing status
│   │   ├── document_chunk.py         # Vector storage for document chunks
│   │   ├── agent.py                  # Agent configuration and execution tracking
│   │   └── questionnaire_draft.py    # Generated questionnaire storage
│   │
│   ├── repositories/                 # Data access layer (Repository pattern)
│   │   ├── __init__.py
│   │   ├── base_repository.py        # Base repository with common operations
│   │   ├── user_repository.py        # User data access operations
│   │   ├── client_repository.py      # Client data access operations
│   │   ├── document_repository.py    # Document data access operations
│   │   └── document_chunk_repository.py # Vector storage operations
│   │
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── base_service.py           # Base service with common patterns
│   │   ├── user_service.py           # User management business logic
│   │   ├── client_service.py         # Client management business logic
│   │   ├── document_service.py       # Document processing orchestration
│   │   ├── document_preprocessing.py # Document preprocessing utilities
│   │   ├── questionnaire_draft_service.py # Questionnaire generation logic
│   │   └── agent_orchestration_service.py # Agent coordination service
│   │
│   ├── agents/                       # Agno autonomous agents
│   │   ├── __init__.py
│   │   ├── base_agent.py             # Base agent class with common functionality
│   │   ├── pdf_processor_agent.py    # PDF processing and analysis agent
│   │   ├── questionnaire_agent.py    # Legal questionnaire generation agent
│   │   ├── client_management_agent.py # Client workflow automation agent
│   │   └── plugin_discovery.py       # Dynamic plugin loading system
│   │
│   ├── tools/                        # Agent tools and utilities
│   │   ├── __init__.py
│   │   ├── pdf_tools.py              # PDF processing utilities (PyMuPDF)
│   │   ├── ocr_tools.py              # OCR processing tools (PyTesseract)
│   │   ├── llm_tools.py              # LLM interaction tools (Gemini API)
│   │   ├── rag_tools.py              # RAG implementation (LlamaIndex)
│   │   ├── template_tools.py         # Document template management
│   │   ├── vector_storage_tools.py   # Vector database operations (pgvector)
│   │   └── security_tools.py         # Security validation and encryption
│   │
│   ├── plugins/                      # Agent plugins for extensibility
│   │   ├── __init__.py
│   │   ├── pdf_processor_plugin.py   # PDF processing plugin implementation
│   │   ├── questionnaire_plugin.py   # Questionnaire generation plugin
│   │   └── monitoring_plugin.py      # Agent monitoring and metrics plugin
│   │
│   ├── api/                          # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── auth.py                   # Authentication and authorization endpoints
│   │   ├── users.py                  # User management endpoints
│   │   ├── clients.py                # Client management endpoints
│   │   ├── documents.py              # Document upload/processing endpoints
│   │   ├── questionnaire.py          # Questionnaire generation endpoints
│   │   ├── agents.py                 # Agent management and execution endpoints
│   │   ├── admin.py                  # Administrative endpoints
│   │   ├── health.py                 # Health check and monitoring endpoints
│   │   └── middleware/               # Custom middleware
│   │       ├── __init__.py
│   │       ├── agent_error_handler.py # Agent-specific error handling
│   │       ├── performance_middleware.py # Performance monitoring
│   │       ├── auth_middleware.py     # Authentication middleware
│   │       └── logging_middleware.py  # Request/response logging
│   │
│   ├── ui_components/                # NiceGUI user interface components
│   │   ├── __init__.py
│   │   ├── base_component.py         # Base UI component with common functionality
│   │   ├── login.py                  # Authentication UI
│   │   ├── register.py               # User registration UI
│   │   ├── dashboard.py              # Main dashboard and navigation
│   │   ├── clients_area.py           # Client management UI
│   │   ├── client_details.py         # Individual client view and editing
│   │   ├── document_upload.py        # Document upload interface with progress
│   │   ├── document_list.py          # Document listing and management
│   │   ├── document_summary.py       # Document analysis display
│   │   ├── questionnaire_writer.py   # Questionnaire generation UI
│   │   ├── admin_dashboard.py        # Admin interface overview
│   │   ├── admin_control_panel.py    # System administration controls
│   │   ├── agent_config_manager.py   # Agent configuration UI
│   │   ├── agent_status_monitor.py   # Real-time agent monitoring
│   │   ├── plugin_manager.py         # Plugin management UI
│   │   ├── settings_2fa.py           # 2FA settings and configuration
│   │   └── error_pages.py            # Error handling UI components
│   │
│   ├── config/                       # Configuration files and settings
│   │   ├── __init__.py
│   │   ├── agents.yaml               # Agent configuration and parameters
│   │   ├── agents.py                 # Agent settings and defaults
│   │   ├── llama_index_config.py     # LlamaIndex configuration
│   │   ├── database_config.py        # Database connection settings
│   │   └── security_config.py        # Security and encryption settings
│   │
│   └── utils/                        # Utility functions and helpers
│       ├── __init__.py
│       ├── security_validators.py    # Security validation utilities
│       ├── file_handlers.py          # File processing utilities
│       ├── datetime_utils.py         # Date/time handling utilities
│       ├── logging_utils.py          # Logging configuration and helpers
│       └── async_utils.py            # Async programming utilities
│
├── tests/                            # Comprehensive test suites
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration and fixtures
│   ├── unit/                         # Unit tests (fast, isolated)
│   │   ├── __init__.py
│   │   ├── test_agents/              # Agent unit tests
│   │   │   ├── test_pdf_processor_agent.py
│   │   │   ├── test_questionnaire_agent.py
│   │   │   └── test_base_agent.py
│   │   ├── test_services/            # Service layer unit tests
│   │   │   ├── test_user_service.py
│   │   │   ├── test_document_service.py
│   │   │   └── test_client_service.py
│   │   ├── test_repositories/        # Repository unit tests
│   │   │   ├── test_user_repository.py
│   │   │   └── test_document_repository.py
│   │   ├── test_models/              # Model unit tests
│   │   │   ├── test_user_model.py
│   │   │   └── test_document_model.py
│   │   └── test_utils/               # Utility function tests
│   │       ├── test_security_validators.py
│   │       └── test_file_handlers.py
│   │
│   ├── integration/                  # Integration tests (real database)
│   │   ├── __init__.py
│   │   ├── test_agent_workflows/     # Agent workflow integration
│   │   │   ├── test_pdf_processing_workflow.py
│   │   │   └── test_questionnaire_workflow.py
│   │   ├── test_api_endpoints/       # API endpoint integration
│   │   │   ├── test_document_api.py
│   │   │   ├── test_user_api.py
│   │   │   └── test_agent_api.py
│   │   └── test_database/            # Database integration tests
│   │       ├── test_migrations.py
│   │       └── test_relationships.py
│   │
│   ├── e2e/                          # End-to-end tests (MCP Playwright)
│   │   ├── __init__.py
│   │   ├── test_user_workflows/      # Complete user journey tests
│   │   │   ├── test_user_registration_login.py
│   │   │   ├── test_document_upload_processing.py
│   │   │   └── test_questionnaire_generation.py
│   │   ├── test_admin_workflows/     # Admin workflow tests
│   │   │   ├── test_user_management.py
│   │   │   └── test_agent_management.py
│   │   └── fixtures/                 # Test data and fixtures
│   │       ├── sample_documents/
│   │       └── test_users.json
│   │
│   └── performance/                  # Performance and load tests
│       ├── __init__.py
│       ├── test_load/                # Load testing scenarios
│       │   ├── test_document_processing_load.py
│       │   └── test_concurrent_users.py
│       └── test_benchmarks/          # Performance benchmarks
│           ├── test_agent_performance.py
│           └── test_database_performance.py
│
├── alembic/                          # Database migration management
│   ├── versions/                     # Migration version files
│   │   └── [timestamp]_initial_migration.py
│   ├── env.py                        # Alembic environment configuration
│   ├── script.py.mako                # Migration template
│   └── alembic.ini                   # Alembic configuration
│
├── scripts/                          # Utility and maintenance scripts
│   ├── setup_dev.py                  # Development environment setup
│   ├── backup_db.py                  # Database backup utilities
│   ├── restore_db.py                 # Database restore utilities
│   ├── deploy.py                     # Deployment automation scripts
│   ├── seed_data.py                  # Database seeding with test data
│   ├── cleanup_temp.py               # Temporary file cleanup
│   └── generate_keys.py              # Security key generation
│
├── uploads/                          # File upload storage
│   ├── documents/                    # PDF and document uploads
│   │   ├── processed/                # Successfully processed documents
│   │   ├── failed/                   # Failed processing documents
│   │   └── temp/                     # Temporary processing files
│   └── exports/                      # Generated exports (questionnaires, reports)
│
├── docs/                             # Comprehensive project documentation
│   ├── README.md                     # Project overview and quick start
│   ├── architecture/                 # Architecture documentation
│   │   ├── index.md                  # Architecture overview
│   │   ├── tech-stack.md             # Technology stack specifications
│   │   ├── coding-standards.md       # Development standards and conventions
│   │   ├── source-tree.md            # This file - project structure guide
│   │   ├── unified-project-structure.md # Unified structure documentation
│   │   ├── section-1-current-state-analysis.md
│   │   ├── section-2-target-architecture-vision.md
│   │   ├── section-3-data-models-and-schema-integration.md
│   │   ├── section-4-component-architecture-and-integration-patterns.md
│   │   ├── section-5-api-design-and-agent-integration.md
│   │   ├── section-6-user-interface-integration.md
│   │   ├── section-7-coding-standards-and-integration-consistency.md
│   │   ├── section-8-testing-strategy.md
│   │   ├── section-9-security-integration.md
│   │   ├── section-10-infrastructure-and-deployment-integration.md
│   │   └── section-11-rollback-procedures-documentation.md
│   │
│   ├── prd/                          # Product requirements documents
│   │   ├── index.md                  # PRD overview
│   │   ├── epic-1-correcao-de-infraestrutura-critica-e-hotswap-de-agentes.md
│   │   ├── epic-2-melhoria-da-experiencia-visual-ui-polish.md
│   │   ├── introducao-e-analise-do-projeto.md
│   │   ├── requisitos-funcionais-e-nao-funcionais.md
│   │   └── estrategia-de-implementacao-e-rollout.md
│   │
│   ├── stories/                      # Development stories (generated by BMad)
│   │   └── [epic].[story].[title].md # Individual story files
│   │
│   ├── api/                          # API documentation
│   │   ├── openapi.yaml              # OpenAPI specification
│   │   └── postman-collection.json   # Postman API collection
│   │
│   └── reference/                    # Technical reference materials
│       ├── deployment-guide.md       # Deployment procedures
│       ├── troubleshooting.md        # Common issues and solutions
│       └── contributing.md           # Contribution guidelines
│
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore patterns
├── .ruff.toml                        # Ruff linting and formatting configuration
├── mypy.ini                          # MyPy type checking configuration
├── pytest.ini                       # Pytest testing configuration
├── docker-compose.yml                # Docker container orchestration (development)
├── docker-compose.prod.yml           # Production Docker configuration
├── Dockerfile                        # Container definition
├── pyproject.toml                    # Python project configuration (UV)
├── uv.lock                          # UV dependency lock file
├── requirements.txt                  # Pip requirements (UV generated)
├── CHANGELOG.md                      # Project changelog
└── README.md                         # Project overview and setup instructions
```

## Directory Purpose and Responsibilities

### Core Application (`app/`)

#### Infrastructure Layer (`app/core/`)
- **Central System Components**: Authentication, database management, agent lifecycle
- **Configuration Management**: Application settings, environment validation
- **Cross-Cutting Concerns**: Logging, monitoring, security validation

#### Data Layer (`app/models/` & `app/repositories/`)
- **Models**: SQLAlchemy ORM definitions with relationships and constraints
- **Repositories**: Data access abstraction following repository pattern
- **Database Operations**: Async operations with proper error handling and transactions

#### Business Logic Layer (`app/services/`)
- **Domain Logic**: Business rules and workflows
- **Agent Orchestration**: Coordination between multiple agents
- **External Integration**: API calls, file processing, third-party services

#### Agent System (`app/agents/`, `app/tools/`, `app/plugins/`)
- **Autonomous Agents**: Agno-based agents for specialized processing tasks
- **Tool Library**: Reusable utilities for PDF, OCR, LLM, and vector operations
- **Plugin Architecture**: Extensible agent capabilities through dynamic loading

#### Presentation Layer (`app/api/` & `app/ui_components/`)
- **REST API**: FastAPI endpoints with proper HTTP semantics
- **Web Interface**: NiceGUI components for user interaction
- **Real-time Updates**: WebSocket integration for live status updates

### Testing Infrastructure (`tests/`)

#### Test Categories
- **Unit Tests**: Fast, isolated tests with mocked dependencies
- **Integration Tests**: Multi-component tests with real database
- **E2E Tests**: Full user workflows using MCP Playwright
- **Performance Tests**: Load testing and benchmarking

#### Test Organization Patterns
- **Co-located Testing**: Tests organized by component they test
- **Shared Fixtures**: Common test setup in `conftest.py`
- **Test Data Management**: Realistic test data and scenarios

### Documentation System (`docs/`)

#### Architecture Documentation
- **Comprehensive Coverage**: All architectural decisions documented
- **Living Documentation**: Updated with code changes
- **Multiple Audiences**: Technical team, stakeholders, new developers

#### Development Process Documentation
- **BMad Method Integration**: Story-driven development process
- **Quality Assurance**: Checklists and validation procedures
- **Deployment Procedures**: Step-by-step deployment guides

## Navigation Patterns and File Discovery

### Feature-Based Navigation
Each business feature follows vertical slice organization:

```
Feature: Document Processing
├── app/models/document.py              # Data model
├── app/repositories/document_repository.py # Data access
├── app/services/document_service.py    # Business logic
├── app/agents/pdf_processor_agent.py   # Agent processing
├── app/api/documents.py                # HTTP endpoints
├── app/ui_components/document_*.py     # UI components
└── tests/*/test_document_*.py          # All test types
```

### Agent Architecture Navigation
Agent system organized by functionality:

```
Agent System Structure:
├── app/agents/{agent_name}_agent.py    # Core agent implementation
├── app/tools/{domain}_tools.py         # Domain-specific tools
├── app/plugins/{agent_name}_plugin.py  # Plugin extensions
├── app/config/agents.yaml              # Configuration
└── tests/*/test_{agent_name}*.py       # Agent tests
```

### Configuration and Settings
```
Configuration Hierarchy:
├── .env.example                        # Environment template
├── app/config/                         # Application configuration
├── .bmad-core/core-config.yaml        # BMad configuration
├── pyproject.toml                      # Python project settings
├── .ruff.toml                          # Code quality settings
└── docker-compose.yml                  # Infrastructure settings
```

## Import Patterns and Module Organization

### Standard Import Hierarchy
```python
# System imports
import asyncio
from datetime import datetime
from typing import Optional, List, Dict

# Third-party imports
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import nicegui as ui

# Local imports - Core
from app.core.database import get_async_db
from app.core.auth import require_auth, get_current_user

# Local imports - Models and Repositories
from app.models.user import User
from app.repositories.user_repository import UserRepository

# Local imports - Services and Agents
from app.services.user_service import UserService
from app.agents.pdf_processor_agent import PDFProcessorAgent
```

### Module Dependency Rules
- **Upward Dependencies Only**: Lower layers don't import from higher layers
- **Core Independence**: Core modules have minimal external dependencies
- **Agent Isolation**: Agents only depend on tools and core infrastructure
- **UI Separation**: UI components only depend on services, never repositories

## File Naming and Organization Standards

### Python Module Naming
```
Naming Convention Examples:
├── user_service.py                     # Service classes
├── pdf_processor_agent.py              # Agent classes
├── document_repository.py              # Repository classes
├── auth_middleware.py                  # Middleware classes
└── security_validators.py              # Utility modules
```

### Configuration File Naming
```
Configuration Files:
├── .env.example                        # Environment template
├── agents.yaml                         # YAML configuration
├── pyproject.toml                      # TOML configuration
├── .ruff.toml                          # Tool configuration
└── docker-compose.yml                  # Infrastructure definition
```

### Documentation File Naming
```
Documentation Files:
├── tech-stack.md                       # Kebab-case for markdown
├── unified-project-structure.md        # Descriptive names
├── section-1-current-state.md         # Numbered sections
└── epic-1-infrastructure.md           # Categorized content
```

## Development Workflow Integration

### Local Development File Flow
```bash
Development Workflow:
1. Edit source files in app/
2. Run tests from tests/ directory
3. Check code quality with .ruff.toml
4. Update documentation in docs/
5. Commit with proper .gitignore
```

### BMad Method Integration
```bash
BMad Workflow:
1. Story creation using .bmad-core/tasks/
2. Template application from .bmad-core/templates/
3. Quality validation with .bmad-core/checklists/
4. Documentation generation in docs/stories/
```

### Deployment File Usage
```bash
Deployment Flow:
1. Container build using Dockerfile
2. Service orchestration with docker-compose.yml
3. Database migration via alembic/
4. Environment configuration from .env files
5. Health monitoring through health endpoints
```

This source tree structure ensures clear separation of concerns, supports autonomous agent architecture, enables efficient development workflows, and maintains high code quality through comprehensive testing and documentation.