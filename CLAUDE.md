# CLAUDE.md - Multi-Agent IAM Dashboard Development Guide

This file provides comprehensive guidance to Claude Code when working on this fullstack multi-agent IAM Dashboard project. The system is built on a **Single-Tenant SaaS architecture** with **independent agents** communicating through a shared database.

## 🚫 CRITICAL RESTRICTIONS

### Directory Access
- **The `.secret-vault` directory is OFF-LIMITS** to Claude Code
- **NEVER read, list, or modify** files in `.secret-vault/`
- This restriction is permanent and non-negotiable

### Language Requirements
- **ALL code, comments, documentation, and technical content MUST be in native English**
- **ALL variable names, function names, class names MUST be in English**
- **ALL commit messages, pull request descriptions, and technical discussions MUST be in English**
- **ALL API endpoints, database schemas, and system logs MUST be in English**
- **User Interface (UI) content MUST be in Portuguese (Brazil)** for ease of use
- **Only user-facing labels, messages, and interface text should be in Portuguese**

## 🛠️ MCP (Model Context Protocol) Tools

### MCP Context7 - Documentation & Code Search
**ALWAYS use MCP Context7** for searching documentation, code examples, and library information:

#### When to Use Context7
- **Before implementing any new feature**: Search for examples and patterns
- **When learning a new library**: Get up-to-date documentation and examples  
- **For code snippets**: Find proven implementations and best practices
- **API references**: Get current API documentation and usage patterns
- **Framework guides**: Access latest framework documentation and tutorials

#### Context7 Usage Pattern
```bash
# 1. First resolve the library ID
mcp__context7__resolve-library-id --libraryName="next.js"

# 2. Then get specific documentation  
mcp__context7__get-library-docs --context7CompatibleLibraryID="/vercel/next.js" --topic="server components"
```

#### Context7 Examples
```bash
# Get FastAPI documentation
mcp__context7__resolve-library-id --libraryName="fastapi"
mcp__context7__get-library-docs --context7CompatibleLibraryID="/tiangolo/fastapi" --topic="authentication"

# Get React 19 examples
mcp__context7__resolve-library-id --libraryName="react"
mcp__context7__get-library-docs --context7CompatibleLibraryID="/facebook/react" --topic="hooks"

# Get shadcn/ui components
mcp__context7__resolve-library-id --libraryName="shadcn/ui"
mcp__context7__get-library-docs --context7CompatibleLibraryID="/shadcn/ui" --topic="theming"
```

#### Context7 Integration Workflow
1. **Before coding**: Always search Context7 for relevant documentation
2. **During implementation**: Reference Context7 for API usage and patterns
3. **When debugging**: Check Context7 for known issues and solutions
4. **For testing**: Find testing examples and patterns in documentation

### MCP Playwright - End-to-End Testing
**ALWAYS use MCP Playwright** for comprehensive E2E testing of the dashboard:

#### When to Use Playwright
- **User journey testing**: Complete workflows across multiple agents
- **Cross-browser testing**: Ensure compatibility across different browsers
- **Responsive testing**: Validate UI behavior on different screen sizes
- **Authentication flows**: Test login, 2FA, and role-based access
- **Agent interactions**: Test data flow between different agents
- **White-label theming**: Validate theme applications and customizations

#### Playwright Testing Strategy
```javascript
// Example E2E test structure
describe('Agent 1 - Client Management', () => {
  test('should create new client and verify in Agent 2', async () => {
    // Navigate to Agent 1
    await mcp__playwright__browser_navigate({ url: 'http://localhost:3000/agent1' });
    
    // Take snapshot of current state
    const snapshot = await mcp__playwright__browser_snapshot();
    
    // Fill client form
    await mcp__playwright__browser_type({
      element: 'Client Name Input',
      ref: 'input[name="clientName"]',
      text: 'John Doe'
    });
    
    // Submit form
    await mcp__playwright__browser_click({
      element: 'Submit Button',
      ref: 'button[type="submit"]'
    });
    
    // Verify client appears in Agent 2
    await mcp__playwright__browser_navigate({ url: 'http://localhost:3000/agent2' });
    
    // Take screenshot for verification
    await mcp__playwright__browser_take_screenshot({
      filename: 'client-created-verification.png'
    });
  });
});
```

#### Critical E2E Test Scenarios
1. **Authentication Flow**
   ```javascript
   // Test 2FA login process
   await mcp__playwright__browser_navigate({ url: 'http://localhost:3000/login' });
   await mcp__playwright__browser_type({
     element: 'Email Input',
     ref: 'input[name="email"]',
     text: 'admin@example.com'
   });
   // Continue with 2FA flow...
   ```

2. **Agent Data Flow**
   ```javascript
   // Test data consistency across agents
   // 1. Create client in Agent 1
   // 2. Process PDF in Agent 2 for that client
   // 3. Generate report in Agent 3
   // 4. Verify all data is consistent
   ```

3. **Responsive Design**
   ```javascript
   // Test mobile responsiveness
   await mcp__playwright__browser_resize({ width: 375, height: 667 });
   await mcp__playwright__browser_take_screenshot({
     filename: 'mobile-dashboard.png'
   });
   ```

4. **Theme Customization**
   ```javascript
   // Test white-label theming
   await mcp__playwright__browser_navigate({ url: 'http://localhost:3000/admin/themes' });
   // Change primary color
   // Apply theme
   // Verify changes across all pages
   ```

#### Playwright Integration Commands
```bash
# Navigate and interact
mcp__playwright__browser_navigate --url="http://localhost:3000"
mcp__playwright__browser_click --element="Login Button" --ref="button.login"
mcp__playwright__browser_type --element="Username" --ref="input[name='username']" --text="admin"

# Validation and debugging
mcp__playwright__browser_snapshot  # Get accessible page structure
mcp__playwright__browser_take_screenshot --filename="test-result.png"
mcp__playwright__browser_console_messages  # Check for JavaScript errors

# Advanced interactions
mcp__playwright__browser_drag --startElement="File" --startRef=".file" --endElement="Upload Area" --endRef=".dropzone"
mcp__playwright__browser_wait_for --text="Upload Complete"
```

#### E2E Testing Best Practices
1. **Always take snapshots** before interactions to understand page state
2. **Use descriptive element names** for better test readability
3. **Verify state changes** after each major action
4. **Test error scenarios** not just happy paths
5. **Include accessibility testing** in E2E flows
6. **Test theme consistency** across all agents
7. **Validate responsive behavior** on different screen sizes

#### Required E2E Test Coverage
- [ ] **Login Flow**: Email/password + 2FA authentication
- [ ] **Role-based Access**: sysadmin, admin, user permissions
- [ ] **Agent 1 (Client Management)**: 
  - [ ] Create client with name, SSN, birthdate validation
  - [ ] Edit and update existing client information
  - [ ] Delete client and handle cascading effects
  - [ ] Bulk operations (CSV export, multiple selection)
  - [ ] SSN validation and duplicate prevention
- [ ] **Agent 2 (PDF Processing)**: 
  - [ ] Upload PDF files with validation
  - [ ] Process PDFs and create vector embeddings
  - [ ] Search and retrieve document chunks
  - [ ] Associate PDFs with specific clients
- [ ] **Agent 3 (Reports & Analysis)**: 
  - [ ] Generate reports from client and PDF data
  - [ ] Export reports in different formats
  - [ ] Customizable report templates
- [ ] **Agent 4 (Audio Recording)**: 
  - [ ] Record audio consultations
  - [ ] Transcribe audio to text
  - [ ] Associate recordings with clients
  - [ ] LLM analysis of transcriptions
- [ ] **Cross-Agent Data Flow**: Data consistency between agents
- [ ] **Theme Customization**: 
  - [ ] Logo and favicon upload
  - [ ] Color scheme customization
  - [ ] Typography selection
  - [ ] Real-time theme preview
- [ ] **Responsive Design**: Mobile, tablet, desktop layouts
- [ ] **Error Handling**: Network errors, validation errors, system errors
- [ ] **Configuration Management**: 
  - [ ] User role management
  - [ ] System configuration files
  - [ ] Agent card configuration

## Core Development Philosophy

### KISS (Keep It Simple, Stupid)
Simplicity should be a key goal in design. Choose straightforward solutions over complex ones whenever possible. Simple solutions are easier to understand, maintain, and debug.

### YAGNI (You Aren't Gonna Need It)
Avoid building functionality on speculation. Implement features only when they are needed, not when you anticipate they might be useful in the future.

### Design Principles
- **Dependency Inversion**: High-level modules should not depend on low-level modules. Both should depend on abstractions
- **Open/Closed Principle**: Software entities should be open for extension but closed for modification
- **Vertical Slice Architecture**: Organize by features, not layers
- **Component-First**: Build with reusable, composable components with single responsibility
- **Fail Fast**: Validate inputs early, throw errors immediately when issues occur

## 🏗️ Project Architecture Overview

### Multi-Agent System Structure
This is a **Single-Tenant SaaS Dashboard** where each client gets their own VPS instance. The system follows a **Core + Independent Agents** architecture:

#### Core System
- **Frontend**: Next.js 15 + React 19 + TypeScript + shadcn/ui
- **Backend**: FastAPI + SQLModel + PostgreSQL
- **Authentication**: OAuth2 + JWT + 2FA
- **Deployment**: Docker Compose on Ubuntu Server VPS

#### Agent Communication Model
- **Shared Database**: All agents communicate through PostgreSQL tables
- **Read-Only Access**: Agents can read from other agents' tables but never modify them
- **Own Tables**: Each agent maintains its own tables for generated data
- **Independence**: Each agent functions completely independently
- **Hierarchical Dependencies**: Explicit dependency hierarchy between agents

### Agent Examples
1. **Agent 1 (Client Management)**: CRUD operations for client data (name, SSN, birthdate)
2. **Agent 2 (PDF Processing)**: RAG processing with pgvector, references client data
3. **Agent 3 (Reports & Analysis)**: Structured reports using data from Agents 1 & 2
4. **Agent 4 (Audio Recording)**: Consultation recordings with transcription and analysis

## 📂 Project Structure

```
/
├── frontend/                 # Next.js 15 application
│   ├── src/
│   │   ├── app/             # App Router (Next.js 15)
│   │   │   ├── (auth)/      # Authentication route group
│   │   │   ├── (dashboard)/ # Main dashboard routes
│   │   │   ├── admin/       # Admin interface routes
│   │   │   ├── agents/      # Agent-specific pages
│   │   │   ├── globals.css  # Global styles
│   │   │   ├── layout.tsx   # Root layout
│   │   │   └── page.tsx     # Home page
│   │   ├── components/      # Shared UI components
│   │   │   ├── ui/          # shadcn/ui base components
│   │   │   ├── common/      # App-specific shared components
│   │   │   └── forms/       # Reusable form components
│   │   ├── features/        # Feature-based modules
│   │   │   ├── auth/        # Authentication features
│   │   │   ├── dashboard/   # Dashboard features
│   │   │   ├── agents/      # Agent-specific features
│   │   │   └── themes/      # White-label theming
│   │   ├── lib/             # Utilities & configurations
│   │   │   ├── utils.ts     # Utility functions
│   │   │   ├── auth.ts      # Authentication config
│   │   │   ├── api.ts       # API client configuration
│   │   │   └── env.ts       # Environment validation
│   │   ├── hooks/           # Shared custom hooks
│   │   ├── styles/          # Additional styling files
│   │   └── types/           # TypeScript type definitions
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── tsconfig.json
├── backend/                 # FastAPI application
│   ├── src/
│   │   ├── core/           # Core system modules
│   │   │   ├── database.py  # Database connection
│   │   │   ├── auth.py      # Authentication logic
│   │   │   ├── config.py    # Application configuration
│   │   │   └── exceptions.py # Custom exceptions
│   │   ├── agents/         # Agent implementations
│   │   │   ├── agent1/     # Client management
│   │   │   │   ├── models.py # SQLModel definitions
│   │   │   │   ├── routes.py # FastAPI routes
│   │   │   │   ├── services.py # Business logic
│   │   │   │   └── schemas.py # Pydantic schemas
│   │   │   ├── agent2/     # PDF processing (RAG)
│   │   │   ├── agent3/     # Reports & analysis
│   │   │   └── agent4/     # Audio recording
│   │   ├── shared/         # Shared utilities
│   │   │   ├── models.py   # Base models
│   │   │   ├── utils.py    # Utility functions
│   │   │   └── validators.py # Input validators
│   │   ├── api/            # API route aggregation
│   │   │   └── v1/         # API version 1
│   │   ├── tests/          # Test files
│   │   └── main.py         # FastAPI application entry
│   ├── pyproject.toml      # UV dependency management
│   ├── alembic/            # Database migrations
│   │   ├── versions/       # Migration files
│   │   ├── env.py         # Alembic configuration
│   │   └── alembic.ini    # Alembic settings
│   └── Dockerfile         # Backend container
├── docker-compose.yml      # Container orchestration
├── Caddyfile              # Reverse proxy configuration
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore patterns
├── README.md              # Project documentation
└── CLAUDE.md              # This file
```

## 🛠️ Technology Stack

### Backend Stack
- **FastAPI**: Modern Python web framework
- **SQLModel**: Database ORM combining SQLAlchemy + Pydantic
- **PostgreSQL**: Primary database with pgvector extension
- **Agno**: Multi-agent framework (https://github.com/agno-agi/agno)
- **Celery + Redis**: Asynchronous task processing
- **Alembic**: Database migrations
- **pytest**: Testing framework
- **Gunicorn + Uvicorn**: ASGI server

### Frontend Stack
- **Next.js 15**: React framework with App Router
- **React 19**: UI library with new features
- **TypeScript**: Type-safe JavaScript
- **shadcn/ui**: Component library for theming
- **Tailwind CSS**: Utility-first CSS framework
- **Zod**: Runtime type validation
- **TanStack Query**: Server state management
- **React Hook Form**: Form handling with validation
- **@hookform/resolvers**: Form validation resolvers

### Infrastructure
- **Docker + Docker Compose**: Containerization
- **Caddy**: Reverse proxy with automatic HTTPS
- **Ubuntu Server 24.x**: Host operating system

## 🎨 White-Label Theming System

### Theme Architecture
The system implements a complete **white-label solution** using shadcn/ui's CSS variable system:

#### CSS Variables Structure
```css
:root {
  /* Primary Colors */
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  
  /* Secondary Colors */
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  
  /* Complete color system for theming */
  --background: 0 0% 100%;
  --foreground: 222.2 47.4% 11.2%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 47.4% 11.2%;
  
  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  /* Layout */
  --radius: 0.5rem;
}
```

#### Customizable Elements
- **Colors**: Primary, secondary, accent, background, foreground
- **Typography**: Font families from pre-approved list
- **Branding**: Logos, favicons, company names
- **Layout**: Border radius, spacing (within limits)

#### Non-Customizable Elements (Security)
- Main navigation structure
- Agent workflow processes
- Security components (2FA, login)
- Critical form layouts

### 100% Responsive Design
- **Mobile-first approach** with Tailwind CSS
- **Adaptive components** for phone, tablet, desktop
- **Consistent behavior** across all screen sizes
- **Touch-friendly interfaces** with proper tap targets

## 🔐 Security Requirements

### Authentication & Authorization
- **2FA Authentication**: TOTP-based two-factor authentication
- **JWT Tokens**: Secure session management
- **OAuth2**: Standard authentication protocol
- **Role-based access**: sysadmin, admin, user levels

### Input Validation
- **Zod validation**: ALL external data must be validated
- **Fail fast**: Validate at system boundaries
- **Sanitization**: Prevent XSS and injection attacks
- **File upload security**: Type, size, and content validation

### Data Protection
- **Single-tenant isolation**: Each client has own VPS
- **Database isolation**: Row-level security where applicable
- **Encryption**: Sensitive data encrypted at rest
- **Audit logging**: Complete access and modification logs

## 🧪 Testing Strategy

### Required Testing Standards
- **Minimum 80% code coverage** - NO EXCEPTIONS
- **Test-Driven Development (TDD)** when possible
- **Co-located tests** with components
- **Integration tests** for agent interactions
- **End-to-end tests** for critical user workflows

### Testing Tools
- **pytest**: Backend testing
- **Vitest**: Frontend testing
- **React Testing Library**: Component testing
- **Factory patterns**: Test data generation

### Example Test Structure
```python
# Backend test example
def test_client_agent_creates_client():
    """Test that Agent1 can create a new client with valid data."""
    client_data = ClientCreateFactory()
    result = agent1.create_client(client_data)
    
    assert result.success is True
    assert result.client.name == client_data.name
    assert validate_ssn(result.client.ssn) is True
```

## 🗄️ Database Design

### Naming Conventions
- **Primary Keys**: `{entity}_id` (e.g., `client_id`, `pdf_id`)
- **Foreign Keys**: `{referenced_entity}_id`
- **Timestamps**: `{action}_at` (e.g., `created_at`, `updated_at`)
- **Booleans**: `is_{state}` (e.g., `is_active`, `is_processed`)
- **Counts**: `{entity}_count`

### Agent Table Structure
Each agent maintains its own tables with references to other agents:

```sql
-- Agent 1: Client Management
CREATE TABLE agent1_clients (
    client_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ssn VARCHAR(11) UNIQUE NOT NULL,
    birth_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Agent 2: PDF Processing
CREATE TABLE agent2_documents (
    document_id UUID PRIMARY KEY,
    client_id UUID REFERENCES agent1_clients(client_id),
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    vector_chunks JSONB,
    is_processed BOOLEAN DEFAULT FALSE
);
```

### Data Sharing Rules
1. **Read-Only Access**: Agents can read from other agents' tables
2. **No Modifications**: Agents CANNOT modify other agents' tables
3. **Own Tables Only**: Agents only write to their own tables
4. **Reference Integrity**: Use foreign keys to maintain relationships

## 🤖 Agent Development with Agno

### Agent Implementation Pattern
```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.postgresql import PostgresStorage

def create_client_agent():
    """Create Agent1 for client management."""
    return Agent(
        name="Client Management Agent",
        role="Register and manage client information",
        model=OpenAIChat(id="gpt-4o"),
        storage=PostgresStorage(
            table_name="agent1_clients",
            db_url=settings.database_url
        ),
        instructions=[
            "Validate SSN format before registration",
            "Check for duplicate SSN entries",
            "Maintain complete audit trail of changes"
        ],
        structured_outputs=True
    )
```

### Agent Communication
```python
# Agents communicate through database queries
async def get_client_for_pdf_processing(client_id: UUID):
    """Agent2 reads client data from Agent1's table."""
    query = "SELECT * FROM agent1_clients WHERE client_id = $1"
    return await database.fetch_one(query, client_id)
```

### Agent Independence
- Each agent functions without others (except core dependencies)
- Graceful degradation when dependencies are unavailable
- Clear dependency hierarchy documentation

## 💻 Development Commands

### Backend Development (UV Package Manager)
```bash
# Setup UV environment
cd backend
uv venv
source .venv/bin/activate  # Linux/Mac
uv sync

# Add dependencies (NEVER edit pyproject.toml directly)
uv add fastapi sqlmodel alembic
uv add --dev pytest pytest-cov pytest-asyncio

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"

# Run development server
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Code quality
uv run ruff format .
uv run ruff check .
uv run mypy src/

# Testing
uv run pytest
uv run pytest --cov=src --cov-report=html
```

### Frontend Development
```bash
# Dependencies
cd frontend
npm install

# Development server
npm run dev

# Type checking
npm run type-check

# Testing
npm run test
npm run test:coverage

# Build
npm run build
```

### Docker Development
```bash
# Build and run all services
docker-compose up --build

# Run specific service
docker-compose up backend

# View logs
docker-compose logs -f backend

# Database shell
docker-compose exec postgres psql -U postgres -d dashboard
```

## 🚀 Performance Guidelines

### Backend Optimization
- **Async/await**: Use asyncio for I/O operations
- **Database indexing**: Proper indexes on foreign keys and search fields
- **Query optimization**: Use SQLModel's query optimization features
- **Caching**: Redis for frequently accessed data
- **Connection pooling**: Optimize database connections

### Frontend Optimization
- **Server Components**: Use React Server Components by default
- **Client Components**: Only when interactivity is needed
- **Dynamic imports**: Code splitting for large components
- **Image optimization**: next/image for all images
- **Bundle analysis**: Regular bundle size monitoring

## 📝 Code Style & Quality

### Python Style (Backend)
- **PEP 8 compliance**: Use `ruff format` (faster than black)
- **Line length**: Maximum 100 characters (configured in pyproject.toml)
- **Type hints**: Required for all functions and variables
- **Docstrings**: Google-style docstrings for all public functions
- **Error handling**: Explicit exception handling with custom exceptions
- **Logging**: Structured logging with proper levels
- **UV package management**: NEVER edit pyproject.toml directly, always use `uv add/remove`
- **File limits**: Maximum 500 lines per file, functions under 50 lines

### TypeScript Style (Frontend)
- **Strict mode**: Enable all strict TypeScript options
- **No `any` type**: Use proper typing or `unknown`
- **React 19 patterns**: Use modern React patterns and hooks
- **Component documentation**: JSDoc for all exported components
- **Zod validation**: Validate all external data

### File Organization
- **Maximum 500 lines per file**: Split larger files into modules
- **Co-located tests**: Tests in `__tests__` folders next to code
- **Clear naming**: Descriptive file and function names
- **Single responsibility**: Each file should have one clear purpose

## 🔧 Configuration Management

### Environment Variables
```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost:5432/dashboard
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=IAM Dashboard
```

### Docker Configuration
All services configured in `docker-compose.yml`:
- **Backend**: FastAPI application
- **Frontend**: Next.js application
- **Database**: PostgreSQL with pgvector
- **Cache**: Redis
- **Proxy**: Caddy reverse proxy
- **Queue**: Celery worker

## 📊 Monitoring & Observability

### Logging
- **Structured logging**: JSON format for all logs
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Request tracking**: Unique request IDs for tracing
- **Agent activity**: Log all agent interactions and decisions

### Health Checks
- **Database connectivity**: PostgreSQL health endpoint
- **Redis connectivity**: Cache service health
- **Agent status**: Individual agent health checks
- **External APIs**: Third-party service availability

## ⚠️ Critical Development Rules

### MUST DO
1. **Follow KISS and YAGNI principles** in all decisions
2. **Validate ALL external data** with Zod (frontend) and Pydantic (backend)
3. **Write tests BEFORE implementation** when possible (TDD approach)
4. **Maintain 80%+ test coverage** across all modules
5. **Use TypeScript strictly** - no `any` types allowed
6. **Document all public APIs** with comprehensive JSDoc/docstrings
7. **Follow the agent independence principle** - no tight coupling
8. **Implement proper error handling** with custom exceptions
9. **Use async/await patterns** for I/O operations
10. **Maintain responsive design** across all screen sizes
11. **Use UV for Python package management** - never edit pyproject.toml directly
12. **Use `rg` (ripgrep)** instead of grep/find commands
13. **Co-locate tests** with code in `__tests__` or `tests/` directories
14. **Implement fail-fast validation** at system boundaries
15. **Follow vertical slice architecture** organized by features

### NEVER DO
1. **Never access `.secret-vault` directory**
2. **Never modify other agents' database tables**
3. **Never ignore TypeScript errors** with `@ts-ignore`
4. **Never skip input validation** for external data
5. **Never hardcode sensitive information** in code
6. **Never break the single-tenant isolation** model
7. **Never exceed file size limits** (500 lines max)
8. **Never compromise on test coverage** requirements
9. **Never use `any` type** in TypeScript
10. **Never commit without passing all quality checks**

## 🔍 Development Workflow

### Git Strategy
- **Main branch**: Production-ready code
- **Feature branches**: `feature/agent-name-functionality`
- **Semantic commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- **Pull requests**: Required for all changes to main

### Quality Gates
Before any merge to main:
- [ ] All tests pass with 80%+ coverage
- [ ] TypeScript compiles without errors
- [ ] Code style checks pass (black, eslint)
- [ ] Security scans pass
- [ ] Performance benchmarks meet requirements
- [ ] Documentation is updated

---

**Last Updated**: Agosto 2025  
**Project**: Multi-Agent IAM Dashboard  
**Language**: 100% English (native)  
**Architecture**: Single-Tenant SaaS with Independent Agents

*This document is the single source of truth for development guidelines. Keep it updated as the project evolves and new patterns emerge.*