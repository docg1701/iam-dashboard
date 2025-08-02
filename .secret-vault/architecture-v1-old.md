# Multi-Agent IAM Dashboard Fullstack Architecture Document

*Generated on August 1, 2025*

---

## Introduction

This document outlines the complete fullstack architecture for Multi-Agent IAM Dashboard, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This unified approach combines what would traditionally be separate backend and frontend architecture documents, streamlining the development process for modern fullstack applications where these concerns are increasingly intertwined.

### Starter Template or Existing Project

**N/A - Greenfield project**

This is a completely new custom implementation service being built from scratch, designed specifically for the Multi-Agent IAM Dashboard with custom branding and dedicated VPS deployment model.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-08-01 | 1.0 | Initial architecture document creation | Winston (System Architect) |

---

## High Level Architecture

### Technical Summary

The Multi-Agent IAM Dashboard implements a **Custom VPS + Docker Compose** architecture supporting a **Custom Implementation Service** business model. The system uses **FastAPI + SQLModel + PostgreSQL** for the backend with **Next.js 15 + React 19 + shadcn/ui** for the frontend, coordinated through **Agno framework** for multi-agent AI automation with 10,000x performance improvement. Each client receives a **dedicated VPS instance** with complete **custom branding integration** and **independent agent systems** that communicate through a **shared PostgreSQL database**. The infrastructure is **fully automated** through **Terraform + Ansible** enabling **30-day implementation cycles** and supporting the **$600K ARR premium service model** with **99.9% uptime SLA** guarantees.

### Platform and Infrastructure Choice

**Platform:** Custom VPS + Docker Compose Stack  
**Key Services:** DigitalOcean VPS, PostgreSQL 17.5, Redis 7.2, Caddy Reverse Proxy, Docker Compose  
**Deployment Host and Regions:** Multi-region VPS deployment (US-East, US-West, EU-West, Asia-Pacific)

### Repository Structure

**Structure:** Monorepo with dedicated application and infrastructure separation  
**Monorepo Tool:** Turborepo for optimized build caching and task orchestration  
**Package Organization:** Apps (frontend/backend), packages (shared types/utilities), infrastructure (Terraform/Ansible)

### High Level Architecture Diagram

```mermaid
graph TB
    subgraph "Client Access"
        Users[End Users] --> CDN[Vercel Edge Network]
        Admins[System Admins] --> CDN
    end
    
    subgraph "Frontend Layer"
        CDN --> Frontend[Next.js 15 + React 19]
        Frontend --> BrandSystem[Custom Branding System]
    end
    
    subgraph "API Gateway"
        Frontend --> Caddy[Caddy Reverse Proxy]
        Caddy --> API[FastAPI Backend]
    end
    
    subgraph "Multi-Agent System"
        API --> AgnoCore[Agno Agent Framework]
        AgnoCore --> Agent1[Agent 1: Client Management]
        AgnoCore --> Agent2[Agent 2: PDF Processing]
        AgnoCore --> Agent3[Agent 3: Reports & Analysis]
        AgnoCore --> Agent4[Agent 4: Audio Recording]
    end
    
    subgraph "Data Layer"
        API --> DB[(PostgreSQL 17.5 + pgvector)]
        Agent1 --> DB
        Agent2 --> DB
        Agent3 --> DB
        Agent4 --> DB
        API --> Cache[(Redis 7.2)]
    end
    
    subgraph "External Services"
        AgnoCore --> OpenAI[OpenAI API]
        API --> Twilio[Twilio SMS]
        API --> SendGrid[SendGrid Email]
        API --> Stripe[Stripe Payments]
    end
    
    subgraph "Infrastructure Automation"
        Terraform[Terraform Scripts] --> VPS[Client VPS Instances]
        Ansible[Ansible Playbooks] --> VPS
        VPS --> Docker[Docker Compose Stack]
    end
    
    subgraph "Monitoring & Observability"
        VPS --> Datadog[Datadog Monitoring]
        API --> Sentry[Sentry Error Tracking]
        DB --> Backups[Automated Backups]
    end
    
    classDef frontend fill:#e1f5fe
    classDef backend fill:#f3e5f5
    classDef agent fill:#fff3e0
    classDef data fill:#fce4ec
    classDef infra fill:#e8f5e8
    
    class Frontend,BrandSystem,CDN frontend
    class API,Caddy backend
    class AgnoCore,Agent1,Agent2,Agent3,Agent4 agent
    class DB,Cache data
    class Terraform,Ansible,VPS,Docker infra
```

### Architectural Patterns

- **Custom Implementation Service Architecture:** Dedicated VPS instances per client with complete isolation and customization - _Rationale:_ Enables premium pricing model and enterprise-grade data isolation
- **Database-Centric Multi-Agent Communication:** Agents communicate through shared PostgreSQL database rather than direct messaging - _Rationale:_ Ensures data consistency and enables Agno framework's 10,000x performance benefits
- **CSS Variable-Based Custom Branding:** Dynamic theming system using CSS custom properties for real-time brand customization - _Rationale:_ Enables complete visual customization without code changes per client
- **Infrastructure as Code Deployment:** Complete automation through Terraform + Ansible for consistent, repeatable deployments - _Rationale:_ Supports 30-day implementation promise and reduces operational overhead
- **Monorepo with Independent Applications:** Single repository with separate frontend/backend applications sharing common types and utilities - _Rationale:_ Enables coordinated development while maintaining clear boundaries
- **Server Components + Client Components:** Next.js 15 pattern using Server Components by default with Client Components for interactivity - _Rationale:_ Optimal performance with minimal client-side JavaScript
- **Repository Pattern:** Abstracted data access layer with comprehensive CRUD operations and business logic separation - _Rationale:_ Enables testing and future database migration flexibility
- **Event-Driven Agent Architecture:** Agents respond to database triggers and events rather than direct function calls - _Rationale:_ Maintains agent independence and supports horizontal scaling

---

## Tech Stack

### Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| Frontend Language | TypeScript | 5.9.2 | Type-safe JavaScript for frontend development | Ensures code quality and reduces runtime errors |
| Frontend Framework | Next.js | 15.4.0 | React framework with App Router and Server Components | Latest features for optimal performance and developer experience |
| UI Component Library | shadcn/ui | 0.8.0 | Component library with custom theming support | Enables complete custom branding while maintaining consistency |
| State Management | TanStack Query | 5.84.0 | Server state management and caching | Optimal for API-heavy applications with real-time updates |
| Backend Language | Python | 3.11 | Modern Python for backend development | Excellent AI/ML ecosystem support and developer productivity |
| Backend Framework | FastAPI | 0.116.1 | Modern async Python web framework | High performance with automatic API documentation |
| API Style | REST | OpenAPI 3.0 | RESTful API with comprehensive documentation | Industry standard with excellent tooling support |
| Database | PostgreSQL | 17.5 | Primary database with advanced features | ACID compliance, JSON support, and pgvector for AI operations |
| Cache | Redis | 7.2 | In-memory caching and session storage | High performance caching with persistence options |
| File Storage | Local + S3 Compatible | - | File storage with cloud backup | Cost-effective with enterprise backup capabilities |
| Authentication | OAuth2 + JWT | PyJWT 2.10.1 | Token-based authentication with 2FA | Secure, stateless authentication suitable for distributed architecture |
| Frontend Testing | Vitest | 2.1.8 | Fast unit testing for frontend | Modern testing framework with excellent TypeScript support |
| Backend Testing | pytest | 8.3.4 | Comprehensive Python testing framework | Industry standard with excellent async support |
| E2E Testing | Playwright | 1.54.0 | Cross-browser end-to-end testing | Reliable testing across all target browsers |
| Build Tool | Turborepo | 2.3.0 | Monorepo build orchestration | Optimized caching and parallel execution |
| Bundler | Next.js Built-in | - | Webpack-based bundling with optimizations | Integrated solution with excellent performance |
| IaC Tool | Terraform | 1.7.0 | Infrastructure provisioning and management | Industry standard for cloud infrastructure automation |
| CI/CD | GitHub Actions | - | Continuous integration and deployment | Integrated with repository and excellent ecosystem |
| Monitoring | Datadog | - | Application and infrastructure monitoring | Comprehensive observability with multi-client support |
| Logging | Structured JSON | - | Centralized logging with search capabilities | Enables efficient debugging and compliance auditing |
| CSS Framework | Tailwind CSS | 4.1.0 | Utility-first styling with custom theming | Perfect for custom branding with design system consistency |
| Multi-Agent Framework | Agno | Latest | AI agent coordination and management | 10,000x faster instantiation with 50x less memory usage |
| Package Manager (Python) | UV | 0.8.4 | Modern Python dependency management | Faster, more reliable than pip with lock file support |
| Package Manager (Node) | npm | 10.8.0 | Node.js dependency management | Integrated with Node.js and excellent ecosystem |
| ORM | SQLModel | 0.0.24 | Database ORM combining SQLAlchemy + Pydantic | Type-safe database operations with validation |
| Validation (Frontend) | Zod | 3.24.1 | TypeScript-first validation library | Runtime type validation with excellent TypeScript integration |
| Validation (Backend) | Pydantic | 2.10.4 | Data validation using Python type annotations | Integrated with FastAPI for automatic validation |
| Container Runtime | Docker | 24.0+ | Application containerization | Consistent deployment environment across all client instances |
| Reverse Proxy | Caddy | 2.7+ | Automatic HTTPS and reverse proxy | Minimal configuration with automatic SSL certificate management |
| AI/ML API | OpenAI API | v1 | AI-powered agent capabilities | Industry-leading AI capabilities for intelligent automation |

---

## Data Models

Based on the PRD requirements and multi-agent architecture, I've defined four core entities that support the custom implementation service model with complete audit trails and agent independence.

### User

**Purpose:** Complete user management with role-based access control and 2FA authentication

**Key Attributes:**
- user_id: UUID - Unique identifier for distributed system support
- email: string - Primary authentication identifier with uniqueness validation
- full_name: string - Display name for user interface
- role: enum - Role-based access control (sysadmin, admin, user)
- two_fa_enabled: boolean - TOTP-based two-factor authentication status
- created_at: timestamp - Audit trail timestamp
- updated_at: timestamp - Automatic update tracking

#### TypeScript Interface

```typescript
interface User {
  user_id: string;
  email: string;
  full_name: string;
  role: 'sysadmin' | 'admin' | 'user';
  is_active: boolean;
  two_fa_enabled: boolean;
  two_fa_secret?: string;
  last_login_at?: string;
  password_changed_at: string;
  failed_login_attempts: number;
  locked_until?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}
```

#### Relationships
- One-to-many with Clients (created_by relationship)
- One-to-many with AuditLogs (user_id relationship)
- Self-referential for created_by tracking

### Client

**Purpose:** Core client data management with AI insights and comprehensive validation

**Key Attributes:**
- client_id: UUID - Unique identifier for client records
- name: string - Client full name with search indexing
- ssn: string - Social Security Number with format validation (XXX-XX-XXXX)
- birth_date: date - Client birth date with business rule validation
- is_active: boolean - Soft delete and status management
- ai_insights: JSON - Agent-generated insights and analysis
- metadata: JSON - Flexible additional client data

#### TypeScript Interface

```typescript
interface Client {
  client_id: string;
  name: string;
  ssn: string; // Format: XXX-XX-XXXX
  birth_date: string; // ISO date string
  is_active: boolean;
  metadata: Record<string, any>;
  ai_insights: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by?: string;
}
```

#### Relationships
- Many-to-one with Users (created_by and updated_by)
- One-to-many with AuditLogs (entity_id when entity_type='client')
- Referenced by agent processing tables (documents, reports, etc.)

### AuditLog

**Purpose:** Comprehensive audit trail for SOC 2 compliance and forensic analysis

**Key Attributes:**
- audit_id: UUID - Unique audit record identifier
- entity_type: enum - Type of entity being audited (user, client, agent_config, system)
- entity_id: UUID - Reference to the audited entity
- action: enum - Type of action performed (create, update, delete, login, logout, export, import)
- changes: JSON - Before/after values for data modifications
- user_id: UUID - User who performed the action
- ip_address: string - Source IP for security tracking
- timestamp: timestamp - Exact time of action

#### TypeScript Interface

```typescript
interface AuditLog {
  audit_id: string;
  entity_type: 'user' | 'client' | 'agent_config' | 'system';
  entity_id: string;
  action: 'create' | 'update' | 'delete' | 'login' | 'logout' | 'export' | 'import';
  changes?: Record<string, any>;
  user_id?: string;
  ip_address?: string;
  user_agent?: string;
  session_id?: string;
  timestamp: string;
  request_id?: string;
  correlation_id?: string;
}
```

#### Relationships
- Many-to-one with Users (user_id relationship)
- References any entity through entity_id + entity_type pattern
- Partitioned by date for performance optimization

### AgentConfig

**Purpose:** Dynamic multi-agent configuration and performance monitoring

**Key Attributes:**
- config_id: UUID - Unique configuration identifier
- agent_name: string - Human-readable agent identifier
- agent_type: string - Agent category (client_management, pdf_processing, etc.)
- configuration: JSON - Agent-specific configuration parameters
- is_active: boolean - Agent enable/disable control
- version: integer - Configuration versioning for rollback
- performance_metrics: JSON - Agent performance and health data

#### TypeScript Interface

```typescript
interface AgentConfig {
  config_id: string;
  agent_name: string;
  agent_type: 'client_management' | 'pdf_processing' | 'report_generation' | 'audio_recording';
  configuration: Record<string, any>;
  is_active: boolean;
  version: number;
  deployment_status: 'active' | 'inactive' | 'deploying' | 'failed';
  performance_metrics: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by?: string;
}
```

#### Relationships
- Many-to-one with Users (created_by and updated_by)
- One-to-many with AuditLogs (entity_id when entity_type='agent_config')
- Referenced by agent processing operations for configuration lookup

---

## API Specification

Based on our chosen FastAPI REST API approach from the tech stack, I'll create a comprehensive OpenAPI 3.0 specification that covers all the endpoints identified in the PRD epics and stories.

```yaml
openapi: 3.0.0
info:
  title: Multi-Agent IAM Dashboard API
  version: 1.0.0
  description: |
    REST API for the Multi-Agent IAM Dashboard custom implementation service.
    Provides comprehensive client management, user administration, and system operations
    with role-based access control and complete audit trails.
  contact:
    name: IAM Dashboard API Support
    email: api-support@iamdashboard.com
  license:
    name: Proprietary
    url: https://iamdashboard.com/license

servers:
  - url: https://api.iamdashboard.com/v1
    description: Production API
  - url: https://staging-api.iamdashboard.com/v1
    description: Staging API
  - url: http://localhost:8000/v1
    description: Development API

security:
  - bearerAuth: []

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    User:
      type: object
      properties:
        user_id:
          type: string
          format: uuid
          description: Unique user identifier
        email:
          type: string
          format: email
          description: User email address
        full_name:
          type: string
          description: User's full name
        role:
          type: string
          enum: [sysadmin, admin, user]
          description: User role for access control
        is_active:
          type: boolean
          description: Account active status
        two_fa_enabled:
          type: boolean
          description: Two-factor authentication status
        last_login_at:
          type: string
          format: date-time
          nullable: true
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    Client:
      type: object
      properties:
        client_id:
          type: string
          format: uuid
          description: Unique client identifier
        name:
          type: string
          description: Client full name
        ssn:
          type: string
          pattern: '^\d{3}-\d{2}-\d{4}$'
          description: Social Security Number (XXX-XX-XXXX format)
        birth_date:
          type: string
          format: date
          description: Client birth date
        is_active:
          type: boolean
          description: Client active status
        created_by:
          type: string
          format: uuid
          description: User ID who created the client
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    ApiResponse:
      type: object
      properties:
        success:
          type: boolean
        message:
          type: string
        data:
          type: object
        timestamp:
          type: string
          format: date-time

    ApiError:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: object
            timestamp:
              type: string
              format: date-time
            request_id:
              type: string
              format: uuid

paths:
  # Authentication Endpoints
  /auth/login:
    post:
      tags: [Authentication]
      summary: User login with 2FA support
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                totp_code:
                  type: string
                  description: TOTP code for 2FA (if enabled)
              required: [email, password]
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                allOf:
                  - $ref: '#/components/schemas/ApiResponse'
                  - type: object
                    properties:
                      data:
                        type: object
                        properties:
                          access_token:
                            type: string
                          refresh_token:
                            type: string
                          user:
                            $ref: '#/components/schemas/User'
        '401':
          description: Authentication failed

  # Client Management Endpoints
  /clients:
    get:
      tags: [Clients]
      summary: List clients with search and filtering
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: per_page
          in: query
          schema:
            type: integer
            default: 20
        - name: search
          in: query
          schema:
            type: string
          description: Search by name or SSN
      responses:
        '200':
          description: Clients retrieved successfully

    post:
      tags: [Clients]
      summary: Create new client
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                ssn:
                  type: string
                  pattern: '^\d{3}-\d{2}-\d{4}$'
                birth_date:
                  type: string
                  format: date
              required: [name, ssn, birth_date]
      responses:
        '201':
          description: Client created successfully
        '400':
          description: Validation error (duplicate SSN, invalid format)

  /clients/{client_id}:
    get:
      tags: [Clients]
      summary: Get client by ID
      parameters:
        - name: client_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Client retrieved successfully
        '404':
          description: Client not found

    put:
      tags: [Clients]
      summary: Update client
      parameters:
        - name: client_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                ssn:
                  type: string
                  pattern: '^\d{3}-\d{2}-\d{4}$'
                birth_date:
                  type: string
                  format: date
                is_active:
                  type: boolean
      responses:
        '200':
          description: Client updated successfully
        '404':
          description: Client not found

  # System Health
  /system/health:
    get:
      tags: [System]
      summary: System health check
      security: []
      responses:
        '200':
          description: System is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    enum: [healthy, degraded, unhealthy]
                  timestamp:
                    type: string
                    format: date-time
                  services:
                    type: object
                    properties:
                      database:
                        type: string
                        enum: [up, down]
                      cache:
                        type: string
                        enum: [up, down]
```

---

## Components

Based on our architectural patterns, tech stack, and data models, I'll identify the major logical components across the fullstack Multi-Agent IAM Dashboard system.

### Frontend Core Components

**Authentication Component**
**Responsibility:** Complete authentication flow including 2FA, session management, and role-based access control

**Key Interfaces:**
- `useAuth()` hook for authentication state
- `ProtectedRoute` component for route guarding
- `LoginForm` with 2FA integration
- JWT token management and refresh

**Dependencies:** Backend Auth Service, React Context API, TanStack Query

**Technology Stack:** React 19, TypeScript, React Hook Form, Zod validation, TOTP library

**Dashboard Component**
**Responsibility:** Main dashboard interface with real-time metrics, activity feeds, and quick actions

**Key Interfaces:**
- `DashboardMetrics` for statistics display
- `ActivityFeed` for recent actions
- `QuickActions` toolbar
- Role-based content rendering

**Dependencies:** Client Service, User Service, System Monitoring Service

**Technology Stack:** React 19, shadcn/ui components, TanStack Query, Chart.js for metrics

**Client Management Component**
**Responsibility:** Complete client CRUD operations, search, filtering, and bulk operations

**Key Interfaces:**
- `ClientList` with pagination and filtering
- `ClientForm` for creation/editing
- `ClientDetail` view with audit history
- `BulkOperations` for CSV import/export

**Dependencies:** Backend Client Service, File Upload Service

**Technology Stack:** React 19, React Hook Form, React Table, CSV parsing libraries

**Custom Branding Component**
**Responsibility:** Real-time brand customization interface with live preview and deployment

**Key Interfaces:**
- `BrandingEditor` for color/logo/typography changes
- `LivePreview` showing changes across components
- `BrandingDeployment` for applying changes
- Asset upload and validation

**Dependencies:** Brand Management Service, Asset Storage Service

**Technology Stack:** React 19, CSS-in-JS, Color picker libraries, File upload components

### Backend Core Components

**FastAPI Application Layer**
**Responsibility:** HTTP request handling, routing, middleware, and API endpoint management

**Key Interfaces:**
- RESTful API endpoints following OpenAPI specification
- JWT authentication middleware
- CORS and security headers
- Request/response validation

**Dependencies:** Database Layer, Authentication Service, Business Logic Services

**Technology Stack:** FastAPI 0.116.1, Pydantic v2, Uvicorn/Gunicorn

**Database Layer**
**Responsibility:** Data persistence, relationships, migrations, and query optimization

**Key Interfaces:**
- SQLModel ORM with PostgreSQL
- Alembic migration management
- Connection pooling and transactions
- Audit trail logging

**Dependencies:** PostgreSQL 17.5, Redis for caching

**Technology Stack:** SQLModel 0.0.24, Alembic, asyncpg, PostgreSQL with pgvector

**Authentication Service**
**Responsibility:** User authentication, JWT token management, 2FA, and session handling

**Key Interfaces:**
- OAuth2 + JWT token creation/validation
- TOTP-based 2FA implementation
- Password hashing and validation
- Session management and refresh

**Dependencies:** Database Layer, Redis for token storage

**Technology Stack:** PyJWT, passlib, python-multipart, pyotp for 2FA

**Client Management Service**
**Responsibility:** Business logic for client operations, validation, and audit trail maintenance

**Key Interfaces:**
- Client CRUD operations with validation
- SSN format validation and duplicate prevention
- Search and filtering logic
- Bulk operations coordination

**Dependencies:** Database Layer, Audit Service

**Technology Stack:** SQLModel, Pydantic validation, custom business logic

### Multi-Agent System Components

**Agno Agent Framework**
**Responsibility:** Multi-agent coordination, independent agent lifecycle management, and database communication

**Key Interfaces:**
- Agent instantiation and configuration
- Database-centric communication patterns
- Agent state management
- Performance monitoring (10,000x faster instantiation)

**Dependencies:** PostgreSQL shared database, Agent Configuration Service

**Technology Stack:** Agno framework, PostgreSQL for agent communication

**Agent 1: Client Management Agent**
**Responsibility:** Autonomous client data operations with AI-enhanced validation and processing

**Key Interfaces:**
- AI-powered client data validation
- Intelligent duplicate detection
- Automated client categorization
- Smart search and recommendation

**Dependencies:** Agno Framework, Client Management Service, PostgreSQL

**Technology Stack:** Agno agents, OpenAI API integration, SQLModel

**Agent Configuration Service**
**Responsibility:** Dynamic agent management, configuration updates, and deployment coordination

**Key Interfaces:**
- Agent configuration management
- Runtime agent parameter updates
- Agent health monitoring
- Multi-agent workflow orchestration

**Dependencies:** Database Layer, System Monitoring

**Technology Stack:** Agno framework, SQLModel, async task processing

### Infrastructure and Deployment Components

**VPS Provisioning Service**
**Responsibility:** Automated infrastructure provisioning using Terraform scripts

**Key Interfaces:**
- Terraform script execution
- VPS provider API integration (DigitalOcean, Linode, AWS)
- DNS and SSL certificate management
- Resource monitoring and scaling

**Dependencies:** Terraform, Ansible Deployment Service

**Technology Stack:** Terraform, Python automation scripts, VPS provider APIs

**Ansible Deployment Service**
**Responsibility:** Automated application deployment and configuration management

**Key Interfaces:**
- Ansible playbook execution
- Environment-specific configuration
- Docker Compose orchestration
- Service health validation

**Dependencies:** VPS Provisioning Service, Custom Branding Service

**Technology Stack:** Ansible, Docker Compose, shell scripting

**Custom Branding Service**
**Responsibility:** Brand asset management, CSS variable generation, and deployment pipeline

**Key Interfaces:**
- Brand asset processing and validation
- CSS variable generation from brand settings
- Real-time brand deployment
- Brand configuration templating

**Dependencies:** Asset Storage Service, Deployment Service

**Technology Stack:** Python image processing, CSS generation, file system operations

---

## External APIs

Based on the PRD requirements and component design, the Multi-Agent IAM Dashboard requires several external API integrations to support the custom implementation service model, infrastructure automation, and AI-enhanced client management capabilities.

### OpenAI API
- **Purpose:** AI-powered client management, intelligent data validation, and agent decision-making capabilities
- **Documentation:** https://platform.openai.com/docs/api-reference
- **Base URL(s):** https://api.openai.com/v1
- **Authentication:** Bearer token (API key)
- **Rate Limits:** 3,500 requests per minute (tier-dependent)

**Key Endpoints Used:**
- `POST /chat/completions` - Agent reasoning and client data analysis
- `POST /embeddings` - Document similarity and client matching
- `POST /moderations` - Content safety validation

**Integration Notes:** Used by Agno agents for intelligent client management, data validation, and automated decision-making. Critical for the AI automation value proposition of the custom implementation service.

### DigitalOcean API
- **Purpose:** Primary VPS provisioning and management for client infrastructure deployment
- **Documentation:** https://docs.digitalocean.com/reference/api/
- **Base URL(s):** https://api.digitalocean.com/v2
- **Authentication:** Bearer token (Personal Access Token)
- **Rate Limits:** 5,000 requests per hour

**Key Endpoints Used:**
- `POST /droplets` - Create VPS instances for client implementations
- `GET /droplets/{droplet_id}` - Monitor VPS status and health
- `POST /domains` - DNS management for client custom domains
- `POST /certificates` - SSL certificate management
- `POST /load_balancers` - Load balancer configuration for high-traffic clients

**Integration Notes:** Primary infrastructure provider for VPS deployment automation. Integrated with Terraform scripts for infrastructure-as-code deployment. Supports the dedicated VPS model that differentiates our service from shared SaaS solutions.

### Twilio API
- **Purpose:** SMS delivery for 2FA authentication and system notifications
- **Documentation:** https://www.twilio.com/docs/api
- **Base URL(s):** https://api.twilio.com
- **Authentication:** Basic Auth (Account SID + Auth Token)
- **Rate Limits:** 1 request per second per phone number

**Key Endpoints Used:**
- `POST /2010-04-01/Accounts/{AccountSid}/Messages.json` - Send SMS for 2FA codes
- `GET /2010-04-01/Accounts/{AccountSid}/Messages/{MessageSid}.json` - Check delivery status

**Integration Notes:** Critical for 2FA implementation across client instances. Provides reliable SMS delivery with delivery confirmation for security compliance.

### SendGrid API
- **Purpose:** Transactional email delivery for notifications, alerts, and user communications
- **Documentation:** https://docs.sendgrid.com/api-reference
- **Base URL(s):** https://api.sendgrid.com/v3
- **Authentication:** Bearer token (API key)
- **Rate Limits:** 600 requests per minute

**Key Endpoints Used:**
- `POST /mail/send` - Send transactional emails (password resets, alerts, notifications)
- `GET /stats` - Email delivery statistics and bounce management
- `POST /marketing/contacts` - Manage client communication preferences

**Integration Notes:** Handles all transactional email communications across client instances. Includes template management for branded client communications and delivery tracking for compliance.

---

## Core Workflows

I'll illustrate the key system workflows using sequence diagrams to show how our components interact across the fullstack architecture, including external APIs and multi-agent coordination.

### Workflow 1: User Authentication with 2FA

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend Auth Component
    participant API as FastAPI Application
    participant AuthSvc as Authentication Service
    participant DB as PostgreSQL
    participant Twilio as Twilio API
    participant Cache as Redis Cache

    U->>FE: Enter email/password
    FE->>API: POST /auth/login
    API->>AuthSvc: Validate credentials
    AuthSvc->>DB: Query user record
    DB-->>AuthSvc: User data with 2FA status
    
    alt 2FA Enabled
        AuthSvc->>Twilio: Send SMS with TOTP code
        Twilio-->>AuthSvc: SMS delivery confirmation
        AuthSvc-->>API: Require 2FA verification
        API-->>FE: 2FA required response
        FE->>U: Show 2FA input form
        U->>FE: Enter TOTP code
        FE->>API: POST /auth/login with TOTP
        API->>AuthSvc: Validate TOTP code
        AuthSvc->>AuthSvc: Verify TOTP against secret
    end

    alt Authentication Success
        AuthSvc->>Cache: Store session data
        AuthSvc->>DB: Log successful login
        AuthSvc-->>API: JWT tokens + user data
        API-->>FE: Authentication success
        FE->>FE: Store tokens securely
        FE->>U: Redirect to dashboard
    else Authentication Failure
        AuthSvc->>DB: Log failed attempt
        AuthSvc-->>API: Authentication error
        API-->>FE: Error response
        FE->>U: Show error message
    end
```

### Workflow 2: Client Registration with AI Validation

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Client Management Component
    participant API as FastAPI Application
    participant ClientSvc as Client Management Service
    participant Agent1 as Agno Client Agent
    participant DB as PostgreSQL
    participant OpenAI as OpenAI API
    participant AuditSvc as Audit Service

    U->>FE: Fill client registration form
    FE->>FE: Client-side validation (Zod)
    FE->>API: POST /clients (with JWT)
    API->>API: Validate JWT and permissions
    API->>ClientSvc: Process client creation
    
    ClientSvc->>DB: Check SSN uniqueness
    DB-->>ClientSvc: SSN validation result
    
    alt SSN Already Exists
        ClientSvc-->>API: Duplicate SSN error
        API-->>FE: Validation error
        FE->>U: Show duplicate SSN message
    else SSN Unique
        ClientSvc->>DB: Insert client record (pending)
        ClientSvc->>Agent1: Trigger AI validation
        Agent1->>OpenAI: Analyze client data for anomalies
        OpenAI-->>Agent1: Validation insights
        Agent1->>DB: Update client with AI insights
        
        alt AI Validation Passed
            Agent1->>DB: Activate client record
            Agent1->>AuditSvc: Log client creation
            AuditSvc->>DB: Insert audit record
            ClientSvc-->>API: Client created successfully
            API-->>FE: Success response with client data
            FE->>U: Show success confirmation
        else AI Validation Failed
            Agent1->>DB: Mark client for review
            Agent1->>AuditSvc: Log validation failure
            ClientSvc-->>API: Validation warning
            API-->>FE: Success with warning
            FE->>U: Show success + manual review notice
        end
    end
```

### Workflow 3: Custom Branding Deployment

```mermaid
sequenceDiagram
    participant Admin as Admin User
    participant FE as Branding Component
    participant API as FastAPI Application
    participant BrandSvc as Custom Branding Service
    participant Storage as Asset Storage Service
    participant Ansible as Ansible Deployment
    participant VPS as Client VPS Instance
    participant DB as PostgreSQL

    Admin->>FE: Upload logo and select colors
    FE->>FE: Real-time preview generation
    Admin->>FE: Confirm branding changes
    FE->>API: POST /branding/deploy
    API->>BrandSvc: Process branding update
    
    BrandSvc->>Storage: Upload and process assets
    Storage->>Storage: Optimize images, generate variants
    Storage-->>BrandSvc: Asset URLs and metadata
    
    BrandSvc->>BrandSvc: Generate CSS variables
    BrandSvc->>DB: Save branding configuration
    
    BrandSvc->>Ansible: Trigger deployment playbook
    Ansible->>VPS: Deploy updated assets
    Ansible->>VPS: Update CSS variables
    Ansible->>VPS: Restart frontend services
    VPS-->>Ansible: Deployment confirmation
    
    Ansible-->>BrandSvc: Deployment success
    BrandSvc->>DB: Update deployment status
    BrandSvc-->>API: Branding deployed successfully
    API-->>FE: Success response
    FE->>Admin: Show deployment confirmation
    
    FE->>FE: Refresh preview with live changes
```

---

## Database Schema

I'll transform our conceptual data models into concrete PostgreSQL schemas that support the multi-agent architecture, custom implementation service, and all the workflows we've defined.

```sql
-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Custom types for consistent enums
CREATE TYPE user_role AS ENUM ('sysadmin', 'admin', 'user');
CREATE TYPE audit_action AS ENUM ('create', 'update', 'delete', 'login', 'logout', 'export', 'import');
CREATE TYPE entity_type AS ENUM ('user', 'client', 'agent_config', 'system');
CREATE TYPE implementation_status AS ENUM ('pending', 'provisioning', 'deploying', 'active', 'maintenance', 'failed');

-- Core Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    two_fa_enabled BOOLEAN DEFAULT FALSE,
    two_fa_secret VARCHAR(32),
    last_login_at TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id)
);

-- Core Clients table (Agent 1 primary responsibility)
CREATE TABLE clients (
    client_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    ssn VARCHAR(11) UNIQUE NOT NULL, -- Format: XXX-XX-XXXX
    birth_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}', -- Flexible additional data
    ai_insights JSONB DEFAULT '{}', -- Agent 1 AI analysis results
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    
    -- Constraints
    CONSTRAINT valid_ssn_format CHECK (ssn ~ '^\d{3}-\d{2}-\d{4}$'),
    CONSTRAINT valid_birth_date CHECK (birth_date <= CURRENT_DATE),
    CONSTRAINT future_birth_date CHECK (birth_date >= '1900-01-01')
);

-- Comprehensive audit trail
CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type entity_type NOT NULL,
    entity_id UUID NOT NULL,
    action audit_action NOT NULL,
    changes JSONB, -- Before/after values for updates
    user_id UUID REFERENCES users(user_id),
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional context for compliance
    request_id UUID,
    correlation_id UUID -- For tracking related operations
);

-- Agent configuration management
CREATE TABLE agent_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(255) NOT NULL UNIQUE,
    agent_type VARCHAR(100) NOT NULL, -- 'client_management', 'pdf_processing', etc.
    configuration JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    deployment_status VARCHAR(50) DEFAULT 'active',
    performance_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id)
);

-- Custom branding configurations
CREATE TABLE brand_configs (
    brand_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_instance_id VARCHAR(255) UNIQUE NOT NULL, -- VPS instance identifier
    brand_name VARCHAR(255) NOT NULL,
    primary_color VARCHAR(7) NOT NULL, -- Hex color
    secondary_color VARCHAR(7) NOT NULL,
    logo_url VARCHAR(500),
    favicon_url VARCHAR(500),
    font_primary VARCHAR(100) DEFAULT 'Inter',
    font_secondary VARCHAR(100) DEFAULT 'Inter',
    css_variables JSONB NOT NULL DEFAULT '{}',
    custom_css TEXT,
    deployment_status VARCHAR(50) DEFAULT 'pending',
    last_deployed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(user_id),
    
    -- Color validation constraints
    CONSTRAINT valid_primary_color CHECK (primary_color ~ '^#[0-9A-Fa-f]{6}$'),
    CONSTRAINT valid_secondary_color CHECK (secondary_color ~ '^#[0-9A-Fa-f]{6}$')
);

-- Performance optimization: Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_clients_ssn ON clients(ssn);
CREATE INDEX idx_clients_name_gin ON clients USING GIN (to_tsvector('english', name));
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_agent_configs_name ON agent_configs(agent_name);
CREATE INDEX idx_brand_instance ON brand_configs(client_instance_id);

-- Automatic audit triggers
CREATE OR REPLACE FUNCTION trigger_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        entity_type,
        entity_id,
        action,
        changes,
        user_id,
        timestamp
    ) VALUES (
        TG_ARGV[0]::entity_type,
        COALESCE(NEW.client_id, NEW.user_id, NEW.config_id),
        CASE TG_OP
            WHEN 'INSERT' THEN 'create'::audit_action
            WHEN 'UPDATE' THEN 'update'::audit_action
            WHEN 'DELETE' THEN 'delete'::audit_action
        END,
        CASE TG_OP
            WHEN 'UPDATE' THEN jsonb_build_object('before', to_jsonb(OLD), 'after', to_jsonb(NEW))
            WHEN 'INSERT' THEN to_jsonb(NEW)
            WHEN 'DELETE' THEN to_jsonb(OLD)
        END,
        COALESCE(NEW.updated_by, NEW.created_by, OLD.updated_by, OLD.created_by),
        NOW()
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers
CREATE TRIGGER audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_audit_log('user');

CREATE TRIGGER audit_clients
    AFTER INSERT OR UPDATE OR DELETE ON clients
    FOR EACH ROW EXECUTE FUNCTION trigger_audit_log('client');
```

---

## Frontend Architecture

I'll define the frontend-specific architecture details for our Next.js 15 + React 19 application, focusing on component organization, state management patterns, and service layer integration.

### Component Architecture

#### Component Organization

```
frontend/src/
├── app/                          # Next.js 15 App Router
│   ├── (auth)/                   # Route group for authentication
│   │   ├── login/
│   │   │   └── page.tsx          # Server Component
│   │   └── layout.tsx            # Auth layout
│   ├── (dashboard)/              # Route group for main app
│   │   ├── dashboard/
│   │   │   └── page.tsx          # Dashboard Server Component
│   │   ├── clients/
│   │   │   ├── page.tsx          # Client list Server Component
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx      # Client detail Server Component
│   │   │   └── new/
│   │   │       └── page.tsx      # Client creation page
│   │   ├── users/                # Admin/Sysadmin only
│   │   ├── system/               # Sysadmin only
│   │   └── layout.tsx            # Dashboard layout with nav
│   ├── api/                      # Minimal API routes
│   ├── globals.css               # Global styles + CSS variables
│   ├── layout.tsx                # Root layout
│   └── loading.tsx               # Global loading component
├── components/                   # Reusable components
│   ├── ui/                       # shadcn/ui base components
│   ├── common/                   # App-specific shared components
│   ├── forms/                    # Form components
│   ├── dashboard/                # Dashboard-specific components
│   └── providers/                # Context providers
├── lib/                          # Utilities and configurations
├── hooks/                        # Custom React hooks
├── services/                     # API service layer
└── types/                        # TypeScript definitions
```

#### Component Template

```typescript
'use client' // Only when interactivity is needed

import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { Client } from '@/types/client.types'

interface ClientCardProps {
  client: Client
  onEdit?: (client: Client) => void
  onDelete?: (clientId: string) => void
  className?: string
}

export function ClientCard({ 
  client, 
  onEdit, 
  onDelete, 
  className 
}: ClientCardProps) {
  const [isLoading, setIsLoading] = useState(false)
  const { user, hasPermission } = useAuth()
  
  const handleEdit = async () => {
    if (!hasPermission('clients:update')) return
    setIsLoading(true)
    try {
      onEdit?.(client)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className={cn("transition-all hover:shadow-md", className)}>
      <CardHeader>
        <CardTitle className="flex justify-between items-center">
          <span>{client.name}</span>
          <div className="flex gap-2">
            {hasPermission('clients:update') && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleEdit}
                disabled={isLoading}
              >
                Edit
              </Button>
            )}
            {hasPermission('clients:delete') && (
              <Button 
                variant="destructive" 
                size="sm" 
                onClick={() => onDelete?.(client.client_id)}
              >
                Delete
              </Button>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            SSN: {client.ssn.replace(/\d(?=\d{4})/g, '*')}
          </p>
          <p className="text-sm text-muted-foreground">
            Birth Date: {new Date(client.birth_date).toLocaleDateString()}
          </p>
          <p className="text-sm text-muted-foreground">
            Created: {new Date(client.created_at).toLocaleDateString()}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
```

### State Management Architecture

#### State Structure

```typescript
// Authentication State (React Context)
interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  permissions: string[]
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
}

// Branding State (React Context + localStorage)
interface BrandingState {
  currentBrand: BrandConfig | null
  isCustomizing: boolean
  previewMode: boolean
  applyBranding: (config: BrandConfig) => void
  deployBranding: () => Promise<void>
  togglePreview: () => void
}

// Server State (TanStack Query)
interface ServerState {
  // Clients
  clients: UseQueryResult<PaginatedResponse<Client>>
  clientDetails: UseQueryResult<Client>
  createClient: UseMutationResult<Client, Error, CreateClientData>
  updateClient: UseMutationResult<Client, Error, UpdateClientData>
  deleteClient: UseMutationResult<void, Error, string>
  
  // Users (Admin only)
  users: UseQueryResult<PaginatedResponse<User>>
  createUser: UseMutationResult<User, Error, CreateUserData>
  
  // System data
  auditLogs: UseQueryResult<PaginatedResponse<AuditLog>>
  systemHealth: UseQueryResult<SystemHealth>
}
```

#### State Management Patterns

- **Authentication**: React Context with localStorage persistence and automatic token refresh
- **Server State**: TanStack Query for caching, background updates, and optimistic updates
- **Form State**: React Hook Form with Zod validation for type-safe form handling
- **UI State**: Component-level useState for ephemeral UI state
- **Global UI State**: React Context for theme, branding, and modal management
- **URL State**: Next.js searchParams for shareable application state

### Routing Architecture

#### Route Organization

```
app/
├── (auth)/
│   ├── login/page.tsx            # Public route
│   └── layout.tsx                # Auth-specific layout
├── (dashboard)/
│   ├── dashboard/page.tsx        # Protected route (all roles)
│   ├── clients/
│   │   ├── page.tsx              # Protected route (all roles)
│   │   ├── [id]/page.tsx         # Protected route (all roles)
│   │   └── new/page.tsx          # Protected route (admin+)
│   ├── users/
│   │   └── page.tsx              # Protected route (sysadmin only)
│   ├── system/
│   │   ├── page.tsx              # Protected route (sysadmin only)
│   │   ├── audit/page.tsx        # Protected route (admin+)
│   │   └── branding/page.tsx     # Protected route (admin+)
│   └── layout.tsx                # Dashboard layout with nav
├── api/                          # Minimal API routes
│   └── auth/
│       └── callback/route.ts     # OAuth callback
├── layout.tsx                    # Root layout
├── loading.tsx                   # Global loading UI
├── error.tsx                     # Global error UI
└── not-found.tsx                 # 404 page
```

### Frontend Services Layer

#### API Client Setup

```typescript
// lib/api.ts - Centralized API client
import axios, { AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth.store'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        await useAuthStore.getState().refreshToken()
        const newToken = useAuthStore.getState().accessToken
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// Type-safe API response wrapper
export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
  timestamp: string
}

export interface PaginatedResponse<T> {
  success: boolean
  data: T[]
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
  }
  timestamp: string
}
```

#### Service Example

```typescript
// services/clients.service.ts - Client management API
import { apiClient, ApiResponse, PaginatedResponse } from '@/lib/api'
import type { Client, CreateClientData, UpdateClientData } from '@/types/client.types'

export class ClientsService {
  static async getClients(params?: {
    page?: number
    per_page?: number
    search?: string
    active_only?: boolean
    created_after?: string
    created_before?: string
  }): Promise<PaginatedResponse<Client>> {
    const response = await apiClient.get<PaginatedResponse<Client>>('/clients', {
      params
    })
    return response.data
  }

  static async getClientById(id: string): Promise<ApiResponse<Client>> {
    const response = await apiClient.get<ApiResponse<Client>>(`/clients/${id}`)
    return response.data
  }

  static async createClient(data: CreateClientData): Promise<ApiResponse<Client>> {
    const response = await apiClient.post<ApiResponse<Client>>('/clients', data)
    return response.data
  }

  static async updateClient(
    id: string, 
    data: UpdateClientData
  ): Promise<ApiResponse<Client>> {
    const response = await apiClient.put<ApiResponse<Client>>(`/clients/${id}`, data)
    return response.data
  }

  static async deleteClient(id: string): Promise<ApiResponse<void>> {
    const response = await apiClient.delete<ApiResponse<void>>(`/clients/${id}`)
    return response.data
  }
}

// Custom hook for client data management
export function useClients(params?: Parameters<typeof ClientsService.getClients>[0]) {
  return useQuery({
    queryKey: ['clients', params],
    queryFn: () => ClientsService.getClients(params),
    staleTime: 30000, // 30 seconds
    gcTime: 300000, // 5 minutes
  })
}

export function useCreateClient() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ClientsService.createClient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}
```

---

## Backend Architecture

I'll define the backend-specific architecture details for our FastAPI application, focusing on service organization, database access patterns, and authentication implementation that supports the multi-agent architecture and custom implementation service model.

### Service Architecture

#### Controller/Route Organization

```
backend/src/
├── main.py                       # FastAPI application entry point
├── core/                         # Core system modules
│   ├── __init__.py
│   ├── config.py                 # Application configuration
│   ├── database.py               # Database connection and session management
│   ├── security.py               # Authentication and authorization
│   ├── exceptions.py             # Custom exception handlers
│   └── middleware.py             # Custom middleware (CORS, logging, etc.)
├── api/                          # API layer
│   ├── __init__.py
│   ├── dependencies.py           # Common dependencies and auth
│   └── v1/                       # API version 1
│       ├── __init__.py
│       ├── auth.py               # Authentication endpoints
│       ├── clients.py            # Client management endpoints
│       ├── users.py              # User management endpoints
│       ├── audit.py              # Audit trail endpoints
│       ├── system.py             # System health and monitoring
│       └── branding.py           # Custom branding endpoints
├── services/                     # Business logic layer
│   ├── __init__.py
│   ├── auth_service.py           # Authentication business logic
│   ├── client_service.py         # Client management business logic
│   ├── user_service.py           # User management business logic
│   ├── audit_service.py          # Audit logging service
│   ├── branding_service.py       # Custom branding service
│   └── agent_service.py          # Agent coordination service
├── models/                       # SQLModel database models
│   ├── __init__.py
│   ├── base.py                   # Base model with common fields
│   ├── user.py                   # User model and relationships
│   ├── client.py                 # Client model and relationships
│   ├── audit.py                  # Audit log models
│   ├── agent.py                  # Agent configuration models
│   └── system.py                 # System and monitoring models
├── repositories/                 # Data access layer
│   ├── __init__.py
│   ├── base.py                   # Base repository with CRUD operations
│   ├── client_repository.py      # Client data access
│   ├── user_repository.py        # User data access
│   ├── audit_repository.py       # Audit log data access
│   └── agent_repository.py       # Agent configuration data access
├── agents/                       # Multi-agent system integration
│   ├── __init__.py
│   ├── base_agent.py             # Base agent class
│   ├── client_agent.py           # Agent 1: Client management
│   ├── agent_manager.py          # Agent lifecycle management
│   └── communication.py          # Database-centric agent communication
├── utils/                        # Utility functions
│   ├── __init__.py
│   ├── validators.py             # Custom validation functions
│   ├── formatters.py             # Data formatting utilities
│   ├── encryption.py             # Encryption and hashing utilities
│   └── notifications.py          # Email/SMS notification utilities
└── tests/                        # Test files
    ├── __init__.py
    ├── conftest.py               # Test configuration and fixtures
    ├── test_auth.py              # Authentication tests
    ├── test_clients.py           # Client management tests
    ├── test_agents.py            # Agent integration tests
    └── test_integration.py       # End-to-end integration tests
```

### Database Architecture

#### Data Access Layer

```python
# repositories/base.py - Base repository with common CRUD operations
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID
from sqlmodel import Session, select, func, and_, or_
from sqlalchemy.orm import selectinload
from models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, session: Session, id: UUID) -> Optional[ModelType]:
        """Get a single record by ID."""
        statement = select(self.model).where(self.model.id == id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        session: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get multiple records with filtering and pagination."""
        statement = select(self.model)
        
        # Apply filters
        if filters:
            conditions = []
            for key, value in filters.items():
                if value is not None:
                    if hasattr(self.model, key):
                        conditions.append(getattr(self.model, key) == value)
            
            if conditions:
                statement = statement.where(and_(*conditions))
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            statement = statement.order_by(getattr(self.model, order_by))
        
        # Apply pagination
        statement = statement.offset(skip).limit(limit)
        
        result = await session.execute(statement)
        return result.scalars().all()

    async def create(self, session: Session, *, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], Any]
    ) -> ModelType:
        """Update an existing record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
```

### Authentication and Authorization

#### Auth Flow

```mermaid
sequenceDiagram
    participant Client as Frontend Client
    participant API as FastAPI Server
    participant Auth as Auth Service
    participant DB as PostgreSQL
    participant Cache as Redis Cache
    participant SMS as Twilio API

    Client->>API: POST /auth/login {email, password}
    API->>Auth: validate_credentials()
    Auth->>DB: Query user by email
    DB-->>Auth: User data with hashed password
    Auth->>Auth: Verify password hash
    
    alt Password Valid and 2FA Enabled
        Auth->>SMS: Send TOTP code via SMS
        SMS-->>Auth: SMS sent confirmation
        Auth-->>API: {requires_2fa: true}
        API-->>Client: 2FA required response
        
        Client->>API: POST /auth/login {email, password, totp_code}
        API->>Auth: validate_credentials_with_2fa()
        Auth->>Auth: Verify TOTP code
        
        alt TOTP Valid
            Auth->>Cache: Store session data
            Auth->>Auth: Generate JWT tokens
            Auth->>DB: Update last_login_at
            Auth-->>API: {access_token, refresh_token, user}
            API-->>Client: Authentication success
        else TOTP Invalid
            Auth->>DB: Log failed 2FA attempt
            Auth-->>API: Invalid 2FA code error
            API-->>Client: Authentication error
        end
        
    alt Password Valid and 2FA Disabled
        Auth->>Cache: Store session data
        Auth->>Auth: Generate JWT tokens
        Auth->>DB: Update last_login_at
        Auth-->>API: {access_token, refresh_token, user}
        API-->>Client: Authentication success
        
    else Password Invalid
        Auth->>DB: Increment failed_login_attempts
        Auth-->>API: Invalid credentials error
        API-->>Client: Authentication error
    end
```

#### Middleware/Guards

```python
# core/security.py - Authentication and authorization
import jwt
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from passlib.context import CryptContext
import pyotp

from core.config import settings
from core.database import get_session
from models.user import User
from repositories.user_repository import UserRepository

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# User repository
user_repo = UserRepository()

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Dependency for getting current user from JWT token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = AuthService.verify_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_repo.get(session, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        )
    
    return user

# Permission checking
async def require_permission(user: User, permission: str) -> bool:
    """Check if user has required permission based on role."""
    role_permissions = {
        "sysadmin": ["*"],  # All permissions
        "admin": [
            "clients:*", "users:read", "system:read", 
            "audit:read", "branding:*", "reports:*"
        ],
        "user": ["clients:read", "clients:create", "clients:update"]
    }
    
    user_permissions = role_permissions.get(user.role, [])
    
    # Sysadmin has all permissions
    if "*" in user_permissions:
        return True
    
    # Check specific permission or wildcard
    permission_parts = permission.split(":")
    resource = permission_parts[0]
    action = permission_parts[1] if len(permission_parts) > 1 else "read"
    
    return (
        permission in user_permissions or
        f"{resource}:*" in user_permissions
    )
```

---

## Unified Project Structure

I'll create a comprehensive monorepo structure that accommodates both frontend and backend components, infrastructure automation, and multi-agent architecture while supporting the custom implementation service model.

```
iam-dashboard/
├── .github/                           # GitHub Actions workflows
│   └── workflows/
│       ├── ci.yml                     # Continuous integration pipeline
│       ├── deploy-staging.yml         # Staging deployment
│       ├── deploy-production.yml      # Production deployment
│       ├── security-scan.yml          # Security scanning
│       └── backup-verification.yml    # Backup testing
├── apps/                              # Application packages
│   ├── frontend/                      # Next.js 15 + React 19 application
│   │   ├── src/
│   │   │   ├── app/                   # Next.js App Router
│   │   │   │   ├── (auth)/            # Authentication route group
│   │   │   │   │   ├── login/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   └── layout.tsx
│   │   │   │   ├── (dashboard)/       # Main application routes
│   │   │   │   │   ├── dashboard/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── clients/
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   ├── [id]/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   └── new/
│   │   │   │   │   │       └── page.tsx
│   │   │   │   │   ├── users/         # Admin/Sysadmin only
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   ├── system/        # System administration
│   │   │   │   │   │   ├── audit/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   ├── branding/
│   │   │   │   │   │   │   └── page.tsx
│   │   │   │   │   │   └── health/
│   │   │   │   │   │       └── page.tsx
│   │   │   │   │   └── layout.tsx
│   │   │   │   ├── api/               # Minimal API routes
│   │   │   │   │   └── auth/
│   │   │   │   │       └── callback/
│   │   │   │   │           └── route.ts
│   │   │   │   ├── globals.css        # Global styles + CSS variables
│   │   │   │   ├── layout.tsx         # Root layout
│   │   │   │   ├── loading.tsx        # Global loading component
│   │   │   │   ├── error.tsx          # Global error boundary
│   │   │   │   └── not-found.tsx      # 404 page
│   │   │   ├── components/            # React components
│   │   │   │   ├── ui/                # shadcn/ui base components
│   │   │   │   ├── common/            # Shared app components
│   │   │   │   ├── forms/             # Form components
│   │   │   │   ├── dashboard/         # Dashboard components
│   │   │   │   └── providers/         # Context providers
│   │   │   ├── lib/                   # Frontend utilities
│   │   │   ├── hooks/                 # Custom React hooks
│   │   │   ├── services/              # API service layer
│   │   │   ├── types/                 # Frontend-specific types
│   │   │   └── styles/                # Additional styling
│   │   ├── public/                    # Static assets
│   │   ├── tests/                     # Frontend tests
│   │   ├── .env.local.example         # Environment variables template
│   │   ├── .eslintrc.json             # ESLint configuration
│   │   ├── next.config.js             # Next.js configuration
│   │   ├── package.json               # Frontend dependencies
│   │   ├── tailwind.config.js         # Tailwind CSS configuration
│   │   ├── tsconfig.json              # TypeScript configuration
│   │   └── vitest.config.ts           # Vitest configuration
│   └── backend/                       # FastAPI application
│       ├── src/
│       │   ├── main.py                # FastAPI application entry
│       │   ├── core/                  # Core system modules
│       │   ├── api/                   # API layer
│       │   ├── services/              # Business logic layer
│       │   ├── models/                # SQLModel database models
│       │   ├── schemas/               # Pydantic request/response schemas
│       │   ├── repositories/          # Data access layer
│       │   ├── agents/                # Multi-agent system
│       │   ├── utils/                 # Utility functions
│       │   └── migrations/            # Database migrations
│       ├── tests/                     # Backend tests
│       ├── alembic/                   # Database migration management
│       ├── .env.example               # Environment variables template
│       ├── Dockerfile                 # Backend container definition
│       ├── pyproject.toml             # UV dependency management
│       └── pytest.ini                 # pytest configuration
├── packages/                          # Shared packages
│   ├── shared/                        # Shared types and utilities
│   │   ├── src/
│   │   │   ├── types/                 # TypeScript interfaces
│   │   │   ├── constants/             # Shared constants
│   │   │   ├── utils/                 # Shared utilities
│   │   │   └── schemas/               # Shared Zod schemas
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── ui/                            # Shared UI components
│   │   ├── src/
│   │   │   ├── components/            # Reusable components
│   │   │   ├── hooks/                 # Shared hooks
│   │   │   └── styles/                # Shared styles
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── config/                        # Shared configuration
│       ├── eslint/                    # ESLint configurations
│       ├── typescript/                # TypeScript configurations
│       ├── tailwind/                  # Tailwind configurations
│       ├── jest/                      # Jest configurations
│       └── package.json
├── infrastructure/                    # Infrastructure as Code
│   ├── terraform/                     # Terraform configurations
│   │   ├── modules/                   # Reusable Terraform modules
│   │   │   ├── vps/                   # VPS provisioning module
│   │   │   ├── dns/                   # DNS management module
│   │   │   ├── ssl/                   # SSL certificate module
│   │   │   └── monitoring/            # Monitoring setup module
│   │   ├── environments/              # Environment-specific configs
│   │   │   ├── staging/
│   │   │   ├── production/
│   │   │   └── client-template/       # Template for client instances
│   │   ├── scripts/                   # Terraform automation scripts
│   │   └── README.md                  # Terraform documentation
│   ├── ansible/                       # Ansible configurations
│   │   ├── playbooks/                 # Ansible playbooks
│   │   ├── roles/                     # Ansible roles
│   │   ├── inventories/               # Inventory files
│   │   ├── group_vars/                # Group variables
│   │   ├── host_vars/                 # Host-specific variables
│   │   ├── ansible.cfg                # Ansible configuration
│   │   └── requirements.yml           # Ansible Galaxy requirements
│   ├── docker/                        # Docker configurations
│   │   ├── production/                # Production Docker configs
│   │   ├── staging/                   # Staging Docker configs
│   │   └── development/               # Development Docker configs
│   └── monitoring/                    # Monitoring configurations
│       ├── grafana/                   # Grafana dashboards
│       ├── prometheus/                # Prometheus configuration
│       └── alertmanager/              # Alert configurations
├── scripts/                           # Build and deployment scripts
│   ├── dev/                           # Development scripts
│   ├── build/                         # Build scripts
│   ├── deploy/                        # Deployment scripts
│   └── maintenance/                   # Maintenance scripts
├── docs/                              # Documentation
│   ├── api/                           # API documentation
│   ├── deployment/                    # Deployment guides
│   ├── development/                   # Development guides
│   ├── user/                          # User documentation
│   ├── prd.md                         # Product Requirements Document
│   ├── front-end-spec.md              # Frontend specification
│   ├── architecture.md                # This architecture document
│   └── CHANGELOG.md                   # Change log
├── .env.example                       # Root environment template
├── .gitignore                         # Git ignore patterns
├── .gitattributes                     # Git attributes
├── docker-compose.yml                 # Development Docker Compose
├── docker-compose.override.yml        # Development overrides
├── package.json                       # Root package.json (workspace)
├── turbo.json                         # Turborepo configuration
├── README.md                          # Project overview and setup
├── LICENSE                            # License information
└── CLAUDE.md                          # AI development instructions
```

---

## Development Workflow

I'll define the complete development setup and workflow for the Multi-Agent IAM Dashboard fullstack application, focusing on developer experience, team collaboration, and operational efficiency.

### Local Development Setup

#### Prerequisites

```bash
# System requirements for development
node --version    # >= 18.17.0 (for Next.js 15)
python --version  # >= 3.11 (for FastAPI)
docker --version  # >= 24.0 (for containerization)
git --version     # >= 2.40 (for version control)

# Install required global tools
npm install -g turbo@latest          # Monorepo task runner
curl -LsSf https://astral.sh/uv/install.sh | sh  # UV Python package manager
pip install pre-commit               # Git hooks for quality gates

# Database requirements (via Docker)
# PostgreSQL 17.5 with pgvector extension
# Redis 7.2 for caching and sessions

# Optional but recommended
brew install caddy                   # Local reverse proxy (macOS)
# or
sudo apt install caddy              # Linux
```

#### Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-org/iam-dashboard.git
cd iam-dashboard

# Copy environment configuration
cp .env.example .env
cp apps/frontend/.env.local.example apps/frontend/.env.local
cp apps/backend/.env.example apps/backend/.env

# Install dependencies (monorepo root)
npm install                          # Install Node.js dependencies
turbo build --filter=@iam/shared    # Build shared packages first

# Backend setup with UV
cd apps/backend
uv venv                              # Create virtual environment
source .venv/bin/activate            # Activate virtual environment (Linux/Mac)
# or .venv\Scripts\activate          # Windows
uv sync                              # Install all dependencies from pyproject.toml

# Database setup
cd ../../
docker-compose up -d postgres redis # Start databases
cd apps/backend
uv run alembic upgrade head          # Run database migrations
uv run python scripts/seed_dev_data.py  # Seed development data

# Pre-commit hooks setup
cd ../../
pre-commit install                   # Install git hooks
pre-commit run --all-files          # Run initial checks

# Verify setup
npm run dev:check                    # Verify all services can start
```

#### Development Commands

```bash
# Start all services in development mode
npm run dev                          # Start frontend, backend, and databases
# This runs:
# - Frontend: Next.js dev server on port 3000
# - Backend: FastAPI with hot reload on port 8000
# - PostgreSQL: Database on port 5432
# - Redis: Cache on port 6379
# - Caddy: Reverse proxy on port 80 (optional)

# Start individual services
npm run dev:frontend                 # Frontend only (port 3000)
npm run dev:backend                  # Backend only (port 8000)
npm run dev:db                       # Databases only

# Alternative: Docker development environment
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
# Provides identical environment across all developers

# Build commands
turbo build                          # Build all packages and applications
turbo build --filter=@iam/frontend  # Build frontend only
turbo build --filter=@iam/backend   # Build backend only

# Testing commands
turbo test                           # Run all tests
turbo test --filter=@iam/frontend   # Frontend tests only
turbo test --filter=@iam/backend    # Backend tests only
turbo test:e2e                       # End-to-end tests
turbo test:coverage                  # Test coverage reports

# Code quality commands
turbo lint                           # Lint all code
turbo lint:fix                       # Auto-fix linting issues
turbo format                         # Format all code
turbo typecheck                      # TypeScript type checking

# Database commands
cd apps/backend
uv run alembic revision --autogenerate -m "Description"  # Create migration
uv run alembic upgrade head          # Apply migrations
uv run alembic downgrade -1          # Rollback last migration
uv run python scripts/seed_dev_data.py  # Reseed development data

# Agent development commands
cd apps/backend
uv run python -m agents.client_agent  # Test individual agent
uv run python scripts/test_agents.py  # Test all agents
uv run python scripts/agent_monitor.py  # Monitor agent performance

# Infrastructure commands
cd infrastructure/terraform/environments/development
terraform init                       # Initialize Terraform
terraform plan                       # Plan infrastructure changes
terraform apply                      # Apply infrastructure changes

cd ../../ansible
ansible-playbook -i inventories/development deploy-application.yml  # Deploy via Ansible
```

### Environment Configuration

#### Required Environment Variables

```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000/v1
NEXT_PUBLIC_APP_NAME="IAM Dashboard"
NEXT_PUBLIC_ENVIRONMENT=development
NEXT_PUBLIC_VERSION=1.0.0

# Branding customization
NEXT_PUBLIC_DEFAULT_THEME=light
NEXT_PUBLIC_ENABLE_THEME_CUSTOMIZATION=true

# Analytics and monitoring (development)
NEXT_PUBLIC_ANALYTICS_ENABLED=false
NEXT_PUBLIC_SENTRY_DSN=""

# Backend (.env)
# Database configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/iam_dashboard
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis configuration
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# Security configuration
SECRET_KEY=your-super-secret-development-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API configuration
API_V1_PREFIX=/v1
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
PROJECT_NAME="IAM Dashboard API"
PROJECT_VERSION=1.0.0

# External service APIs (development)
OPENAI_API_KEY=your-openai-api-key
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
SENDGRID_API_KEY=your-sendgrid-api-key

# VPS Provider APIs (development - use test/sandbox)
DIGITALOCEAN_TOKEN=your-digitalocean-token
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-east-1

# Monitoring and logging
LOG_LEVEL=DEBUG
ENABLE_DETAILED_LOGGING=true
SENTRY_DSN=""
DATADOG_API_KEY=""

# Development features
ENABLE_DEV_ENDPOINTS=true
ENABLE_AGENT_DEBUG_MODE=true
ENABLE_PERFORMANCE_MONITORING=true

# Shared environment variables
# PostgreSQL (for Docker Compose)
POSTGRES_DB=iam_dashboard
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis (for Docker Compose)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=""

# Application configuration
APP_ENV=development
TZ=UTC
```

---

## Deployment Architecture

I'll define the comprehensive deployment strategy that supports the custom implementation service model, enabling automated VPS provisioning, application deployment, and client-specific customizations within the 30-day implementation promise.

### Deployment Strategy

**Frontend Deployment:**
- **Platform:** Vercel (primary) with DigitalOcean App Platform (fallback)
- **Build Command:** `turbo build --filter=@iam/frontend`
- **Output Directory:** `apps/frontend/.next`
- **CDN/Edge:** Vercel Edge Network with global distribution and automatic image optimization

**Backend Deployment:**
- **Platform:** Self-hosted on client VPS instances via Docker Compose
- **Build Command:** `docker build -f apps/backend/Dockerfile.prod`
- **Deployment Method:** Blue-green deployment with Ansible automation and health checks

**Database Deployment:**
- **Platform:** PostgreSQL 17.5 on client VPS with automated backups
- **Migration Strategy:** Alembic migrations with rollback capability
- **Backup Strategy:** Daily automated backups with 30-day retention and cross-region storage

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml - Continuous Integration
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  NODE_VERSION: '18.17.0'
  PYTHON_VERSION: '3.11'

jobs:
  # Frontend CI
  frontend-ci:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build shared packages
        run: turbo build --filter=@iam/shared

      - name: Lint frontend
        run: turbo lint --filter=@iam/frontend

      - name: Type check frontend
        run: turbo typecheck --filter=@iam/frontend

      - name: Test frontend
        run: turbo test --filter=@iam/frontend

      - name: Build frontend
        run: turbo build --filter=@iam/frontend

  # Backend CI
  backend-ci:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg17
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7.2-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v3
        with:
          version: "0.8.4"

      - name: Setup Python
        run: uv python install ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          cd apps/backend
          uv sync

      - name: Run database migrations
        run: |
          cd apps/backend
          uv run alembic upgrade head
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db

      - name: Lint backend
        run: |
          cd apps/backend
          uv run ruff check src/
          uv run ruff format --check src/

      - name: Type check backend
        run: |
          cd apps/backend
          uv run mypy src/

      - name: Test backend
        run: |
          cd apps/backend
          uv run pytest --cov=src --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0

  # Security Scans
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

### Environments

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|-------------|-------------|---------|
| Development | http://localhost:3000 | http://localhost:8000 | Local development and testing |
| Staging | https://staging.iamdashboard.com | https://api-staging.iamdashboard.com | Pre-production testing and QA |
| Production | https://app.iamdashboard.com | https://api.iamdashboard.com | Service provider management interface |
| Client Instances | https://client-name.com | https://api.client-name.com | Individual client implementations |

---

## Security and Performance

I'll define comprehensive security and performance considerations for the Multi-Agent IAM Dashboard that ensure enterprise-grade security standards while maintaining optimal performance across all client implementations.

### Security Requirements

**Frontend Security:**
- CSP Headers: `default-src 'self'; script-src 'self' 'unsafe-inline' https://vercel.live; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.*.com;`
- XSS Prevention: Content Security Policy, input sanitization with DOMPurify, React's built-in XSS protection
- Secure Storage: JWT tokens in httpOnly cookies, sensitive data encrypted in localStorage with Web Crypto API

**Backend Security:**
- Input Validation: Comprehensive Pydantic validation on all endpoints with custom validators for SSN, email, and business rules
- Rate Limiting: 100 requests per minute per IP, 1000 requests per hour per authenticated user, progressive backoff for repeated violations
- CORS Policy: Restricted to approved origins only, credentials allowed for authenticated requests, preflight caching enabled

**Authentication Security:**
- Token Storage: JWT access tokens (30min expiry) in httpOnly cookies, refresh tokens (7 days) in secure httpOnly cookies with SameSite=Strict
- Session Management: Redis-based session storage with automatic cleanup, concurrent session limits per user, session invalidation on password change
- Password Policy: Minimum 12 characters, mixed case, numbers, symbols required, bcrypt hashing with cost factor 12, password history prevention (last 5 passwords)

### Performance Optimization

**Frontend Performance:**
- Bundle Size Target: < 250KB initial bundle, < 100KB per route chunk, tree shaking enabled for all dependencies
- Loading Strategy: Server-side rendering for initial page load, progressive hydration, lazy loading for below-fold components
- Caching Strategy: Service worker for static assets (1 year), API responses cached for 5 minutes, browser cache headers optimized

**Backend Performance:**
- Response Time Target: < 200ms for 95% of requests, < 500ms for 99% of requests, < 1000ms for complex operations
- Database Optimization: Query optimization with EXPLAIN ANALYZE, indexed foreign keys and search fields, connection pooling with 20-50 connections
- Caching Strategy: Redis caching for user sessions (30min TTL), database query results (5min TTL), computed aggregations (1 hour TTL)

---

## Testing Strategy

I'll define a comprehensive testing approach for the Multi-Agent IAM Dashboard that ensures reliability across the fullstack application, multi-agent interactions, and client-specific customizations.

### Testing Pyramid

```
                  E2E Tests
                 /        \
            Integration Tests
               /            \
          Frontend Unit  Backend Unit
```

**Test Distribution Target:**
- **Unit Tests**: 70% of total tests (fast, isolated, comprehensive coverage)
- **Integration Tests**: 20% of total tests (API endpoints, database interactions, agent communication)
- **E2E Tests**: 10% of total tests (critical user workflows, cross-browser compatibility)

### Test Organization

#### Frontend Tests

```
apps/frontend/tests/
├── __mocks__/                     # Test mocks and fixtures
├── components/                    # Component tests
├── hooks/                         # Custom hook tests
├── services/                      # Service layer tests
├── pages/                         # Page component tests
├── utils/                         # Utility function tests
├── integration/                   # Frontend integration tests
├── setup.ts                       # Test setup and configuration
└── vitest.config.ts              # Vitest configuration
```

#### Backend Tests

```
apps/backend/tests/
├── conftest.py                    # pytest configuration and fixtures
├── factories/                     # Test data factories
├── unit/                          # Unit tests
│   ├── models/                    # Model tests
│   ├── services/                  # Service layer tests
│   ├── repositories/              # Repository tests
│   ├── utils/                     # Utility tests
│   └── agents/                    # Agent unit tests
├── integration/                   # Integration tests
├── e2e/                          # End-to-end tests
├── performance/                   # Performance tests
├── security/                      # Security tests
└── fixtures/                      # Test data fixtures
```

#### E2E Tests

```
tests/e2e/
├── specs/                         # E2E test specifications
│   ├── auth/                      # Authentication flows
│   ├── clients/                   # Client management workflows
│   ├── users/                     # User management (admin)
│   ├── branding/                  # Custom branding system
│   ├── agents/                    # Multi-agent workflows
│   └── cross-browser/             # Cross-browser compatibility
├── fixtures/                      # E2E test fixtures
├── page-objects/                  # Page object models
├── utils/                         # E2E test utilities
└── playwright.config.ts           # Playwright configuration
```

---

## Coding Standards

I'll define minimal but critical coding standards specifically focused on preventing common mistakes in AI-driven fullstack development while maintaining code quality and consistency across the Multi-Agent IAM Dashboard project.

### Critical Fullstack Rules

- **Type Sharing:** Always define types in packages/shared and import from there - prevents type inconsistencies between frontend and backend
- **API Calls:** Never make direct HTTP calls - use the service layer to ensure consistent error handling and authentication
- **Environment Variables:** Access only through config objects, never process.env directly - prevents configuration issues in production
- **Error Handling:** All API routes must use the standard error handler - ensures consistent error responses across the application
- **State Updates:** Never mutate state directly - use proper state management patterns to prevent React rendering issues
- **Database Queries:** Always use repository pattern - prevents SQL injection and ensures consistent data access
- **Agent Communication:** Agents communicate only through database, never direct function calls - maintains agent independence
- **Authentication:** Always validate JWT tokens in middleware, never in route handlers - ensures security consistency
- **File Uploads:** All file uploads must include validation and virus scanning - prevents security vulnerabilities
- **Audit Logging:** All data modifications must trigger audit logs - ensures compliance and traceability
- **Permission Checks:** Use permission decorators, never inline permission logic - ensures consistent access control
- **CSS Variables:** Use CSS custom properties for all theming, never hardcoded colors - enables custom branding system
- **Component Props:** Always destructure props with TypeScript interfaces - prevents prop drilling and type errors
- **Async Operations:** Always handle loading and error states in UI components - ensures good user experience
- **Database Migrations:** Never modify existing migrations, always create new ones - prevents deployment issues

### Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| Components | PascalCase | - | `UserProfile.tsx` |
| Hooks | camelCase with 'use' | - | `useAuth.ts` |
| Services | camelCase with 'Service' | camelCase with 'Service' | `AuthService`, `client_service.py` |
| API Routes | - | kebab-case | `/api/user-profile` |
| Database Tables | - | snake_case | `user_profiles` |
| Environment Variables | SCREAMING_SNAKE_CASE | SCREAMING_SNAKE_CASE | `DATABASE_URL` |
| Constants | SCREAMING_SNAKE_CASE | SCREAMING_SNAKE_CASE | `MAX_FILE_SIZE` |
| Functions | camelCase | snake_case | `handleSubmit`, `create_client` |
| Interfaces/Types | PascalCase with 'I' prefix | PascalCase | `IUserProfile`, `UserCreate` |

---

## Error Handling Strategy

I'll define a unified error handling approach across the fullstack Multi-Agent IAM Dashboard that ensures consistent user experience, proper debugging information, and reliable system operation.

### Error Flow

```mermaid
sequenceDiagram
    participant User as User
    participant FE as Frontend
    participant API as FastAPI Backend
    participant Agent as Multi-Agent System
    participant DB as PostgreSQL
    participant Monitor as Monitoring System

    User->>FE: Perform Action
    FE->>API: API Request
    
    alt Validation Error
        API->>API: Validate Input
        API-->>FE: 400 Bad Request
        FE->>FE: Show Validation Error
        FE-->>User: User-Friendly Message
    
    else Business Logic Error
        API->>Agent: Process Request
        Agent->>DB: Database Operation
        DB-->>Agent: Constraint Violation
        Agent-->>API: Business Error
        API->>Monitor: Log Error Details
        API-->>FE: 422 Unprocessable Entity
        FE->>FE: Handle Business Error
        FE-->>User: Contextual Error Message
    
    else System Error
        API->>DB: Database Operation
        DB-->>API: Connection Error
        API->>Monitor: Log Critical Error
        API->>API: Attempt Retry/Fallback
        
        alt Retry Successful
            API-->>FE: 200 Success (Delayed)
            FE-->>User: Success Message
        else Retry Failed
            API-->>FE: 503 Service Unavailable
            FE->>FE: Show System Error
            FE-->>User: "Please Try Again" Message
        end
    
    else Agent Communication Error
        API->>Agent: Agent Request
        Agent->>DB: Database Communication
        DB-->>Agent: Timeout/Error
        Agent->>Agent: Fallback to Direct Database
        Agent-->>API: Partial Success Response
        API-->>FE: 206 Partial Content
        FE->>FE: Show Partial Success Warning
        FE-->>User: "Action Completed with Warnings"
    end
```

### Error Response Format

```typescript
// Standardized error response interface
interface ApiError {
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable error message
    details?: Record<string, any>; // Additional error context
    timestamp: string;      // ISO 8601 timestamp
    requestId: string;      // Unique request identifier for tracking
    field?: string;         // Specific field causing validation error
    retryable?: boolean;    // Whether the operation can be retried
  };
}

// Success response interface for consistency
interface ApiResponse<T> {
  success: true;
  data: T;
  message?: string;
  timestamp: string;
  requestId: string;
}
```

---

## Monitoring and Observability

I'll define a comprehensive monitoring strategy for the Multi-Agent IAM Dashboard that ensures 99.9% uptime SLA across all client implementations while providing deep insights into system performance, user behavior, and agent operations.

### Monitoring Stack

- **Frontend Monitoring:** Sentry for error tracking and performance monitoring, Vercel Analytics for Core Web Vitals
- **Backend Monitoring:** Datadog APM for request tracing and performance insights, custom metrics for business logic
- **Error Tracking:** Sentry for both frontend and backend with automated issue grouping and alerting
- **Performance Monitoring:** Datadog for infrastructure metrics, custom dashboards for agent performance tracking

### Key Metrics

**Frontend Metrics:**
- Core Web Vitals: Largest Contentful Paint (LCP < 2.5s), First Input Delay (FID < 100ms), Cumulative Layout Shift (CLS < 0.1)
- JavaScript errors: Error rate < 1%, critical errors = 0, unhandled promise rejections
- API response times: 95th percentile < 500ms, 99th percentile < 1000ms
- User interactions: Page load success rate > 99.5%, form submission success rate > 99%

**Backend Metrics:**
- Request rate: Requests per second across all endpoints, peak load handling capacity
- Error rate: HTTP 4xx errors < 2%, HTTP 5xx errors < 0.1%, timeout rate < 0.01%
- Response time: Median < 200ms, 95th percentile < 500ms, 99th percentile < 1000ms  
- Database query performance: Query execution time < 100ms for 95% of queries, connection pool utilization < 80%

**Multi-Agent System Metrics:**
- Agent response time: Processing time per agent operation, agent-to-agent communication latency
- Agent success rate: Successful operation completion rate > 99%, agent failure recovery time < 30 seconds
- Database communication: Agent database query performance, concurrent agent operation handling
- AI processing metrics: OpenAI API response times, token usage optimization, processing accuracy rates

**Infrastructure Metrics:**
- System resources: CPU utilization < 70%, memory usage < 80%, disk usage < 85%
- Network performance: Bandwidth utilization, connection latency, packet loss < 0.01%
- Database performance: Connection count, query cache hit rate > 95%, replication lag < 1 second
- Container health: Container restart frequency, resource limits adherence, health check success rate

---

*Architecture document completed on August 1, 2025*  
*Ready for development team handoff and implementation*

**Document Status**: ✅ Complete  
**Next Phase**: Development Sprint Planning & Team Assignments  
**Estimated Implementation**: 16-20 weeks with dedicated fullstack development team