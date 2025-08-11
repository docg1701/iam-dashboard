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

### Tool Usage Rules
- **MANDATORY: Read before Edit** - ALWAYS use `Read` tool before any `Edit` operation
- **File-specific editing** - NEVER attempt to edit directories as if they were files
- **Correct workflow**: `Read` → `Edit` → `Bash` (for validation)
- **NEVER skip reading** - Even for "obvious" changes, read the file first

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

### Docker Environment Preparation
```bash
# MANDATORY: Before ANY testing, ALWAYS ensure Docker environment is ready
./scripts/deploy-production.sh                    # Setup Docker environment with health checks
SKIP_ALEMBIC_CHECK=true ./scripts/deploy-production.sh  # Initial setup without Alembic migrations

# This script MUST be executed before running any test scripts to ensure:
# - PostgreSQL and Redis are running and healthy
# - Backend API is accessible at http://localhost:8000
# - Database migrations are applied (unless skipped)
# - All services are properly configured
```

**🔴 CRITICAL RULE: Docker Environment First**
- **MANDATORY**: Execute `./scripts/deploy-production.sh` before ANY other test script execution
- **NEVER run tests** without confirmed Docker environment readiness
- **VERIFY services** are healthy before proceeding with other test scripts
- **All OTHER 11 test scripts** depend on this Docker environment being ready

### Development
```bash
# Setup and start
npm run setup  # Install all dependencies
npm run dev    # Start both frontend and backend
```

### Environment Variables
**Script timeout and configuration** (optional):
```bash
export BUILD_TIMEOUT=900                # Build operations → run-build-validation.sh, run-accessibility-tests.sh
export TEST_TIMEOUT=600                 # Test execution → run-backend-tests.sh, run-frontend-tests.sh, run-security-tests.sh
export DEPLOYMENT_TIMEOUT=600           # Production deployment → deploy-production.sh
export HEALTH_CHECK_RETRIES=30          # Health check attempts → deploy-production.sh
export DOCKER_AUTO_CLEANUP=true         # Auto-cleanup → run-docker-tests.sh
export BACKUP_VOLUMES=true              # Enable backups → deploy-production.sh
export SKIP_ALEMBIC_CHECK=true          # Skip Alembic validation for initial setup → deploy-production.sh
# Database testing (run-database-tests.sh):
export DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=password
```

## 📋 FOCUSED TEST CATEGORIES (12 Scripts)
**CRITICAL: Use focused test scripts with real data capture**

### 🔒 SECURITY STATUS: PRODUCTION READY ✅
**Latest Security Analysis**: August 2025  
**Security Grade**: A+ (92% secure, 8% requires monitoring)  
**All critical vulnerabilities eliminated** - Scripts are production-ready

### 🧪 Frontend Tests
```bash
./scripts/run-frontend-tests.sh                       # Frontend unit & integration tests with coverage
# Results: ./scripts/test-results/frontend-unit-tests_TIMESTAMP.log
# Results: ./scripts/test-results/frontend-integration-tests_TIMESTAMP.log
# Results: ./scripts/test-results/frontend-responsive-tests_TIMESTAMP.log
# Report: ./scripts/test-results/frontend-test-report_TIMESTAMP.log
# Coverage: ./apps/frontend/coverage/index.html
```

### 🔧 Backend Tests
```bash
./scripts/run-backend-tests.sh                        # Backend unit, integration & E2E tests with coverage
# Results: ./scripts/test-results/backend-unit-tests_TIMESTAMP.log
# Results: ./scripts/test-results/backend-integration-tests_TIMESTAMP.log
# Results: ./scripts/test-results/backend-e2e-tests_TIMESTAMP.log
# Results: ./scripts/test-results/backend-coverage-report_TIMESTAMP.log
# Report: ./scripts/test-results/backend-test-report_TIMESTAMP.log  
# Coverage: ./apps/backend/htmlcov/index.html
```

### ✨ Code Quality Checks
```bash
./scripts/run-quality-checks.sh                       # Linting, formatting, type checking, Alembic validation
# Results: ./scripts/test-results/frontend-lint_TIMESTAMP.log
# Results: ./scripts/test-results/backend-lint_TIMESTAMP.log
# Results: ./scripts/test-results/frontend-formatting_TIMESTAMP.log
# Results: ./scripts/test-results/backend-formatting_TIMESTAMP.log
# Results: ./scripts/test-results/typescript-check_TIMESTAMP.log
# Results: ./scripts/test-results/alembic-check_TIMESTAMP.log
# Results: ./scripts/test-results/alembic-history_TIMESTAMP.log
```

### 🔒 Security & Performance Tests  
```bash
./scripts/run-security-tests.sh                       # Security vulnerabilities & performance benchmarks
# Results: ./scripts/test-results/security-tests_TIMESTAMP.log
# Results: ./scripts/test-results/performance-tests_TIMESTAMP.log
# Audits: ./scripts/test-results/frontend-security-audit_TIMESTAMP.log
# Audits: ./scripts/test-results/backend-security-audit_TIMESTAMP.log
```

### 🗄️ Database Migration & Schema Tests
```bash
./scripts/run-database-tests.sh                       # Database migrations, schema consistency, data integrity
# Report: ./scripts/test-results/database-test-report_TIMESTAMP.log
# Results: ./scripts/test-results/db-migration-*_TIMESTAMP.log
# Results: ./scripts/test-results/db-schema-consistency_TIMESTAMP.log
# Results: ./scripts/test-results/db-seed-data_TIMESTAMP.log
```

### 🐳 Docker Container & Orchestration Tests
```bash
./scripts/run-docker-tests.sh                         # Optimized Docker builds, container validation, compose integration
# Report: ./scripts/test-results/docker-test-report_TIMESTAMP.log
# Results: ./scripts/test-results/docker-dockerfile-check_TIMESTAMP.log
# Results: ./scripts/test-results/docker-backend-build_TIMESTAMP.log
# Results: ./scripts/test-results/docker-frontend-build_TIMESTAMP.log
# Results: ./scripts/test-results/docker-stack-readiness_TIMESTAMP.log
```

### 🎭 End-to-End Tests (MCP Playwright Integration)
```bash
./scripts/run-e2e-tests.sh                           # E2E test documentation & MCP Playwright scenarios
# Report: ./scripts/test-results/e2e-test-report_TIMESTAMP.log
# Status: ./scripts/test-results/e2e-service-status_TIMESTAMP.log
# Scenarios: ./scripts/test-results/e2e-test-scenarios_TIMESTAMP.log
```

### ♿ Accessibility & WCAG Compliance Tests
```bash
./scripts/run-accessibility-tests.sh                 # Accessibility compliance, keyboard navigation, ARIA
# Report: ./scripts/test-results/accessibility-test-report_TIMESTAMP.log
# Results: ./scripts/test-results/a11y-component-*_TIMESTAMP.log
# Results: ./scripts/test-results/a11y-keyboard-*_TIMESTAMP.log
# MCP Scenarios: ./scripts/test-results/a11y-mcp-scenarios_TIMESTAMP.log
```

### 🏗️ Build Validation & Deployment Checks
```bash
./scripts/run-build-validation.sh                     # Production build & deployment checks
# Results: ./scripts/test-results/build-validation_TIMESTAMP.log
# Results: ./scripts/test-results/build-info_TIMESTAMP.log
```

### 📊 Coverage Analysis & Reporting
```bash
./scripts/analyze-coverage.sh                         # Comprehensive coverage analysis
# Report: ./scripts/test-results/coverage-analysis_TIMESTAMP.log
# Backend Coverage: ./apps/backend/htmlcov/index.html
# Frontend Coverage: ./apps/frontend/coverage/index.html
```

### 🕵️ Mock Violations Scanner
```bash
./scripts/run-mock-violations-scan.sh                 # CLAUDE.md compliance validation
# Report: ./scripts/test-results/mock-violations-report_TIMESTAMP.log
# Results: ./scripts/test-results/backend-*-mocks_TIMESTAMP.log
# Results: ./scripts/test-results/frontend-*-mocks_TIMESTAMP.log
# Results: ./scripts/test-results/approved-*-mocks_TIMESTAMP.log
```
**Purpose**: Validates compliance with testing directives:
- ❌ **PROHIBITED**: Mock internal business logic (PermissionService, authentication flows)
- ❌ **PROHIBITED**: Mock internal frontend code (components, hooks, utilities)  
- ✅ **APPROVED**: Mock external boundaries (APIs, time/UUID, external services)

### 🚀 Production Deployment
```bash
./scripts/deploy-production.sh                        # Secure production deployment
SKIP_ALEMBIC_CHECK=true ./scripts/deploy-production.sh # Initial setup without Alembic
# Automatic service deployment with enterprise security
# Health checks, rollback capability, secure backups
```

## 🎭 MCP Playwright E2E Testing Workflow
**CRITICAL: Use this for interactive E2E testing**

**Step 1: Prepare E2E Environment**
```bash
./scripts/run-e2e-tests.sh  # Check service status and get test scenarios
# Read: ./scripts/test-results/e2e-service-status_TIMESTAMP.log
# Read: ./scripts/test-results/e2e-test-scenarios_TIMESTAMP.log
```

**Step 2: Interactive E2E Testing with MCP Playwright**
```bash
# Essential MCP Playwright Commands:
mcp__playwright__browser_navigate --url="http://localhost:3000"
mcp__playwright__browser_click --element="Login Button" --ref="button[type='submit']"
mcp__playwright__browser_type --element="Email" --ref="input[name='email']" --text="admin@example.com"
mcp__playwright__browser_snapshot  # Get page structure for validation
mcp__playwright__browser_take_screenshot --filename="test-result.png"
mcp__playwright__browser_console_messages  # Check for JavaScript errors

# Accessibility Testing:
mcp__playwright__browser_press_key --key="Tab"  # Keyboard navigation
mcp__playwright__browser_resize --width="375" --height="667"  # Mobile testing
mcp__playwright__browser_evaluate --function="() => document.querySelectorAll('[aria-label]').length"

# PREREQUISITES: 
# - Backend running: npm run dev (or uv run uvicorn src.main:app --reload)
# - Frontend running: npm run dev
```

**Step 3: Follow Documented Test Scenarios**
- Read `e2e-test-scenarios_TIMESTAMP.log` for specific test flows
- Use authentication, client management, and permission scenarios
- Test responsive design and accessibility compliance

## 📈 ACCESSING REAL TEST DATA
All test results are saved with timestamps in `./scripts/test-results/` directory.

**Key Files to Analyze (12 Focused Test Scripts):**
- `frontend-test-report_TIMESTAMP.log` - Frontend unit & integration test analysis
- `backend-test-report_TIMESTAMP.log` - Backend unit, integration & E2E test analysis  
- `database-test-report_TIMESTAMP.log` - Database migration and schema validation
- `docker-test-report_TIMESTAMP.log` - Optimized container builds and orchestration
- `e2e-test-report_TIMESTAMP.log` - E2E testing scenarios and MCP Playwright integration
- `accessibility-test-report_TIMESTAMP.log` - WCAG compliance and accessibility
- `security-tests_TIMESTAMP.log` - Security vulnerability scans
- `performance-tests_TIMESTAMP.log` - Performance benchmarks
- `build-validation_TIMESTAMP.log` - Production build validation
- `coverage-analysis_TIMESTAMP.log` - Coverage analysis report
- `mock-violations-report_TIMESTAMP.log` - CLAUDE.md compliance validation
- HTML Coverage Reports: Open in browser for visual coverage analysis

**CRITICAL: Never guess test results** - Always read the actual log files for accurate data and metrics.

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
1. **CRITICAL: Docker Environment First** - ALWAYS execute `./scripts/deploy-production.sh` before ANY test execution
2. **Follow KISS and YAGNI principles**
3. **Validate ALL external data** with Zod (frontend) and Pydantic (backend)
4. **Maintain 80%+ test coverage** - NO EXCEPTIONS
5. **Use TypeScript strictly** - no `any` types
6. **Use UV for Python packages** - NEVER edit pyproject.toml directly
7. **Co-locate tests** in `__tests__` folders
8. **CRITICAL: Use Test Scripts** - Use dedicated test scripts:
   - ✅ `./scripts/deploy-production.sh` (MANDATORY: Execute FIRST to prepare Docker environment)
   - ✅ `./scripts/run-frontend-tests.sh` (recommended)
   - ✅ `./scripts/run-backend-tests.sh` (recommended)
   - ✅ `./scripts/run-mock-violations-scan.sh` (CLAUDE.md compliance)
   - ✅ `npm run test:coverage` (direct command if needed)
9. **CRITICAL: Command Output Management**:
   - ❌ **Complex pipes get truncated** - leads to invented data
   - ✅ **Use native tool flags**: `--quiet`, `--reporter=basic`, `--tb=short`
   - ✅ **Keep commands simple**: One tool per command, avoid chaining
   - ✅ **Have fallback commands**: If npm script fails, try direct tool

### NEVER DO
1. **Never access `.secret-vault` directory**
2. **Never run tests without Docker environment ready** - Always execute `./scripts/deploy-production.sh` first
3. **Never mock internal business logic in tests**
4. **Never ignore TypeScript errors** with `@ts-ignore`
5. **Never skip input validation** for external data
6. **Never exceed 500 lines per file**
7. **Never use `any` type** in TypeScript
8. **Never commit without passing quality checks**
9. **Never edit files without reading them first** - Always `Read` before `Edit`
10. **Never attempt to edit directories as if they were files** - Use `Edit` only on specific files
11. **Never invent data when commands fail or get truncated** - Use simpler commands with native flags
12. **Never use complex command chains** - Keep one tool per command for reliability
13. **Never use `eval` in scripts** - Command injection vulnerability, use direct execution
14. **Never skip input validation in production scripts** - All parameters must be validated
15. **Never ignore security vulnerabilities** - All Critical/High severity issues must be fixed

## 🔐 SECURITY & PRODUCTION GUIDELINES

### Security Validation Requirements
- **Run security analysis** before any production deployment
- **Mock violations must be zero** - Use `run-mock-violations-scan.sh` to validate
- **All Critical/High vulnerabilities** must be resolved
- **Input validation mandatory** for all production scripts

### Production Deployment Checklist
1. ✅ Run full test suite (all 12 scripts)
2. ✅ Verify mock violations compliance (zero violations)
3. ✅ Security scans pass (no Critical/High vulnerabilities)
4. ✅ Coverage reports meet >80% threshold
5. ✅ Build validation passes in production mode
6. ✅ Deploy using secure deployment script: `./scripts/deploy-production.sh`

### Environment Variables for Production
```bash
# Security and deployment configuration:
export DEPLOYMENT_TIMEOUT=600           # Max deployment time (validated: 60-1800s)
export HEALTH_CHECK_RETRIES=30          # Health check attempts (validated: 5-100)
export BACKUP_VOLUMES=true              # Enable secure volume backups
export BUILD_TIMEOUT=900                # Build timeout (configurable)
export ALLOW_ROOT_DEPLOYMENT=false      # Security: block root deployment
```

---