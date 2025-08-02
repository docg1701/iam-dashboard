# Unified Project Structure

Comprehensive monorepo structure accommodating both frontend and backend while supporting the custom implementation service model:

```
multi-agent-iam-dashboard/
├── .github/                              # CI/CD workflows and issue templates
├── apps/                                 # Main application packages
│   ├── frontend/                         # Next.js 15 application
│   │   ├── src/
│   │   │   ├── app/                      # Next.js App Router
│   │   │   ├── components/               # React components
│   │   │   ├── lib/                      # Utilities & configurations
│   │   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── store/                    # Client state management (Zustand)
│   │   │   └── types/                    # TypeScript type definitions
│   │   ├── public/                       # Static assets
│   │   ├── tests/                        # Frontend tests
│   │   ├── next.config.js                # Next.js configuration
│   │   ├── tailwind.config.js            # Tailwind CSS configuration
│   │   └── package.json                  # Frontend dependencies
│   └── backend/                          # FastAPI application
│       ├── src/
│       │   ├── main.py                   # FastAPI entry point
│       │   ├── core/                     # Core system modules
│       │   ├── api/                      # REST API endpoints
│       │   ├── services/                 # Business logic layer
│       │   ├── models/                   # SQLModel database models
│       │   ├── agents/                   # Agno agent implementations
│       │   ├── schemas/                  # Pydantic request/response schemas
│       │   └── utils/                    # Utility functions
│       ├── alembic/                      # Database migrations
│       ├── pyproject.toml                # UV dependencies and configuration
│       └── Dockerfile                    # Backend container definition
├── packages/                             # Shared packages
│   ├── shared/                           # Shared utilities and types
│   ├── ui/                               # Shared UI components (if needed)
│   └── config/                           # Shared configuration
├── infrastructure/                       # Infrastructure as Code
│   ├── terraform/                        # VPS provisioning
│   ├── ansible/                          # Configuration management
│   └── docker/                           # Docker configurations
├── scripts/                              # Build and deployment scripts
├── docs/                                 # Project documentation
├── package.json                          # Root package.json with workspaces
├── docker-compose.yml                    # Development docker compose
├── Makefile                              # Common development commands
├── CLAUDE.md                             # Claude development guidelines
└── README.md                             # Project overview and setup
```

### Monorepo Configuration

**Root Package.json with Workspaces:**
```json
{
  "name": "multi-agent-iam-dashboard",
  "version": "1.0.0",
  "private": true,
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "dev": "concurrently \"npm run dev:backend\" \"npm run dev:frontend\"",
    "build": "npm run build --workspaces",
    "test": "npm run test --workspaces",
    "lint": "npm run lint --workspaces"
  }
}
```
