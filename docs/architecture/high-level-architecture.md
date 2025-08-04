# High Level Architecture

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
            A --> D[Permission Guards & Hooks]
            D --> E[WebSocket Connection]
        end
        
        subgraph "Backend Layer"
            F[FastAPI API] --> G[Permission Middleware]
            G --> H[SQLModel ORM]
            H --> I[PostgreSQL + pgvector]
            F --> J[WebSocket Manager]
            J --> K[Redis Cache]
            K --> I
        end
        
        subgraph "Permission System"
            L[Permission Service] --> K
            L --> I
            M[Permission Templates] --> L
            N[Audit Service] --> I
            L --> N
        end
        
        subgraph "Agent Layer"
            O[Client Management Agent] --> G
            P[PDF Processing Agent] --> G
            Q[Reports Agent] --> G
            R[Audio Recording Agent] --> G
            O --> I
            P --> I
            Q --> I
            R --> I
        end
        
        subgraph "Infrastructure"
            S[Caddy Reverse Proxy] --> A
            S --> F
            T[Docker Compose] --> S
            T --> A
            T --> F
            T --> I
            T --> K
        end
    end
    
    subgraph "Service Provider Infrastructure"
        U[Terraform Scripts] --> T
        V[Ansible Playbooks] --> T
        W[Monitoring Dashboard] --> S
        X[Backup System] --> I
    end
    
    Y[Client Users] --> S
    Z[Service Provider] --> U
    Z --> V
    Z --> W
    
    %% Permission Flow
    A -.->|Permission Check| D
    D -.->|Validate| L
    L -.->|Cache Hit/Miss| K
    L -.->|DB Query| I
    L -.->|Real-time Update| J
    J -.->|Broadcast| E
```

### Architectural Patterns

- **Custom Implementation Service**: Dedicated VPS per client with complete isolation and branding - *Rationale:* Enables premium pricing through true customization vs. generic SaaS limitations
- **Monolith + Independent Agents**: Core platform with autonomous AI agents - *Rationale:* Simplifies deployment while allowing agent independence and specialized functionality
- **Database-Centric Communication**: Agents communicate through shared PostgreSQL - *Rationale:* Ensures data consistency and simplifies inter-agent dependencies
- **CSS Variable Theming**: Complete visual customization via CSS variables - *Rationale:* Enables real-time brand application without code changes
- **Infrastructure as Code**: Terraform + Ansible automation - *Rationale:* Ensures consistent deployments and reduces implementation time from months to weeks
- **Container-First Deployment**: Docker Compose over Kubernetes - *Rationale:* Simpler per-client deployment model with lower operational complexity
- **Progressive Web App**: Next.js with service worker for offline capability - *Rationale:* Professional user experience with mobile and offline support
- **Layered Permission Architecture**: Agent-based permissions with role inheritance and caching - *Rationale:* Transforms rigid role hierarchy into flexible, granular access control while maintaining performance through Redis caching
- **Permission-First API Design**: All endpoints protected by default with explicit permission decorators - *Rationale:* Secure by default approach prevents accidental privilege escalation and ensures comprehensive audit trails
