# Security Integration

## Agent Security Framework

**Authentication and Authorization:**
```python
class AgentSecurityManager:
    """Security manager for agent operations."""
    
    async def authorize_agent_operation(
        self, 
        user: User, 
        agent_id: str, 
        operation: str
    ) -> bool:
        """Authorize user to perform agent operations."""
        # Check user roles
        if not user.is_admin and operation in ["enable", "disable", "configure"]:
            return False
        
        # Check agent-specific permissions
        agent_permissions = await self._get_agent_permissions(user, agent_id)
        return operation in agent_permissions
    
    async def audit_agent_operation(
        self, 
        user: User, 
        agent_id: str, 
        operation: str, 
        success: bool
    ) -> None:
        """Audit log for agent operations."""
        await self._log_security_event(
            event_type="agent_operation",
            user_id=user.id,
            agent_id=agent_id,
            operation=operation,
            success=success,
            timestamp=datetime.utcnow()
        )
```

**Data Protection:**
```python
class AgentDataProtection:
    """Data protection for agent processing."""
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data before agent processing."""
        # Remove sensitive information
        # Validate input format
        # Apply data protection rules
        return sanitized_data
    
    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data in agent processing."""
        sensitive_fields = ["cpf", "rg", "credit_card", "bank_account"]
        
        for field in sensitive_fields:
            if field in data:
                data[field] = self._encrypt_field(data[field])
        
        return data
```

## API Security

**Secure Agent Management Endpoints:**
```python
# Secure agent management endpoints
@router.post("/admin/agents/{agent_id}/enable")
@require_admin_role
@rate_limit("5/minute")
async def enable_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    security_manager: AgentSecurityManager = Depends(get_security_manager)
):
    # Authorize operation
    authorized = await security_manager.authorize_agent_operation(
        current_user, agent_id, "enable"
    )
    
    if not authorized:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Perform operation
    success = await agent_manager.enable_agent(agent_id)
    
    # Audit log
    await security_manager.audit_agent_operation(
        current_user, agent_id, "enable", success
    )
    
    return {"agent_id": agent_id, "enabled": success}
```

## Configuration Security

**Secure Configuration Management:**
```python
class SecureConfigManager:
    """Secure configuration management for agents."""
    
    def __init__(self, encryption_key: str):
        self.encryption_key = encryption_key
        self.cipher = Fernet(encryption_key.encode())
    
    async def store_sensitive_config(self, agent_id: str, config: dict) -> None:
        """Store agent configuration with sensitive data encrypted."""
        # Identify sensitive configuration fields
        sensitive_fields = ["api_keys", "database_urls", "secrets"]
        
        for field in sensitive_fields:
            if field in config:
                # Encrypt sensitive fields
                encrypted_value = self.cipher.encrypt(
                    json.dumps(config[field]).encode()
                )
                config[field] = encrypted_value.decode()
        
        # Store configuration securely
        await self._store_config(agent_id, config)
    
    async def load_sensitive_config(self, agent_id: str) -> dict:
        """Load and decrypt agent configuration."""
        config = await self._load_config(agent_id)
        
        # Decrypt sensitive fields
        sensitive_fields = ["api_keys", "database_urls", "secrets"]
        for field in sensitive_fields:
            if field in config:
                decrypted_value = self.cipher.decrypt(config[field].encode())
                config[field] = json.loads(decrypted_value.decode())
        
        return config
```

## Input Validation and Sanitization

**Agent Input Validation:**
```python
class AgentInputValidator:
    """Validate and sanitize inputs for agent processing."""
    
    def validate_document_upload(self, file_data: bytes, filename: str) -> bool:
        """Validate uploaded document for security."""
        # Check file size limits
        if len(file_data) > 50 * 1024 * 1024:  # 50MB limit
            raise SecurityError("File size exceeds limit")
        
        # Validate file type
        allowed_types = ['.pdf', '.doc', '.docx', '.txt']
        if not any(filename.lower().endswith(ext) for ext in allowed_types):
            raise SecurityError("File type not allowed")
        
        # Scan for malicious content
        if self._contains_malicious_patterns(file_data):
            raise SecurityError("Malicious content detected")
        
        return True
    
    def sanitize_questionnaire_input(self, user_input: str) -> str:
        """Sanitize questionnaire generation input."""
        # Remove HTML tags
        sanitized = bleach.clean(user_input, tags=[], strip=True)
        
        # Limit length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]
        
        # Remove SQL injection patterns
        sql_injection_patterns = [
            r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b)",
            r"(\bDROP\b|\bCREATE\b|\bALTER\b)"
        ]
        
        for pattern in sql_injection_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        return sanitized
```

## Agent Runtime Security

**Secure Agent Execution Environment:**
```python
class SecureAgentRuntime:
    """Secure runtime environment for agents."""
    
    def __init__(self):
        self.resource_limits = {
            "memory_mb": 512,
            "cpu_percentage": 50,
            "execution_time_seconds": 300,
            "network_access": False  # Agents should not have direct network access
        }
    
    async def execute_agent_with_sandbox(
        self, 
        agent: Agent, 
        request: Any
    ) -> Any:
        """Execute agent in sandboxed environment."""
        # Set resource limits
        resource.setrlimit(resource.RLIMIT_AS, (
            self.resource_limits["memory_mb"] * 1024 * 1024,
            self.resource_limits["memory_mb"] * 1024 * 1024
        ))
        
        # Set execution timeout
        signal.alarm(self.resource_limits["execution_time_seconds"])
        
        try:
            # Execute agent
            result = await agent.process(request)
            
            # Validate output
            self._validate_agent_output(result)
            
            return result
            
        except TimeoutError:
            raise SecurityError("Agent execution timeout")
        except MemoryError:
            raise SecurityError("Agent memory limit exceeded")
        finally:
            # Clear alarm
            signal.alarm(0)
```

## Audit and Monitoring

**Security Event Logging:**
```python
class SecurityEventLogger:
    """Log security events for agent operations."""
    
    def __init__(self):
        self.logger = logging.getLogger("security.agents")
        self.logger.setLevel(logging.INFO)
    
    async def log_agent_access(
        self, 
        user_id: str, 
        agent_id: str, 
        operation: str,
        success: bool,
        additional_context: dict = None
    ):
        """Log agent access events."""
        event_data = {
            "event_type": "agent_access",
            "user_id": user_id,
            "agent_id": agent_id,
            "operation": operation,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": self._get_client_ip(),
            "user_agent": self._get_user_agent()
        }
        
        if additional_context:
            event_data.update(additional_context)
        
        self.logger.info(
            f"Agent access: {operation} on {agent_id} by {user_id}",
            extra=event_data
        )
    
    async def log_security_violation(
        self,
        violation_type: str,
        details: str,
        severity: str = "HIGH"
    ):
        """Log security violations."""
        event_data = {
            "event_type": "security_violation",
            "violation_type": violation_type,
            "details": details,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": self._get_client_ip()
        }
        
        self.logger.warning(
            f"Security violation: {violation_type} - {details}",
            extra=event_data
        )
```

## Secrets Management

**Agent Secrets Management:**
```python
class AgentSecretsManager:
    """Manage secrets for agent operations."""
    
    def __init__(self, key_vault_url: str = None):
        self.key_vault_url = key_vault_url
        self.local_secrets = {}
    
    async def get_agent_secret(self, agent_id: str, secret_name: str) -> str:
        """Retrieve secret for agent."""
        # Try key vault first (if configured)
        if self.key_vault_url:
            return await self._get_from_key_vault(agent_id, secret_name)
        
        # Fallback to encrypted local storage
        return await self._get_from_local_storage(agent_id, secret_name)
    
    async def rotate_agent_secrets(self, agent_id: str) -> None:
        """Rotate secrets for specific agent."""
        secrets_to_rotate = await self._get_agent_secrets(agent_id)
        
        for secret_name in secrets_to_rotate:
            # Generate new secret
            new_secret = self._generate_secret()
            
            # Update in storage
            await self._update_secret(agent_id, secret_name, new_secret)
            
            # Notify agent of rotation
            await self._notify_agent_secret_rotation(agent_id, secret_name)
```

## Network Security

**Agent Network Isolation:**
```python
class AgentNetworkSecurity:
    """Network security for agent communications."""
    
    def __init__(self):
        self.allowed_hosts = [
            "api.gemini.google.com",  # For Gemini API
            "localhost",              # For database connections
            "127.0.0.1"              # Local services
        ]
    
    def validate_network_request(self, url: str) -> bool:
        """Validate network requests from agents."""
        parsed_url = urlparse(url)
        
        # Check if host is in allowed list
        if parsed_url.hostname not in self.allowed_hosts:
            raise SecurityError(f"Network access to {parsed_url.hostname} not allowed")
        
        # Ensure HTTPS for external APIs
        if parsed_url.hostname != "localhost" and parsed_url.scheme != "https":
            raise SecurityError("Only HTTPS connections allowed for external services")
        
        return True
    
    async def proxy_agent_request(self, url: str, data: dict) -> dict:
        """Proxy agent requests through security layer."""
        # Validate request
        self.validate_network_request(url)
        
        # Add security headers
        headers = {
            "User-Agent": "IAM-Dashboard-Agent/1.0",
            "Authorization": f"Bearer {await self._get_api_token()}",
            "Content-Type": "application/json"
        }
        
        # Make request with timeout
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=headers)
            return response.json()
```

## Security Testing

**Agent Security Tests:**
```python
class AgentSecurityTests:
    """Security tests for agent operations."""
    
    async def test_unauthorized_agent_access(self):
        """Test that unauthorized users cannot access agents."""
        regular_user = await self.create_regular_user()
        
        with pytest.raises(HTTPException) as exc_info:
            await self.client.post(
                "/admin/agents/pdf_processor/enable",
                headers={"Authorization": f"Bearer {regular_user.token}"}
            )
        
        assert exc_info.value.status_code == 403
    
    async def test_agent_input_sanitization(self):
        """Test that agent inputs are properly sanitized."""
        malicious_input = "<script>alert('xss')</script>"
        
        sanitized = self.input_validator.sanitize_questionnaire_input(malicious_input)
        
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
    
    async def test_agent_resource_limits(self):
        """Test that agents respect resource limits."""
        # Create memory-intensive request
        large_request = {"data": "x" * (600 * 1024 * 1024)}  # 600MB
        
        with pytest.raises(SecurityError) as exc_info:
            await self.secure_runtime.execute_agent_with_sandbox(
                self.test_agent, 
                large_request
            )
        
        assert "memory limit exceeded" in str(exc_info.value)
```

## Compliance Integration

**LGPD/GDPR Compliance:**
```python
class AgentComplianceManager:
    """Ensure agent operations comply with data protection regulations."""
    
    async def process_data_with_consent(
        self, 
        user_id: str, 
        data: dict, 
        processing_purpose: str
    ) -> dict:
        """Process data only with proper consent."""
        # Check consent
        consent = await self.consent_service.get_user_consent(
            user_id, 
            processing_purpose
        )
        
        if not consent.is_valid():
            raise ComplianceError("No valid consent for data processing")
        
        # Log processing activity
        await self.audit_logger.log_data_processing(
            user_id=user_id,
            purpose=processing_purpose,
            data_categories=self._categorize_data(data),
            legal_basis="consent"
        )
        
        return data
    
    async def anonymize_agent_logs(self, retention_days: int = 365):
        """Anonymize agent logs after retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Anonymize personal data in logs
        await self.log_anonymizer.anonymize_logs_before(cutoff_date)
```