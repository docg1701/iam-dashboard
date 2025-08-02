# Multi-Agent IAM Dashboard - Development Commands
.PHONY: help setup dev build test lint format clean docker-up docker-down docker-logs db-migrate db-migration type-check

# Default target
help: ## Show this help message
	@echo "Multi-Agent IAM Dashboard - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Setup and Installation
setup: ## Install all dependencies and setup development environment
	@echo "🔧 Setting up development environment..."
	npm install
	cd apps/backend && uv sync
	@echo "✅ Setup complete!"

# Development
dev: ## Start development servers (frontend and backend)
	@echo "🚀 Starting development servers..."
	npm run dev

dev-frontend: ## Start only frontend development server
	@echo "🚀 Starting frontend development server..."
	npm run dev:frontend

dev-backend: ## Start only backend development server
	@echo "🚀 Starting backend development server..."
	npm run dev:backend

# Building
build: ## Build all applications
	@echo "🏗️ Building all applications..."
	npm run build

build-frontend: ## Build frontend application
	@echo "🏗️ Building frontend application..."
	npm run build:frontend

build-backend: ## Build backend application
	@echo "🏗️ Building backend application..."
	npm run build:backend

# Testing
test: ## Run all tests
	@echo "🧪 Running all tests..."
	npm run test

test-frontend: ## Run frontend tests
	@echo "🧪 Running frontend tests..."
	npm run test:frontend

test-backend: ## Run backend tests
	@echo "🧪 Running backend tests..."
	npm run test:backend

test-e2e: ## Run end-to-end tests
	@echo "🧪 Running E2E tests..."
	npm run test:e2e

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	npm run test:frontend -- --coverage
	cd apps/backend && uv run pytest --cov=src --cov-report=html

# Code Quality
lint: ## Run linting for all code
	@echo "🔍 Linting all code..."
	npm run lint

lint-frontend: ## Run frontend linting
	@echo "🔍 Linting frontend code..."
	npm run lint:frontend

lint-backend: ## Run backend linting
	@echo "🔍 Linting backend code..."
	npm run lint:backend

format: ## Format all code
	@echo "🎨 Formatting all code..."
	npm run format

format-frontend: ## Format frontend code
	@echo "🎨 Formatting frontend code..."
	npm run format:frontend

format-backend: ## Format backend code
	@echo "🎨 Formatting backend code..."
	npm run format:backend

type-check: ## Run TypeScript type checking
	@echo "🔍 Running type checks..."
	npm run type-check

# Database
db-migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	npm run db:migrate

db-migration: ## Create new database migration
	@echo "🗄️ Creating new database migration..."
	@read -p "Migration name: " name; \
	cd apps/backend && uv run alembic revision --autogenerate -m "$$name"

db-reset: ## Reset database (WARNING: destructive)
	@echo "⚠️ Resetting database..."
	@read -p "Are you sure? This will delete all data. (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker compose down postgres; \
		docker volume rm iam-dashboard_postgres_data || true; \
		docker compose up -d postgres; \
		sleep 5; \
		make db-migrate; \
	else \
		echo "Database reset cancelled."; \
	fi

# Docker
docker-up: ## Start all Docker services
	@echo "🐳 Starting Docker services..."
	docker compose up -d

docker-down: ## Stop all Docker services
	@echo "🐳 Stopping Docker services..."
	docker compose down

docker-logs: ## Show Docker service logs
	@echo "🐳 Showing Docker logs..."
	docker compose logs -f

docker-rebuild: ## Rebuild and restart Docker services
	@echo "🐳 Rebuilding Docker services..."
	docker compose down
	docker compose build --no-cache
	docker compose up -d

# Cleanup
clean: ## Clean all node_modules and build artifacts
	@echo "🧹 Cleaning up..."
	npm run clean
	cd apps/backend && rm -rf .uv-cache __pycache__ .pytest_cache
	docker system prune -f

clean-all: ## Clean everything including Docker volumes
	@echo "🧹 Deep cleaning..."
	make clean
	docker compose down -v
	docker volume prune -f

# Quality Gates
check: ## Run all quality checks (lint, type-check, test)
	@echo "✅ Running all quality checks..."
	make lint
	make type-check
	make test

ci: ## Run CI pipeline locally
	@echo "🔄 Running CI pipeline..."
	make setup
	make check
	make build

# Development Utilities
logs: ## Show all application logs
	@echo "📋 Showing application logs..."
	make docker-logs

status: ## Show status of all services
	@echo "📊 Service status:"
	docker compose ps

shell-backend: ## Open shell in backend container
	@echo "🐚 Opening backend shell..."
	docker compose exec backend bash

shell-db: ## Open PostgreSQL shell
	@echo "🐚 Opening database shell..."
	docker compose exec postgres psql -U postgres -d dashboard

# Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@echo "Documentation generation not yet implemented"

.DEFAULT_GOAL := help