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
- **Node.js 18+** for frontend development
- **Python 3.11+** with **UV** package manager
- **Docker** and **Docker Compose**
- **Terraform** and **Ansible** for deployment

### Quick Start

```bash
# Clone repository
git clone https://github.com/docg1701/iam-dashboard.git
cd iam-dashboard

# Start development services
docker-compose up --build

# Frontend (separate terminal)
cd frontend
npm install
npm run dev

# Backend (separate terminal)
cd backend
uv venv && source .venv/bin/activate
uv sync
uv run uvicorn src.main:app --reload
```

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