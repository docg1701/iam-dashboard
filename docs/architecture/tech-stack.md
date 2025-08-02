# Tech Stack

This is the **DEFINITIVE technology selection** for the entire project. This table serves as the single source of truth - all development must use these exact versions and technologies.

### Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| Frontend Language | TypeScript | >=5.9 | Type-safe frontend development | Prevents runtime errors, enables better IDE support, aligns with enterprise development standards |
| Frontend Framework | Next.js | >=15.4.5 | React-based fullstack framework | App Router for modern routing, React Server Components, built-in optimization, excellent shadcn/ui compatibility |
| UI Component Library | shadcn/ui | >=2.9.3 | Customizable component system | Perfect for brand customization via CSS variables, Tailwind integration, accessibility built-in |
| State Management | TanStack Query + Zustand | >=5.84.0 + >=5.0.7 | Server and client state management | TanStack Query for server state caching, Zustand for lightweight client state, avoids Redux complexity |
| Backend Language | Python | >=3.13.5 | Backend API development | Excellent FastAPI support, mature ecosystem, strong typing with Pydantic integration |
| Backend Framework | FastAPI | >=0.116.1 | Modern Python web framework | Automatic OpenAPI generation, async support, Pydantic integration, excellent performance |
| Backend Validation | Pydantic | >=2.11.7 | Data validation and settings management | Integrates seamlessly with FastAPI, uses Python type hints for robust validation |
| Web Server | Gunicorn + Uvicorn | >=23.0.0 + >=0.35.0 | ASGI server and process manager | Gunicorn manages Uvicorn workers for production-grade performance and reliability |
| API Style | REST + OpenAPI 3.0 | >=3.1.1 | API architecture and documentation | Standard REST for simplicity, OpenAPI for automatic documentation, easier than GraphQL for this use case |
| Database | PostgreSQL | >=17.5 | Primary data storage with vector support | ACID compliance, excellent JSON support, pgvector extension for future AI features, mature ecosystem |
| DB Migration | Alembic | >=1.16.4 | Database schema migrations | Industry standard for SQLAlchemy/SQLModel, enables version-controlled database changes |
| Cache | Redis | >=8.0.3 | Session storage and caching | FastAPI session management, agent task queuing, improves response times for frequent queries |
| Async Task Queue | Celery | >=5.5.0 | Asynchronous task processing | Handles long-running tasks without blocking API responses, ensures system scalability |
| File Storage | Local FS + S3 Compatible | N/A | File uploads and static assets | Local storage for development, S3-compatible (DigitalOcean Spaces) for production backups |
| Authentication | FastAPI Security + JWT | OAuth2 | Authentication and authorization | Industry standard OAuth2 + JWT, integrates with FastAPI security middleware, supports 2FA |
| Frontend Testing | Vitest + Testing Library | >=3.2.4 + >=16.3.0 | Component and integration testing | Faster than Jest, excellent TypeScript support, React Testing Library for user-centric testing |
| Backend Testing | pytest + pytest-asyncio | >=8.4.1 + >=1.1.0 | API and business logic testing | Python standard for testing, async support for FastAPI, excellent fixture system |
| E2E Testing | Playwright | >=1.54 | End-to-end workflow testing | Best-in-class browser automation, excellent TypeScript support, reliable for CI/CD |
| Build Tool | Vite (via Next.js) | >=7.0.6 | Frontend build and bundling | Built into Next.js 15, fastest build times, excellent HMR, optimal for development |
| Bundler | Turbopack (Next.js 15) | Latest | Production optimization | Next.js 15 default bundler, faster than Webpack, optimized for React Server Components |
| IaC Tool | Terraform | >=1.12.1 | Infrastructure provisioning | Industry standard for VPS provisioning, excellent provider ecosystem, declarative approach |
| CI/CD | GitHub Actions | >=2.327.1 | Automated testing and deployment | Integrated with GitHub, excellent ecosystem, supports parallel testing across services |
| Monitoring | Grafana + Prometheus | >=12.1.0 + >=3.5.0 | Application and infrastructure monitoring | Open source monitoring stack, excellent alerting, cost-effective for multi-instance monitoring |
| Logging | Structured Logging (JSON) | N/A | Application logging and debugging | JSON format for log aggregation, compatible with standard log analysis tools |
| CSS Framework | Tailwind CSS | >=4.1.11 | Utility-first styling with theming | Perfect shadcn/ui integration, CSS variables for brand customization, rapid development |
