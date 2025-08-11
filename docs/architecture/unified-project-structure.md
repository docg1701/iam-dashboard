# Unified Project Structure

The monorepo structure accommodates both frontend and backend development with shared tooling, coordinated deployments, and clear separation of concerns optimized for the custom implementation service model:

```plaintext
multi-agent-iam-dashboard/
├── .github/                    # CI/CD workflows and automation
│   └── workflows/
│       ├── ci.yaml            # Continuous integration pipeline
│       ├── deploy-staging.yaml # Staging deployment automation
│       ├── deploy-production.yaml # Production deployment pipeline
│       └── quality-checks.yaml # Code quality and security scans
├── apps/                       # Application packages
│   ├── web/                    # Next.js 15 Frontend Application
│   │   ├── src/
│   │   │   ├── app/           # Next.js App Router pages
│   │   │   ├── components/    # Reusable UI components
│   │   │   ├── hooks/         # Custom React hooks
│   │   │   ├── services/      # API client services
│   │   │   ├── stores/        # Zustand state management
│   │   │   ├── styles/        # Global styles and themes
│   │   │   └── utils/         # Frontend utilities
│   │   ├── public/            # Static assets and branding
│   │   ├── tests/             # Frontend testing
│   │   ├── next.config.js     # Next.js configuration
│   │   ├── tailwind.config.js # Tailwind CSS configuration
│   │   ├── tsconfig.json      # TypeScript configuration
│   │   └── package.json       # Frontend dependencies
│   └── api/                   # FastAPI Backend Application
│       ├── src/
│       │   ├── main.py        # FastAPI application entry
│       │   ├── core/          # Core application configuration
│       │   ├── api/           # API route controllers
│       │   ├── services/      # Business logic services
│       │   ├── models/        # SQLModel data models
│       │   ├── schemas/       # Pydantic request/response schemas
│       │   ├── middleware/    # Custom middleware
│       │   ├── agents/        # Independent agent implementations
│       │   └── utils/         # Backend utilities
│       ├── tests/             # Backend testing
│       ├── alembic/           # Database migrations
│       ├── requirements.txt   # Python dependencies
│       ├── pyproject.toml     # Python project configuration
│       └── Dockerfile         # Backend container definition
├── packages/                  # Shared packages across applications
│   ├── shared/                # Shared types and utilities
│   │   ├── src/
│   │   │   ├── types/         # TypeScript interfaces
│   │   │   ├── constants/     # Shared constants
│   │   │   └── utils/         # Shared utilities
│   │   ├── package.json       # Shared package dependencies
│   │   └── tsconfig.json      # Shared TypeScript config
│   ├── ui/                    # Shared UI component library
│   │   ├── src/
│   │   │   ├── components/    # Reusable components
│   │   │   ├── hooks/         # Shared React hooks
│   │   │   └── styles/        # Component styles
│   │   ├── package.json       # UI package dependencies
│   │   └── tsconfig.json      # UI TypeScript config
│   └── config/                # Shared configuration
│       ├── eslint/            # ESLint configurations
│       ├── typescript/        # TypeScript configurations
│       ├── jest/              # Jest test configurations
│       └── prettier/          # Prettier configurations
├── deployment/                # SSH deployment configurations
│   ├── scripts/               # Deployment automation scripts
│   │   ├── setup-vps.sh       # Initial VPS setup script
│   │   ├── deploy-app.sh      # Application deployment
│   │   ├── backup-db.sh       # Database backup script
│   │   └── health-check.sh    # Service health validation
│   ├── systemd/               # systemd service configurations
│   │   ├── iam-frontend.service    # Frontend service
│   │   ├── iam-backend.service     # Backend service
│   │   └── iam-agents.service      # Agents service
│   └── configs/               # Server configuration templates
│       ├── caddy/             # Caddy reverse proxy configs
│       ├── postgresql/        # PostgreSQL configurations
│       └── redis/             # Redis configurations
│   ├── docker/                # Docker configurations
│   │   ├── docker-compose.yml # Local development stack
│   │   ├── docker-compose.prod.yml # Production stack
│   │   ├── Dockerfile.frontend # Frontend container
│   │   └── Dockerfile.backend # Backend container
│   └── monitoring/            # Monitoring configurations
│       ├── prometheus/        # Prometheus configuration
│       ├── grafana/           # Grafana dashboards
│       └── loki/              # Log aggregation config
├── scripts/                   # Build and deployment scripts
│   ├── setup.sh              # Development environment setup
│   ├── build.sh              # Production build script
│   ├── deploy.sh             # Deployment automation
│   ├── test.sh               # Test execution script
│   ├── backup.sh             # Database backup script
│   └── monitoring.sh         # Monitoring setup script
├── docs/                     # Documentation
│   ├── prd.md                # Product Requirements Document
│   ├── front-end-spec.md     # Frontend Specification
│   ├── architecture.md       # This architecture document
│   ├── api/                  # API documentation
│   ├── deployment/           # Deployment guides
│   └── user-guides/          # User documentation
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore patterns
├── .nvmrc                    # Node.js version specification
├── package.json              # Root package.json for workspaces
├── turbo.json                # Turborepo build configuration
├── tsconfig.json             # Root TypeScript configuration
├── docker-compose.yml        # Local development services
├── CLAUDE.md                 # Claude Code development guidelines
└── README.md                 # Project documentation
```

---
