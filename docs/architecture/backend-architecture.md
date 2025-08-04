# Backend Architecture

**Backend-specific architecture details based on FastAPI + SQLModel + PostgreSQL with Agno agent framework integration and comprehensive permission system**

> ๐ **Quick Navigation**: [API Patterns](./permission-integration-guide.md#backend-permission-patterns) | [Developer Reference](./developer-reference.md#backend-patterns) | [Permission Architecture](./permissions-architecture.md#backend-architecture) | [Database Schema](./database-schema.md)

---

### Service Architecture

**FastAPI Application Structure:**
```
apps/backend/src/
├── main.py                       # FastAPI application entry point
├── core/                         # Core system modules
│   ├── config.py                 # Environment configuration
│   ├── database.py               # Database connection and session management
│   ├── security.py               # Authentication and JWT handling
│   ├── exceptions.py             # Custom exception classes
│   ├── middleware.py             # Custom middleware (CORS, logging, permissions)
│   └── websockets.py             # WebSocket manager for real-time updates
├── api/                          # REST API routes
│   └── v1/                       # API version 1
│       ├── auth.py               # Authentication endpoints
│       ├── clients.py            # Client management endpoints (with permissions)
│       ├── users.py              # User management endpoints
│       ├── permissions.py        # Permission management endpoints
│       └── audit.py              # Audit trail endpoints
├── services/                     # Business logic layer
│   ├── client_service.py         # Client business logic
│   ├── user_service.py           # User business logic
│   ├── permission_service.py     # Permission validation and management
│   ├── permission_template_service.py # Permission template management
│   └── permission_audit_service.py # Permission change auditing
├── models/                       # SQLModel database models
│   ├── user.py                   # User model
│   ├── client.py                 # Client model
│   ├── permissions.py            # UserAgentPermission model
│   └── audit.py                  # Audit models
├── agents/                       # Agno agent implementations
├── schemas/                      # Pydantic request/response schemas
│   ├── auth.py                   # Authentication schemas
│   ├── clients.py                # Client schemas
│   ├── users.py                  # User schemas
│   ├── permissions.py            # Permission schemas
│   └── common.py                 # Shared schemas
└── utils/                        # Utility functions
    ├── audit.py                  # Audit logging utilities
    ├── validation.py             # Validation utilities
    └── seed_data.py              # Database seeding
```

### Database Architecture

**SQLModel Integration:**
```python
class ClientBase(SQLModel):
    """Base client fields for sharing between models"""
    full_name: str = Field(min_length=2, max_length=255)
    ssn: str = Field(regex=r'^\d{3}-\d{2}-\d{4}$'
    birth_date: date
    status: ClientStatus = ClientStatus.ACTIVE
    notes: Optional[str] = Field(default=None, max_length=1000)

class Client(BaseModel, ClientBase, table=True):
    """Client database model"""
    __tablename__ = "clients"
    
    client_id: UUID = Field(primary_key=True, alias="id")
    created_by: UUID = Field(foreign_key="users.user_id")
    updated_by: UUID = Field(foreign_key="users.user_id")
    
    # Relationships
    creator: User = Relationship(back_populates="created_clients")
    documents: List["Agent2Document"] = Relationship(back_populates="client")
```

### Authentication and Authorization

**JWT Authentication Flow:**
```python
class AuthService:
    def create_access_token(self, user_id: str, user_role: str) -> dict:
        """Create secure JWT token with session tracking"""
        payload = {
            "sub": user_id,
            "role": user_role,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=15),
        }
        
        access_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 900
        }

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenData(user_id=UUID(payload["sub"]), role=payload["role"])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

### Permission System Architecture

**Enhanced Permission Model:**
The system implements a flexible agent-based permission model that transforms the rigid 3-role hierarchy into granular, assignable permissions per agent.

**Permission Service Layer:**
```python
class PermissionService:
    """Core service for permission validation and management"""
    
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.cache_ttl = 300  # 5 minutes
    
    async def has_agent_permission(
        self, 
        user_id: UUID, 
        agent_name: str, 
        operation: str
    ) -> bool:
        """Check if user has permission for specific agent operation with caching"""
        # Sysadmin bypass - always has access
        user = await self.get_user(user_id)
        if user.role == "sysadmin":
            return True
            
        # Check Redis cache first for performance
        cache_key = f"permissions:{user_id}:{agent_name}"
        cached_permissions = await self.redis.get(cache_key)
        
        if cached_permissions:
            permissions = json.loads(cached_permissions)
        else:
            # Load from database
            permission_record = await self.db.get(
                UserAgentPermission,
                {"user_id": user_id, "agent_name": agent_name}
            )
            
            if not permission_record:
                return False
                
            permissions = permission_record.permissions
            # Cache for performance
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(permissions))
        
        return permissions.get(operation, False)
    
    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate all cached permissions for a user"""
        pattern = f"permissions:{user_id}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
    
    async def warm_cache_for_user(self, user_id: UUID) -> None:
        """Pre-load permissions for all agents for a user"""
        user_permissions = await self.get_user_permissions(user_id)
        for agent_name, permissions in user_permissions.items():
            cache_key = f"permissions:{user_id}:{agent_name}"
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(permissions))
    
    async def assign_agent_permissions(
        self,
        user_id: UUID,
        agent_name: str,
        permissions: Dict[str, bool],
        assigned_by: UUID
    ) -> UserAgentPermission:
        """Assign or update user permissions for a specific agent"""
        # Validate permission structure
        valid_operations = {"create", "read", "update", "delete"}
        if not all(op in valid_operations for op in permissions.keys()):
            raise ValueError("Invalid permission operation")
        
        # Check if permission record exists
        existing = await self.db.get(
            UserAgentPermission,
            {"user_id": user_id, "agent_name": agent_name}
        )
        
        if existing:
            # Update existing permissions
            old_permissions = existing.permissions.copy()
            existing.permissions = permissions
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            
            # Log audit trail
            await self.log_permission_change(
                user_id, agent_name, old_permissions, permissions, assigned_by
            )
        else:
            # Create new permission record
            new_permission = UserAgentPermission(
                user_id=user_id,
                agent_name=agent_name,
                permissions=permissions,
                created_by_user_id=assigned_by
            )
            self.db.add(new_permission)
            await self.db.commit()
            
            # Log audit trail
            await self.log_permission_change(
                user_id, agent_name, {}, permissions, assigned_by
            )
        
        # Invalidate cache for consistency (immediate invalidation per NFR12)
        cache_key = f"permissions:{user_id}:{agent_name}"
        await self.redis.delete(cache_key)
        
        # Also invalidate user's complete permission cache
        await self.invalidate_user_cache(user_id)
        
        return new_permission or existing
    
    async def get_user_permissions(self, user_id: UUID) -> Dict[str, Dict[str, bool]]:
        """Get complete permission set for a user"""
        permissions = {}
        
        # Get all permission records for user
        records = await self.db.exec(
            select(UserAgentPermission).where(
                UserAgentPermission.user_id == user_id
            )
        )
        
        for record in records:
            permissions[record.agent_name] = record.permissions
            
        return permissions
```

**Permission Validation Middleware:**
```python
def require_agent_permission(agent_name: str, operation: str):
    """Decorator for API endpoint permission validation"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
            # Sysadmin bypass
            if current_user.role == "sysadmin":
                return await func(*args, current_user=current_user, **kwargs)
            
            # Admin has access to client_management and reports_analysis
            if current_user.role == "admin" and agent_name in ["client_management", "reports_analysis"]:
                return await func(*args, current_user=current_user, **kwargs)
            
            # Check specific permission for users
            permission_service = get_permission_service()
            has_permission = await permission_service.has_agent_permission(
                current_user.user_id, agent_name, operation
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Insufficient permissions",
                        "required_permission": f"{agent_name}:{operation}",
                        "user_role": current_user.role,
                        "message": f"Access denied for {operation} operation on {agent_name} agent"
                    }
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage in API endpoints
@router.post("/clients", response_model=ClientResponse)
@require_agent_permission("client_management", "create")
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user)
):
    return await client_service.create_client(client_data, current_user.user_id)
```

**Permission API Endpoints:**
```python
@router.get("/users/{user_id}/permissions")
@require_role("admin")
async def get_user_permissions(
    user_id: UUID,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Dict[str, bool]]:
    """Get all agent permissions for a specific user"""
    return await permission_service.get_user_permissions(user_id)

@router.put("/users/{user_id}/permissions")
@require_role("admin")
async def update_user_permissions(
    user_id: UUID,
    permissions_update: UserPermissionsUpdate,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Update user permissions for multiple agents"""
    results = {}
    
    for agent_name, permissions in permissions_update.permissions.items():
        try:
            await permission_service.assign_agent_permissions(
                user_id=user_id,
                agent_name=agent_name,
                permissions=permissions,
                assigned_by=current_user.user_id
            )
            results[agent_name] = "success"
        except Exception as e:
            results[agent_name] = f"error: {str(e)}"
    
    return results

@router.put("/permissions/bulk")
@require_role("admin")
async def bulk_update_permissions(
    bulk_request: BulkPermissionRequest,
    current_user: User = Depends(get_current_user)
) -> BulkPermissionResponse:
    """Apply permission changes to multiple users simultaneously"""
    results = []
    
    for user_id in bulk_request.user_ids:
        try:
            for agent_name, permissions in bulk_request.permissions.items():
                await permission_service.assign_agent_permissions(
                    user_id=user_id,
                    agent_name=agent_name,
                    permissions=permissions,
                    assigned_by=current_user.user_id
                )
            results.append({"user_id": user_id, "status": "success"})
        except Exception as e:
            results.append({"user_id": user_id, "status": "error", "error": str(e)})
    
    return BulkPermissionResponse(results=results)
```

**Real-time Permission Updates:**
```python
class PermissionUpdateManager:
    """WebSocket manager for real-time permission updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis_client = get_redis_client()
    
    async def connect(self, websocket: WebSocket, user_id: UUID):
        await websocket.accept()
        self.active_connections.append({"socket": websocket, "user_id": user_id})
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            conn for conn in self.active_connections 
            if conn["socket"] != websocket
        ]
    
    async def broadcast_permission_update(self, user_id: UUID, permissions: Dict):
        """Broadcast permission updates to affected users"""
        message = {
            "type": "permission_update",
            "user_id": str(user_id),
            "permissions": permissions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to specific user and all admin users
        for connection in self.active_connections:
            try:
                conn_user_id = connection["user_id"]
                user = await get_user_by_id(conn_user_id)
                
                # Send to target user or admin users
                if conn_user_id == user_id or user.role in ["admin", "sysadmin"]:
                    await connection["socket"].send_json(message)
            except ConnectionClosedOK:
                self.disconnect(connection["socket"])

permission_manager = PermissionUpdateManager()

@app.websocket("/ws/permissions")
async def websocket_endpoint(
    websocket: WebSocket, 
    current_user: User = Depends(get_current_user_ws)
):
    await permission_manager.connect(websocket, current_user.user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        permission_manager.disconnect(websocket)
```

### Performance Optimization Strategies

**Permission Caching Strategy:**
- Redis caching with 5-minute (300 seconds) TTL for frequently accessed permissions
- Immediate cache invalidation on permission updates to maintain consistency
- Bulk cache operations for admin interfaces to reduce database load
- Target 90%+ cache hit ratio for active users to meet <10ms response requirement
- Cache warming strategy for high-traffic permission checks
- Graceful degradation to database queries when Redis is unavailable

**Database Optimization:**
- Composite indexes on (user_id, agent_name) for O(1) permission lookups
- JSONB GIN indexes for permission operation queries
- Connection pooling optimized for high-concurrency permission checks
- Query optimization ensures database fallback stays under 50ms

**API Performance Targets:**
- Permission checks add <10ms overhead to API calls (meets NFR11 requirement)
- Total permission validation overhead <5% of total API response time
- Bulk operations use database transactions for consistency
- WebSocket connections for real-time updates reduce polling load
- Cache failure monitoring with automatic alerting for degraded performance

### Redis Configuration & Failure Handling

**Redis Setup:**
```python
# Redis connection configuration
redis_config = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "password": os.getenv("REDIS_PASSWORD"),
    "socket_connect_timeout": 5,
    "socket_timeout": 5,
    "retry_on_timeout": True,
    "health_check_interval": 30,
    "max_connections": 100
}

# Cache key patterns
CACHE_PATTERNS = {
    "user_permissions": "permissions:{user_id}:{agent_name}",
    "user_all_permissions": "permissions:all:{user_id}",
    "bulk_operations": "permissions:bulk:{operation_id}"
}

# TTL configuration
CACHE_TTL = {
    "permission_check": 300,  # 5 minutes
    "bulk_operations": 60,    # 1 minute
    "admin_interface": 120    # 2 minutes
}
```

**Failure Scenarios & Recovery:**
- **Redis Unavailable**: Automatic fallback to database queries with <50ms target
- **Cache Miss**: Transparent database query with automatic cache population
- **Connection Timeout**: Circuit breaker pattern with exponential backoff
- **Memory Pressure**: LRU eviction with priority for active users
- **Network Issues**: Automatic retry with graceful degradation

**Monitoring Hooks:**
```python
async def monitor_cache_performance():
    """Monitor cache performance metrics"""
    hit_ratio = await calculate_hit_ratio()
    avg_response_time = await get_avg_response_time()
    
    if hit_ratio < 0.9:  # 90% threshold
        await alert_cache_efficiency_degraded()
    
    if avg_response_time > 10:  # 10ms threshold
        await alert_performance_degraded()
```
