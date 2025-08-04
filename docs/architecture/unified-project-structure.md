# Unified Project Structure

*Last Updated: August 2025*

This document defines the **overall project architecture patterns**, **principles**, and **unified structure guidance** for the Multi-Agent IAM Dashboard. It serves as the architectural blueprint for organizing the fullstack multi-agent system and guides development decisions throughout all project phases.

## Architectural Overview

The Multi-Agent IAM Dashboard implements a **Custom Implementation Service** architecture delivering dedicated VPS instances with complete brand customization. The system uses a **monolithic core platform** (FastAPI backend + Next.js 15 frontend) supporting **independent AI agents** that communicate through a shared PostgreSQL database.

### Core Architectural Patterns

#### 1. Custom Implementation Service Pattern
- **Dedicated VPS per client** with complete isolation and branding
- **Premium pricing model** through true customization vs. generic SaaS limitations
- **3-4 week implementation cycles** enabled by automation
- **Complete visual identity integration** via CSS variables

#### 2. Monolith + Independent Agents Pattern
- **Core platform** handles authentication, routing, and shared services
- **Autonomous AI agents** with specialized functionality
- **Database-centric communication** ensuring data consistency
- **Simplified deployment** while allowing agent independence

#### 3. Infrastructure as Code Pattern
- **Terraform + Ansible automation** for consistent deployments
- **Container-first deployment** with Docker Compose
- **Multi-region support** based on client geographic requirements
- **Automated monitoring** and backup systems

#### 4. Progressive Web App Pattern
- **Next.js with service worker** for offline capability
- **Mobile-first responsive design** with touch-friendly interfaces
- **Real-time updates** via WebSocket connections
- **Professional user experience** across all devices

## Technology Stack Foundation

### Backend Architecture
- **FastAPI**: Modern Python web framework with automatic OpenAPI generation
- **SQLModel**: Database ORM combining SQLAlchemy + Pydantic for type safety
- **PostgreSQL + pgvector**: Primary database with vector extension for AI features
- **Redis**: Session storage and async task queuing
- **Celery**: Asynchronous task processing for long-running operations

### Frontend Architecture
- **Next.js 15**: React framework with App Router and React Server Components
- **React 19**: UI library with latest features and performance improvements
- **shadcn/ui**: Component library optimized for custom branding via CSS variables
- **Tailwind CSS**: Utility-first CSS framework with theming support
- **TanStack Query + Zustand**: Server and client state management

### Multi-Agent Framework
- **Agno**: Multi-agent framework for AI agent instantiation and management
- **Independent agent processes** with shared database communication
- **Agent-specific tables** with read-only access to other agents' data
- **Hierarchical dependencies** with explicit dependency mapping

## Database Architecture Principles

### Agent Communication Model
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Agent 1      │    │    Agent 2      │    │    Agent 3      │
│ Client Mgmt     │    │ PDF Processing  │    │ Report Gen      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ writes                │ writes                │ writes
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ agent1_clients  │    │ agent2_documents│    │ agent3_reports  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │ all agents can read
                                 ▼
                    ┌─────────────────────────┐
                    │   Shared Database       │
                    │   (PostgreSQL)          │
                    └─────────────────────────┘
```

### Data Sharing Rules
1. **Own Tables Only**: Each agent writes only to its own tables (agent{N}_{entity})
2. **Read-Only Access**: Agents can read from other agents' tables but never modify
3. **Reference Integrity**: Use foreign keys to maintain relationships across agents
4. **Audit Trail**: Complete logging of all data access and modifications

### Table Naming Convention
- **Core Tables**: Standard naming (users, audit_log, permissions)
- **Agent Tables**: Prefixed with agent number (agent1_clients, agent2_documents)
- **Shared References**: Foreign keys reference core or other agent tables appropriately

## Component Architecture Patterns

### Frontend Component Organization
```
Frontend Components Hierarchy:
├── App Router Pages (Next.js 15)
├── Layout Components (Header, Sidebar, Navigation)
├── Feature Components (Auth, Clients, Users, Agents)
├── Form Components (Create, Edit, Search)
├── UI Components (shadcn/ui base components)
└── Utility Components (Loading, Error, Toast)
```

### Backend Service Layer
```
Backend Service Architecture:
├── FastAPI Core Application (main.py)
├── API Routes (/api/v1/{resource})
├── Service Layer (business logic)
├── Repository Layer (data access)
├── Model Layer (SQLModel ORM)
└── Agent Integration Layer
```

### Agent Architecture
```
Agent Structure:
├── Agent Core (Agno framework integration)
├── Agent Models (SQLModel for agent-specific tables)
├── Agent Services (business logic)
├── Agent Schemas (Pydantic request/response)
└── Agent Utilities (helper functions)
```

## Security Architecture

### Authentication & Authorization Flow
```
Authentication Flow:
User → Frontend → FastAPI → JWT Validation → Role Check → Agent Access → Database
```

### Security Layers
1. **Frontend Security**: CSP headers, XSS prevention, secure token storage
2. **API Security**: JWT authentication, rate limiting, input validation
3. **Database Security**: Row-level security, audit logging, encrypted connections
4. **Infrastructure Security**: VPS isolation, firewall rules, SSL/TLS encryption

### Permission System
- **Role-Based Access Control**: sysadmin, admin, user roles
- **Agent-Based Permissions**: Granular access control per agent
- **Resource-Level Permissions**: CRUD permissions on specific resources
- **Audit Trail**: Complete logging of all permission changes and access

## Custom Branding Architecture

### CSS Variable System
```css
:root {
  /* Primary Brand Colors */
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  
  /* Secondary Colors */
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  
  /* Custom Branding Variables */
  --brand-logo: url('/custom/logo.svg');
  --brand-font: 'Custom-Font', system-ui;
  --brand-radius: 0.5rem;
}
```

### Branding Components
- **Real-time Color Customization**: CSS variable updates via admin interface
- **Logo and Asset Management**: Dynamic asset loading with fallbacks
- **Typography System**: Font selection from approved font library
- **Theme Preview**: Live preview of branding changes before deployment

## Testing Architecture

### Testing Pyramid Structure
```
Testing Levels:
┌─────────────────┐  ← E2E Tests (Playwright)
│   Integration   │  ← Integration Tests (API + Database)
│      Unit       │  ← Unit Tests (Components + Services)
└─────────────────┘
```

### Testing Standards
- **80% Minimum Coverage**: Enforced across all modules and agents
- **Co-located Tests**: Tests placed near the code they test
- **Factory Patterns**: Consistent test data generation
- **Agent Testing**: Cross-agent integration testing for data flow validation

## Deployment Architecture

### VPS Deployment Model
```
Client VPS Instance:
├── Caddy Reverse Proxy (HTTPS termination)
├── Next.js Frontend (Static + SSR)
├── FastAPI Backend (API + Agent coordination)
├── PostgreSQL Database (Data + Vector storage)
├── Redis Cache (Sessions + Task queue)
└── Monitoring Stack (Prometheus + Grafana)
```

### Infrastructure Automation
- **Terraform**: VPS provisioning and DNS configuration
- **Ansible**: Application deployment and configuration management
- **Docker Compose**: Container orchestration and service management
- **CI/CD**: Automated testing, building, and deployment pipelines

## Performance Architecture

### Caching Strategy
```
Caching Layers:
├── CDN/Edge Caching (Static assets)
├── Application Caching (Redis)
├── Database Query Caching (PostgreSQL)
└── Browser Caching (Service Worker)
```

### Performance Targets
- **API Response Time**: Sub-200ms average
- **Frontend Load Time**: <2.5s First Contentful Paint
- **Database Query Time**: <50ms for 95th percentile
- **Bundle Size**: <500KB initial load

## Monitoring and Observability

### Monitoring Stack
- **Application Metrics**: Prometheus + Grafana
- **Error Tracking**: Structured logging with correlation IDs
- **Performance Monitoring**: APM with distributed tracing
- **Infrastructure Monitoring**: System metrics and alerting

### Key Metrics
- **Business Metrics**: User engagement, feature usage, conversion rates
- **Technical Metrics**: Response times, error rates, resource utilization
- **Security Metrics**: Authentication attempts, permission violations, audit events

## Development Workflow Patterns

### Git Workflow
- **Main Branch**: Production-ready code
- **Feature Branches**: `feature/agent-name-functionality`
- **Semantic Commits**: Conventional commit format
- **Pull Requests**: Required for all changes with automated checks

### Quality Gates
- **Code Quality**: Linting, formatting, type checking
- **Testing**: Unit, integration, and E2E test passes
- **Security**: Vulnerability scans and dependency checks
- **Performance**: Bundle size and performance regression tests

## Monorepo Organization

### Workspace Structure
```json
{
  "workspaces": [
    "apps/frontend",
    "apps/backend", 
    "packages/shared",
    "packages/ui",
    "packages/config"
  ]
}
```

### Dependency Management
- **Frontend**: npm for JavaScript dependencies
- **Backend**: UV for Python dependencies with pyproject.toml
- **Shared**: npm workspaces for cross-package dependencies
- **Infrastructure**: Terraform modules and Ansible roles

## Scalability Patterns

### Horizontal Scaling
- **Multiple VPS Instances**: Independent client deployments
- **Database Scaling**: Connection pooling and read replicas
- **Agent Scaling**: Independent agent processes with shared database
- **CDN Integration**: Static asset distribution

### Vertical Scaling
- **Resource Optimization**: Efficient memory and CPU usage
- **Database Optimization**: Query optimization and indexing
- **Caching Strategies**: Multi-level caching implementation
- **Bundle Optimization**: Code splitting and lazy loading

## Error Handling Patterns

### Unified Error Handling
```typescript
interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
    timestamp: string;
    requestId: string;
    agent?: string;
  };
}
```

### Error Flow
1. **Error Generation**: Structured errors with context
2. **Error Logging**: Centralized logging with correlation IDs
3. **Error Response**: Consistent API error format
4. **Error Display**: User-friendly error messages in UI

## Configuration Management

### Environment Configuration
- **Development**: Local development with Docker Compose
- **Staging**: Pre-production testing environment
- **Production**: Client-specific VPS deployments
- **Environment Variables**: Secure configuration management

### Feature Flags
- **Agent Features**: Toggle agent functionality per client
- **UI Features**: Progressive feature rollout
- **Branding Options**: Client-specific customization options
- **Performance Features**: A/B testing for optimizations

## Documentation Standards

### Architecture Documentation
- **Decision Records**: Architectural decision documentation
- **API Documentation**: OpenAPI 3.0 specifications
- **User Guides**: Client and end-user documentation
- **Developer Guides**: Setup and development instructions

### Code Documentation
- **Inline Comments**: Complex logic explanation
- **JSDoc/Docstrings**: Function and class documentation
- **README Files**: Package and module overviews
- **Type Definitions**: Comprehensive TypeScript types

This unified project structure provides the architectural foundation for building a scalable, maintainable, and customizable Multi-Agent IAM Dashboard that supports the custom implementation service business model while maintaining high technical standards and development efficiency.