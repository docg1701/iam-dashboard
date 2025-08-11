# Development Workflow

The development workflow is optimized for the custom implementation service model, supporting 5-8 concurrent client implementations with coordinated team development and reliable deployment automation.

## Local Development Setup

### Prerequisites
```bash
# System requirements
node --version        # Node.js 18.0+ required
python --version      # Python 3.12+ required
docker --version      # Docker 24.0+ required
git --version         # Git 2.30+ required

# Install UV for Python package management
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install global tools
npm install -g turbo@latest
```

### Initial Setup
```bash
# Clone repository and setup development environment
git clone <repository-url> multi-agent-iam-dashboard
cd multi-agent-iam-dashboard

# Install all dependencies (monorepo + Python)
npm install                    # Install Node.js dependencies
cd apps/api && uv sync && cd ../..  # Install Python dependencies

# Setup environment variables
cp .env.example .env
# Edit .env with your local configuration

# Start local services (PostgreSQL, Redis, etc.)
docker-compose up -d

# Run database migrations
cd apps/api && uv run alembic upgrade head && cd ../..

# Seed development data (optional)
cd apps/api && uv run python -m src.scripts.seed_dev_data && cd ../..
```

### Development Commands
```bash
# Start all services in development mode
npm run dev                    # Starts frontend + backend + shared packages

# Start individual services
npm run dev:frontend          # Next.js frontend only (http://localhost:3000)
npm run dev:backend           # FastAPI backend only (http://localhost:8000)
npm run dev:docs              # API documentation server

# Build commands
npm run build                 # Build all packages and applications
npm run build:frontend        # Build frontend for production
npm run build:backend         # Build backend with dependencies

# Testing commands
npm run test                  # Run all tests across monorepo
npm run test:frontend         # Frontend unit + integration tests
npm run test:backend          # Backend unit + integration tests
npm run test:e2e             # MCP Playwright end-to-end tests
npm run test:coverage        # Generate coverage reports

# Code quality commands
npm run lint                  # Lint all code (ESLint + Ruff)
npm run lint:fix             # Auto-fix linting issues
npm run type-check           # TypeScript type checking
npm run format               # Format code (Prettier + Black)

# Database commands
npm run db:migrate           # Run pending migrations
npm run db:rollback          # Rollback last migration
npm run db:reset             # Reset database to initial state
npm run db:seed              # Seed development data
```

---