# Deployment Guide - Agent-Based Architecture

This guide covers deployment procedures for the IAM Dashboard after migration to autonomous agent architecture. All legacy Celery components have been removed.

## Prerequisites

- Docker and Docker Compose
- PostgreSQL with pgvector extension
- Redis (for agent caching)
- Python 3.12+ (for local development)

## Environment Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/advocacia_db

# Redis (for agent caching)
REDIS_URL=redis://localhost:6379/0

# Application
ENVIRONMENT=production
SECRET_KEY=your-secure-secret-key-here
DEBUG=false

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-pro
GEMINI_EMBEDDING_MODEL=embedding-001

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 2FA Configuration
TOTP_ISSUER_NAME=IAM Dashboard

# Agent Management
AGENT_API_BASE_URL=http://localhost:8080/v1
```

## Docker Deployment

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./uploads:/app/uploads
      - /app/.venv
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/advocacia_db
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
    depends_on:
      - db
      - redis
    command: python -m app.main
    restart: unless-stopped

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=advocacia_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  caddy:
    image: caddy:2.10-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  caddy_data:
  caddy_config:
```

### Key Changes from Legacy System

1. **No Celery Worker Service**: The `worker` service has been completely removed
2. **Agent-Based Processing**: Document processing now handled by autonomous agents
3. **Simplified Architecture**: Only app, database, Redis (for caching), and reverse proxy services

## Deployment Steps

### 1. Prepare Environment

```bash
# Clone repository
git clone <repository-url>
cd iam-dashboard

# Copy and configure environment
cp .env.example .env
# Edit .env with production values
```

### 2. Database Setup

```bash
# Start database service
docker-compose up -d db

# Run migrations
uv run alembic upgrade head

# Verify pgvector extension
psql -h localhost -U postgres -d advocacia_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Agent Configuration

Ensure agent configuration files are properly set up:

```bash
# Verify agent configuration
cat app/config/agents.yaml

# Test agent connectivity
uv run python -c "from app.core.agent_manager import AgentManager; print('Agents OK')"
```

### 4. Deploy Application

```bash
# Build and start all services
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs app
```

### 5. Health Checks

```bash
# Check application health
curl http://localhost:8080/v1/admin/system/health

# Check agent status
curl http://localhost:8080/v1/admin/agents

# Verify database connectivity
docker-compose exec db psql -U postgres -d advocacia_db -c "SELECT 1;"
```

## Agent Management

### Starting/Stopping Agents

```bash
# Start specific agent
curl -X POST http://localhost:8080/v1/admin/agents/pdf_processor/start

# Stop specific agent
curl -X POST http://localhost:8080/v1/admin/agents/pdf_processor/stop

# Restart all agents
curl -X POST http://localhost:8080/v1/admin/system/restart-all
```

### Agent Configuration Updates

```bash
# Update agent configuration
curl -X PUT http://localhost:8080/v1/admin/agents/pdf_processor/config \
  -H "Content-Type: application/json" \
  -d '{"max_concurrent_tasks": 5, "timeout_seconds": 300}'

# Validate configuration
curl -X POST http://localhost:8080/v1/admin/agents/pdf_processor/config/validate \
  -H "Content-Type: application/json" \
  -d '{"config": {"max_concurrent_tasks": 5}}'
```

## Monitoring

### System Health Monitoring

```bash
# Overall system health
curl http://localhost:8080/v1/admin/system/health

# Performance metrics
curl http://localhost:8080/v1/admin/system/metrics

# Agent-specific health
curl http://localhost:8080/v1/admin/agents/pdf_processor/health
```

### Log Management

```bash
# Application logs
docker-compose logs -f app

# Agent-specific logs
docker-compose exec app tail -f /app/logs/agents/pdf_processor.log

# Database logs
docker-compose logs -f db
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U postgres advocacia_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T db psql -U postgres advocacia_db < backup_file.sql
```

### Agent Configuration Backup

```bash
# Backup agent configurations
cp -r app/config/ backups/config_$(date +%Y%m%d_%H%M%S)/

# Backup uploaded documents
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz uploads/
```

## Troubleshooting

### Common Issues

1. **Agents Not Starting**
   ```bash
   # Check agent manager logs
   docker-compose logs app | grep -i agent
   
   # Verify Redis connectivity
   docker-compose exec redis redis-cli ping
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   docker-compose exec app python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
   ```

3. **Performance Issues**
   ```bash
   # Run performance tests
   uv run pytest tests/performance/ -v
   
   # Check resource usage
   docker stats
   ```

### Recovery Procedures

1. **Agent System Failure**
   ```bash
   # Restart all agents
   curl -X POST http://localhost:8080/v1/admin/system/restart-all
   
   # If that fails, restart application
   docker-compose restart app
   ```

2. **Database Recovery**
   ```bash
   # Stop application
   docker-compose stop app
   
   # Restore database
   docker-compose exec -T db psql -U postgres advocacia_db < backup_file.sql
   
   # Restart application
   docker-compose start app
   ```

## Security Considerations

### Production Security

1. **Environment Variables**: Never commit secrets to version control
2. **Database Security**: Use strong passwords and limit network access
3. **Agent Security**: Ensure agent configurations don't expose sensitive data
4. **SSL/TLS**: Configure Caddy with proper SSL certificates
5. **Rate Limiting**: Monitor and configure rate limiting for admin endpoints

### Security Checklist

- [ ] All secrets in environment variables
- [ ] Database credentials secured
- [ ] SSL certificates configured
- [ ] Agent access controls in place
- [ ] Log files properly secured
- [ ] Backup encryption enabled

## Performance Optimization

### Agent Performance

1. **Concurrent Processing**: Configure `max_concurrent_tasks` appropriately
2. **Memory Management**: Monitor agent memory usage
3. **Timeout Settings**: Adjust timeout values based on workload

### Database Performance

1. **Connection Pooling**: Configured in SQLAlchemy settings
2. **Index Optimization**: Ensure proper indexes on frequently queried columns
3. **pgvector Optimization**: Configure appropriate vector dimensions and indexes

## Scaling Considerations

### Horizontal Scaling

The agent-based architecture supports horizontal scaling:

1. **Multiple App Instances**: Run multiple app containers behind load balancer
2. **Agent Distribution**: Agents can be distributed across instances
3. **Database Scaling**: Consider read replicas for heavy read workloads

### Vertical Scaling

1. **CPU**: Agents benefit from multiple cores for parallel processing
2. **Memory**: Ensure sufficient memory for document processing and vector operations
3. **Storage**: Fast SSD storage recommended for document uploads and database