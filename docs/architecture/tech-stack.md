# Tech Stack

This is the DEFINITIVE technology selection for the entire project. This table serves as the single source of truth - all development must use these exact versions based on the PRD requirements and architectural decisions.

## Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| Frontend Language | TypeScript | >=5.9 | Type-safe frontend development | Essential for enterprise-grade code quality and developer productivity across team |
| Frontend Framework | Next.js | >=15.4.5 | Full-stack React framework with App Router | Modern SSR/SSG capabilities, excellent performance, built-in optimization for professional UX |
| UI Component Library | shadcn/ui | >=2.9.3 | Accessible, customizable component system | Perfect balance of design quality and customization flexibility for branding system |
| State Management | TanStack Query + Zustand | >=5.84.0 + >=5.0.7 | Server and client state management | TanStack Query for server state caching, Zustand for lightweight client state, avoids Redux complexity |
| Backend Language | Python | >=3.13.5 | Backend API and agent development | Excellent AI/ML ecosystem for future agent capabilities, mature FastAPI integration |
| Backend Framework | FastAPI | >=0.116.1 | High-performance async API framework | Industry-leading performance, automatic OpenAPI docs, excellent typing integration |
| Backend Validation | Pydantic | >=2.11.7 | Data validation and settings management | Integrates seamlessly with FastAPI, uses Python type hints for robust validation |
| CPF/CNPJ Validation | cnpj-cpf-validator | >=0.1.2 | Brazilian document validation | Validates CPF and CNPJ numbers with proper check digit algorithm, supports formatting |
| Web Server | Gunicorn + Uvicorn | >=23.0.0 + >=0.35.0 | ASGI server and process manager | Gunicorn manages Uvicorn workers for production-grade performance and reliability |
| API Style | REST API | OpenAPI >=3.1.1 | RESTful HTTP APIs with OpenAPI specification | Proven, well-understood pattern optimal for multi-agent communication and client integrations |
| Database | PostgreSQL | >=17.5 | Primary data store with ACID compliance | Required for agent data consistency, excellent performance, pgvector ready for AI features |
| DB Migration | Alembic | >=1.16.4 | Database schema migrations | Industry standard for SQLAlchemy/SQLModel, enables version-controlled database changes |
| Cache | Redis | >=8.0.3 | Session cache and permission validation | Critical for <10ms permission checks, session management, real-time features |
| File Storage | Local VPS Storage + S3-compatible | Local + Optional S3 | Client files, backups, static assets | Local storage with optional S3 backup for cost optimization |
| Authentication | OAuth2 + JWT + TOTP | RFC standards | Secure authentication with 2FA | Enterprise security requirements, industry standard, supports custom branding |
| Frontend Testing | Vitest + React Testing Library | >=3.2.4 + >=16.3.0 | Unit and integration testing | Fast, modern testing with excellent React component testing capabilities |
| Backend Testing | pytest + pytest-asyncio | >=8.4.1 + >=1.1.0 | Unit, integration, and E2E testing | Comprehensive Python testing ecosystem, async support for FastAPI |
| E2E Testing | Playwright | >=1.54 | Browser automation and E2E testing | Cross-browser support, excellent debugging, handles complex permission scenarios |
| Build Tool | Vite (via Next.js) | >=7.0.6 | Frontend build and bundling | Built into Next.js 15, fastest build times, excellent HMR, optimal for development |
| Bundler | Turbo (Turborepo) | >=1.10 | Monorepo build optimization | Essential for efficient concurrent implementation development |
| Deployment Tool | SSH + systemd | Ubuntu 24.x | Automated VPS deployment and service management | Simple, reliable deployment without API dependencies, cost-effective for Brazilian market |
| CI/CD | GitHub Actions | >=2.326.0 | Automated testing and deployment | Integrated with repository, excellent ecosystem, supports custom implementation workflows |
| Monitoring | Grafana + Prometheus | >=12.1.0 + >=3.5.0 | System metrics and application monitoring | Open source, excellent for multi-client monitoring, cost-effective |
| Logging | Structured Logging (JSON) | N/A | Application logging and debugging | JSON format for log aggregation, compatible with standard log analysis tools |
| CSS Framework | Tailwind CSS | >=4.1.11 | Utility-first CSS with design system | Perfect for custom branding system, excellent performance, developer productivity |

---
