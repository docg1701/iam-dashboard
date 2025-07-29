# IAM Dashboard

**SaaS platform for autonomous legal agents with document processing, questionnaire generation, and user management capabilities.**

## Features

- 🤖 **Autonomous Legal Agents** - Powered by Agno framework with plugin system
- 📄 **Document Processing** - PDF processing with OCR support for scanned documents
- 📝 **AI Questionnaire Generation** - Automated legal questionnaire creation
- 🔐 **Secure Authentication** - JWT + 2FA (TOTP) for enhanced security
- 🗄️ **Vector Search** - PostgreSQL with pgvector for semantic document search
- 🎯 **Modern UI** - Built with NiceGUI for responsive web interface

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0
- **Database**: PostgreSQL with pgvector extension
- **Frontend**: NiceGUI
- **AI/ML**: Google Gemini API, LlamaIndex
- **Agents**: Agno autonomous agents
- **Container**: Docker with docker-compose

## Installation & Setup

### Prerequisites

Before starting, make sure you have installed:

- **Python 3.12+** - [Download here](https://www.python.org/downloads/)
- **Docker & Docker Compose** - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **UV Package Manager** - [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
- **Git** - [Download here](https://git-scm.com/downloads)

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/your-username/iam-dashboard.git
cd iam-dashboard
```

#### 2. Install UV (if not already installed)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

#### 3. Install Python Dependencies
```bash
# Install all dependencies including dev tools
uv sync

# Verify Python environment
uv run python --version
```

#### 4. Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file to add your API keys and configuration
nano .env  # or use your preferred editor
```

**⚠️ Important**: You need to update the `.env` file with:
- **GEMINI_API_KEY**: Your Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **SECRET_KEY**: A secure secret key for JWT tokens (generate with `openssl rand -base64 32`)
- **JWT_SECRET_KEY**: Another secure key for JWT signing
- Other configuration values as needed for your environment

#### 5. Start Database and Services
```bash
# Start PostgreSQL, Redis, and Caddy
docker compose up -d db redis caddy

# Wait for database to be ready (takes ~30 seconds)
sleep 30

# Verify services are running
docker compose ps
```

#### 6. Initialize Database
```bash
# Run database migrations
uv run alembic upgrade head

# Verify database setup
uv run python -c "from app.core.database import get_engine; print('Database connection successful!')"
```

#### 7. Start the Application

**Option A: Using UV (Recommended for Development)**
```bash
# Start the application
uv run python -m app.main

# The app will be available at:
# - http://localhost:8080 (direct access)
# - http://localhost (via Caddy proxy)
```

**Option B: Using Docker (Full Container Setup)**
```bash
# Stop the local app if running, then start full stack
docker compose up -d

# View logs
docker compose logs -f app
```

#### 8. Verify Installation
Open your browser and navigate to:
- **Main Application**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

### Quick Development Setup

For rapid development setup, use this one-liner:
```bash
git clone https://github.com/your-username/iam-dashboard.git && \
cd iam-dashboard && \
uv sync && \
cp .env.example .env && \
echo "⚠️ Don't forget to edit .env with your API keys!" && \
docker compose up -d db redis && \
sleep 30 && \
uv run alembic upgrade head && \
uv run python -m app.main
```

### Troubleshooting

**Database Connection Issues:**
```bash
# Check if PostgreSQL is running
docker compose ps db

# View database logs
docker compose logs db

# Reset database
docker compose down -v && docker compose up -d db
```

**Missing Dependencies:**
```bash
# Reinstall dependencies
uv sync --reinstall

# Check for missing system dependencies
uv run python -c "import cv2, tesseract, fitz; print('All imports successful')"
```

**Port Conflicts:**
```bash
# Check what's using port 8080
lsof -i :8080

# Use different port
uv run python -m app.main --port 8081
```

## Development

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

# Type checking
uv run mypy app/

# Database migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

### Project Structure

```
app/
├── agents/           # Autonomous agents using Agno
├── api/             # FastAPI endpoints
├── core/            # Core infrastructure
├── models/          # SQLAlchemy models
├── repositories/    # Data access layer
├── services/        # Business logic
├── tools/           # Agent tools and utilities
├── plugins/         # Agent plugins
├── ui_components/   # NiceGUI components
└── utils/           # Utility functions
```

### Environment Variables

Copy the example file and configure your environment:

```bash
cp .env.example .env
# Then edit .env with your specific values
```

Key variables to configure:
- `GEMINI_API_KEY` - Your Google Gemini API key
- `SECRET_KEY` - JWT secret for authentication  
- `JWT_SECRET_KEY` - Additional JWT secret
- `DATABASE_URL` - Database connection string (defaults work for Docker setup)
- `REDIS_URL` - Redis connection string (defaults work for Docker setup)

## Testing

The project includes comprehensive testing:

- **Unit Tests**: `tests/unit/` - Individual components and agents
- **Integration Tests**: `tests/integration/` - Agent workflows and API
- **E2E Tests**: `tests/e2e/` - Full user workflows
- **Performance Tests**: `tests/performance/` - Agent benchmarking

```bash
# Run all tests
uv run pytest

# Run specific test types
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/e2e/

# Generate coverage report
uv run pytest --cov=app --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/feature-name`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `uv run pytest`
6. Lint your code: `uv run ruff check --fix .`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For documentation and technical details, see the `docs/` directory:
- `docs/architecture/` - Architecture decisions and design
- `docs/prd/` - Product requirements
- `docs/reference/` - Technical references