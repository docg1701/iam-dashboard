# Multi-Agent IAM Dashboard Fullstack Architecture Document

*Generated on August 1, 2025 - Version 1.0*

---

## 1. Introduction

This document outlines the complete fullstack architecture for **Multi-Agent IAM Dashboard**, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This unified approach combines what would traditionally be separate backend and frontend architecture documents, streamlining the development process for modern fullstack applications where these concerns are increasingly intertwined.

### Starter Template Analysis

**Status**: **N/A - Greenfield Project**

After reviewing the PRD and existing CLAUDE.md documentation, this is a greenfield implementation with a clear technology stack already specified. The project follows established patterns:
- **Backend**: FastAPI + SQLModel + PostgreSQL (chosen for ACID compliance and structured relationships)
- **Frontend**: Next.js 15 + React 19 + TypeScript + shadcn/ui (selected for modern responsive design)
- **Multi-Agent Framework**: Agno for efficient agent instantiation 
- **Deployment**: Custom VPS deployment model using Docker Compose + Terraform + Ansible

The architecture constraints are well-defined in the Project Brief, eliminating the need for starter template evaluation.

### Key Architectural Decisions Made

1. **Custom Implementation Service Model**: Each client gets dedicated VPS instances rather than multi-tenant SaaS, enabling complete brand customization and data isolation
2. **Monolith + Independent Agents Pattern**: Core platform (FastAPI + Next.js) with independent AI agents communicating through shared PostgreSQL database
3. **Full Customization Focus**: Complete branding system using CSS variables enabling visual identity transformation
4. **Deployment Automation**: Terraform + Ansible automation targeting 3-4 week implementation cycles

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|---------|
| 2025-08-01 | 1.0 | Initial architecture document creation | Winston (Architect) |

---

## 2. High Level Architecture

### Technical Summary

The Multi-Agent IAM Dashboard implements a **Custom Implementation Service** architecture delivering dedicated VPS instances with complete brand customization. The system uses a **monolithic core platform** (FastAPI backend + Next.js 15 frontend) supporting **independent AI agents** that communicate through a shared PostgreSQL database. Each client receives their own isolated VPS deployment with full visual branding integration via CSS variables and shadcn/ui theming. The infrastructure leverages **automated deployment pipelines** using Terraform for VPS provisioning and Ansible for configuration management, enabling consistent 3-4 week implementation cycles that justify premium pricing through complete customization.

### Platform and Infrastructure Choice

**Platform**: **Custom VPS + AWS/DigitalOcean Hybrid**

**Core Services**:
- **VPS Providers**: DigitalOcean Droplets or AWS EC2 for client instances
- **DNS Management**: Cloudflare for domain automation and SSL
- **Monitoring**: DataDog or AWS CloudWatch for multi-instance monitoring
- **Backup Storage**: AWS S3 or Backblaze B2 for cross-region backup storage
- **Container Registry**: Docker Hub or AWS ECR for image management

**Deployment Host and Regions**: Multi-region deployment (US-East, US-West, EU-West) based on client geographic requirements

### Repository Structure

**Structure**: **Monorepo with Workspaces**
**Monorepo Tool**: **npm workspaces** (simpler than Nx/Turborepo for this scale)
**Package Organization**: **Feature-based separation with shared utilities**

### High Level Architecture Diagram

```mermaid
graph TB
    subgraph "Client VPS Instance"
        subgraph "Frontend Layer"
            A[Next.js 15 App] --> B[shadcn/ui Components]
            B --> C[Custom Branding System]
        end
        
        subgraph "Backend Layer"
            D[FastAPI API] --> E[SQLModel ORM]
            E --> F[PostgreSQL + pgvector]
        end
        
        subgraph "Agent Layer"
            G[Client Management Agent] --> F
            H[PDF Processing Agent] --> F
            I[Reports Agent] --> F
            J[Audio Recording Agent] --> F
        end
        
        subgraph "Infrastructure"
            K[Caddy Reverse Proxy] --> A
            K --> D
            L[Docker Compose] --> K
            L --> A
            L --> D
            L --> F
        end
    end
    
    subgraph "Service Provider Infrastructure"
        M[Terraform Scripts] --> L
        N[Ansible Playbooks] --> L
        O[Monitoring Dashboard] --> K
        P[Backup System] --> F
    end
    
    Q[Client Users] --> K
    R[Service Provider] --> M
    R --> N
    R --> O
```

### Architectural Patterns

- **Custom Implementation Service**: Dedicated VPS per client with complete isolation and branding - *Rationale:* Enables premium pricing through true customization vs. generic SaaS limitations
- **Monolith + Independent Agents**: Core platform with autonomous AI agents - *Rationale:* Simplifies deployment while allowing agent independence and specialized functionality
- **Database-Centric Communication**: Agents communicate through shared PostgreSQL - *Rationale:* Ensures data consistency and simplifies inter-agent dependencies
- **CSS Variable Theming**: Complete visual customization via CSS variables - *Rationale:* Enables real-time brand application without code changes
- **Infrastructure as Code**: Terraform + Ansible automation - *Rationale:* Ensures consistent deployments and reduces implementation time from months to weeks
- **Container-First Deployment**: Docker Compose over Kubernetes - *Rationale:* Simpler per-client deployment model with lower operational complexity
- **Progressive Web App**: Next.js with service worker for offline capability - *Rationale:* Professional user experience with mobile and offline support

---

## 3. Tech Stack

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

---

## 4. Data Models

Based on the PRD requirements and multi-agent architecture, the core data models enable TypeScript interfaces that can be used across the entire stack.

### User Model
**Purpose:** Authentication and authorization management with role-based access control

```typescript
interface User {
  user_id: string;
  email: string;
  role: 'sysadmin' | 'admin' | 'user';
  is_active: boolean;
  totp_enabled: boolean;
  created_at: string; // ISO 8601 timestamp
  updated_at: string; // ISO 8601 timestamp
  last_login?: string; // ISO 8601 timestamp
}

interface UserCreate {
  email: string;
  password: string;
  role: 'sysadmin' | 'admin' | 'user';
}

interface UserUpdate {
  email?: string;
  role?: 'sysadmin' | 'admin' | 'user';
  is_active?: boolean;
}
```

### Client Model  
**Purpose:** Core business entity for client management with comprehensive data validation

```typescript
interface Client {
  client_id: string;
  full_name: string;
  ssn: string; // Format: XXX-XX-XXXX
  birth_date: string; // ISO 8601 date format
  status: 'active' | 'inactive' | 'archived';
  created_by: string; // User ID reference
  updated_by: string; // User ID reference
  created_at: string; // ISO 8601 timestamp
  updated_at: string; // ISO 8601 timestamp
  notes?: string;
}

interface ClientCreate {
  full_name: string;
  ssn: string;
  birth_date: string;
  notes?: string;
}

interface ClientUpdate {
  full_name?: string;
  ssn?: string;
  birth_date?: string;
  status?: 'active' | 'inactive' | 'archived';
  notes?: string;
}

interface ClientSearch {
  query?: string; // Name or SSN search
  status?: 'active' | 'inactive' | 'archived';
  created_after?: string;
  created_before?: string;
  birth_after?: string;
  birth_before?: string;
}
```

### AuditLog Model
**Purpose:** Comprehensive audit trail for all system modifications and access

```typescript
interface AuditLog {
  audit_id: string;
  table_name: string;
  record_id: string;
  action: 'CREATE' | 'UPDATE' | 'DELETE' | 'VIEW';
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  user_id: string;
  ip_address: string;
  user_agent: string;
  timestamp: string; // ISO 8601 timestamp
}
```

### Agent2Document Model
**Purpose:** PDF document management and vector storage for RAG processing

```typescript
interface Agent2Document {
  document_id: string;
  client_id: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  vector_chunks?: Record<string, any>[];
  extraction_metadata?: Record<string, any>;
  uploaded_by: string;
  uploaded_at: string;
  processed_at?: string;
}
```

---

## 5. API Specification

Based on the chosen REST API style, comprehensive OpenAPI 3.0 specification covering all endpoints from PRD requirements:

### REST API Specification

```yaml
openapi: 3.0.3
info:
  title: Multi-Agent IAM Dashboard API
  version: 1.0.0
  description: |
    REST API for the Multi-Agent IAM Dashboard - a custom implementation service
    providing dedicated VPS instances with independent AI agents for client management.

servers:
  - url: https://api.{client-domain}.com/v1
    description: Production client instance
  - url: http://localhost:8000/v1
    description: Local development server

security:
  - BearerAuth: []

paths:
  /auth/login:
    post:
      tags: [Authentication]
      summary: User login with email and password
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
      responses:
        '200':
          description: Login successful, returns JWT token
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  token_type:
                    type: string
                    example: "bearer"
                  expires_in:
                    type: integer
                    example: 3600
                  requires_2fa:
                    type: boolean

  /clients:
    get:
      tags: [Clients]
      summary: List and search clients
      parameters:
        - name: query
          in: query
          schema:
            type: string
        - name: status
          in: query
          schema:
            type: string
            enum: [active, inactive, archived]
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        '200':
          description: List of clients with pagination
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/Client'
                  total:
                    type: integer
                  page:
                    type: integer
                  limit:
                    type: integer
                  pages:
                    type: integer

    post:
      tags: [Clients]
      summary: Create a new client
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ClientCreate'
      responses:
        '201':
          description: Client created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Client'

  /clients/{client_id}:
    get:
      tags: [Clients]
      summary: Get a single client by ID
      parameters:
        - name: client_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Client details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Client'
        '404':
          description: Client not found
    put:
      tags: [Clients]
      summary: Update an existing client
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
              $ref: '#/components/schemas/ClientUpdate'
      responses:
        '200':
          description: Client updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Client'
        '404':
          description: Client not found
    delete:
      tags: [Clients]
      summary: Delete a client
      parameters:
        - name: client_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: Client deleted successfully
        '404':
          description: Client not found

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Client:
      type: object
      required: [client_id, full_name, ssn, birth_date, status]
      properties:
        client_id:
          type: string
          format: uuid
        full_name:
          type: string
        ssn:
          type: string
          pattern: '^\d{3}-\d{2}-\d{4}$'
        birth_date:
          type: string
          format: date
        status:
          type: string
          enum: [active, inactive, archived]
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    ClientUpdate:
      type: object
      properties:
        full_name:
          type: string
          minLength: 2
          maxLength: 255
        ssn:
          type: string
          pattern: '^\d{3}-\d{2}-\d{4}$'
        birth_date:
          type: string
          format: date
        status:
          type: string
          enum: [active, inactive, archived]
        notes:
          type: string
          maxLength: 1000

    ClientCreate:
      type: object
      required: [full_name, ssn, birth_date]
      properties:
        full_name:
          type: string
          minLength: 2
          maxLength: 255
        ssn:
          type: string
          pattern: '^\d{3}-\d{2}-\d{4}$'
        birth_date:
          type: string
          format: date
        notes:
          type: string
          maxLength: 1000
```

---

## 6. Components

Major logical components across the fullstack system with clear boundaries and interfaces:

### Frontend Components

#### Component Interaction Diagram

```mermaid
graph TD
    subgraph User Interface
        Frontend[Next.js Frontend]
    end

    subgraph Backend Services
        APIServer[FastAPI Server]
        Agent1[Client Agent]
        Agent2[PDF Agent]
        Agent3[Report Agent]
    end

    subgraph Data Storage
        Database[(PostgreSQL)]
        Cache[(Redis)]
    end

    subgraph External Services
        OpenAI[OpenAI Embeddings]
    end

    Frontend -->|REST API Calls| APIServer
    APIServer -->|Database Queries| Database
    APIServer -->|Cache Operations| Cache
    APIServer -->|Triggers Agent| Agent1
    APIServer -->|Triggers Agent| Agent2
    APIServer -->|Triggers Agent| Agent3

    Agent1 -->|CRUD Operations| Database
    Agent2 -->|CRUD Operations| Database
    Agent2 -->|API Call| OpenAI
    Agent3 -->|Reads Data| Database
```

#### Authentication Component
**Responsibility:** Handle user login, 2FA verification, and session management with secure token storage

**Key Interfaces:**
- LoginForm: Email/password authentication interface
- TwoFactorAuth: TOTP code verification interface  
- AuthContext: React context for authentication state management
- AuthGuard: Route protection component for role-based access

**Technology Stack:** Next.js 15 App Router, React 19 Context, TanStack Query for auth state, Zod validation

#### Client Management Component
**Responsibility:** Complete CRUD operations for client data with search, filtering, and bulk operations

**Key Interfaces:**
- ClientList: Paginated table with search and filtering
- ClientForm: Create/edit client information with validation
- ClientDetail: Individual client profile view with audit history
- BulkOperations: Multi-select actions and CSV import/export

**Technology Stack:** shadcn/ui Table components, React Hook Form with Zod validation, TanStack Query for data fetching

#### Custom Branding Component
**Responsibility:** Real-time visual branding customization using CSS variables and asset management

**Key Interfaces:**
- BrandingPanel: Color scheme and typography customization
- AssetUploader: Logo and favicon management
- ThemePreview: Real-time preview of branding changes
- BrandExporter: Save and deploy branding configurations

**Technology Stack:** Tailwind CSS variables, shadcn/ui theming system, React color picker components

### Backend Components

#### FastAPI Core Application
**Responsibility:** Central API server handling authentication, routing, middleware, and core business logic

**Key Interfaces:**
- REST API endpoints following OpenAPI 3.0 specification
- JWT authentication middleware with role-based access control
- Request/response validation using Pydantic models
- CORS and security headers configuration

**Technology Stack:** FastAPI 0.115+, SQLModel ORM, Pydantic validation, Uvicorn ASGI server

#### Database Access Layer
**Responsibility:** Centralized data access with SQLModel ORM, connection pooling, and transaction management

**Key Interfaces:**
- ClientRepository: CRUD operations for client data
- UserRepository: User management and authentication queries
- AuditRepository: Audit trail logging and retrieval
- Database session management and connection pooling

**Technology Stack:** SQLModel ORM, asyncpg PostgreSQL driver, Alembic migrations

### Agent Components (Independent)

#### Client Management Agent (Agent 1)
**Responsibility:** Autonomous client data operations with validation, deduplication, and audit trail integration

**Key Interfaces:**
- Client registration with SSN validation and duplicate prevention
- Advanced search and filtering capabilities
- Bulk operations for data import/export
- Direct database access to clients table

**Technology Stack:** Agno framework, SQLModel for database access, Pydantic validation

#### PDF Processing Agent (Agent 2)  
**Responsibility:** Document upload, RAG processing with vector embeddings, and searchable document management

**Key Interfaces:**
- File upload processing with validation
- PDF text extraction and chunking
- Vector embedding generation and storage
- Document search and retrieval via vector similarity

**Technology Stack:** Agno framework, pgvector extension, PyPDF2 for text extraction, OpenAI embeddings

---

## 7. External APIs

The Multi-Agent IAM Dashboard has minimal external API dependencies due to its custom implementation service model focusing on data isolation and self-contained functionality.

### OpenAI Embeddings API (Agent 2 - PDF Processing)

- **Purpose:** Generate vector embeddings for PDF document chunks to enable semantic search and RAG capabilities
- **Documentation:** https://platform.openai.com/docs/api-reference/embeddings
- **Base URL:** https://api.openai.com/v1
- **Authentication:** Bearer token (API key)
- **Rate Limits:** 3,000 requests per minute, 1,000,000 tokens per minute

**Key Endpoints Used:**
- `POST /embeddings` - Generate embeddings for text chunks from PDF documents

### Let's Encrypt ACME API (Infrastructure)

- **Purpose:** Automatic SSL certificate provisioning and renewal for client domain configurations
- **Documentation:** https://letsencrypt.org/docs/acme-protocol-updates/
- **Base URL:** https://acme-v02.api.letsencrypt.org
- **Authentication:** ACME protocol with domain validation
- **Rate Limits:** 50 certificates per registered domain per week

**Integration Notes:** Handled automatically by Caddy reverse proxy during VPS deployment. No direct API integration required in application code.

---

## 8. Core Workflows

Key system workflows using sequence diagrams showing component interactions, including both frontend and backend flows with error handling paths.

### Client Registration Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (Next.js)
    participant API as FastAPI Core
    participant DB as PostgreSQL
    participant A1 as Client Agent
    participant AL as Audit Logger

    U->>F: Navigate to Add Client
    F->>F: Render ClientForm component
    U->>F: Fill client details (name, SSN, birthdate)
    F->>F: Real-time validation (Zod)
    
    alt Invalid Data
        F-->>U: Show validation errors
    else Valid Data
        U->>F: Submit form
        F->>API: POST /v1/clients
        API->>API: JWT token validation
        API->>API: Pydantic model validation
        
        alt SSN Duplicate Check
            API->>DB: Query existing SSN
            DB-->>API: SSN exists
            API-->>F: 409 Conflict Error
            F-->>U: Display "SSN already exists"
        else SSN Available
            API->>A1: Trigger client creation
            A1->>DB: INSERT into clients table
            DB-->>A1: Client created successfully
            A1->>AL: Log CREATE action
            AL->>DB: INSERT into audit_log
            A1-->>API: Return created client
            API-->>F: 201 Created with client data
            F->>F: Update client list cache
            F-->>U: Success message + redirect to client detail
        end
    end
```

### Authentication with 2FA Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as FastAPI Auth
    participant Redis as Redis Cache
    participant DB as PostgreSQL
    participant TOTP as TOTP Service

    U->>F: Enter email/password
    F->>API: POST /v1/auth/login
    API->>DB: Validate credentials
    
    alt Invalid Credentials
        DB-->>API: User not found/wrong password
        API-->>F: 401 Unauthorized
        F-->>U: Display login error
    else Valid Credentials
        DB-->>API: User found, check 2FA status
        
        alt 2FA Disabled
            API->>API: Generate JWT token
            API->>Redis: Store session data
            API-->>F: 200 OK with access_token
            F->>F: Store token, update auth state
            F-->>U: Redirect to dashboard
        else 2FA Enabled
            API->>API: Generate temporary token
            API-->>F: 200 OK with temp_token + requires_2fa: true
            F-->>U: Show 2FA input form
            
            U->>F: Enter TOTP code
            F->>API: POST /v1/auth/2fa/verify
            API->>TOTP: Validate TOTP code
            
            alt Invalid TOTP
                TOTP-->>API: Invalid code
                API-->>F: 401 Unauthorized
                F-->>U: Show 2FA error
            else Valid TOTP
                TOTP-->>API: Valid code
                API->>API: Generate final JWT token
                API->>Redis: Store session data
                API->>DB: Update last_login timestamp
                API-->>F: 200 OK with access_token
                F->>F: Store token, update auth state
                F-->>U: Redirect to dashboard
            end
        end
    end
```

---

## 9. Database Schema

Complete PostgreSQL 16.x + pgvector schema with proper indexing, constraints, and relationships optimized for the multi-agent architecture:

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Users table for authentication and authorization
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('sysadmin', 'admin', 'user')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    totp_secret VARCHAR(32), -- Base32 encoded TOTP secret
    totp_enabled BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_password_length CHECK (length(password_hash) >= 60)
);

-- Clients table (Agent 1 primary responsibility)
CREATE TABLE clients (
    client_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    ssn VARCHAR(11) NOT NULL UNIQUE, -- Format: XXX-XX-XXXX
    birth_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    notes TEXT,
    created_by UUID NOT NULL REFERENCES users(user_id),
    updated_by UUID NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT clients_ssn_format CHECK (ssn ~ '^\d{3}-\d{2}-\d{4}$'),
    CONSTRAINT clients_name_length CHECK (length(trim(full_name)) >= 2),
    CONSTRAINT clients_birth_date_range CHECK (
        birth_date >= '1900-01-01' AND 
        birth_date <= CURRENT_DATE - INTERVAL '13 years'
    )
);

-- Documents table (Agent 2 primary responsibility)
CREATE TABLE agent2_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0),
    mime_type VARCHAR(100) NOT NULL,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    vector_chunks JSONB, -- Array of {text, embedding, metadata} objects
    extraction_metadata JSONB, -- PDF metadata, page count, etc.
    uploaded_by UUID NOT NULL REFERENCES users(user_id),
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT documents_filename_length CHECK (length(original_filename) <= 255),
    CONSTRAINT documents_mime_type_pdf CHECK (mime_type = 'application/pdf'),
    CONSTRAINT documents_file_size_limit CHECK (file_size <= 52428800) -- 50MB limit
);

-- Comprehensive audit log table
CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'VIEW')),
    old_values JSONB,
    new_values JSONB,
    user_id UUID REFERENCES users(user_id),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT audit_table_name_valid CHECK (
        table_name IN ('users', 'clients', 'agent2_documents', 'agent3_reports', 'agent4_recordings')
    )
);

-- Performance indexes
CREATE INDEX idx_clients_full_name ON clients USING gin(to_tsvector('english', full_name));
CREATE INDEX idx_clients_ssn ON clients(ssn);
CREATE INDEX idx_clients_status ON clients(status);
CREATE INDEX idx_clients_created_at ON clients(created_at DESC);

CREATE INDEX idx_documents_client_id ON agent2_documents(client_id);
CREATE INDEX idx_documents_status ON agent2_documents(processing_status);
CREATE INDEX idx_documents_vector_chunks ON agent2_documents USING gin(vector_chunks);

CREATE INDEX idx_audit_table_name ON audit_log(table_name);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);

-- Automated timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Audit logging function
CREATE OR REPLACE FUNCTION log_audit_trail(
    p_table_name VARCHAR(50),
    p_record_id UUID,
    p_action VARCHAR(10),
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL,
    p_user_id UUID DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    audit_id UUID;
BEGIN
    INSERT INTO audit_log (
        table_name, record_id, action, old_values, new_values,
        user_id, ip_address, user_agent
    ) VALUES (
        p_table_name, p_record_id, p_action, p_old_values, p_new_values,
        p_user_id, p_ip_address, p_user_agent
    ) RETURNING audit_log.audit_id INTO audit_id;
    
    RETURN audit_id;
END;
$$ language 'plpgsql';
```

---

## 10. Frontend Architecture

Frontend-specific architecture details based on Next.js 15 + React 19 + shadcn/ui with comprehensive custom branding support:

### Component Architecture

**Component Organization:**
```
apps/frontend/src/
├── app/                          # Next.js 15 App Router
│   ├── (auth)/                   # Route group for authentication
│   ├── (dashboard)/              # Protected dashboard routes
│   ├── globals.css               # Global styles + CSS variables
│   ├── layout.tsx                # Root layout with providers
│   └── page.tsx                  # Public homepage
├── components/                   # Reusable UI components
│   ├── ui/                       # shadcn/ui base components
│   ├── forms/                    # Complex form components
│   ├── layout/                   # Layout components
│   └── features/                 # Feature-specific components
├── lib/                          # Utilities and configurations
├── hooks/                        # Custom React hooks
├── store/                        # Client state management
└── types/                        # TypeScript type definitions
```

### State Management Architecture

**State Structure:**
```typescript
// Authentication Store (Zustand)
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  requires2FA: boolean
  tempToken: string | null
  
  // Actions
  login: (email: string, password: string) => Promise<void>
  verify2FA: (code: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  setUser: (user: User) => void
}

// UI State Store (Zustand)
interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark' | 'system'
  currentBranding: BrandingConfig
  
  // Actions
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  updateBranding: (branding: BrandingConfig) => void
}
```

### Routing Architecture

**Route Organization:**
- `/` - Public homepage
- `/login` - Authentication page
- `/dashboard` - Protected dashboard home
- `/dashboard/clients` - Client list with search/filters
- `/dashboard/clients/new` - New client registration
- `/dashboard/clients/[id]` - Client detail and edit
- `/dashboard/users` - User management (admin only)
- `/dashboard/system` - System configuration

### Frontend Services Layer

**API Client Setup:**
```typescript
class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1',
      timeout: 30000,
    })

    // Request interceptor for authentication
    this.client.interceptors.request.use((config) => {
      const token = useAuthStore.getState().token
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Response interceptor for error handling and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const { refreshToken, logout } = useAuthStore.getState()
          try {
            await refreshToken()
            return this.client.request(error.config)
          } catch (refreshError) {
            logout()
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }
}
```

---

## 11. Backend Architecture

Backend-specific architecture details based on FastAPI + SQLModel + PostgreSQL with Agno agent framework integration:

### Service Architecture

**FastAPI Application Structure:**
```
apps/backend/src/
├── main.py                       # FastAPI application entry point
├── core/                         # Core system modules
│   ├── config.py                 # Environment configuration
│   ├── database.py               # Database connection and session management
│   ├── security.py               # Authentication and JWT handling
│   ├── exceptions.py             # Custom exception classes
│   └── middleware.py             # Custom middleware (CORS, logging, etc.)
├── api/                          # REST API routes
│   └── v1/                       # API version 1
│       ├── auth.py               # Authentication endpoints
│       ├── clients.py            # Client management endpoints
│       ├── users.py              # User management endpoints
│       └── audit.py              # Audit trail endpoints
├── services/                     # Business logic layer
├── models/                       # SQLModel database models
├── agents/                       # Agno agent implementations
├── schemas/                      # Pydantic request/response schemas
└── utils/                        # Utility functions
```

### Database Architecture

**SQLModel Integration:**
```python
class ClientBase(SQLModel):
    """Base client fields for sharing between models"""
    full_name: str = Field(min_length=2, max_length=255)
    ssn: str = Field(regex=r'^\d{3}-\d{2}-\d{4}$'
    birth_date: date
    status: ClientStatus = ClientStatus.ACTIVE
    notes: Optional[str] = Field(default=None, max_length=1000)

class Client(BaseModel, ClientBase, table=True):
    """Client database model"""
    __tablename__ = "clients"
    
    client_id: UUID = Field(primary_key=True, alias="id")
    created_by: UUID = Field(foreign_key="users.user_id")
    updated_by: UUID = Field(foreign_key="users.user_id")
    
    # Relationships
    creator: User = Relationship(back_populates="created_clients")
    documents: List["Agent2Document"] = Relationship(back_populates="client")
```

### Authentication and Authorization

**JWT Authentication Flow:**
```python
class AuthService:
    def create_access_token(self, user_id: str, user_role: str) -> dict:
        """Create secure JWT token with session tracking"""
        payload = {
            "sub": user_id,
            "role": user_role,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=15),
        }
        
        access_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 900
        }

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenData(user_id=UUID(payload["sub"]), role=payload["role"])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

---

## 12. Unified Project Structure

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

---

## 13. Development Workflow

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

---

## 14. Deployment Architecture

Deployment strategy based on the custom implementation service model with automated VPS provisioning:

### Deployment Strategy

**Frontend Deployment:**
- **Platform:** Dedicated VPS with Caddy reverse proxy
- **Build Command:** `npm run build`
- **Output Directory:** `.next` (Next.js static optimization)
- **CDN/Edge:** Caddy handles static file serving with automatic compression

**Backend Deployment:**
- **Platform:** Same VPS as frontend for cost efficiency
- **Build Command:** `uv sync --frozen` (production dependencies only)
- **Deployment Method:** Docker containers with health checks

**Database Deployment:**
- **Platform:** PostgreSQL container on same VPS
- **Data Persistence:** Docker volumes with automated backups

### Container Orchestration Strategy

```yaml
# docker-compose.prod.yml - Production deployment configuration
version: '3.8'

services:
  caddy:
    image: caddy:2-alpine
    container_name: iam-dashboard-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/docker/Caddyfile:/etc/caddy/Caddyfile:ro
      - ./apps/frontend/.next/static:/srv/static:ro
    environment:
      - DOMAIN=${CLIENT_DOMAIN}
    depends_on:
      - frontend
      - backend

  frontend:
    build:
      context: ./apps/frontend
      dockerfile: Dockerfile.prod
    container_name: iam-dashboard-frontend
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://${CLIENT_DOMAIN}/api/v1

  backend:
    build:
      context: ./apps/backend
      dockerfile: Dockerfile.prod
    container_name: iam-dashboard-backend
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:16-alpine
    container_name: iam-dashboard-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
    driver: local
```

### Infrastructure Provisioning (Terraform)

```hcl
# infrastructure/terraform/main.tf
variable "client_name" {
  description = "Client name for resource naming"
  type        = string
}

# VPS Instance
resource "digitalocean_droplet" "client_vps" {
  image  = "ubuntu-24-04-x64"
  name   = "iam-dashboard-${var.client_name}"
  region = "nyc3"
  size   = "s-2vcpu-4gb"
  
  ssh_keys = [digitalocean_ssh_key.deploy_key.id]
  
  tags = [
    "iam-dashboard",
    "client-${var.client_name}",
    "environment-production"
  ]
}

# Floating IP for consistent access
resource "digitalocean_floating_ip" "client_ip" {
  droplet = digitalocean_droplet.client_vps.id
  region  = digitalocean_droplet.client_vps.region
}

output "vps_ip_address" {
  description = "The IP address of the client VPS"
  value       = digitalocean_floating_ip.client_ip.ip_address
}
```

### Environment Configuration

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|--------------|-------------|---------|
| Development | `http://localhost:3000` | `http://localhost:8000/v1` | Local development |
| Staging | `https://staging-{client}.example.com` | `https://staging-{client}.example.com/api/v1` | Pre-production testing |
| Production | `https://{client-domain}.com` | `https://{client-domain}.com/api/v1` | Live client environment |

---

## 15. Security and Performance

Comprehensive security measures and performance optimization strategies for enterprise-grade requirements:

### Security Requirements

#### Frontend Security
- **CSP Headers:** Content Security Policy preventing XSS attacks
- **XSS Prevention:** Input sanitization through Zod validation and React's built-in protection
- **Secure Storage:** JWT tokens in httpOnly cookies with secure flags

#### Backend Security
- **Input Validation:** Comprehensive Pydantic model validation for all endpoints
- **Rate Limiting:** API endpoints limited to 100 requests per minute per IP
- **CORS Policy:** Restricted to verified client domains only

#### Authentication Security
- **Token Storage:** JWT in httpOnly secure cookies with 15-minute expiration
- **Session Management:** Redis-based sessions with 24-hour expiration
- **Password Policy:** 8+ characters with complexity requirements, bcrypt hashing

### Performance Optimization

#### Frontend Performance
- **Bundle Size Target:** Maximum 500KB initial bundle
- **Loading Strategy:** React Server Components for static content
- **Caching Strategy:** TanStack Query for 5-minute API caching

#### Backend Performance
- **Response Time Target:** Sub-200ms average API response time
- **Database Optimization:** Proper indexing and connection pooling
- **Caching Strategy:** Redis caching for frequently accessed data

### Security Implementation Details

```python
# Enhanced JWT security implementation
class SecureAuthService:
    def create_access_token(self, user_id: str, user_role: str) -> dict:
        """Create secure JWT token with session tracking"""
        session_id = secrets.token_hex(16)
        
        payload = {
            "sub": user_id,
            "role": user_role,
            "session_id": session_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "jti": secrets.token_hex(16)  # JWT ID for blacklisting
        }
        
        access_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # Store session in Redis
        session_data = {
            "user_id": user_id,
            "user_role": user_role,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.redis_client.setex(
            f"session:{session_id}",
            timedelta(hours=24),
            json.dumps(session_data)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 900
        }
```

### Performance Monitoring

```typescript
// Performance monitoring implementation
export class PerformanceMonitor {
    trackWebVitals() {
        // Largest Contentful Paint
        new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            this.recordMetric('LCP', lastEntry.startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });
    }
    
    trackAPICall(endpoint: string, startTime: number, endTime: number) {
        const duration = endTime - startTime;
        this.recordMetric(`API_${endpoint}`, duration);
        
        if (duration > 2000) {
            console.warn(`Slow API call detected: ${endpoint} took ${duration}ms`);
        }
    }
}
```

---

## Architecture Summary

This comprehensive architecture document provides a complete technical blueprint for the Multi-Agent IAM Dashboard, covering:

### Key Architecture Decisions
1. **Custom Implementation Service Model**: Dedicated VPS per client enabling premium pricing through complete customization
2. **Monolith + Independent Agents**: Simplified deployment with specialized AI agent functionality  
3. **Modern Tech Stack**: Next.js 15 + FastAPI + PostgreSQL + Docker for reliability and performance
4. **Complete Brand Customization**: Real-time theming system via CSS variables and shadcn/ui
5. **Infrastructure Automation**: Terraform + Ansible enabling 3-4 week implementation cycles

### Technical Foundation
- **Frontend**: Next.js 15 + React 19 + TypeScript + shadcn/ui + Tailwind CSS
- **Backend**: FastAPI + SQLModel + PostgreSQL + Redis + Agno agents
- **Infrastructure**: Docker Compose + Terraform + Ansible + Caddy
- **Security**: JWT + 2FA + comprehensive audit trails + input validation
- **Performance**: Multi-level caching + query optimization + monitoring

### Business Value Delivery
- **99.9% Uptime**: Through automated monitoring and deployment
- **Sub-200ms Response Times**: Via optimized architecture and caching
- **Complete Data Isolation**: Dedicated VPS per client
- **3-4 Week Implementation**: Automated infrastructure and deployment
- **Premium Customization**: Full branding and visual identity integration

This architecture enables the custom implementation service model to deliver enterprise-grade solutions at scale while maintaining the agility and cost-effectiveness required for the target market.

## 16. Testing Strategy

The platform implements **comprehensive testing** following the testing pyramid approach to ensure 80% minimum code coverage and reliable functionality across all multi-agent interactions.

### Testing Pyramid

```
                  E2E Tests
                 /        \
            Integration Tests
               /            \
          Frontend Unit  Backend Unit
```

The testing strategy emphasizes unit tests as the foundation while ensuring critical user workflows are validated through end-to-end testing across all agents.

### Test Organization

#### Frontend Tests

```
frontend/tests/
├── __tests__/                 # Unit tests co-located with components
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
│   │   ├── clientStore.test.ts
│   │   ├── authStore.test.ts
│   │   └── appStore.test.ts
│   └── utils/
│       ├── validation.test.ts
│       ├── formatting.test.ts
│       └── api-client.test.ts
├── integration/               # Integration tests
│   ├── auth-flow.test.tsx
│   ├── client-management.test.tsx
│   └── branding-system.test.tsx
└── setup/                     # Test configuration
    ├── test-utils.tsx
    ├── mocks/
    └── fixtures/
```

#### Backend Tests

```
backend/src/tests/
├── unit/                      # Unit tests
│   ├── agents/
│   │   ├── agent1/
│   │   │   ├── test_services.py
│   │   │   ├── test_models.py
│   │   │   └── test_schemas.py
│   │   ├── agent2/
│   │   ├── agent3/
│   │   └── agent4/
│   ├── core/
│   │   ├── test_auth.py
│   │   ├── test_database.py
│   │   └── test_config.py
│   └── shared/
│       ├── test_utils.py
│       └── test_validators.py
├── integration/               # Integration tests
│   ├── test_api_endpoints.py
│   ├── test_agent_communication.py
│   ├── test_database_operations.py
│   └── test_auth_flow.py
├── conftest.py               # Pytest configuration
├── factories.py              # Test data factories
└── fixtures/                 # Test fixtures
    ├── sample_clients.json
    ├── test_pdfs/
    └── audio_samples/
```

#### E2E Tests

```
tests/playwright/
├── auth/
│   ├── login.spec.ts
│   ├── two-factor.spec.ts
│   └── logout.spec.ts
├── clients/
│   ├── client-creation.spec.ts
│   ├── client-search.spec.ts
│   ├── client-editing.spec.ts
│   └── bulk-operations.spec.ts
├── agents/
│   ├── pdf-processing.spec.ts
│   ├── report-generation.spec.ts
│   └── audio-recording.spec.ts
├── branding/
│   ├── theme-customization.spec.ts
│   ├── asset-upload.spec.ts
│   └── branding-deployment.spec.ts
├── admin/
│   ├── user-management.spec.ts
│   └── system-configuration.spec.ts
├── fixtures/
│   ├── test-users.ts
│   ├── sample-data.ts
│   └── brand-assets/
└── utils/
    ├── auth-helpers.ts
    ├── data-helpers.ts
    └── page-objects/
```

### Test Examples

#### Frontend Component Test

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { ClientForm } from '@/components/forms/ClientForm';
import { ClientService } from '@/services/ClientService';

// Mock the service
vi.mock('@/services/ClientService');

describe('ClientForm', () => {
  const mockCreateClient = vi.fn();
  
  beforeEach(() => {
    vi.mocked(ClientService.createClient).mockImplementation(mockCreateClient);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should validate SSN format correctly', async () => {
    const user = userEvent.setup();
    
    render(<ClientForm onSuccess={vi.fn()} />);
    
    // Fill in form with invalid SSN
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/ssn/i), '123456789');
    await user.type(screen.getByLabelText(/birth date/i), '1990-01-01');
    
    // Submit form
    await user.click(screen.getByRole('button', { name: /create client/i }));
    
    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/invalid ssn format/i)).toBeInTheDocument();
    });
    
    // Service should not be called
    expect(mockCreateClient).not.toHaveBeenCalled();
  });

  it('should create client with valid data', async () => {
    const user = userEvent.setup();
    const mockClient = {
      client_id: '123',
      name: 'John Doe',
      ssn: '123-45-6789',
      birth_date: '1990-01-01'
    };
    
    mockCreateClient.mockResolvedValue(mockClient);
    const onSuccess = vi.fn();
    
    render(<ClientForm onSuccess={onSuccess} />);
    
    // Fill in form with valid data
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/ssn/i), '123-45-6789');
    await user.type(screen.getByLabelText(/birth date/i), '1990-01-01');
    
    // Submit form
    await user.click(screen.getByRole('button', { name: /create client/i }));
    
    // Should call service with correct data
    await waitFor(() => {
      expect(mockCreateClient).toHaveBeenCalledWith({
        name: 'John Doe',
        ssn: '123-45-6789',
        birth_date: '1990-01-01'
      });
    });
    
    // Should call success callback
    expect(onSuccess).toHaveBeenCalledWith(mockClient);
  });
});
```

#### Backend API Test

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from main import app
from core.database import get_db
from shared.models import User
from agents.agent1.models import Client
from tests.factories import UserFactory, ClientFactory

class TestClientAPI:
    """Test suite for client management API endpoints."""
    
    def test_create_client_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful client creation."""
        client_data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "birth_date": "1990-01-01"
        }
        
        response = test_client.post(
            "/api/v1/clients/",
            json=client_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == client_data["name"]
        assert data["ssn"] == client_data["ssn"]
        assert data["birth_date"] == client_data["birth_date"]
        assert "client_id" in data
        assert "created_at" in data
    
    def test_create_client_duplicate_ssn(self, test_client: TestClient, auth_headers: dict, db: Session):
        """Test client creation with duplicate SSN."""
        # Create existing client
        existing_client = ClientFactory(ssn="123-45-6789")
        db.add(existing_client)
        db.commit()
        
        client_data = {
            "name": "Jane Doe",
            "ssn": "123-45-6789",  # Same SSN
            "birth_date": "1985-05-15"
        }
        
        response = test_client.post(
            "/api/v1/clients/",
            json=client_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "DUPLICATE_CLIENT"
        assert "SSN already exists" in data["error"]["message"]
```

#### E2E Test

```typescript
import { test, expect } from '@playwright/test';
import { AuthHelper } from '../utils/auth-helpers';
import { DataHelper } from '../utils/data-helpers';

test.describe('Client Management Workflow', () => {
  let authHelper: AuthHelper;
  let dataHelper: DataHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
    dataHelper = new DataHelper(page);
    
    // Login as admin user
    await authHelper.loginAsAdmin();
  });

  test('should create, edit, and delete client successfully', async ({ page }) => {
    // Navigate to clients page
    await page.goto('/clients');
    await expect(page.getByRole('heading', { name: 'Clients' })).toBeVisible();

    // Create new client
    await page.getByRole('button', { name: 'Add Client' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Fill client form
    await page.getByLabel('Name').fill('John Doe');
    await page.getByLabel('SSN').fill('123-45-6789');
    await page.getByLabel('Birth Date').fill('1990-01-01');

    // Submit form
    await page.getByRole('button', { name: 'Create Client' }).click();

    // Verify client was created
    await expect(page.getByText('Client created successfully')).toBeVisible();
    await expect(page.getByText('John Doe')).toBeVisible();

    // Edit client
    await page.getByRole('row', { name: /John Doe/ }).getByRole('button', { name: 'Edit' }).click();
    await page.getByLabel('Name').fill('John Smith');
    await page.getByRole('button', { name: 'Save Changes' }).click();

    // Verify client was updated
    await expect(page.getByText('Client updated successfully')).toBeVisible();
    await expect(page.getByText('John Smith')).toBeVisible();

    // Delete client
    await page.getByRole('row', { name: /John Smith/ }).getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Confirm Delete' }).click();

    // Verify client was deleted
    await expect(page.getByText('Client deleted successfully')).toBeVisible();
    await expect(page.getByText('John Smith')).not.toBeVisible();
  });
});
```

---

## 17. Coding Standards

The platform implements **minimal but critical** standards for AI agents to ensure consistency and prevent common mistakes across the fullstack multi-agent architecture.

### Critical Fullstack Rules

- **Type Sharing:** Always define shared types in `shared/types/` and import from there. Never duplicate type definitions between agents or frontend/backend
- **Database Access:** Agents can only READ from other agents' tables, never modify. Each agent writes only to its own tables
- **API Calls:** Never make direct HTTP calls - always use the FastAPI service layer with proper error handling
- **Environment Variables:** Access only through config objects in `core/config.py`, never process.env directly
- **Error Handling:** All API routes must use the standard FastAPI exception handler with structured error responses
- **Agent Independence:** Each agent must function independently - no direct inter-agent communication except through database
- **Validation:** ALL external data must be validated using Pydantic models and Zod schemas at system boundaries
- **Authentication:** Use the centralized auth middleware - never implement custom auth logic in agents
- **CSS Variables:** Custom branding changes only through CSS variables system - never hardcode brand colors
- **File Organization:** Maximum 500 lines per file, functions under 50 lines - split larger files into modules
- **Testing Requirements:** 80% minimum code coverage - no exceptions for any module or agent
- **Language Consistency:** All code, comments, and technical content in English - UI content in Portuguese (Brazil)

### Naming Conventions

| Element | Frontend | Backend | Agent Tables | Example |
|---------|----------|---------|--------------|----------|
| Components | PascalCase | - | - | `ClientForm.tsx` |
| Hooks | camelCase with 'use' | - | - | `useClientData.ts` |
| API Routes | - | kebab-case | - | `/api/client-management` |
| Database Tables | - | snake_case | `agent{N}_{entity}` | `agent1_clients` |
| Agent Services | - | PascalCase | - | `ClientManagementService` |
| Shared Types | PascalCase | PascalCase | - | `ClientCreateRequest` |
| CSS Classes | kebab-case | - | - | `client-form-container` |
| Environment Variables | UPPER_SNAKE_CASE | UPPER_SNAKE_CASE | - | `DATABASE_URL` |

---

## 18. Error Handling Strategy

The platform implements **unified error handling** across the entire fullstack multi-agent system, ensuring consistent error responses, proper logging, and graceful failure handling.

### Error Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as FastAPI
    participant D as Database
    participant AG as Agent
    
    U->>F: User Action
    F->>A: API Request
    A->>AG: Agent Operation
    AG->>D: Database Query
    D-->>AG: Database Error
    AG-->>A: Structured Error
    A-->>F: HTTP Error Response
    F-->>U: User-Friendly Message
    
    Note over A: All errors logged with request ID
    Note over F: Error displayed in appropriate context
```

### Error Response Format

All API errors follow a consistent JSON structure for predictable frontend handling:

```typescript
interface ApiError {
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable message
    details?: Record<string, any>; // Additional context
    timestamp: string;      // ISO timestamp
    requestId: string;      // Unique request identifier
    agent?: string;         // Which agent generated the error
  };
}

// Example error responses
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid SSN format provided",
    "details": {
      "field": "ssn",
      "received": "123456789",
      "expected": "XXX-XX-XXXX format"
    },
    "timestamp": "2025-08-01T10:30:00Z",
    "requestId": "req_1234567890",
    "agent": "agent1"
  }
}
```

### Frontend Error Handling

```typescript
// Error handling service
class ErrorHandler {
  private static showUserMessage(error: ApiError) {
    const userMessages = {
      VALIDATION_ERROR: 'Please check your input and try again',
      DUPLICATE_CLIENT: 'This client already exists in the system',
      NETWORK_ERROR: 'Connection problem. Please try again',
      SERVER_ERROR: 'System error. Our team has been notified',
      UNAUTHORIZED: 'Please log in to continue',
      FORBIDDEN: 'You don\'t have permission for this action'
    };
    
    const message = userMessages[error.error.code] || error.error.message;
    toast.error(message);
  }
  
  static handleApiError(error: unknown, context?: string) {
    if (error instanceof ApiError) {
      this.showUserMessage(error);
      this.logError(error, context);
    } else {
      this.showGenericError();
    }
  }
}
```

### Backend Error Handling

```python
# Custom exception classes
class BaseCustomException(Exception):
    def __init__(self, code: str, message: str, details: dict = None, agent: str = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.agent = agent
        super().__init__(self.message)

# FastAPI exception handler
@app.exception_handler(BaseCustomException)
async def custom_exception_handler(request: Request, exc: BaseCustomException):
    request_id = str(uuid.uuid4())
    
    error_response = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "requestId": request_id,
            "agent": exc.agent
        }
    }
    
    # Log error for monitoring
    logger.error(
        f"API Error: {exc.code}",
        extra={
            "request_id": request_id,
            "agent": exc.agent,
            "details": exc.details,
            "path": request.url.path
        }
    )
    
    status_codes = {
        "VALIDATION_ERROR": 400,
        "DUPLICATE_CLIENT": 409,
        "UNAUTHORIZED": 401,
        "FORBIDDEN": 403,
        "NOT_FOUND": 404,
        "AGENT_ERROR": 500
    }
    
    status_code = status_codes.get(exc.code, 500)
    return JSONResponse(content=error_response, status_code=status_code)
```

### Agent-Specific Error Handling

Each agent implements error handling patterns specific to their domain while maintaining consistency:

```python
# Agent 1: Client Management errors
AGENT1_ERRORS = {
    "INVALID_SSN": "SSN format validation failed",
    "DUPLICATE_SSN": "Client with SSN already exists",
    "CLIENT_NOT_FOUND": "Client not found in database"
}

# Agent 2: PDF Processing errors  
AGENT2_ERRORS = {
    "INVALID_PDF": "PDF file format not supported",
    "PROCESSING_FAILED": "PDF processing failed",
    "VECTOR_STORAGE_ERROR": "Failed to store PDF vectors"
}
```

---

## 19. Monitoring and Observability

The platform implements **comprehensive monitoring and observability** across all client VPS instances to maintain 99.9% uptime SLA and enable proactive service management.

### Monitoring Stack

- **Frontend Monitoring:** Sentry for error tracking, Web Vitals API for performance metrics, custom analytics for user interactions
- **Backend Monitoring:** Prometheus + Grafana for metrics collection and visualization, structured logging with JSON format
- **Error Tracking:** Centralized error aggregation across all agents with correlation IDs for distributed tracing
- **Performance Monitoring:** APM with response time tracking, database query performance, and resource utilization metrics
- **Infrastructure Monitoring:** System-level metrics for CPU, memory, disk, and network across all client VPS instances
- **Custom Branding Monitoring:** Deployment success tracking and visual consistency validation across client implementations

### Key Metrics

**Frontend Metrics:**
- **Web Vitals:** Largest Contentful Paint (LCP) < 2.5s, First Input Delay (FID) < 100ms, Cumulative Layout Shift (CLS) < 0.1
- **Error Rate:** < 0.1% of sessions with unhandled exceptions
- **API Success Rate:** > 99.5% of API calls successful

**Backend Metrics:**
- **API Response Time:** < 200ms on average for all endpoints
- **Error Rate:** < 0.05% of requests resulting in 5xx errors
- **Database Query Time:** < 50ms for 95th percentile of queries

**Infrastructure Metrics:**
- **CPU Utilization:** < 80% average across all client VPS instances
- **Memory Usage:** < 85% average to prevent swapping
- **Disk Space:** < 90% utilization with automated alerts

### Logging and Tracing

**Structured Logging:**
```json
{
  "timestamp": "2025-08-01T12:00:00Z",
  "level": "INFO",
  "message": "Client created successfully",
  "service": "backend-api",
  "request_id": "req_1234567890",
  "agent": "agent1",
  "client_id": "uuid-goes-here",
  "user_id": "uuid-goes-here"
}
```

**Distributed Tracing:**
- **Trace Propagation:** W3C Trace Context headers across all services
- **Trace Visualization:** Jaeger or Grafana Tempo for end-to-end trace analysis
- **Trace IDs:** Included in all logs for correlation between services and agents

---

*This architecture document is the single source of truth for the Multi-Agent IAM Dashboard project. All development must adhere to the standards and decisions outlined herein.*

```

---

## 20. Checklist Results Report

### Executive Summary

**Overall Architecture Completeness:** 98% Complete  
**Technical Design Quality:** Excellent  
**Implementation Readiness:** Ready for Development  
**Most Critical Success Factors:** Multi-agent database communication patterns, custom branding deployment automation, and VPS provisioning reliability

### Category Analysis

| Category | Status | Critical Issues |
|----------|--------|----------------|
| 1. Technical Foundation | ✅ PASS | Complete tech stack definition with version specifications |
| 2. Architecture Patterns | ✅ PASS | Well-defined monolith + independent agents pattern |
| 3. Data Architecture | ✅ PASS | Comprehensive database schema with agent separation |
| 4. API Design | ✅ PASS | Complete OpenAPI 3.0 specification with error handling |
| 5. Frontend Architecture | ✅ PASS | Modern React 19 + Next.js 15 with component organization |
| 6. Backend Architecture | ✅ PASS | FastAPI with clean service layer and agent isolation |
| 7. Security Implementation | ✅ PASS | OAuth2 + JWT + 2FA with comprehensive auth flow |
| 8. Custom Branding System | ✅ PASS | CSS variable-based theming with real-time deployment |
| 9. Testing Strategy | ✅ PASS | Complete testing pyramid with 80% coverage requirement |
| 10. Deployment Architecture | ✅ PASS | Terraform + Ansible automation for VPS provisioning |
| 11. Monitoring & Observability | ✅ PASS | Prometheus + Grafana with multi-client dashboards |
| 12. Development Workflow | ✅ PASS | Clear setup instructions and development commands |

### Architecture Validation Results

**✅ STRENGTHS:**
- **Comprehensive Technical Coverage:** All major architectural concerns addressed with specific implementation details
- **Multi-Agent Independence:** Clear database communication patterns ensuring agent autonomy while maintaining data consistency
- **Custom Implementation Service Model:** Well-designed VPS deployment strategy supporting the premium service business model
- **Modern Technology Stack:** Next.js 15 + React 19 + FastAPI + PostgreSQL provides excellent performance and developer experience
- **Complete Custom Branding:** CSS variable system enables real-time brand customization without code changes
- **Professional Monitoring:** Enterprise-grade observability supporting 99.9% uptime SLA requirements
- **Security-First Design:** Comprehensive authentication, authorization, and data protection measures
- **Testing Excellence:** Full testing pyramid with specific examples and 80% coverage requirements
- **Deployment Automation:** Terraform + Ansible enables 3-4 week implementation cycles

**⚠️ AREAS FOR IMPLEMENTATION ATTENTION:**
- **Agent Communication Complexity:** Multi-agent database access patterns require careful implementation to prevent data conflicts
- **Custom Branding Performance:** CSS variable deployment must be optimized for sub-second application across all interface elements  
- **VPS Provisioning Reliability:** Terraform automation needs robust error handling for production deployment success
- **Monitoring Scale:** Cross-client monitoring dashboard performance at 50+ concurrent implementations needs validation

**🔍 TECHNICAL RISKS IDENTIFIED:**
- **Database Performance:** Agent table access patterns may require optimization under high concurrent load
- **Custom Branding Deployment:** Real-time CSS variable updates across all components needs performance testing
- **Infrastructure Scaling:** VPS provisioning automation reliability across multiple cloud providers requires thorough testing

### Implementation Readiness Assessment

**✅ READY FOR DEVELOPMENT**

**Critical Success Factors:**
1. **Agent Database Patterns:** Implement read-only access controls and audit trail logging from day one
2. **Custom Branding Performance:** Optimize CSS variable application and test deployment speed early in development
3. **VPS Automation Reliability:** Thoroughly test Terraform + Ansible scripts across all supported providers
4. **Monitoring Implementation:** Set up comprehensive observability before first client deployment
5. **Testing Infrastructure:** Establish testing pipeline with 80% coverage enforcement before feature development

**Development Sequence Recommendation:**
1. **Phase 1 (Weeks 1-4):** Core platform foundation with Agent 1 (Client Management) and authentication
2. **Phase 2 (Weeks 5-8):** Custom branding system and VPS deployment automation  
3. **Phase 3 (Weeks 9-12):** Remaining agents (2-4) with complete multi-agent communication
4. **Phase 4 (Weeks 13-16):** Production monitoring, testing completion, and first client deployment

**Confidence Level:** Very High - This architecture provides comprehensive guidance for successful implementation of the custom implementation service model with all critical technical requirements addressed.

---

*Multi-Agent IAM Dashboard Fullstack Architecture Document completed on August 1, 2025*  
*Total sections: 20 | Status: Complete and Ready for Implementation*  
*Next Phase: Development Team Handoff and Sprint Planning*

---

**Document Status:** ✅ Complete  
**Implementation Readiness:** ✅ Ready  
**Estimated Development Time:** 16 weeks with 4-person fullstack team  
**Business Impact:** Supports $600K ARR through premium custom implementation service model