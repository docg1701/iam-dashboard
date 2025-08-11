# Technical Assumptions

## Repository Structure: Monorepo

Based on the Project Brief analysis, a monorepo structure provides optimal organization for the custom implementation service. This allows unified version control, shared tooling, and coordinated deployments across frontend, backend, and deployment components while maintaining clear separation of concerns for the multi-agent architecture.

## Service Architecture

**Monolith with Independent Agents:** The system follows a hybrid approach with a monolithic core platform (FastAPI backend + Next.js frontend) supporting independent AI agents that communicate through the shared PostgreSQL database. Each agent operates autonomously while leveraging the common infrastructure, providing both simplicity and scalability for the custom implementation model.

## Testing Requirements

**Full Testing Pyramid:** Given the custom implementation service model where each deployment must be reliable and professional, comprehensive testing is essential including:
- **Unit Tests:** 80% minimum coverage for all business logic and utilities
- **Integration Tests:** Database operations, agent interactions, and API endpoints
- **End-to-End Tests:** Critical user workflows and custom branding deployment
- **Manual Testing:** Custom implementation validation and client-specific branding verification

## Additional Technical Assumptions and Requests

**Technology Stack Decisions (based on Project Brief):**
- **Backend:** FastAPI + SQLModel + PostgreSQL for ACID compliance and structured relationships
- **Frontend:** Next.js 15 + React 19 + TypeScript + shadcn/ui + Tailwind CSS for modern responsive design
- **AI Framework:** Agno for 10,000x faster agent instantiation with 50x less memory usage
- **Database:** PostgreSQL with pgvector extension for future agent capabilities
- **Deployment:** Docker Compose over Kubernetes for simpler per-client deployment model
- **Infrastructure:** SSH-based deployment scripts + systemd services for cost-effective VPS provisioning and configuration
- **Proxy:** Caddy for automatic HTTPS and reverse proxy with minimal configuration

**Performance & Scalability Assumptions:**
- Each client VPS instance targets 50-200 concurrent users maximum
- Database performance optimized for single-tenant workloads per instance
- Agent response times under 2 seconds for typical AI processing tasks
- Custom branding deployment completed within 5 minutes of configuration changes
- Permission system performance targets <10ms for permission checks via Redis caching
- Redis cache maintains 90%+ hit ratio for active user permission queries
- Permission validation adds minimal overhead to API response times (<5% increase)

**Security & Compliance Assumptions:**
- OAuth2 + JWT + 2FA sufficient for target business market security requirements
- GDPR compliance addressed through dedicated VPS data isolation model
- Audit logging meets SOC 2 Type II requirements for managed service model
- SSL/TLS termination at Caddy proxy level with automated certificate management

**Development & Deployment Assumptions:**
- Semi-automated deployment scripts reduce implementation time to 3-4 weeks
- Standardized deployment templates support 80% of client customization needs
- Development team capacity supports 5-8 concurrent implementations
- Client-specific branding requires maximum 4 hours development time per implementation

---
