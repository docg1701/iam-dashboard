# Infrastructure and Deployment Integration

## Deployment Strategy

**Current Deployment (VPS + Docker):**
```yaml
# docker-compose.yml (existing)
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: iam_dashboard
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
  
  redis:
    image: redis:7-alpine
  
  celery_worker:  # TO BE REMOVED
    build: .
    command: celery -A app.workers.celery_app worker
    depends_on:
      - redis
      - postgres
```

**Target Deployment (Agent-based):**
```yaml
# docker-compose.yml (updated)
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AGNO_CONFIG_PATH=/app/config/agents.yaml
      - AGENT_MANAGEMENT_ENABLED=true
    volumes:
      - ./app/config:/app/config
    depends_on:
      - postgres
      - redis  # Still used for caching
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: iam_dashboard
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
  
  redis:
    image: redis:7-alpine
    # Still used for caching and session storage
```

## Environment Configuration

**Agent-specific Environment Variables:**
```bash
# .env additions
# Agent Configuration
AGNO_CONFIG_PATH="/app/config/agents.yaml"
AGENT_MANAGEMENT_ENABLED=true
AGENT_LOG_LEVEL="INFO"
AGENT_HEALTH_CHECK_INTERVAL=30

# Agent Resources
MAX_CONCURRENT_AGENTS=5
AGENT_MEMORY_LIMIT="512MB"
AGENT_TIMEOUT_SECONDS=300

# Tool Configuration
OCR_ENGINE="tesseract"  # or "gemini"
PDF_PROCESSING_TIMEOUT=120
VECTOR_BATCH_SIZE=100
```

## Resource Requirements

**Updated Resource Requirements:**
```yaml
# Previous: 4 vCPUs, 4GB RAM
# Updated for agents: 4 vCPUs, 6GB RAM

# Memory allocation:
# - FastAPI + NiceGUI: 1.5GB
# - PostgreSQL: 1GB
# - Redis: 256MB
# - Agent Manager + Active Agents: 2GB
# - PDF/OCR Processing: 1GB
# - System overhead: 256MB
```

## Monitoring and Health Checks

**Agent Health Monitoring:**
```python
class AgentHealthCheck:
    async def check_agent_health(self, agent_id: str) -> HealthStatus:
        agent = await self.agent_manager.get_agent(agent_id)
        
        return HealthStatus(
            agent_id=agent_id,
            status=agent.status,
            last_activity=agent.last_activity,
            memory_usage=agent.memory_usage,
            response_time=await self._measure_response_time(agent)
        )
```

**Prometheus Metrics (if monitoring available):**
```python
# app/monitoring/agent_metrics.py
from prometheus_client import Counter, Histogram, Gauge

agent_processing_total = Counter('agent_processing_total', 'Total agent processing requests', ['agent_id'])
agent_processing_duration = Histogram('agent_processing_duration_seconds', 'Agent processing duration', ['agent_id'])
agent_active_count = Gauge('agent_active_count', 'Number of active agents')
```

## Backup and Recovery

**Agent Configuration Backup:**
- **YAML Files:** Version controlled in repository
- **Runtime Configuration:** Backed up with regular database backups
- **Agent State:** Stateless agents, no persistent state backup needed

**Recovery Procedures:**
1. **Agent Failure:** Automatic restart via AgentManager
2. **Configuration Corruption:** Rollback to previous YAML configuration
3. **System Failure:** Standard database recovery + agent reinitialization

## Migration Strategy

**Phase 1: Infrastructure Preparation**
- Update docker-compose.yml with agent environment variables
- Deploy Agno framework and dependencies
- Configure agent management endpoints
- Set up monitoring and health checks

**Phase 2: Parallel Deployment**
- Deploy agents alongside existing Celery workers
- Gradual traffic shifting from Celery to agents
- Monitor performance and stability metrics
- Rollback capability maintained

**Phase 3: Legacy Cleanup**
- Remove Celery worker containers
- Clean up Redis job queues
- Update monitoring configurations
- Final performance validation

## Deployment Checklist

**Pre-deployment:**
- [ ] Agent configuration files validated
- [ ] Environment variables configured
- [ ] Resource requirements verified
- [ ] Backup procedures tested
- [ ] Rollback plan documented

**Deployment:**
- [ ] Infrastructure updated with agent support
- [ ] Agent manager initialized successfully
- [ ] All agents loading and responding to health checks
- [ ] API endpoints responding correctly
- [ ] UI components functioning properly

**Post-deployment:**
- [ ] Performance monitoring active
- [ ] Error rates within acceptable limits
- [ ] User acceptance testing completed
- [ ] Documentation updated
- [ ] Team training completed