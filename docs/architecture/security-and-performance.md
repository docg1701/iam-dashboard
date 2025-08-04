# Security and Performance

Comprehensive security measures and performance optimization strategies for enterprise-grade requirements:

### Security Requirements

#### Frontend Security
- **CSP Headers:** Content Security Policy preventing XSS attacks
- **XSS Prevention:** Input sanitization through Zod validation and React's built-in protection
- **Secure Storage:** JWT tokens in httpOnly cookies with secure flags

#### Backend Security
- **Input Validation:** Comprehensive Pydantic model validation for all endpoints
- **Rate Limiting:** API endpoints limited to 100 requests per minute per IP
- **CORS Policy:** Restricted to verified client domains only

#### Authentication Security
- **Token Storage:** JWT in httpOnly secure cookies with 15-minute expiration
- **Session Management:** Redis-based sessions with 24-hour expiration
- **Password Policy:** 8+ characters with complexity requirements, bcrypt hashing

#### Permission System Security
- **Permission Validation Boundaries:** All API endpoints protected with permission decorators
- **Fail-Safe Defaults:** Users have no permissions by default, explicit grants required
- **Role Hierarchy:** Sysadmin bypass, admin inherits specific permissions, user requires explicit grants
- **Permission Caching Security:** Redis cache invalidation on permission changes to prevent stale access
- **Audit Trail:** Complete logging of all permission changes with administrator attribution
- **JSONB Validation:** Database-level constraints ensure permission structure integrity
- **WebSocket Security:** Real-time permission updates authenticated via JWT tokens

### Performance Optimization

#### Frontend Performance
- **Bundle Size Target:** Maximum 500KB initial bundle
- **Loading Strategy:** React Server Components for static content
- **Caching Strategy:** TanStack Query for 5-minute API caching
- **Permission UI Performance:** Virtualized tables for large user lists, optimistic updates for permission changes
- **WebSocket Optimization:** Connection pooling and automatic reconnection for real-time updates

#### Backend Performance
- **Response Time Target:** Sub-200ms average API response time
- **Database Optimization:** Proper indexing and connection pooling
- **Caching Strategy:** Redis caching for frequently accessed data

#### Permission System Performance
- **Permission Caching:** Redis-based permission cache with 5-minute TTL
- **Database Indexing:** Composite indexes on (user_id, agent_name) for O(1) permission lookups
- **JSONB Optimization:** GIN indexes on permission JSONB fields for operation-specific queries
- **Bulk Operations:** Database transactions for consistent bulk permission updates
- **Query Optimization:** Permission checks add <10ms overhead to API calls
- **Cache Strategy:** Lazy loading of permissions with proactive cache warming for active users

### Security Implementation Details

```python
# Enhanced JWT security implementation
class SecureAuthService:
    def create_access_token(self, user_id: str, user_role: str) -> dict:
        """Create secure JWT token with session tracking"""
        session_id = secrets.token_hex(16)
        
        payload = {
            "sub": user_id,
            "role": user_role,
            "session_id": session_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "jti": secrets.token_hex(16)  # JWT ID for blacklisting
        }
        
        access_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # Store session in Redis
        session_data = {
            "user_id": user_id,
            "user_role": user_role,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.redis_client.setex(
            f"session:{session_id}",
            timedelta(hours=24),
            json.dumps(session_data)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 900
        }
```

### Permission System Security Implementation

```python
# Secure permission validation with caching
class SecurePermissionService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 10000  # Prevent cache overflow
    
    async def validate_permission_safely(
        self,
        user_id: UUID,
        agent_name: str,
        operation: str,
        request_context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """Secure permission validation with context logging"""
        try:
            # Input validation
            if not self._validate_inputs(user_id, agent_name, operation):
                return False, "Invalid permission parameters"
            
            # Rate limiting for permission checks
            if await self._check_rate_limit(user_id):
                return False, "Permission check rate limit exceeded"
            
            # Get user with active status check
            user = await self._get_active_user(user_id)
            if not user:
                return False, "User not found or inactive"
            
            # Sysadmin bypass with audit
            if user.role == "sysadmin":
                await self._log_permission_access(
                    user_id, agent_name, operation, "SYSADMIN_BYPASS", request_context
                )
                return True, None
            
            # Admin role inheritance
            if user.role == "admin" and agent_name in ["client_management", "reports_analysis"]:
                await self._log_permission_access(
                    user_id, agent_name, operation, "ADMIN_INHERIT", request_context
                )
                return True, None
            
            # Check cached permissions with integrity validation
            cached_result = await self._get_cached_permission(user_id, agent_name, operation)
            if cached_result is not None:
                await self._log_permission_access(
                    user_id, agent_name, operation, "CACHED_GRANT" if cached_result else "CACHED_DENY", 
                    request_context
                )
                return cached_result, None
            
            # Database permission check
            has_permission = await self._check_database_permission(user_id, agent_name, operation)
            
            # Cache the result
            await self._cache_permission_result(user_id, agent_name, operation, has_permission)
            
            # Log access attempt
            await self._log_permission_access(
                user_id, agent_name, operation, 
                "DB_GRANT" if has_permission else "DB_DENY", 
                request_context
            )
            
            return has_permission, None
            
        except Exception as e:
            # Security: Log but don't expose internal errors
            await self._log_security_event(
                "PERMISSION_CHECK_ERROR", 
                {"user_id": str(user_id), "agent": agent_name, "operation": operation, "error": str(e)}
            )
            return False, "Permission validation failed"
    
    def _validate_inputs(self, user_id: UUID, agent_name: str, operation: str) -> bool:
        """Validate permission check inputs"""
        valid_agents = {"client_management", "pdf_processing", "reports_analysis", "audio_recording"}
        valid_operations = {"create", "read", "update", "delete"}
        
        return (
            isinstance(user_id, UUID) and
            agent_name in valid_agents and
            operation in valid_operations
        )
    
    async def _check_rate_limit(self, user_id: UUID) -> bool:
        """Rate limit permission checks to prevent abuse"""
        key = f"permission_rate_limit:{user_id}"
        current = await self.redis.get(key)
        
        if current is None:
            await self.redis.setex(key, 60, 1)  # 1 check per minute window
            return False
        
        count = int(current)
        if count >= 100:  # Max 100 permission checks per minute
            return True
        
        await self.redis.incr(key)
        return False

# Secure API endpoint protection
def require_agent_permission_secure(agent_name: str, operation: str):
    """Enhanced security decorator with context logging"""
    def decorator(func):
        @wraps(func)
        async def wrapper(
            request: Request,
            *args, 
            current_user: User = Depends(get_current_user), 
            **kwargs
        ):
            # Gather request context for security logging
            request_context = {
                "endpoint": str(request.url),
                "method": request.method,
                "user_agent": request.headers.get("user-agent"),
                "ip_address": request.client.host,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Validate permission with context
            permission_service = get_permission_service()
            has_permission, error_msg = await permission_service.validate_permission_safely(
                current_user.user_id, agent_name, operation, request_context
            )
            
            if not has_permission:
                # Security event logging for denied access
                await log_security_event("ACCESS_DENIED", {
                    **request_context,
                    "user_id": str(current_user.user_id),
                    "user_role": current_user.role,
                    "required_permission": f"{agent_name}:{operation}",
                    "error": error_msg
                })
                
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Access denied",
                        "required_permission": f"{agent_name}:{operation}",
                        "message": "Insufficient permissions for this operation"
                    }
                )
            
            # Execute the protected function
            return await func(request, *args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

### Performance Monitoring

```typescript
// Performance monitoring implementation with permission system tracking
export class PerformanceMonitor {
    trackWebVitals() {
        // Largest Contentful Paint
        new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            this.recordMetric('LCP', lastEntry.startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });
    }
    
    trackAPICall(endpoint: string, startTime: number, endTime: number) {
        const duration = endTime - startTime;
        this.recordMetric(`API_${endpoint}`, duration);
        
        if (duration > 2000) {
            console.warn(`Slow API call detected: ${endpoint} took ${duration}ms`);
        }
    }
    
    trackPermissionCheck(agent: string, operation: string, startTime: number, endTime: number, cached: boolean) {
        const duration = endTime - startTime;
        const metricName = `PERMISSION_${agent}_${operation}_${cached ? 'CACHED' : 'DB'}`;
        this.recordMetric(metricName, duration);
        
        // Alert on slow permission checks
        if (duration > 50) {
            console.warn(`Slow permission check: ${agent}:${operation} took ${duration}ms`);
        }
        
        // Track cache hit rate
        this.recordMetric(`PERMISSION_CACHE_${cached ? 'HIT' : 'MISS'}`, 1);
    }
    
    trackPermissionMatrixLoad(userCount: number, startTime: number, endTime: number) {
        const duration = endTime - startTime;
        this.recordMetric('PERMISSION_MATRIX_LOAD', duration);
        this.recordMetric('PERMISSION_MATRIX_USERS', userCount);
        
        // Performance alert for large matrices
        if (userCount > 100 && duration > 5000) {
            console.warn(`Permission matrix slow for ${userCount} users: ${duration}ms`);
        }
    }
    
    trackWebSocketConnection(event: 'connect' | 'disconnect' | 'message', duration?: number) {
        this.recordMetric(`WEBSOCKET_${event.toUpperCase()}`, duration || 1);
        
        if (event === 'message' && duration && duration > 100) {
            console.warn(`Slow WebSocket message processing: ${duration}ms`);
        }
    }
}

// Backend performance monitoring
export class BackendPerformanceMonitor {
    trackPermissionValidation(
        user_id: str,
        agent_name: str,
        operation: str,
        start_time: float,
        end_time: float,
        cache_hit: bool,
        result: bool
    ):
        duration = (end_time - start_time) * 1000  # Convert to ms
        
        # Log performance metrics
        metrics = {
            'permission_check_duration': duration,
            'cache_hit': cache_hit,
            'result': result,
            'agent': agent_name,
            'operation': operation
        }
        
        # Alert on slow checks
        if duration > 10:  # More than 10ms is considered slow
            logger.warning(f"Slow permission check: {agent_name}:{operation} took {duration}ms")
        
        # Track cache performance
        cache_status = 'hit' if cache_hit else 'miss'
        metrics[f'cache_{cache_status}'] = 1
        
        return metrics
    
    trackBulkPermissionOperation(
        operation_type: str,
        user_count: int,
        start_time: float,
        end_time: float,
        success_count: int,
        error_count: int
    ):
        duration = (end_time - start_time) * 1000
        
        metrics = {
            'bulk_permission_duration': duration,
            'user_count': user_count,
            'success_rate': success_count / user_count if user_count > 0 else 0,
            'error_count': error_count,
            'operation_type': operation_type
        }
        
        # Performance thresholds
        if duration > 5000:  # More than 5 seconds
            logger.warning(f"Slow bulk operation: {operation_type} for {user_count} users took {duration}ms")
        
        return metrics
}
```

### Permission System Monitoring Metrics

**Key Performance Indicators:**
- **Permission Check Duration:** <10ms average, <50ms 95th percentile
- **Cache Hit Rate:** >80% for active users
- **Permission Matrix Load Time:** <2s for 100 users, <5s for 500 users
- **Bulk Operations:** <5s for 50 users, <15s for 200 users
- **WebSocket Message Latency:** <100ms for permission updates
- **Database Query Performance:** Composite index usage >95%

**Alerting Thresholds:**
- Permission check >50ms: Performance alert
- Cache hit rate <70%: Cache efficiency alert
- Bulk operation failure rate >5%: System health alert
- WebSocket disconnection rate >10%: Connection stability alert
- Permission audit log growth >1GB/day: Storage capacity alert
