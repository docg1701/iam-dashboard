# GEMINI.md - IAM Dashboard Development Guide

This document provides essential guidance for working on the full-stack IAM Dashboard project, based on the detailed instructions in `CLAUDE.md`.

## 1. Project Overview

This is a full-stack Identity and Access Management (IAM) Dashboard. The project is built with a modern tech stack and has a strong focus on automated testing, security, and production readiness.

*   **Frontend**: Next.js 15, React 19, TypeScript, shadcn/ui
*   **Backend**: FastAPI, SQLModel, PostgreSQL, Alembic
*   **Testing**: pytest, Vitest, Playwright, React Testing Library
*   **Package Management**: npm workspaces, UV (Python)
*   **Containerization**: Docker

## 2. Critical Rules & Restrictions

### Language Requirements
-   **Code & Docs**: Must be in **English**.
-   **UI Content**: Must be in **Portuguese (Brazil)**.

### Directory Access
-   The `.secret-vault/` directory is **strictly off-limits**. Do not read, list, or modify its contents.

### Tool Usage
-   **Read Before Edit**: ALWAYS read a file's content before editing it.
-   **File-Specific Edits**: Only edit files, never directories.
-   **Workflow**: `Read` → `Edit` → `Bash` (for validation).

## 3. Building and Running

### Development Environment
To set up and run the development environment:
```bash
# Install all dependencies
npm run setup

# Start both frontend and backend
npm run dev
```

### Docker Environment (for Testing & Deployment)
A Docker environment is **required** for all testing and deployment operations.

```bash
# MANDATORY: Setup Docker environment with health checks before any testing
./scripts/deploy-production.sh

# Use this for initial setup to avoid migration errors
SKIP_ALEMBIC_CHECK=true ./scripts/deploy-production.sh
```
**CRITICAL**: The Docker environment **must** be running and healthy before executing any of the 12 test scripts.

## 4. Testing

This project has a comprehensive suite of **12 focused test scripts**. All test results are saved with timestamps in the `./scripts/test-results/` directory.

### Testing Philosophy
-   **Golden Rule**: "Mock the boundaries, not the behavior."
-   **Backend**: **NEVER** mock internal business logic (e.g., `PermissionService`, auth flows). **ONLY** mock external dependencies (e.g., HTTP calls, SMTP servers).
-   **Frontend**: **NEVER** mock internal code (components, hooks). **ONLY** mock external APIs.
-   The `./scripts/run-mock-violations-scan.sh` script exists specifically to enforce these rules.

### Recommended Test Execution Order
```bash
# 1. Code Quality
./scripts/run-quality-checks.sh

# 2. Unit & Integration Tests
./scripts/run-frontend-tests.sh
./scripts/run-backend-tests.sh

# 3. Security & Compliance
./scripts/run-security-tests.sh
./scripts/run-mock-violations-scan.sh

# 4. Full Suite (for pre-production validation)
./scripts/run-database-tests.sh
./scripts/run-docker-tests.sh
./scripts/run-accessibility-tests.sh
./scripts/run-build-validation.sh
./scripts/analyze-coverage.sh
```

### Viewing Test Results & Coverage
-   **Logs**: Check the timestamped files in `scripts/test-results/`.
-   **Coverage Reports**: Open the `index.html` files in a browser:
    -   **Backend**: `apps/backend/htmlcov/index.html`
    -   **Frontend**: `apps/frontend/coverage/index.html`

## 5. Critical Development Rules

### MUST DO
-   **Docker First**: Always run `./scripts/deploy-production.sh` before tests.
-   **Validate Data**: Use Zod (frontend) and Pydantic (backend) for all external data.
-   **Test Coverage**: Maintain **80%+** test coverage.
-   **Strict TypeScript**: No `any` types allowed.
-   **Use `uv`**: Manage Python packages with `uv`; do not edit `pyproject.toml` directly.
-   **Co-locate Tests**: Keep tests in `__tests__` folders.
-   **Simple Commands**: Use native tool flags (`--quiet`, `--reporter=basic`) and avoid complex pipes to prevent truncated output.

### NEVER DO
-   **Access `.secret-vault`**.
-   **Mock internal logic**.
-   **Ignore TypeScript errors** with `@ts-ignore`.
-   **Exceed 500 lines** per file.
-   **Commit without passing quality checks**.
-   **Use `eval` in scripts**.

## 6. Production Deployment

The project is **production-ready**, with a security grade of A+.

### Checklist
1.  Run the full test suite (all 12 scripts).
2.  Verify zero mock violations.
3.  Ensure no Critical/High security vulnerabilities are present.
4.  Confirm test coverage is >80%.
5.  Validate the production build using `./scripts/run-build-validation.sh`.
6.  Deploy using the secure script: `./scripts/deploy-production.sh`.

### Environment Variables
Several environment variables are available to control timeouts, health checks, and other script behaviors.
```bash
# Example:
export BUILD_TIMEOUT=900
export TEST_TIMEOUT=600
export DEPLOYMENT_TIMEOUT=600
export HEALTH_CHECK_RETRIES=30
export BACKUP_VOLUMES=true
```
