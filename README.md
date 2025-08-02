# IAM Dashboard - Custom Implementation Service

> **Custom AI automation infrastructure delivered in 30 days with complete visual customization and dedicated VPS deployment.**

## Overview

IAM Dashboard is a custom implementation service that delivers dedicated multi-agent AI automation infrastructure tailored to each client's specific needs. Each implementation includes complete visual branding, dedicated VPS deployment, and specialized agent configuration.

## Key Features

- **🎨 Custom Branding**: Complete visual identity integration (logos, colors, typography)
- **🖥️ Dedicated VPS**: Single-tenant infrastructure with complete data isolation
- **🤖 AI Agents**: Autonomous agents powered by the Agno framework
- **⚡ Rapid Deployment**: Full implementation in 3-4 weeks via automated scripts
- **🛠️ Managed Service**: Ongoing maintenance, updates, and 24/7 monitoring
- **📱 100% Responsive**: Mobile-first design across all devices

## Target Market

- **Growing businesses** (50-500 employees, $5M-$100M revenue)
- **Service-based companies** requiring professional branded interfaces
- **Organizations** needing custom workflows and dedicated infrastructure

## Technology Stack

### Backend
- **FastAPI** + **SQLModel** + **PostgreSQL**
- **Agno** multi-agent framework
- **Celery** + **Redis** for async processing

### Frontend
- **Next.js 15** + **React 19** + **TypeScript**
- **shadcn/ui** + **Tailwind CSS** for custom theming

### Infrastructure
- **Docker** + **Docker Compose**
- **Terraform** for infrastructure provisioning
- **Ansible** for configuration management
- **Caddy** reverse proxy with automatic HTTPS

## MVP Agent

**Client Management Agent**: Complete CRUD operations with SSN validation, search capabilities, and bulk operations. Serves as the foundation for demonstrating multi-agent architecture.

## Pricing Model

- **Setup Fee**: $3,500 (one-time)
- **Monthly Service**: $2,000/month
- **Includes**: Infrastructure, maintenance, updates, support

## Project Structure

```
/
├── frontend/          # Next.js 15 application
├── backend/           # FastAPI application
├── infrastructure/    # Terraform configurations
├── deployment/        # Ansible playbooks
├── docs/             # Project documentation
├── docker-compose.yml
└── CLAUDE.md         # Development guidelines
```

## Development

### Prerequisites
- **Node.js 20+** and **npm 10+**
- **Python 3.13.5+** with **UV** package manager
- **Docker** and **Docker Compose**
- **Terraform** and **Ansible** for deployment

### Quick Start

```bash
# Install all dependencies
make setup

# Start development environment
make docker-up
make dev

# Run database migrations
make db-migrate
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs

### Development Commands

```bash
# Development
make dev                   # Start both frontend and backend
make dev-frontend         # Start only frontend
make dev-backend          # Start only backend

# Testing
make test                 # Run all tests
make test-coverage        # Run tests with coverage (>80% required)

# Code Quality
make lint                 # Lint all code
make format              # Format all code
make type-check          # Run TypeScript checks

# Database
make db-migrate          # Run database migrations
make db-migration        # Create new migration

# Docker
make docker-up          # Start all services
make docker-down        # Stop all services
```

### Technology Stack Details

#### Backend
- **FastAPI** 0.116.1+ - Modern Python web framework
- **SQLModel** 0.0.21+ - Database ORM combining SQLAlchemy + Pydantic  
- **PostgreSQL** 17.5+ with pgvector extension
- **Pydantic** 2.11.7+ - Data validation and settings management
- **Alembic** 1.16.4+ - Database migrations
- **pytest** 8.4.1+ with 92.75% code coverage

#### Frontend
- **Next.js** 15.4.5+ with App Router
- **React** 19+ - Latest features
- **TypeScript** 5.9+ in strict mode
- **shadcn/ui** 2.9.3+ - Customizable component library
- **Tailwind CSS** 4.1.11+ - Utility-first CSS
- **Vitest** 3.2.4+ - Fast testing framework

### Code Quality Standards
- **Backend**: Ruff formatting + mypy type checking
- **Frontend**: ESLint + TypeScript strict mode
- **Coverage**: 80% minimum (enforced)
- **Testing**: pytest (backend) + Vitest (frontend)

## Implementation Process

1. **Discovery** (Week 1): Requirements gathering and workflow analysis
2. **Customization** (Week 2): Visual branding and configuration
3. **Deployment** (Week 3): VPS provisioning and stack deployment
4. **Delivery** (Week 4): Testing, training, and go-live

## Documentation

- **[Project Brief](docs/brief.md)**: Complete business requirements and technical specifications
- **[Development Guidelines](CLAUDE.md)**: Comprehensive development guide for contributors

## Architecture

**Custom Implementation Service** with dedicated VPS instances per client. Independent AI agents communicate through shared PostgreSQL database while maintaining complete data isolation and unlimited customization capabilities.

## License

Private project - All rights reserved

---

**Status**: In Development | **Target**: MVP completion Q1 2025