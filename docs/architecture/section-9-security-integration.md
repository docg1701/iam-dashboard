# Section 9: Security Integration

### 9.1 Enhanced Authentication and Authorization

**Complete Security Implementation**:

```python
# app/core/security/agent_security.py
class AgentSecurityManager:
    """Comprehensive security manager for agent operations."""
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.access_logger = SecurityAuditLogger()
        self.rate_limiter = RateLimiter()
        self.encryption = DocumentEncryption()
    
    async def authorize_agent_operation(
        self,
        user_token: str,
        agent_id: str,
        operation: str,
        resource_id: str = None
    ) -> AuthorizationResult:
        """Comprehensive authorization for agent operations."""
        
        try:
            # Validate user token
            user = await self.auth_manager.validate_token(user_token)
            if not user:
                await self.access_logger.log_unauthorized_access(user_token, agent_id, operation)
                return AuthorizationResult(authorized=False, reason="Invalid token")
            
            # Check rate limiting
            if not await self.rate_limiter.check_rate_limit(user["user_id"], operation):
                await self.access_logger.log_rate_limit_exceeded(user["user_id"], agent_id, operation)
                return AuthorizationResult(authorized=False, reason="Rate limit exceeded")
            
            # Validate agent permissions
            if not await self._check_agent_permission(user, agent_id, operation):
                await self.access_logger.log_permission_denied(user["user_id"], agent_id, operation)
                return AuthorizationResult(authorized=False, reason="Insufficient permissions")
            
            # Resource-specific authorization
            if resource_id and not await self._check_resource_access(user, resource_id, operation):
                await self.access_logger.log_resource_access_denied(user["user_id"], resource_id, operation)
                return AuthorizationResult(authorized=False, reason="Resource access denied")
            
            # Log successful authorization
            await self.access_logger.log_successful_authorization(user["user_id"], agent_id, operation, resource_id)
            
            return AuthorizationResult(
                authorized=True,
                user_context={
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "role": user["role"],
                    "permissions": await self._get_user_permissions(user)
                }
            )
            
        except Exception as e:
            await self.access_logger.log_security_error(str(e), agent_id, operation)
            return AuthorizationResult(authorized=False, reason="Security check failed")
```

#### 9.1.1 Role-Based Access Control Implementation

**CRITICAL IMPLEMENTATION REQUIREMENT**: Addresses SYSADMIN role cannot access admin endpoints issue.

##### Admin Access Pattern Specification

```python
# app/core/security/rbac_manager.py
class RoleBasedAccessManager:
    """Enhanced RBAC implementation with admin endpoint access patterns."""
    
    def __init__(self):
        self.role_permissions = self._initialize_role_permissions()
        self.endpoint_role_mapping = self._initialize_endpoint_mappings()
    
    def _initialize_role_permissions(self) -> dict:
        """UserRole enum verification procedures."""
        
        return {
            UserRole.SYSADMIN: {
                "agent_management": ["create", "delete", "configure", "hot_deploy", "execute", "monitor"],
                "user_management": ["create", "read", "update", "delete", "manage"],
                "admin_panel": ["full_access"],  # CRITICAL FIX: Explicit admin panel access
                "system_admin": ["full_access"], # CRITICAL FIX: System admin operations
                "monitoring": ["full_access"],   # CRITICAL FIX: Full monitoring access
                "configuration": ["full_access"]# CRITICAL FIX: Configuration management
            },
            UserRole.ADMIN_USER: {
                "agent_management": ["execute", "monitor"],
                "user_management": ["read", "update"],
                "admin_panel": ["limited_access"]
            },
            UserRole.COMMON_USER: {
                "agent_management": ["execute"],
                "admin_panel": ["no_access"]
            }
        }
    
    def _initialize_endpoint_mappings(self) -> dict:
        """Role-to-endpoint mapping strategy."""
        
        return {
            # Admin Panel Endpoints - CRITICAL FIX
            "/admin": [UserRole.SYSADMIN],
            "/admin/users": [UserRole.SYSADMIN],
            "/admin/system": [UserRole.SYSADMIN],
            "/admin/agents": [UserRole.SYSADMIN, UserRole.ADMIN_USER],
            
            # Agent Management Endpoints
            "/api/agents/create": [UserRole.SYSADMIN],
            "/api/agents/*/configure": [UserRole.SYSADMIN],
            "/api/agents/*/hot-deploy": [UserRole.SYSADMIN],
            "/api/agents/*/execute": [UserRole.SYSADMIN, UserRole.ADMIN_USER, UserRole.COMMON_USER],
            "/api/agents/*/health": [UserRole.SYSADMIN, UserRole.ADMIN_USER]
        }
```