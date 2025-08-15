# 🧪 IAM Dashboard Test Scripts Manual

**Comprehensive test execution suite with 12 focused scripts, profile-based execution, and real-time statistics.**

📌 **Note**: This manual provides detailed documentation for the test scripts referenced in [CLAUDE.md](../CLAUDE.md). For general project guidelines and restrictions, see CLAUDE.md first.

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+** (frontend tests)
- **Python 3.10+ with UV** (backend tests)  
- **Docker 20+** (container and E2E tests)
- **PostgreSQL client tools** (database tests)

### Essential Workflow
```bash
# 1. MANDATORY: Setup Docker environment first
./deploy-production.sh

# 2. Run core test suite
./run-quality-checks.sh fast       # Code quality
./run-frontend-tests.sh fast       # Frontend tests  
./run-backend-tests.sh fast        # Backend tests

# 3. View results
ls test-results/                   # All timestamped results
```

### Common Commands
```bash
# Development workflow
./run-frontend-tests.sh fast && ./run-backend-tests.sh fast

# Pre-commit validation  
./run-quality-checks.sh complete && ./run-backend-tests.sh coverage

# Full production validation
./run-security-tests.sh complete && ./run-database-tests.sh complete
```

## 📋 Test Scripts Overview

| Script | Profiles | Default Timeout | Purpose | Key Outputs |
|--------|----------|----------------|---------|-------------|
| `run-frontend-tests.sh` | complete, fast, coverage, debug, single | 30s | React/Next.js testing | Unit, integration, responsive |
| `run-backend-tests.sh` | complete, fast, coverage, unit, integration | 600s | FastAPI/Python testing | Unit, integration, E2E |
| `run-quality-checks.sh` | complete, fast, fix, lint, format | 30s | Code quality | Lint, format, TypeScript |
| `run-security-tests.sh` | complete, fast, audit, performance | 600s | Security scanning | Vulnerabilities, performance |
| `run-database-tests.sh` | complete, fast, migration, integrity, performance | 1800s | Database validation | Migration, schema, integrity |
| `run-docker-tests.sh` | complete, fast, build, integration, security | 600s | Container testing | Build, compose, security |
| `run-e2e-tests.sh` | complete, fast, critical, mobile, accessibility | 300s | End-to-end flows | Service status, scenarios |
| `run-accessibility-tests.sh` | complete, fast, coverage, debug | 30s | WCAG compliance | A11y components, keyboard |
| `run-build-validation.sh` | complete, fast, info | 600s | Production builds | Build validation, info |
| `analyze-coverage.sh` | complete, fast, backend, frontend, generate | 60s | Coverage analysis | Coverage reports |
| `run-mock-violations-scan.sh` | complete, fast, backend, frontend, patterns | 60s | Mock compliance | Violation patterns |
| `deploy-production.sh` | - | 600s | Production deployment | Service health, deployment |

**Results Location**: All outputs saved to `test-results/` with timestamps

## 🎯 Profile System

### Profile Types
- **complete** (default): Full execution with comprehensive results
- **fast**: Rapid feedback with fail-fast behavior  
- **coverage**: Enhanced coverage analysis and reporting
- **debug**: Hanging detection and detailed debugging
- **Specialized**: Script-specific profiles (migration, build, audit, etc.)

### Profile Selection Guidelines
```bash
# Development (immediate feedback)
./run-frontend-tests.sh fast

# Quality assurance (thorough validation)  
./run-backend-tests.sh coverage

# Debugging (when tests hang or fail mysteriously)
./run-frontend-tests.sh debug

# Targeted testing (specific subsystem)
./run-database-tests.sh migration
```

### Timeout Behavior
- **Fast profiles**: Shorter timeouts (30-60s) for quick feedback
- **Complete profiles**: Standard timeouts (300-1800s) for thorough execution
- **Coverage profiles**: Extended timeouts to allow detailed analysis
- **Debug profiles**: Extended timeouts with hanging detection

## ⚙️ Environment Configuration

### Core Variables
```bash
# Test execution timeouts (each script has its own default)
export TEST_TIMEOUT=30                  # Override test timeout (frontend: 30s, backend: 600s)

# Build and deployment
export BUILD_TIMEOUT=900                # Build operations timeout
export DEPLOYMENT_TIMEOUT=600           # Deployment timeout (60-1800s)
export HEALTH_CHECK_RETRIES=30          # Health check attempts (5-100)
export HEALTH_CHECK_INTERVAL=10         # Check interval (1-60s)

# Docker and database
export DOCKER_AUTO_CLEANUP=false        # Auto-cleanup test images
export BACKUP_VOLUMES=true              # Enable volume backups
export DB_HOST=localhost                # Database connection
export DB_PORT=5432
export DB_USER=postgres

# Security
export ALLOW_ROOT_DEPLOYMENT=false      # Block root deployment
```

### Development vs Production
```bash
# Development (faster feedback)
export TEST_TIMEOUT=30
export BUILD_TIMEOUT=300

# Production (thorough validation)
export TEST_TIMEOUT=600
export BUILD_TIMEOUT=900
export BACKUP_VOLUMES=true
```

## 🔧 Troubleshooting Guide

### Common Issues

#### Tests Hanging or Timing Out
```bash
# Solution 1: Use debug profile to identify hanging tests
./run-frontend-tests.sh debug

# Solution 2: Increase timeout for specific script
TEST_TIMEOUT=120 ./run-frontend-tests.sh

# Solution 3: Single fork mode for complex debugging
./run-frontend-tests.sh single
```

#### Coverage Reports Missing
```bash
# Solution 1: Run tests first to generate coverage
./run-frontend-tests.sh coverage

# Solution 2: Generate fresh coverage reports
./analyze-coverage.sh generate

# Solution 3: Check coverage locations
ls apps/web/coverage/index.html      # Frontend
ls apps/api/htmlcov/index.html       # Backend
```

#### Docker Permission Denied
```bash
# Solution 1: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Solution 2: Check Docker daemon
sudo systemctl status docker

# Solution 3: Use rootless Docker
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
```

#### Database Connection Failed
```bash
# Solution 1: Ensure PostgreSQL is running
./deploy-production.sh

# Solution 2: Check database status
docker compose ps postgres

# Solution 3: Manual database start
docker compose up -d postgres
docker compose exec postgres pg_isready -U postgres
```

#### Build Failures
```bash
# Solution 1: Clean build
rm -rf apps/web/.next apps/web/node_modules/.cache
npm run build

# Solution 2: Check dependencies
npm run setup
uv sync

# Solution 3: Fast validation
./run-build-validation.sh fast
```

### Error Interpretation

#### Exit Codes
- **0**: All tests/checks passed
- **1-99**: Number of failed tests/checks  
- **124**: Command timed out
- **130**: Script interrupted (Ctrl+C)

#### Statistics Output
```
📋 EXECUTION STATISTICS - COMPLETED
======================================
🕰️ Total Execution Time: 53s (0m 53s)
🏃 Tests Executed: 3
✅ Successful: 1
⚠️ Failed/Timed out: 2
📊 Success Rate: 33%
======================================
```

## 🎭 MCP Playwright E2E Testing

### Interactive E2E Workflow
```bash
# 1. Prepare environment and get scenarios
./run-e2e-tests.sh critical

# 2. Use MCP Playwright for actual testing
mcp__playwright__browser_navigate --url="http://localhost:3000"
mcp__playwright__browser_click --element="Login Button" --ref="button[type='submit']"
mcp__playwright__browser_type --element="Email" --ref="input[name='email']" --text="admin@example.com"
mcp__playwright__browser_snapshot  # Get page structure

# 3. Follow scenarios from test-results/e2e-test-scenarios_*.log
```

### Mobile & Accessibility Testing
```bash
# Mobile responsive testing
mcp__playwright__browser_resize --width="375" --height="667"

# Accessibility testing
mcp__playwright__browser_press_key --key="Tab"
mcp__playwright__browser_evaluate --function="() => document.querySelectorAll('[aria-label]').length"
```

## 🗄️ Database Testing Workflow

### Migration Testing
```bash
# Complete migration validation
./run-database-tests.sh migration

# Fast essential checks
./run-database-tests.sh fast

# Performance testing
./run-database-tests.sh performance
```

### Manual Database Operations
```bash
# Connect to test database
docker compose exec postgres psql -U postgres -d iam_dashboard_test

# Check migration status
cd apps/api && uv run alembic current

# Manual migration
cd apps/api && uv run alembic upgrade head
```

## 🐳 Docker Testing Workflow

### Container Validation
```bash
# Full Docker testing
./run-docker-tests.sh complete

# Quick validation
./run-docker-tests.sh fast

# Build testing only
./run-docker-tests.sh build
```

### Manual Docker Operations
```bash
# Check container health
docker compose ps

# View logs
docker compose logs backend frontend

# Restart services
docker compose restart backend
```

## 📊 Understanding Test Results

### File Naming Convention
Format: `{category}-{type}_{YYYYMMDD_HHMMSS}.log`

Examples:
- `frontend-unit-tests_20250814_143028.log`
- `backend-coverage-report_20250814_080817.log`
- `security-tests_20250814_004327.log`

### Key Result Files
- **Test Reports**: `*-test-report_*.log` (execution statistics and recommendations)
- **Coverage**: `coverage-analysis_*.log` + HTML reports in apps/*/coverage/
- **Security**: `security-tests_*.log` + `*-security-audit_*.log`
- **Build**: `build-validation_*.log` + `build-info_*.log`

### Coverage Reports (Open in Browser)
- **Frontend**: `apps/web/coverage/index.html`
- **Backend**: `apps/api/htmlcov/index.html`
- **Clean Summaries**: `apps/web/test-summary-clean.json`

## 🔐 Production Deployment

### Secure Deployment Process
```bash
# Standard deployment
./deploy-production.sh

# With backup
BACKUP_VOLUMES=true ./deploy-production.sh
```

### Deployment Features
- Parameter validation and sanitization
- Docker privilege verification
- Health checks with automatic rollback
- Optional volume backup
- Real-time service monitoring

### Manual Recovery (Emergency)
```bash
# If automated deployment fails
docker compose down --timeout 30
docker compose up -d postgres redis
docker compose exec postgres pg_isready -U postgres
docker compose up -d backend
curl -f http://localhost:8000/health
```

## 🎯 Development Best Practices

### Script Usage Patterns
```bash
# Daily development
./run-frontend-tests.sh fast
./run-backend-tests.sh fast

# Before commit
./run-quality-checks.sh complete
./run-mock-violations-scan.sh complete

# Before production
./run-security-tests.sh complete
./run-database-tests.sh complete
```

### Performance Expectations
- **Fast profiles**: 30-120 seconds
- **Complete profiles**: 2-10 minutes  
- **Coverage profiles**: 5-15 minutes
- **Database tests**: Up to 30 minutes (migration testing)

### CI/CD Integration
Scripts provide proper exit codes for automated pipelines:
- Exit code matches failure count
- Statistics in standardized format
- Timestamped results for archival

---

*All test results include execution statistics, timeout detection, and contextual recommendations for improved development workflow.*