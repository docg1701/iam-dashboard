# CLAUDE.md - IAM Dashboard Development Guide

Essential guidance for Claude Code when working on this fullstack IAM Dashboard project.

## 🚫 CRITICAL RESTRICTIONS

### Directory Access
- **The `.secret-vault` directory is OFF-LIMITS** to Claude Code
- **NEVER read, list, or modify** files in `.secret-vault/`

### Language Requirements
- **ALL code, comments, documentation MUST be in English**
- **ALL variable names, function names, class names MUST be in English**
- **User Interface (UI) content MUST be in Portuguese (Brazil)**

### Backend Testing Directives
- **CRITICAL: Mock only external dependencies - NEVER mock internal business logic**
- **Golden Rule**: "Mock the boundaries, not the behavior"
- **NEVER mock**: PermissionService logic, authentication flows, database operations (in integration), business rules
- **ALWAYS mock**: External HTTP calls, SMTP servers, file I/O, third-party libraries, time/UUID generation

### Frontend Testing Directives
- **NEVER mock internal frontend code, components, hooks, or utilities**
- **ONLY mock external APIs** (fetch calls, third-party services, etc.)
- **Test actual behavior**, not implementation details

## 🛠️ MCP Tools

### Context7 - Documentation Search
**Always use** before implementing new features:

```bash
# 1. Resolve library ID
mcp__context7__resolve-library-id --libraryName="fastapi"
# 2. Get documentation
mcp__context7__get-library-docs --context7CompatibleLibraryID="/tiangolo/fastapi" --topic="authentication"
```

### Playwright - E2E Testing
**Essential commands**:

```bash
# Navigation and interaction
mcp__playwright__browser_navigate --url="http://localhost:3000"
mcp__playwright__browser_click --element="Login Button" --ref="button.login"
mcp__playwright__browser_type --element="Username" --ref="input[name='username']" --text="admin"

# Validation
mcp__playwright__browser_snapshot  # Get page structure
mcp__playwright__browser_take_screenshot --filename="test-result.png"
mcp__playwright__browser_console_messages  # Check errors
```

## 🚀 Essential Commands

### Development
```bash
# Setup and start
npm run setup  # Install all dependencies
npm run dev    # Start both frontend and backend

# Testing (CRITICAL: Use exact commands)
npm run test:coverage          # Frontend tests with coverage - EXACT command
npx vitest run --coverage      # Direct vitest coverage
uv run pytest --cov=src --cov-report=html  # Backend coverage

# Quality checks
npm run lint
npm run type-check
npm run build
```

### Backend (UV Package Manager)
```bash
cd apps/backend
uv sync                      # Sync dependencies
uv add fastapi              # Add dependencies (NEVER edit pyproject.toml)
uv run alembic upgrade head  # Database migrations
uv run pytest              # Run tests
```

## 📋 Development Philosophy

### Core Principles
- **KISS**: Keep it simple, choose straightforward solutions
- **YAGNI**: Implement only when needed, not anticipated
- **Fail Fast**: Validate inputs early, throw errors immediately
- **Component-First**: Reusable, single-responsibility components

## 🏗️ Tech Stack

- **Frontend**: Next.js 15 + React 19 + TypeScript + shadcn/ui
- **Backend**: FastAPI + SQLModel + PostgreSQL + Alembic
- **Testing**: pytest + Vitest + Playwright + React Testing Library
- **Package Management**: npm workspaces + UV (Python)

## ⚠️ CRITICAL DEVELOPMENT RULES

### MUST DO
1. **Follow KISS and YAGNI principles**
2. **Validate ALL external data** with Zod (frontend) and Pydantic (backend)
3. **Maintain 80%+ test coverage** - NO EXCEPTIONS
4. **Use TypeScript strictly** - no `any` types
5. **Use UV for Python packages** - NEVER edit pyproject.toml directly
6. **Co-locate tests** in `__tests__` folders
7. **CRITICAL: Frontend Test Commands** - Use EXACT commands:
   - ✅ `npm run test:coverage` (correct)
   - ✅ `npx vitest run --coverage` (correct)
   - ❌ NEVER use bash redirections with test commands (`2>&1`, etc.)

### NEVER DO
1. **Never access `.secret-vault` directory**
2. **Never mock internal business logic in tests**
3. **Never ignore TypeScript errors** with `@ts-ignore`
4. **Never skip input validation** for external data
5. **Never exceed 500 lines per file**
6. **Never use `any` type** in TypeScript
7. **Never commit without passing quality checks**

---

*Essential development guidelines for Claude Code - Keep focused and functional*