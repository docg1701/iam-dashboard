# IAM Dashboard - Development Guide

SaaS platform for autonomous legal agents with document processing, questionnaire generation, and user management capabilities.

## Tech Stack & Architecture

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL with pgvector
- **Frontend**: NiceGUI (web-based Python UI framework)
- **Async Processing**: Agno autonomous agents with plugin system
- **AI/ML**: Google Gemini API, LlamaIndex for document processing
- **Container**: Docker with docker-compose
- **Authentication**: JWT + 2FA (TOTP)
- **Document Processing**: PyMuPDF, PyTesseract, OpenCV, Pillow

## Project Structure

```
app/
├── main.py                    # FastAPI app entry point
├── containers.py             # Dependency injection setup
├── core/                     # Core infrastructure
│   ├── auth.py              # Authentication & JWT handling
│   └── database.py          # Database configuration
├── models/                   # SQLAlchemy models
├── repositories/            # Data access layer
├── services/               # Business logic layer
├── agents/                 # Agno autonomous agents
├── tools/                  # Agent tools and utilities
├── plugins/                # Agent plugins
├── api/                    # FastAPI endpoints
├── ui_components/          # NiceGUI components
└── utils/                  # Utility functions

docs/                       # Comprehensive project documentation
├── architecture/           # Architecture decisions & design
├── prd/                   # Product requirements
└── reference/             # Technical references
```

## Development Environment

### Package Management
Uses UV for fast Python package management:

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Add dev dependency  
uv add --dev package-name

# Run commands in environment
uv run python -m app.main
uv run pytest
```

### Development Commands

```bash
# Run application
uv run python -m app.main

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Linting & formatting
uv run ruff check .
uv run ruff format .
uv run ruff check --fix .

# Type checking
uv run mypy app/

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

### Docker Environment

```bash
# Start full stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Code Standards & Conventions

### Python Style
- **Line length**: 88 characters (Black standard)
- **Type hints**: Required for all functions and class attributes
- **Formatting**: Use `ruff format` (replaces Black)
- **Linting**: Ruff with strict configuration
- **Docstrings**: Google-style for public functions and classes

### Architecture Patterns
- **Dependency Injection**: Uses `dependency-injector` for IoC
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic separation
- **Vertical Slice**: Features organized by business capability

### File & Function Limits
- **Files**: Maximum 500 lines
- **Functions**: Maximum 50 lines, single responsibility
- **Classes**: Maximum 100 lines

### Database Standards
- **Primary Keys**: Entity-specific (e.g., `user_id`, `client_id`)
- **Foreign Keys**: `{referenced_entity}_id`
- **Timestamps**: `{action}_at` (e.g., `created_at`, `updated_at`)
- **Booleans**: `is_{state}` (e.g., `is_active`)

## Testing Strategy

### Test Organization
- **Unit tests**: `tests/unit/` - Individual components, agents, and tools
- **Integration tests**: `tests/integration/` - Agent workflows and API endpoints
- **E2E tests**: `tests/e2e/` - Full user workflows
- **Performance tests**: `tests/performance/` - Agent benchmarking and load testing

### Testing Requirements
- **Minimum 80% code coverage**
- **Co-locate tests** with code being tested
- **Use pytest fixtures** for setup (see `conftest.py`)
- **Mock external dependencies** (APIs, databases in unit tests)

### Test Commands
```bash
# All tests
uv run pytest

# Specific test types
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest -m "not slow"

# Coverage report
uv run pytest --cov=app --cov-report=html
```

## Security Best Practices

- **Input Validation**: All user inputs validated at API boundaries
- **Authentication**: JWT tokens with proper expiration
- **2FA**: TOTP implementation for enhanced security
- **SQL Injection**: Prevented via SQLAlchemy ORM
- **Environment Variables**: Never commit secrets, use `.env` files
- **Rate Limiting**: Implemented on public-facing endpoints

## AI & Document Processing

### LlamaIndex Integration
- **Vector Store**: PostgreSQL with pgvector extension
- **Embeddings**: Google Gemini embeddings
- **Document Types**: PDF, images with OCR support
- **Processing Pipeline**: Async via Celery workers

### Gemini API Usage
- **Document Analysis**: Content extraction and summarization
- **Questionnaire Generation**: AI-powered legal questionnaires
- **Embeddings**: Vector representations for semantic search

## Migration Status: Agno Integration

**Current State**: ✅ **COMPLETED** - Autonomous agents using Agno framework
**Previous State**: Traditional Celery workers (removed)

The system has successfully completed migration from Celery-based async processing to autonomous agent architecture. All legacy components have been removed and comprehensive testing has been implemented. See `docs/architecture/` for technical details.

## Common Workflows

### Adding New Feature
1. Create feature branch: `git checkout -b feature/feature-name`
2. Implement in service layer first
3. Add repository methods if needed
4. Create API endpoints
5. Add UI components
6. Write comprehensive tests
7. Update documentation
8. Submit PR with tests passing

### Database Changes
1. Modify SQLAlchemy models
2. Generate migration: `uv run alembic revision --autogenerate -m "description"`
3. Review generated migration
4. Apply: `uv run alembic upgrade head`
5. Update repository layer if needed

### Debugging Tips
- **Logs**: Check `app.log` and `celery.log`
- **Database**: Use pgAdmin or direct psql connection
- **Redis**: Use redis-cli for queue inspection
- **Coverage**: Check `htmlcov/index.html` after test runs

## Key Dependencies

- **FastAPI**: Modern Python web framework
- **SQLAlchemy 2.0**: ORM with async support
- **NiceGUI**: Python-based web UI framework
- **Celery**: Distributed task queue (being phased out)
- **LlamaIndex**: Document processing and RAG
- **Dependency Injector**: IoC container
- **Agno**: Autonomous agent framework (integration in progress)

## Environment Variables

Required environment variables (use `.env` file):

```bash
DATABASE_URL=postgresql://user:pass@localhost/iam_dashboard
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
```

## Support & Documentation

- **Architecture**: See `docs/architecture/`
- **API Documentation**: Available at `/docs` when running
- **Technical References**: `docs/reference/`
- **Migration Guide**: `docs/prd/epic-1-direct-migration-to-autonomous-agent-architecture.md`

---

**Last Updated**: January 2025  
**Python Version**: 3.12+  
**Development Status**: Active (Agent Migration Phase)