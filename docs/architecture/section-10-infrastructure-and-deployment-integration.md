# Section 10: Infrastructure and Deployment Integration

### 10.1 Production Container Configuration

**Essential Docker Compose Setup**:
```yaml
# docker-compose.prod.yml
services:
  iam-dashboard:
    build: .
    environment:
      - ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports: ["5432:5432"]
    command: postgres -c max_connections=200 -c shared_buffers=256MB

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --appendonly yes --maxmemory 512mb
```

### 10.2 Kubernetes Deployment

**Core K8s Resources**:
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iam-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: iam-dashboard
  template:
    spec:
      containers:
      - name: iam-dashboard
        image: iam-dashboard:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: iam-secrets
              key: database-url
        resources:
          requests: {memory: "1Gi", cpu: "500m"}
          limits: {memory: "2Gi", cpu: "1000m"}
        livenessProbe:
          httpGet: {path: /health, port: 8000}
          initialDelaySeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: iam-dashboard-service
spec:
  selector:
    app: iam-dashboard
  ports:
  - port: 80
    targetPort: 8000
```