# GEMINI.md - Multi-Agent IAM Dashboard Development Guide

This file provides comprehensive guidance to Gemini when working on this fullstack multi-agent IAM Dashboard project. The system is built as a **Custom Implementation Service** delivering **dedicated VPS instances** with **independent agents** communicating through a shared database.

## 🚫 CRITICAL RESTRICTIONS

### Directory Access
- **The `.secret-vault` directory is OFF-LIMITS** to Gemini.
- **NEVER read, list, or modify** files in `.secret-vault/`.
- This restriction is permanent and non-negotiable.

### Language Requirements
- **ALL code, comments, documentation, and technical content MUST be in native English**.
- **ALL variable names, function names, class names MUST be in English**.
- **ALL commit messages, pull request descriptions, and technical discussions MUST be in English**.
- **ALL API endpoints, database schemas, and system logs MUST be in English**.
- **User Interface (UI) content MUST be in Portuguese (Brazil)** for ease of use.
- **Only user-facing labels, messages, and interface text should be in Portuguese**.

## 🛠️ Available Tools & Workflow

### Documentation & Code Search
**ALWAYS use `google_web_search`, `resolve_library_id`, and `get_library_docs`** for searching documentation, code examples, and library information.

#### When to Use
- **Before implementing any new feature**: Search for examples and patterns.
- **When learning a new library**: Get up-to-date documentation and examples.
- **For code snippets**: Find proven implementations and best practices.
- **API references**: Get current API documentation and usage patterns.
- **Framework guides**: Access latest framework documentation and tutorials.

#### Tool Usage Pattern
```python
# 1. First, resolve the library ID if you don't know the exact one.
print(default_api.resolve_library_id(libraryName="next.js"))

# 2. Then, get specific documentation using the resolved ID.
# Example output from resolve_library_id might be "/vercel/next.js"
print(default_api.get_library_docs(context7CompatibleLibraryID="/vercel/next.js", topic="server components"))

# 3. For general web searches, use google_web_search.
print(default_api.google_web_search(query="FastAPI authentication best practices"))
```

#### Integration Workflow
1.  **Before coding**: Always search for relevant documentation and examples.
2.  **During implementation**: Reference the fetched documentation for API usage and patterns.
3.  **When debugging**: Use web search to find known issues and solutions.

### End-to-End Testing
This environment does not support direct, interactive browser control. Therefore, the E2E testing workflow is as follows:
1.  **Write Test Files**: Create Playwright test files in TypeScript (`.spec.ts`).
2.  **Execute via Shell**: Use `run_shell_command` to execute the tests using the project's test runner (e.g., `npm run test:e2e`).
3.  **Analyze Output**: Review the `stdout` and `stderr` from the command's output to determine success or failure.

#### Example E2E Test File (`/frontend/tests/e2e/example.spec.ts`)
```typescript
import { test, expect } from '@playwright/test';

test.describe('Agent 1 - Client Management', () => {
  test('should create new client and verify in Agent 2', async ({ page }) => {
    // Navigate to Agent 1
    await page.goto('http://localhost:3000/agent1');
    
    // Fill client form
    await page.locator('input[name="clientName"]').fill('John Doe');
    await page.locator('input[name="ssn"]').fill('12345678901');
    await page.locator('input[name="birthDate"]').fill('1990-01-01');
    
    // Submit form
    await page.locator('button[type="submit"]').click();
    
    // Verify success message or navigation
    await expect(page.locator('text=Client created successfully')).toBeVisible();
    
    // Verify client appears in Agent 2
    await page.goto('http://localhost:3000/agent2');
    await expect(page.locator('text=John Doe')).toBeVisible();
  });
});
```

#### E2E Execution Command
```python
# I will first write the test file above using the write_file tool.
# Then, I will execute the tests with this command.
print(default_api.run_shell_command(command="npm run test:e2e", directory="frontend"))
```

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
- [ ] **Custom Branding**: 
  - [ ] Logo and favicon upload and integration
  - [ ] Complete color scheme customization
  - [ ] Typography selection and application
  - [ ] Real-time branding preview and deployment
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
- **Dependency Inversion**: High-level modules should not depend on low-level modules. Both should depend on abstractions.
- **Open/Closed Principle**: Software entities should be open for extension but closed for modification.
- **Vertical Slice Architecture**: Organize by features, not layers.
- **Component-First**: Build with reusable, composable components with single responsibility.
- **Fail Fast**: Validate inputs early, throw errors immediately when issues occur.

## 🏗️ Project Architecture Overview

### Multi-Agent System Structure
This is a **Custom Implementation Service** where each client receives a dedicated VPS instance with complete customization and managed deployment. The system follows a **Core + Independent Agents** architecture:

#### Core System
- **Frontend**: Next.js 15 + React 19 + TypeScript + shadcn/ui
- **Backend**: FastAPI + SQLModel + PostgreSQL
- **Authentication**: OAuth2 + JWT + 2FA
- **Deployment**: Automated via Terraform + Ansible + Docker Compose on Ubuntu Server VPS

#### Agent Communication Model
- **Shared Database**: All agents communicate through PostgreSQL tables.
- **Read-Only Access**: Agents can read from other agents' tables but never modify them.
- **Own Tables**: Each agent maintains its own tables for generated data.
- **Independence**: Each agent functions completely independently.
- **Hierarchical Dependencies**: Explicit dependency hierarchy between agents.

### Agent Examples
1. **Agent 1 (Client Management)**: CRUD operations for client data (name, SSN, birthdate).
2. **Agent 2 (PDF Processing)**: RAG processing with pgvector, references client data.
3. **Agent 3 (Reports & Analysis)**: Structured reports using data from Agents 1 & 2.
4. **Agent 4 (Audio Recording)**: Consultation recordings with transcription and analysis.

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
│   │   ├── hooks/           # Shared custom hooks
│   │   └── types/           # TypeScript type definitions
│   ├── package.json
│   └── tsconfig.json
├── backend/                  # FastAPI application
│   ├── src/
│   │   ├── core/            # Core system modules
│   │   ├── agents/          # Agent implementations (vertical slices)
│   │   │   ├── agent1/      # Client management
│   │   │   ├── agent2/      # PDF processing (RAG)
│   │   │   └── ...
│   │   ├── shared/          # Shared utilities
│   │   ├── tests/           # Test files
│   │   └── main.py          # FastAPI application entry
│   ├── pyproject.toml       # UV dependency management
│   ├── alembic/             # Database migrations
│   └── Dockerfile
├── docker-compose.yml
├── Caddyfile
├── .env.example
├── README.md
└── GEMINI.md                 # This file
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

### Infrastructure & Deployment
- **Docker + Docker Compose**: Containerization
- **Terraform**: Infrastructure as code for VPS provisioning
- **Ansible**: Configuration management and deployment automation
- **Caddy**: Reverse proxy with automatic HTTPS
- **Ubuntu Server 24.x**: Host operating system

## 🎨 Custom Branding & Theming System

The system implements a complete **custom branding solution** for each client using shadcn/ui's CSS variable system.

#### Customizable Elements
- **Colors**: Primary, secondary, accent, background, foreground.
- **Typography**: Font families from a pre-approved list.
- **Branding**: Logos, favicons, company names.
- **Layout**: Border radius, spacing (within limits).

#### Non-Customizable Elements (Security)
- Main navigation structure, agent workflow processes, security components (2FA, login), critical form layouts.

### 100% Responsive Design
- **Mobile-first approach** with Tailwind CSS.
- **Adaptive components** for phone, tablet, and desktop.

## 🔐 Security Requirements

### Authentication & Authorization
- **2FA Authentication**: TOTP-based two-factor authentication.
- **JWT Tokens**: Secure session management.
- **OAuth2**: Standard authentication protocol.
- **Role-based access**: sysadmin, admin, user levels.

### Input Validation
- **Zod validation**: ALL external data must be validated on the frontend.
- **Pydantic/SQLModel validation**: ALL data from requests must be validated on the backend.
- **Fail fast**: Validate at system boundaries.
- **Sanitization**: Prevent XSS and injection attacks.

### Data Protection
- **Single-tenant isolation**: Each client has their own VPS.
- **Database isolation**: Row-level security where applicable.
- **Encryption**: Sensitive data encrypted at rest.
- **Audit logging**: Complete access and modification logs.

## 🧪 Testing Strategy

### Required Testing Standards
- **Minimum 80% code coverage** - NO EXCEPTIONS.
- **Test-Driven Development (TDD)** when possible.
- **Co-located tests** with components.
- **Integration tests** for agent interactions.
- **End-to-end tests** for critical user workflows.

### Testing Tools
- **pytest**: Backend testing.
- **Vitest**: Frontend unit/integration testing.
- **Playwright**: Frontend E2E testing.
- **React Testing Library**: Component testing.

## 🗄️ Database Design

### Naming Conventions
- **Primary Keys**: `{entity}_id` (e.g., `client_id`, `pdf_id`).
- **Foreign Keys**: `{referenced_entity}_id`.
- **Timestamps**: `{action}_at` (e.g., `created_at`, `updated_at`).
- **Booleans**: `is_{state}` (e.g., `is_active`, `is_processed`).

### Agent Table Structure
Each agent maintains its own tables with foreign key references to other agents' tables.
```sql
-- Agent 1: Client Management
CREATE TABLE agent1_clients (
    client_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ssn VARCHAR(11) UNIQUE NOT NULL,
    -- ...
);

-- Agent 2: PDF Processing
CREATE TABLE agent2_documents (
    document_id UUID PRIMARY KEY,
    client_id UUID REFERENCES agent1_clients(client_id),
    -- ...
);
```
### Data Sharing Rules
1.  **Read-Only Access**: Agents can read from other agents' tables.
2.  **No Modifications**: Agents CANNOT modify other agents' tables.
3.  **Own Tables Only**: Agents only write to their own tables.

## 🤖 Agent Development with Agno

The project uses the `Agno` framework. Agent implementation should follow the established patterns in the codebase, using structured outputs and communicating via the shared database.

## 💻 Development Commands

### Backend Development (UV)
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

# Code quality & Testing
uv run ruff format .
uv run ruff check .
uv run mypy src/
uv run pytest
```

### Frontend Development (npm)
```bash
# Dependencies & Dev Server
cd frontend
npm install
npm run dev

# Type checking & Testing
npm run type-check
npm run test
npm run test:e2e
```

### Docker Development
```bash
# Build and run all services
docker compose up --build

# Run specific service
docker compose up backend

# View logs
docker compose logs -f backend

# Database shell
docker compose exec postgres psql -U postgres -d dashboard
```

## 🚀 Performance Guidelines

- **Backend**: Use `async/await`, proper database indexing, query optimization, and Redis caching.
- **Frontend**: Default to React Server Components, use Client Components only when necessary, use `next/image`, and monitor bundle size.

## 📝 Code Style & Quality

### Python Style (Backend)
- **PEP 8 compliance**: Use `ruff format`.
- **Line length**: Max 100 characters.
- **Type hints**: Required for all functions.
- **Docstrings**: Google-style for all public functions.
- **UV package management**: NEVER edit `pyproject.toml` directly, always use `uv add/remove`.
- **File limits**: Max 500 lines per file, functions under 50 lines.

### TypeScript Style (Frontend)
- **Strict mode**: Enable all strict TypeScript options.
- **No `any` type**: Use proper typing or `unknown`.
- **React 19 patterns**: Use modern React patterns and hooks.
- **JSDoc**: For all exported components.

## ⚠️ Critical Development Rules

### MUST DO
1.  **Follow KISS and YAGNI principles**.
2.  **Validate ALL external data** with Zod (frontend) and Pydantic (backend).
3.  **Write tests** to maintain **80%+ test coverage**.
4.  **Use TypeScript strictly** - no `any` types allowed.
5.  **Document all public APIs** with comprehensive JSDoc/docstrings.
6.  **Follow the agent independence principle**.
7.  **Implement proper error handling** with custom exceptions.
8.  **Use `async/await` patterns** for all I/O operations.
9.  **Use UV for Python package management**.
10. **Use `rg` (ripgrep)** instead of `grep` for searching files.
11. **Co-locate tests** with code.
12. **Implement fail-fast validation** at system boundaries.
13. **Follow vertical slice architecture**.

### NEVER DO
1.  **Never access the `.secret-vault` directory**.
2.  **Never modify other agents' database tables**.
3.  **Never ignore TypeScript errors** with `@ts-ignore`.
4.  **Never skip input validation**.
5.  **Never hardcode sensitive information**.
6.  **Never break the single-tenant isolation** model.
7.  **Never exceed file size limits** (500 lines max).
8.  **Never compromise on test coverage**.
9.  **Never use the `any` type** in TypeScript.
10. **Never commit without passing all quality checks**.

## 🔍 Development Workflow

### Git Strategy
- **Main branch**: Production-ready code.
- **Feature branches**: `feature/agent-name-functionality`.
- **Semantic commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.
- **Pull requests**: Required for all changes to main.

### Quality Gates
Before any merge to main, ensure all checks pass: tests (with coverage), type-checking, linting, security scans, and documentation updates.

---

**Last Updated**: August 2025
**Project**: Multi-Agent IAM Dashboard Custom Implementation Service
*This document is the single source of truth for Gemini's development guidelines. Keep it updated as the project evolves.*