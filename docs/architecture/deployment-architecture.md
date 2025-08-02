# Deployment Architecture

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
