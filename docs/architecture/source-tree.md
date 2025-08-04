# Source Tree Architecture

*Last Updated: August 2025*

This document defines the **source tree organization** and **file structure standards** for the Multi-Agent IAM Dashboard project. It serves as the canonical reference for project organization, directory structure, and file naming conventions throughout all development phases.

## Overview

The Multi-Agent IAM Dashboard uses a **monorepo architecture** with npm workspaces to organize the fullstack application, independent agents, and deployment infrastructure. This structure supports the custom implementation service model while maintaining clear separation of concerns.

## Root Directory Structure

```
multi-agent-iam-dashboard/
├── .github/                              # CI/CD workflows and issue templates
├── apps/                                 # Main application packages
│   ├── frontend/                         # Next.js 15 application
│   └── backend/                          # FastAPI application
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

## Frontend Application Structure

```
apps/frontend/
├── src/
│   ├── app/                          # Next.js 15 App Router
│   │   ├── (auth)/                   # Route group for authentication
│   │   │   ├── login/
│   │   │   │   └── page.tsx          # Login page
│   │   │   └── layout.tsx            # Auth layout
│   │   ├── (dashboard)/              # Protected dashboard routes
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx          # Dashboard home
│   │   │   ├── clients/
│   │   │   │   ├── page.tsx          # Client list
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx      # New client form
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx      # Client detail
│   │   │   │       └── edit/
│   │   │   │           └── page.tsx  # Edit client
│   │   │   ├── users/
│   │   │   │   ├── page.tsx          # User management
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx      # User profile
│   │   │   ├── agents/
│   │   │   │   ├── agent1/
│   │   │   │   │   └── page.tsx      # Agent 1 interface
│   │   │   │   ├── agent2/
│   │   │   │   │   └── page.tsx      # Agent 2 interface
│   │   │   │   └── agent3/
│   │   │   │       └── page.tsx      # Agent 3 interface
│   │   │   ├── system/
│   │   │   │   ├── page.tsx          # System settings
│   │   │   │   ├── branding/
│   │   │   │   │   └── page.tsx      # Brand customization
│   │   │   │   └── permissions/
│   │   │   │       └── page.tsx      # Permission management
│   │   │   └── layout.tsx            # Dashboard layout
│   │   ├── globals.css               # Global styles + CSS variables
│   │   ├── layout.tsx                # Root layout with providers
│   │   └── page.tsx                  # Public homepage
│   ├── components/                   # Reusable UI components
│   │   ├── ui/                       # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── table.tsx
│   │   │   ├── form.tsx
│   │   │   ├── select.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   └── textarea.tsx
│   │   ├── forms/                    # Complex form components
│   │   │   ├── ClientRegistrationForm.tsx
│   │   │   ├── UserCreateForm.tsx
│   │   │   ├── UserEditForm.tsx
│   │   │   ├── TwoFactorForm.tsx
│   │   │   └── LoginFormWrapper.tsx
│   │   ├── layout/                   # Layout components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Navigation.tsx
│   │   │   └── Footer.tsx
│   │   ├── common/                   # Common components
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── PasswordStrengthIndicator.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   └── features/                 # Feature-specific components
│   │       ├── auth/
│   │       │   ├── LoginForm.tsx
│   │       │   ├── TwoFactorSetup.tsx
│   │       │   └── AuthProvider.tsx
│   │       ├── clients/
│   │       │   ├── ClientList.tsx
│   │       │   ├── ClientDetail.tsx
│   │       │   ├── ClientSearch.tsx
│   │       │   └── BulkOperations.tsx
│   │       ├── users/
│   │       │   ├── UserList.tsx
│   │       │   ├── UserProfile.tsx
│   │       │   └── RoleSelector.tsx
│   │       ├── agents/
│   │       │   ├── AgentCard.tsx
│   │       │   ├── AgentStatus.tsx
│   │       │   └── AgentSettings.tsx
│   │       └── branding/
│   │           ├── ColorPicker.tsx
│   │           ├── LogoUpload.tsx
│   │           ├── ThemePreview.tsx
│   │           └── BrandingPanel.tsx
│   ├── lib/                          # Utilities & configurations
│   │   ├── utils.ts                  # General utility functions
│   │   ├── auth.ts                   # Authentication utilities
│   │   ├── api.ts                    # API client configuration
│   │   ├── env.ts                    # Environment validation
│   │   ├── constants.ts              # Application constants
│   │   ├── validations.ts            # Zod validation schemas
│   │   └── formatting.ts             # Data formatting utilities
│   ├── hooks/                        # Custom React hooks
│   │   ├── use-auth.ts               # Authentication hook
│   │   ├── use-clients.ts            # Client management hook
│   │   ├── use-users.ts              # User management hook
│   │   ├── use-agents.ts             # Agent interaction hook
│   │   ├── use-branding.ts           # Branding customization hook
│   │   ├── use-toast.ts              # Toast notification hook
│   │   └── use-local-storage.ts      # Local storage hook
│   ├── store/                        # Client state management (Zustand)
│   │   ├── auth-store.ts             # Authentication state
│   │   ├── ui-store.ts               # UI state management
│   │   ├── client-store.ts           # Client data cache
│   │   └── branding-store.ts         # Branding configuration
│   ├── types/                        # TypeScript type definitions
│   │   ├── index.ts                  # Main type exports
│   │   ├── auth.ts                   # Authentication types
│   │   ├── clients.ts                # Client data types
│   │   ├── users.ts                  # User management types
│   │   ├── agents.ts                 # Agent interface types
│   │   ├── api.ts                    # API response types
│   │   └── branding.ts               # Branding system types
│   └── styles/                       # Additional styling files
│       ├── globals.css               # Global CSS styles
│       ├── components.css            # Component-specific styles
│       └── themes.css                # Theme variables
├── public/                           # Static assets
│   ├── images/
│   │   ├── logo.svg
│   │   ├── favicon.ico
│   │   ├── default-avatar.png
│   │   └── branding/
│   │       ├── logo-light.svg
│   │       └── logo-dark.svg
│   ├── fonts/
│   └── icons/
├── __tests__/                        # Frontend tests
│   ├── components/
│   │   ├── forms/
│   │   │   ├── ClientForm.test.tsx
│   │   │   └── UserForm.test.tsx
│   │   ├── common/
│   │   │   ├── Header.test.tsx
│   │   │   └── Sidebar.test.tsx
│   │   └── features/
│   │       ├── auth/
│   │       ├── clients/
│   │       └── branding/
│   ├── hooks/
│   │   ├── useAuth.test.ts
│   │   ├── useClients.test.ts
│   │   └── useBranding.test.ts
│   ├── stores/
│   │   ├── authStore.test.ts
│   │   ├── clientStore.test.ts
│   │   └── uiStore.test.ts
│   ├── utils/
│   │   ├── validation.test.ts
│   │   ├── formatting.test.ts
│   │   └── api-client.test.ts
│   ├── integration/
│   │   ├── auth-flow.test.tsx
│   │   ├── client-management.test.tsx
│   │   └── branding-system.test.tsx
│   └── setup/
│       ├── test-utils.tsx
│       ├── mocks/
│       └── fixtures/
├── next.config.ts                    # Next.js configuration
├── tailwind.config.js                # Tailwind CSS configuration
├── vitest.config.ts                  # Vitest test configuration
├── tsconfig.json                     # TypeScript configuration
├── package.json                      # Frontend dependencies
└── Dockerfile                        # Frontend container definition
```

## Backend Application Structure

```
apps/backend/
├── src/
│   ├── main.py                       # FastAPI application entry point
│   ├── core/                         # Core system modules
│   │   ├── __init__.py
│   │   ├── config.py                 # Environment configuration
│   │   ├── database.py               # Database connection and session management
│   │   ├── security.py               # Authentication and JWT handling
│   │   ├── exceptions.py             # Custom exception classes
│   │   ├── middleware.py             # Custom middleware (CORS, logging, etc.)
│   │   ├── password_security.py      # Password hashing and validation
│   │   └── permissions.py            # Permission system core
│   ├── api/                          # REST API routes
│   │   ├── __init__.py
│   │   └── v1/                       # API version 1
│   │       ├── __init__.py
│   │       ├── auth.py               # Authentication endpoints
│   │       ├── clients.py            # Client management endpoints
│   │       ├── users.py              # User management endpoints
│   │       ├── audit.py              # Audit trail endpoints
│   │       └── agents.py             # Agent interaction endpoints
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── client_service.py         # Client business logic
│   │   ├── user_service.py           # User management logic
│   │   ├── auth_service.py           # Authentication logic
│   │   └── audit_service.py          # Audit trail logic
│   ├── models/                       # SQLModel database models
│   │   ├── __init__.py
│   │   ├── base.py                   # Base model classes
│   │   ├── user.py                   # User model
│   │   ├── client.py                 # Client model
│   │   ├── audit.py                  # Audit log model
│   │   ├── permissions.py            # Permission models
│   │   └── agent_tables.py           # Agent-specific tables
│   ├── agents/                       # Agent implementations
│   │   ├── __init__.py
│   │   ├── agent1/                   # Client Management Agent
│   │   │   ├── __init__.py
│   │   │   ├── client_agent.py       # Main agent implementation
│   │   │   ├── models.py             # Agent-specific models
│   │   │   ├── schemas.py            # Agent request/response schemas
│   │   │   ├── services.py           # Agent business logic
│   │   │   └── utils.py              # Agent utilities
│   │   ├── agent2/                   # PDF Processing Agent
│   │   │   ├── __init__.py
│   │   │   ├── pdf_agent.py          # PDF processing agent
│   │   │   ├── models.py             # Document models
│   │   │   ├── vector_service.py     # Vector embedding service
│   │   │   └── processing.py         # PDF processing utilities
│   │   ├── agent3/                   # Report Generation Agent
│   │   │   ├── __init__.py
│   │   │   ├── report_agent.py       # Report generation agent
│   │   │   ├── models.py             # Report models
│   │   │   ├── templates.py          # Report templates
│   │   │   └── exporters.py          # Report export utilities
│   │   └── agent4/                   # Audio Recording Agent
│   │       ├── __init__.py
│   │       ├── audio_agent.py        # Audio processing agent
│   │       ├── models.py             # Audio models
│   │       ├── transcription.py      # Audio transcription
│   │       └── analysis.py           # Audio analysis
│   ├── schemas/                      # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── common.py                 # Common schemas (pagination, etc.)
│   │   ├── auth.py                   # Authentication schemas
│   │   ├── clients.py                # Client schemas
│   │   ├── users.py                  # User schemas
│   │   ├── audit.py                  # Audit schemas
│   │   └── permissions.py            # Permission schemas
│   └── utils/                        # Utility functions
│       ├── __init__.py
│       ├── validation.py             # Data validation utilities
│       ├── formatting.py             # Data formatting utilities
│       ├── seed_data.py              # Database seeding utilities
│       ├── audit.py                  # Audit logging utilities
│       ├── email.py                  # Email utilities
│       └── encryption.py             # Encryption utilities
├── alembic/                          # Database migrations
│   ├── versions/                     # Migration files
│   │   ├── 001_initial_migration.py
│   │   ├── 002_add_clients_table.py
│   │   ├── 003_add_permissions.py
│   │   └── 004_add_agent_tables.py
│   ├── env.py                        # Alembic configuration
│   └── alembic.ini                   # Alembic settings
├── tests/                            # Backend tests
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration
│   ├── factories.py                  # Test data factories
│   ├── unit/                         # Unit tests
│   │   ├── agents/
│   │   │   ├── agent1/
│   │   │   │   ├── test_services.py
│   │   │   │   ├── test_models.py
│   │   │   │   └── test_schemas.py
│   │   │   ├── agent2/
│   │   │   ├── agent3/
│   │   │   └── agent4/
│   │   ├── core/
│   │   │   ├── test_auth.py
│   │   │   ├── test_database.py
│   │   │   ├── test_security.py
│   │   │   ├── test_middleware.py
│   │   │   └── test_password_security.py
│   │   └── utils/
│   │       ├── test_validation.py
│   │       ├── test_audit.py
│   │       └── test_seed_data.py
│   ├── integration/                  # Integration tests
│   │   ├── test_auth_api.py
│   │   ├── test_client_api.py
│   │   ├── test_client_api_comprehensive.py
│   │   ├── test_client_integration.py
│   │   ├── test_client_service.py
│   │   ├── test_client_service_comprehensive.py
│   │   ├── test_client_service_update_delete.py
│   │   ├── test_user_service.py
│   │   ├── test_agent_communication.py
│   │   └── test_database_operations.py
│   └── fixtures/                     # Test fixtures
│       ├── sample_clients.json
│       ├── test_pdfs/
│       └── audio_samples/
├── pyproject.toml                    # UV dependencies and configuration
├── uv.lock                          # UV lock file
├── Dockerfile                        # Backend container definition
└── htmlcov/                          # Coverage reports
```

## Shared Packages Structure

```
packages/
├── shared/                           # Shared utilities and types
│   ├── src/
│   │   ├── types/
│   │   │   ├── index.ts              # Main type exports
│   │   │   ├── auth.ts               # Authentication types
│   │   │   ├── clients.ts            # Client data types
│   │   │   ├── users.ts              # User types
│   │   │   ├── agents.ts             # Agent types
│   │   │   ├── api.ts                # API types
│   │   │   └── permissions.ts        # Permission types
│   │   ├── utils/
│   │   │   ├── validation.ts         # Shared validation functions
│   │   │   ├── formatting.ts         # Data formatting utilities
│   │   │   └── constants.ts          # Shared constants
│   │   └── schemas/
│   │       ├── client.ts             # Client validation schemas
│   │       ├── user.ts               # User validation schemas
│   │       └── auth.ts               # Auth validation schemas
│   ├── package.json
│   └── tsconfig.json
├── ui/                               # Shared UI components (if needed)
│   ├── src/
│   │   ├── components/
│   │   └── styles/
│   └── package.json
└── config/                           # Shared configuration
    ├── src/
    │   ├── eslint/
    │   ├── prettier/
    │   └── typescript/
    └── package.json
```

## Infrastructure Structure

```
infrastructure/
├── terraform/                        # VPS provisioning
│   ├── main.tf                       # Main Terraform configuration
│   ├── variables.tf                  # Variable definitions
│   ├── outputs.tf                    # Output values
│   ├── providers.tf                  # Provider configurations
│   ├── modules/
│   │   ├── vps/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── dns/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── monitoring/
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
│   └── environments/
│       ├── staging/
│       │   ├── main.tf
│       │   └── terraform.tfvars
│       └── production/
│           ├── main.tf
│           └── terraform.tfvars
├── ansible/                          # Configuration management
│   ├── playbooks/
│   │   ├── deploy-client.yml         # Client deployment playbook
│   │   ├── setup-monitoring.yml      # Monitoring setup
│   │   ├── security-hardening.yml    # Security configuration
│   │   └── backup-setup.yml          # Backup configuration
│   ├── roles/
│   │   ├── docker/
│   │   │   ├── tasks/
│   │   │   ├── templates/
│   │   │   └── vars/
│   │   ├── nginx/
│   │   ├── postgresql/
│   │   └── monitoring/
│   ├── inventory/
│   │   ├── staging
│   │   └── production
│   └── group_vars/
│       ├── all.yml
│       ├── staging.yml
│       └── production.yml
└── docker/                           # Docker configurations
    ├── backend/
    │   ├── Dockerfile
    │   ├── Dockerfile.prod
    │   └── entrypoint.sh
    ├── frontend/
    │   ├── Dockerfile
    │   ├── Dockerfile.prod
    │   └── nginx.conf
    ├── postgres/
    │   ├── Dockerfile
    │   └── init-scripts/
    │       └── 01-create-extensions.sql
    └── monitoring/
        ├── prometheus/
        │   └── prometheus.yml
        └── grafana/
            ├── dashboards/
            └── provisioning/
```

## Documentation Structure

```
docs/
├── architecture/                     # Architecture documentation
│   ├── index.md                      # Architecture overview
│   ├── source-tree.md                # This document
│   ├── unified-project-structure.md  # Project structure guidance
│   ├── high-level-architecture.md    # System architecture
│   ├── tech-stack.md                 # Technology stack
│   ├── data-models.md                # Data models and schemas
│   ├── api-specification.md          # API documentation
│   ├── database-schema.md            # Database design
│   ├── components.md                 # Component architecture
│   ├── frontend-architecture.md      # Frontend specifics
│   ├── backend-architecture.md       # Backend specifics
│   ├── security-and-performance.md   # Security measures
│   ├── testing-strategy.md           # Testing approach
│   ├── deployment-architecture.md    # Deployment strategy
│   ├── monitoring-and-observability.md # Monitoring setup
│   ├── development-workflow.md       # Development process
│   ├── coding-standards.md           # Code standards
│   ├── error-handling-strategy.md    # Error handling
│   ├── permissions-architecture.md   # Permission system
│   ├── ui-design-system.md          # UI design system
│   ├── responsive-design.md          # Responsive design
│   ├── ux-specification.md          # UX specifications
│   └── developer-reference.md        # Developer reference
├── prd/                              # Product requirements
├── stories/                          # User stories
├── deployment/                       # Deployment guides
└── api/                              # API documentation
```

## E2E Tests Structure

```
tests/playwright/
├── auth/                             # Authentication tests
│   ├── login.spec.ts                 # Login flow tests
│   ├── two-factor.spec.ts            # 2FA tests
│   └── logout.spec.ts                # Logout tests
├── clients/                          # Client management tests
│   ├── client-creation.spec.ts       # Client creation flow
│   ├── client-search.spec.ts         # Search functionality
│   ├── client-editing.spec.ts        # Client editing
│   └── bulk-operations.spec.ts       # Bulk operations
├── agents/                           # Agent-specific tests
│   ├── pdf-processing.spec.ts        # PDF agent tests
│   ├── report-generation.spec.ts     # Report agent tests
│   └── audio-recording.spec.ts       # Audio agent tests
├── branding/                         # Custom branding tests
│   ├── theme-customization.spec.ts   # Theme customization
│   ├── asset-upload.spec.ts          # Asset upload
│   └── branding-deployment.spec.ts   # Branding deployment
├── admin/                            # Admin interface tests
│   ├── user-management.spec.ts       # User management
│   └── system-configuration.spec.ts  # System config
├── fixtures/                         # Test fixtures
│   ├── test-users.ts                 # Test user data
│   ├── sample-data.ts                # Sample data
│   └── brand-assets/                 # Test brand assets
└── utils/                            # Test utilities
    ├── auth-helpers.ts               # Auth test helpers
    ├── data-helpers.ts               # Data test helpers
    └── page-objects/                 # Page object models
```

## File Naming Conventions

### TypeScript/JavaScript Files
- **Components**: PascalCase (e.g., `ClientForm.tsx`, `UserList.tsx`)
- **Hooks**: camelCase with 'use' prefix (e.g., `useAuth.ts`, `useClientData.ts`)
- **Utilities**: camelCase (e.g., `validation.ts`, `formatting.ts`)
- **Types**: camelCase (e.g., `auth.ts`, `clients.ts`)
- **Stores**: kebab-case with '-store' suffix (e.g., `auth-store.ts`, `client-store.ts`)
- **Pages**: lowercase (e.g., `page.tsx`, `layout.tsx`)

### Python Files
- **Modules**: snake_case (e.g., `client_service.py`, `auth_middleware.py`)
- **Classes**: PascalCase within files (e.g., `class ClientService`)
- **Functions**: snake_case (e.g., `def create_client()`)
- **Agent Files**: descriptive with agent prefix (e.g., `client_agent.py`, `pdf_agent.py`)
- **Test Files**: prefix with 'test_' (e.g., `test_client_service.py`)

### Database Files
- **Migration Files**: sequential with descriptive name (e.g., `001_initial_migration.py`)
- **Table Names**: snake_case with agent prefix for agent tables (e.g., `agent1_clients`, `agent2_documents`)

### Configuration Files
- **Environment Files**: `.env` pattern (e.g., `.env`, `.env.local`, `.env.production`)
- **Config Files**: descriptive lowercase (e.g., `next.config.js`, `tailwind.config.js`)
- **Docker Files**: capitalized (e.g., `Dockerfile`, `Dockerfile.prod`)

### Documentation Files
- **Markdown Files**: kebab-case (e.g., `source-tree.md`, `api-specification.md`)
- **README Files**: uppercase (e.g., `README.md`)

## Directory Organization Principles

### 1. Feature-Based Organization
Organize code by features rather than file types to improve maintainability and reduce coupling.

### 2. Co-located Tests
Place test files near the code they test to improve discoverability and maintenance.

### 3. Shared Resources
Place shared types, utilities, and components in dedicated shared packages to avoid duplication.

### 4. Agent Independence
Each agent maintains its own directory structure with complete independence from other agents.

### 5. Clear Separation of Concerns
Separate infrastructure, application code, documentation, and configuration into distinct directories.

## Development Standards

### File Size Limits
- **Maximum 500 lines per file** - Split larger files into modules
- **Functions under 50 lines** - Break down complex functions
- **Components under 300 lines** - Extract sub-components when needed

### Import Organization
```typescript
// External imports
import React from 'react'
import { NextRequest } from 'next/server'

// Internal imports - absolute paths
import { ClientService } from '@/services/ClientService'
import { useAuth } from '@/hooks/use-auth'
import { Button } from '@/components/ui/button'

// Relative imports - only for same directory
import './styles.css'
```

### Export Patterns
```typescript
// Named exports preferred
export const ClientForm: React.FC<ClientFormProps> = ({ ... }) => {
  // Component implementation
}

// Default export for pages and main components
export default function ClientPage() {
  // Page implementation
}

// Index files for re-exports
export { ClientForm } from './ClientForm'
export { ClientList } from './ClientList'
export type { ClientFormProps } from './types'
```

This source tree architecture provides a solid foundation for the Multi-Agent IAM Dashboard project, ensuring consistent organization, clear separation of concerns, and optimal maintainability throughout all development phases.