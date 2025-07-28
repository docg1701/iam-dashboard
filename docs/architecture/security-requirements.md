# Security Requirements

## Overview

This document consolidates security requirements for the IAM Dashboard agent migration, combining infrastructure security, API protection, and operational security measures.

## Critical Security Requirements

### 1. Rate Limiting [HIGH PRIORITY]

**Authentication Protection:**
- Login endpoints: 5 attempts/minute per IP
- 2FA verification: 3 attempts/minute per user
- Password reset: 3 attempts/hour per email
- Account lockout: 15 minutes after failed attempts

**API Protection:**
- General endpoints: 100 requests/minute per user
- File upload: 10 requests/minute per user
- Heavy operations: 5 requests/minute per user
- Admin endpoints: 50 requests/minute per admin

**Implementation:**
```python
# FastAPI-Limiter with Redis backend
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/auth/login")
@RateLimiter(times=5, seconds=60)
async def login(credentials: LoginRequest):
    pass

@app.post("/documents/process")
@RateLimiter(times=5, seconds=60)
async def process_document(file: UploadFile):
    pass
```

### 2. Security Headers [HIGH PRIORITY]

**Content Security Policy:**
```http
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' 'nonce-{random}';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  frame-ancestors 'none';
  form-action 'self';
  upgrade-insecure-requests;
```

**Additional Headers:**
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### 3. Input Validation [MEDIUM PRIORITY]

**Server-side Validation:**
- Pydantic models for all API inputs
- File upload validation (type, size, content)
- SQL injection prevention via SQLAlchemy ORM
- HTML sanitization for text inputs
- Path traversal prevention

**Implementation:**
```python
from pydantic import BaseModel, validator
import bleach

class DocumentUploadRequest(BaseModel):
    filename: str
    content_type: str
    
    @validator('filename')
    def validate_filename(cls, v):
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError('File type not allowed')
        return v

def sanitize_html_input(content: str) -> str:
    return bleach.clean(content, tags=[], strip=True)
```

### 4. Security Monitoring [MEDIUM PRIORITY]

**Event Logging:**
- Authentication events (login, logout, failures)
- Authorization violations
- Rate limiting violations
- Input validation failures
- Agent management operations
- File upload/download activities

**Threat Detection:**
- Multiple failed login attempts
- Unusual access patterns
- Suspicious file uploads
- Configuration changes
- Resource limit violations

**Implementation:**
```python
class SecurityEventLogger:
    def __init__(self):
        self.logger = logging.getLogger("security")
    
    async def log_auth_event(self, user_id: str, event: str, success: bool, ip: str):
        self.logger.info(f"Auth event: {event}", extra={
            "user_id": user_id,
            "event_type": event,
            "success": success,
            "ip_address": ip,
            "timestamp": datetime.utcnow()
        })
    
    async def log_security_violation(self, violation_type: str, details: str):
        self.logger.warning(f"Security violation: {violation_type}", extra={
            "violation_type": violation_type,
            "details": details,
            "severity": "HIGH",
            "timestamp": datetime.utcnow()
        })
```

## API Security

### Authentication Infrastructure

**FastAPI Authentication Dependencies:**
```python
# app/api/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.core.auth import AuthManager
from app.models.user import User

oauth2_scheme = HTTPBearer()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_manager: AuthManager = Depends(get_auth_manager)
) -> User:
    """Extract and validate JWT token."""
    try:
        payload = auth_manager.decode_token(token.credentials)
        user = await auth_manager.get_user_by_id(payload["user_id"])
        if not user:
            raise HTTPException(401, "Invalid token")
        return user
    except Exception:
        raise HTTPException(401, "Invalid token")

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user has admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    return current_user
```

### Agent-specific Security

**Agent Authorization:**
```python
async def authorize_agent_operation(
    user: User,
    agent_id: str, 
    operation: str
) -> bool:
    """Authorize agent operations."""
    # Admin users can perform all operations
    if user.is_admin:
        return True
    
    # Regular users can only view status
    if operation in ["status", "health"]:
        return True
    
    return False

@router.post("/admin/agents/{agent_id}/restart")
async def restart_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user)
):
    if not await authorize_agent_operation(current_user, agent_id, "restart"):
        raise HTTPException(403, "Insufficient permissions")
    
    await agent_manager.restart_agent(agent_id)
    return {"status": "restarted"}
```

## Infrastructure Security

### Container Security

**Docker Security Hardening:**
```dockerfile
# Use non-root user
FROM python:3.12-slim
RUN useradd -m -u 1000 appuser
USER appuser

# Security settings
RUN pip install --no-cache-dir --user -r requirements.txt
COPY --chown=appuser:appuser . /app
WORKDIR /app

# Remove unnecessary packages
RUN apt-get remove -y wget curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
```

**Docker Compose Security:**
```yaml
version: '3.8'
services:
  web:
    build: .
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    environment:
      - PYTHONUNBUFFERED=1
```

### Network Security

**Firewall Configuration:**
- Allow only necessary ports (80, 443, 5432 for PostgreSQL)
- Block direct database access from external networks
- Use VPN for administrative access
- Implement network segmentation

**HTTPS/TLS Configuration:**
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
}
```

## Agent Runtime Security

### Sandboxing

**Resource Limits:**
```python
class SecureAgentRuntime:
    def __init__(self):
        self.limits = {
            "memory_mb": 512,
            "cpu_percent": 50,
            "timeout_seconds": 300,
            "network_access": False
        }
    
    async def execute_with_limits(self, agent: Agent, request: Any):
        # Set memory limit
        resource.setrlimit(resource.RLIMIT_AS, (
            self.limits["memory_mb"] * 1024 * 1024,
            self.limits["memory_mb"] * 1024 * 1024
        ))
        
        # Set timeout
        signal.alarm(self.limits["timeout_seconds"])
        
        try:
            return await agent.process(request)
        except TimeoutError:
            raise SecurityError("Agent execution timeout")
        finally:
            signal.alarm(0)
```

### Data Protection

**Sensitive Data Handling:**
```python
class DataProtectionManager:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())
    
    def encrypt_sensitive_fields(self, data: dict) -> dict:
        sensitive_fields = ["cpf", "rg", "credit_card", "ssn"]
        
        for field in sensitive_fields:
            if field in data:
                encrypted = self.cipher.encrypt(str(data[field]).encode())
                data[field] = encrypted.decode()
        
        return data
    
    def sanitize_logs(self, log_data: dict) -> dict:
        # Remove sensitive information from logs
        sensitive_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b',  # CPF
        ]
        
        for key, value in log_data.items():
            if isinstance(value, str):
                for pattern in sensitive_patterns:
                    value = re.sub(pattern, '[REDACTED]', value)
                log_data[key] = value
        
        return log_data
```

## Compliance Requirements

### LGPD/GDPR Compliance

**Data Processing Consent:**
```python
class ComplianceManager:
    async def verify_processing_consent(
        self, 
        user_id: str, 
        processing_purpose: str
    ) -> bool:
        consent = await self.consent_service.get_consent(user_id, processing_purpose)
        return consent and consent.is_valid()
    
    async def log_data_processing(
        self,
        user_id: str,
        purpose: str,
        data_categories: List[str]
    ):
        await self.audit_logger.log_processing_activity(
            user_id=user_id,
            purpose=purpose,
            data_categories=data_categories,
            legal_basis="consent",
            timestamp=datetime.utcnow()
        )
```

**Data Retention:**
- User data: 7 years (legal requirement)
- Logs: 1 year for security, anonymized after
- Backup data: Same retention as primary data
- Agent processing metadata: 1 year

## Implementation Timeline

**Sprint 1 (Week 1): Critical Security**
- Rate limiting implementation
- Security headers configuration
- Basic input validation
- Authentication dependencies

**Sprint 2 (Week 2): Infrastructure Security**
- Container hardening
- Network security configuration
- HTTPS/TLS setup
- Firewall rules

**Sprint 3 (Week 3): Agent Security**
- Agent runtime sandboxing
- Agent authorization
- Security monitoring
- Data protection measures

**Sprint 4 (Week 4): Compliance & Testing**
- LGPD/GDPR compliance measures
- Security testing implementation
- Audit logging completion
- Documentation and training

## Testing Requirements

**Security Testing:**
```python
class SecurityTests:
    async def test_rate_limiting(self):
        # Test rate limits are enforced
        for i in range(10):
            response = await self.client.post("/auth/login", json=invalid_creds)
        
        assert response.status_code == 429  # Too Many Requests
    
    async def test_input_sanitization(self):
        malicious_input = "<script>alert('xss')</script>"
        response = await self.client.post("/questionnaires", json={
            "content": malicious_input
        })
        
        # Should be sanitized
        assert "<script>" not in response.json()["content"]
    
    async def test_unauthorized_agent_access(self):
        regular_user_token = await self.get_regular_user_token()
        
        response = await self.client.post(
            "/admin/agents/pdf_processor/restart",
            headers={"Authorization": f"Bearer {regular_user_token}"}
        )
        
        assert response.status_code == 403
```

## Monitoring and Alerting

**Security Metrics:**
- Failed authentication attempts per minute
- Rate limit violations per hour
- Security header violations
- Agent resource usage anomalies
- Suspicious file upload patterns

**Alert Thresholds:**
- >10 failed logins from same IP in 1 minute
- >100 rate limit violations in 1 hour
- Any privilege escalation attempts
- Agent memory usage >80%
- Configuration changes by non-admin users