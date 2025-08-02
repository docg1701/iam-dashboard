# Development Workflow

Complete development setup and workflow for efficient fullstack development:

### Local Development Setup

**Prerequisites Installation:**
```bash
#!/bin/bash
# scripts/setup-dev.sh - Development environment setup

echo "🚀 Setting up Multi-Agent IAM Dashboard development environment..."

# Check for required tools
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        exit 1
    else
        echo "✅ $1 is installed"
    fi
}

check_tool "node"
check_tool "npm" 
check_tool "python3"
check_tool "docker"
check_tool "docker-compose"

# Install UV if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Install dependencies
npm install
cd apps/frontend && npm install && cd ../..
cd apps/backend && uv sync && cd ../..

# Setup environment files
cp .env.example .env
cp apps/frontend/.env.local.example apps/frontend/.env.local
cp apps/backend/.env.example apps/backend/.env

# Start Docker services
docker-compose up -d postgres redis

# Run database migrations
cd apps/backend && uv run alembic upgrade head && cd ../..

echo "✅ Development environment setup complete!"
```

### Environment Configuration

**Frontend Environment Variables (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/v1
NEXT_PUBLIC_APP_NAME="IAM Dashboard"
NEXT_PUBLIC_ENABLE_2FA=true
NEXT_PUBLIC_MAX_FILE_SIZE=52428800
```

**Backend Environment Variables (.env):**
```bash
DEBUG=true
SECRET_KEY="your-super-secret-development-key"
DATABASE_URL="postgresql://dashboard_user:dashboard_pass@localhost:5432/dashboard_dev"
REDIS_URL="redis://localhost:6379/0"
OPENAI_API_KEY="your-openai-api-key"
```

### Development Commands

```bash
# Start all development services
npm run dev

# Start frontend only
npm run dev:frontend

# Start backend only  
npm run dev:backend

# Run all tests
npm run test

# Type checking
npm run type-check

# Linting and formatting
npm run lint
npm run lint:fix

# Database operations
npm run migrate
npm run migrate:create
```
