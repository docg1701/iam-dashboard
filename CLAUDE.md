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

### ⚠️ CRITICAL COMPATIBILITY RULES
- **NEVER use deprecated `datetime.utcnow()`** - causes Python 3.12+ warnings
- **MANDATORY: Search memory before modifying**:
  - Enums: `recall_memories "SQLModel enum Alembic"`
  - DateTime: `recall_memories "datetime timezone PostgreSQL"`
  - Migrations: `recall_memories "Alembic migration PostgreSQL"`
- **MANDATORY: Store solutions after fixing bugs**: Use `store_memory` with full context

## 🧠 Heimdall MCP - Cognitive Memory System

### MANDATORY Memory Checks
**BEFORE modifying these critical areas, ALWAYS search memory first:**
- Database models (SQLModel, Alembic, enums)
- DateTime handling
- PostgreSQL configurations
- Authentication/security patterns
- Docker configurations

### Memory Workflow

#### 1. Starting Any Task
```bash
# Search for related past issues FIRST
recall_memories "SQLModel enum"           # when working with enums
recall_memories "datetime PostgreSQL"     # when handling timestamps
recall_memories "Alembic migration"       # before generating migrations
recall_memories "FastAPI authentication"  # when touching auth code
recall_memories "Docker deployment"       # when modifying containers
```

#### 2. After Resolving Complex Issues
```bash
# Store solution immediately with rich context
store_memory "PROBLEM: [description] SOLUTION: [fix] PREVENTION: [checklist]"
# Tag properly for future discovery
tags: ["sqlmodel", "critical-bug", "postgresql"]
```

#### 3. End of Session
```bash
# Record session insights
session_lessons "Discovered pattern: [what you learned]"
```

### Tool Reference
| Tool | When to Use | Example Query |
|------|------------|---------------|
| `recall_memories` | Before touching critical code areas | "SQLModel Alembic enum compatibility" |
| `store_memory` | After fixing bugs or discovering patterns | Include problem, solution, test commands |
| `session_lessons` | End of productive sessions | Key patterns or breakthroughs |
| `memory_status` | Weekly health checks | Check for memory bloat |
| `delete_memory` | Remove outdated solutions | By ID when superseded |
| `delete_memories_by_tags` | Major refactors | Clean deprecated patterns |

### Memory Quality Guidelines
- **Be specific**: Include error messages, stack traces, working code
- **Include test commands**: How to verify the fix works
- **Tag thoroughly**: Technology stack, error type, severity
- **Link related memories**: Reference IDs of connected solutions

### Backend Testing Directives
- **CRITICAL: Mock only external dependencies - NEVER mock internal business logic**
- **Golden Rule**: "Mock the boundaries, not the behavior"
- **NEVER mock**: PermissionService logic, authentication flows, database operations (in integration), business rules
- **ALWAYS mock**: External HTTP calls, SMTP servers, file I/O, third-party libraries, time/UUID generation

### Frontend Testing Directives
- **NEVER mock internal frontend code, components, hooks, or utilities**
- **ONLY mock external APIs** (fetch calls, third-party services, etc.)
- **Test actual behavior**, not implementation details

### Test Configuration Troubleshooting
**SYMPTOMS**: Coverage reports incomplete, tests hanging/timing out, or suite interrupted prematurely
**ROOT CAUSE**: Often outdated syntax, misconfiguration, or inappropriate test profile selection
**SOLUTION**:
1. **Verify current syntax** with mcp__context7 for the EXACT testing library (Vitest, pytest, etc.)
2. **Use profile-based execution** for targeted debugging:
   - `./scripts/run-frontend-tests.sh fast` - bail-on-failure mode for quick feedback
   - `./scripts/run-frontend-tests.sh debug` - hanging-process detection for timeout issues
   - `./scripts/run-backend-tests.sh fast` - unit tests only for quick validation
   - `./scripts/run-database-tests.sh fast` - essential database tests only
3. **Fix errors systematically**: Run fast profile → Fix first error → Repeat until clean
4. **Common Vitest 3.x fix**: Use `import { fileURLToPath } from 'node:url'` not old `path` syntax
5. **Progressive test execution**: Start with fast profiles, then move to complete profiles

**Vitest 3.x Configuration Improvements**:
- **Fork Pool Strategy**: `pool: 'forks'` provides better React component stability
- **Timeout Management**: 30s test timeout optimized for complex component interactions
- **Concurrency Control**: Limited to 5 simultaneous files to prevent resource exhaustion  
- **Clean Test Summaries**: Automatic generation reduces log file sizes by 90%+
- **Profile-Based Execution**: Choose optimal testing strategy for development context

### Tool Usage Rules
- **MANDATORY: Read before Edit** - ALWAYS use `Read` tool before any `Edit` operation
- **File-specific editing** - NEVER attempt to edit directories as if they were files
- **Correct workflow**: `Read` → `Edit` → `Bash` (for validation)
- **NEVER skip reading** - Even for "obvious" changes, read the file first


## 🛠️ MCP Tools

**Context7**: `mcp__context7__resolve-library-id` + `mcp__context7__get-library-docs`  
**Playwright E2E**: `mcp__playwright__browser_navigate|click|type|snapshot|take_screenshot`


## 🚀 Essential Commands

### Setup & Development
```bash
# MANDATORY: Setup Docker environment first
./scripts/deploy-production.sh                    # Setup with health checks

# Development
npm run setup  # Install dependencies
npm run dev    # Start frontend and backend
```


### Environment Variables
**Script timeout and configuration with profile support** (optional):
```bash
# Build and test timeouts (profile-dependent)
export BUILD_TIMEOUT=900                # Build operations → run-build-validation.sh, run-docker-tests.sh
export TEST_TIMEOUT=30                  # Test execution timeout (frontend defaults to 30s, backend/security to 600s)

# Docker and deployment configuration
export DEPLOYMENT_TIMEOUT=600           # Production deployment → deploy-production.sh
export HEALTH_CHECK_RETRIES=30          # Health check attempts → deploy-production.sh
export DOCKER_AUTO_CLEANUP=true         # Auto-cleanup → run-docker-tests.sh (all profiles)
export BACKUP_VOLUMES=true              # Enable backups → deploy-production.sh

# Database testing configuration
export DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=password

# Profile-specific optimizations
# Note: Individual scripts handle pool strategies and failure limits internally
```

**Vitest Configuration Notes**:
- **30s timeout** for frontend tests prevents hanging while allowing complex component tests
- **Fork pool strategy** improves React component stability vs threads
- **Clean test summaries** automatically generated to reduce log file sizes
- **Profile-based execution** allows choosing optimal testing strategy for development context

## 📋 FOCUSED TEST CATEGORIES (12 Scripts)
**CRITICAL: Use focused test scripts with real data capture**

**All test scripts now include**: Statistics tracking, timeout detection (exit code 124), signal handling (SIGINT/SIGTERM), and contextual reporting.

### 🔒 SECURITY STATUS: PRODUCTION READY ✅
**Latest Security Analysis**: August 2025  
**Security Grade**: A+ (92% secure, 8% requires monitoring)  
**All critical vulnerabilities eliminated** - Scripts are production-ready

### 🧪 Test Scripts (12 Available)

| Script | Profiles | Purpose |
|--------|----------|---------|
| `run-frontend-tests.sh` | fast, coverage, debug, single | Frontend unit/integration tests |
| `run-backend-tests.sh` | fast, coverage, unit, integration | Backend tests with coverage |
| `run-quality-checks.sh` | fast, fix, lint, format | Code linting and formatting |
| `run-security-tests.sh` | fast, audit, performance | Security scans and performance |
| `run-database-tests.sh` | fast, migration, integrity, performance | Database testing |
| `run-docker-tests.sh` | fast, build, integration, security | Docker containers |
| `run-e2e-tests.sh` | fast, critical, mobile, accessibility | End-to-end testing |
| `run-accessibility-tests.sh` | fast, coverage, debug | WCAG compliance |
| `run-build-validation.sh` | fast, info | Production build validation |
| `analyze-coverage.sh` | fast, backend, frontend, generate | Coverage analysis |
| `run-mock-violations-scan.sh` | fast, backend, frontend, patterns | Mock compliance |
| `deploy-production.sh` | - | Production deployment |

**Results saved to**: `./scripts/test-results/` with timestamps

📚 **For detailed test script documentation**: See [scripts/README.md](scripts/README.md) for:
- Complete profile system documentation
- Troubleshooting guide for common issues  
- Environment variable configuration
- Performance expectations and benchmarks
- CI/CD integration examples

**Mock compliance**:
- ❌ PROHIBITED: Mock internal business logic, components, hooks
- ✅ APPROVED: Mock external boundaries (APIs, time/UUID, services)


## 🎯 Development Workflow

**Fast profiles**: Daily development, immediate feedback  
**Complete profiles**: Before commits, production validation  
**Specialized profiles**: Targeted debugging (debug, migration, build, etc.)

**Common workflows**:
```bash
# Daily development
./scripts/run-frontend-tests.sh fast && ./scripts/run-backend-tests.sh fast

# Before commit  
./scripts/run-quality-checks.sh complete && ./scripts/run-backend-tests.sh coverage
```

## 📈 Test Results

Results saved to `./scripts/test-results/` with timestamps. Always read actual log files.

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

### Backend Development (UV Package Manager)
```bash
cd apps/api
uv sync                      # Sync dependencies
uv add fastapi              # Add dependencies (NEVER edit pyproject.toml)
uv run alembic upgrade head  # Database migrations
uv run pytest              # Run tests
```

## ⚠️ Critical Rules

### Essential Requirements
1. **Docker First**: Always run `./scripts/deploy-production.sh` before testing
2. **Memory System**: MANDATORY `recall_memories` before enum/datetime/migration changes, `store_memory` after fixes
3. **80%+ test coverage** required
4. **Validate external data** with Zod/Pydantic
5. **Use TypeScript strictly** (no `any`)
6. **Use UV for Python** (never edit pyproject.toml directly)
7. **Read before Edit** workflow

### Prohibited Actions  
1. **Never access `.secret-vault`**
2. **Never mock internal business logic/components**
3. **Never skip input validation**
4. **Never commit without quality checks**
5. **Never use `eval` in scripts**

## 🔐 Production Deployment

### Pre-deployment Checklist
1. Run all 12 test scripts 
2. Zero mock violations
3. No Critical/High vulnerabilities
4. >80% coverage
5. Use `./scripts/deploy-production.sh`

### Production Environment Variables
```bash
export DEPLOYMENT_TIMEOUT=600           # Max deployment time (60-1800s)
export HEALTH_CHECK_RETRIES=30          # Health check attempts (5-100)  
export BACKUP_VOLUMES=true              # Enable backups
export ALLOW_ROOT_DEPLOYMENT=false      # Block root deployment
```

---