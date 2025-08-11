# Deployment Architecture

The deployment architecture supports the custom implementation service model with SSH-based VPS deployment, client-specific configurations, and professional managed service delivery across multiple concurrent implementations.

## Deployment Strategy

### Single VPS Full-Stack Deployment (Brazilian Market Optimized)
- **Platform:** Ubuntu Server 24.x VPS with SSH access (Brazilian providers)
- **Frontend:** Next.js static build served by Caddy reverse proxy
- **Backend:** FastAPI with Uvicorn behind Caddy proxy  
- **Database:** Local PostgreSQL + Redis on same VPS
- **Agents:** Docker Compose for lightweight containers
- **Deployment Method:** SSH-based automated scripts with systemd services
- **Cost Optimization:** 70-85% reduction vs. international cloud providers

## Environments

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|--------------|-------------|---------|
| Development | http://localhost:3000 | http://localhost:8000 | Local development and testing |
| Staging | https://staging.iam-dashboard.com.br | https://api-staging.iam-dashboard.com.br | Pre-production testing and validation |
| Production | https://iam-dashboard.com.br | https://api.iam-dashboard.com.br | Live environment for service management |
| Client Instances | https://{client}.com.br | https://api.{client}.com.br | Client-specific implementations |

---
