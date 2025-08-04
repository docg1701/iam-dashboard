# Permission System Architecture

Comprehensive documentation for the enhanced agent-based permission system that transforms the rigid 3-role hierarchy into flexible, granular access control.

## Overview

The permission system addresses the critical limitation where 90% of employees (regular users) cannot perform basic client management functions. It implements a flexible, agent-based permission model while maintaining security boundaries and performance requirements.

### Core Principles

- **Fail-Safe Defaults**: Users have no permissions by default, explicit grants required
- **Role Inheritance**: Sysadmin bypass, admin inherits specific agents, users require explicit grants
- **Performance First**: Redis caching with <10ms permission check overhead
- **Audit Everything**: Complete permission change tracking for compliance
- **Real-time Updates**: WebSocket-based permission propagation

## Permission Model

### Permission Hierarchy

```
sysadmin (full system access)
├── admin (client_management + reports_analysis + user permission management)
└── user (explicit agent permissions only)
    ├── client_management: {create, read, update, delete}
    ├── pdf_processing: {create, read, update, delete}
    ├── reports_analysis: {create, read, update, delete}
    └── audio_recording: {create, read, update, delete}
```

### Permission Structure

```jsonb
{
  "client_management": {
    "create": true,
    "read": true,
    "update": true,
    "delete": false
  },
  "pdf_processing": {
    "create": false,
    "read": true,
    "update": false,
    "delete": false
  }
}
```

## Database Architecture

### Core Tables

#### user_agent_permissions
```sql
CREATE TABLE user_agent_permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    agent_name VARCHAR(50) NOT NULL CHECK (agent_name IN (
        'client_management', 'pdf_processing', 'reports_analysis', 'audio_recording'
    )),
    permissions JSONB NOT NULL DEFAULT '{}',
    created_by_user_id UUID NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id, agent_name)
);
```

#### permission_templates
```sql
CREATE TABLE permission_templates (
    template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB NOT NULL,
    is_system_template BOOLEAN NOT NULL DEFAULT false,
    created_by_user_id UUID NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

#### permission_audit_log
```sql
CREATE TABLE permission_audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    agent_name VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('GRANT', 'REVOKE', 'UPDATE', 'BULK_GRANT', 'BULK_REVOKE', 'TEMPLATE_APPLIED')),
    old_permissions JSONB,
    new_permissions JSONB,
    changed_by_user_id UUID NOT NULL REFERENCES users(user_id),
    change_reason TEXT,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### Performance Indexes

```sql
-- Critical performance indexes
CREATE INDEX idx_user_agent_permissions_composite ON user_agent_permissions(user_id, agent_name);
CREATE INDEX idx_user_agent_permissions_jsonb ON user_agent_permissions USING gin(permissions);
CREATE INDEX idx_permission_audit_user_id ON permission_audit_log(user_id);
CREATE INDEX idx_permission_audit_timestamp ON permission_audit_log(timestamp DESC);
```

## Backend Architecture

### Permission Service Layer

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
        """Check if user has permission with caching and role inheritance"""
        
        # Sysadmin bypass - always has access
        user = await self.get_user(user_id)
        if user.role == "sysadmin":
            return True
        
        # Admin role inheritance for specific agents
        if user.role == "admin" and agent_name in ["client_management", "reports_analysis"]:
            return True
        
        # Check Redis cache first
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
```

### API Protection Middleware

```python
def require_agent_permission(agent_name: str, operation: str):
    """Decorator for API endpoint permission validation"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
            # Sysadmin bypass
            if current_user.role == "sysadmin":
                return await func(*args, current_user=current_user, **kwargs)
            
            # Check specific permission
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
                        "user_role": current_user.role
                    }
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage example
@router.post("/clients", response_model=ClientResponse)
@require_agent_permission("client_management", "create")
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user)
):
    return await client_service.create_client(client_data, current_user.user_id)
```

### Real-time Updates via WebSocket

```python
class PermissionUpdateManager:
    """WebSocket manager for real-time permission updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
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
```

## Frontend Architecture

### UX Permission Flows

The permission system's integration with user experience follows a **progressive disclosure** pattern, where interface elements adapt dynamically based on user permissions while maintaining visual consistency and workflow continuity.

#### Core UX Permission Principles

- **Graceful Degradation**: UI elements gracefully hide or disable rather than showing error states
- **Contextual Feedback**: Users understand why certain actions are unavailable through subtle visual cues
- **Progressive Disclosure**: Advanced features appear only when users have appropriate permissions
- **Visual Hierarchy**: Permission-restricted elements maintain consistent visual weight without disrupting layout
- **Accessibility Compliance**: Screen readers and keyboard navigation respect permission boundaries

#### Permission-Aware Navigation Flow

```typescript
export const NavigationFlow: React.FC = () => {
  const { hasAgentPermission } = useUserPermissions()
  const { user } = useAuth()

  const navigationItems = useMemo(() => {
    const baseItems = [
      { href: '/dashboard', label: 'Dashboard', icon: Home, always: true }
    ]

    const conditionalItems = [
      {
        href: '/clients',
        label: 'Gerenciar Clientes',
        icon: Users,
        condition: hasAgentPermission('client_management', 'read'),
        badge: hasAgentPermission('client_management', 'create') ? 'create' : 'read-only'
      },
      {
        href: '/documents',
        label: 'Processar Documentos',
        icon: FileText,
        condition: hasAgentPermission('pdf_processing', 'read'),
        subItems: [
          {
            href: '/documents/upload',
            label: 'Upload PDFs',
            condition: hasAgentPermission('pdf_processing', 'create')
          },
          {
            href: '/documents/search',
            label: 'Buscar Documentos',
            condition: hasAgentPermission('pdf_processing', 'read')
          }
        ]
      },
      {
        href: '/reports',
        label: 'Relatórios',
        icon: BarChart,
        condition: hasAgentPermission('reports_analysis', 'read')
      },
      {
        href: '/audio',
        label: 'Gravações',
        icon: Mic,
        condition: hasAgentPermission('audio_recording', 'read')
      }
    ]

    return [
      ...baseItems,
      ...conditionalItems.filter(item => item.condition || item.always)
    ]
  }, [hasAgentPermission])

  return (
    <nav className="space-y-2">
      {navigationItems.map(item => (
        <NavigationItem key={item.href} {...item} />
      ))}
    </nav>
  )
}
```

#### Contextual Permission Indicators

```typescript
export const PermissionContextIndicator: React.FC<{
  agent: string
  operations: string[]
  className?: string
}> = ({ agent, operations, className }) => {
  const { hasAgentPermission } = useUserPermissions()
  
  const permissionLevel = operations.reduce((level, op) => {
    if (hasAgentPermission(agent, op)) {
      return op === 'create' || op === 'update' || op === 'delete' ? 'full' : 'read'
    }
    return level
  }, 'none' as 'none' | 'read' | 'full')

  const indicators = {
    none: { color: 'text-gray-400', icon: Lock, text: 'Sem acesso' },
    read: { color: 'text-blue-500', icon: Eye, text: 'Somente leitura' },
    full: { color: 'text-green-500', icon: Edit, text: 'Acesso completo' }
  }

  const indicator = indicators[permissionLevel]

  return (
    <div className={cn('flex items-center gap-2 text-sm', className)}>
      <indicator.icon className={cn('h-4 w-4', indicator.color)} />
      <span className={indicator.color}>{indicator.text}</span>
    </div>
  )
}
```

### User Interface Patterns

#### Permission-Aware Component States

The system implements consistent UI patterns across all permission-restricted components:

```typescript
// Button component with permission awareness
export const PermissionAwareButton: React.FC<{
  agent: string
  operation: string
  children: React.ReactNode
  variant?: 'default' | 'secondary' | 'destructive'
  onClick?: () => void
  disabled?: boolean
}> = ({ agent, operation, children, variant = 'default', onClick, disabled = false, ...props }) => {
  const { hasAgentPermission } = useUserPermissions()
  const hasPermission = hasAgentPermission(agent, operation)

  if (!hasPermission) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              disabled={true}
              className="opacity-50 cursor-not-allowed"
              {...props}
            >
              {children}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Você não tem permissão para {operation} em {agent}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return (
    <Button
      variant={variant}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {children}
    </Button>
  )
}
```

#### Form Field Permission Patterns

```typescript
// Form fields adapt based on user permissions
export const PermissionAwareFormField: React.FC<{
  agent: string
  operation: string
  field: string
  children: React.ReactNode
  readOnlyFallback?: React.ReactNode
}> = ({ agent, operation, field, children, readOnlyFallback }) => {
  const { hasAgentPermission } = useUserPermissions()
  const canEdit = hasAgentPermission(agent, operation)
  const canRead = hasAgentPermission(agent, 'read')

  if (!canRead) {
    return (
      <div className="space-y-2">
        <Label className="text-gray-400">Campo Restrito</Label>
        <div className="h-10 bg-gray-100 border border-gray-200 rounded-md flex items-center justify-center">
          <Lock className="h-4 w-4 text-gray-400" />
        </div>
      </div>
    )
  }

  if (!canEdit) {
    return readOnlyFallback || (
      <div className="space-y-2">
        <Label>{field}</Label>
        <div className="min-h-10 p-3 bg-gray-50 border border-gray-200 rounded-md">
          <span className="text-gray-600">Somente leitura</span>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
```

#### Table Action Permission Patterns

```typescript
export const PermissionAwareDataTable: React.FC<{
  data: any[]
  columns: ColumnDef<any>[]
  agent: string
}> = ({ data, columns, agent }) => {
  const { hasAgentPermission } = useUserPermissions()

  const enhancedColumns = useMemo(() => {
    const actionsColumn: ColumnDef<any> = {
      id: 'actions',
      header: 'Ações',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <PermissionGuard agent={agent} operation="read">
            <Button variant="ghost" size="sm">
              <Eye className="h-4 w-4" />
            </Button>
          </PermissionGuard>
          
          <PermissionGuard agent={agent} operation="update">
            <Button variant="ghost" size="sm">
              <Edit className="h-4 w-4" />
            </Button>
          </PermissionGuard>
          
          <PermissionGuard 
            agent={agent} 
            operation="delete"
            fallback={
              <Button variant="ghost" size="sm" disabled className="opacity-30">
                <Trash className="h-4 w-4" />
              </Button>
            }
          >
            <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-800">
              <Trash className="h-4 w-4" />
            </Button>
          </PermissionGuard>
        </div>
      )
    }

    return [...columns, actionsColumn]
  }, [columns, agent, hasAgentPermission])

  return <DataTable columns={enhancedColumns} data={data} />
}
```

### Cross-references to UX Architecture

This permission system integrates with the broader UX architecture documented in:

- **[Frontend Architecture](/docs/architecture/frontend-architecture.md)**: Component library integration with shadcn/ui theming system
- **[User Experience Design](/docs/ux/user-experience-design.md)**: Interaction patterns and accessibility compliance
- **[Responsive Design System](/docs/ux/responsive-design.md)**: Permission-aware mobile and tablet layouts
- **[Custom Branding Integration](/docs/ux/branding-system.md)**: Permission indicators within custom theme systems
- **[Accessibility Compliance](/docs/ux/accessibility.md)**: Screen reader support for permission boundaries

#### UX Architecture Integration Points

1. **Theme System Integration**: Permission indicators inherit from custom branding color schemes
2. **Responsive Behavior**: Permission UI adapts across breakpoints maintaining usability
3. **Accessibility Standards**: All permission boundaries are screen reader accessible
4. **Animation System**: Smooth transitions when permissions change in real-time
5. **Loading States**: Consistent loading patterns during permission validation

### Permission Hooks

```typescript
export const useUserPermissions = (userId?: string) => {
  const { user } = useAuth()
  const permissionStore = usePermissionStore()
  const targetUserId = userId || user?.user_id

  const { data: permissions, isLoading, error } = useQuery({
    queryKey: ['user-permissions', targetUserId],
    queryFn: () => permissionsAPI.getUserPermissions(targetUserId!),
    enabled: !!targetUserId && user?.role !== 'sysadmin',
    staleTime: 5 * 60 * 1000, // 5 minutes
    onSuccess: (data) => {
      permissionStore.setPermissions(data)
    }
  })

  const hasAgentPermission = useCallback((agent: string, operation: string): boolean => {
    // Sysadmin always has access
    if (user?.role === 'sysadmin') return true
    
    // Admin has access to client_management and reports_analysis
    if (user?.role === 'admin') {
      return ['client_management', 'reports_analysis'].includes(agent)
    }
    
    // Check specific permissions for regular users
    return permissions?.[agent]?.[operation] || false
  }, [user?.role, permissions])

  return { permissions, isLoading, error, hasAgentPermission }
}
```

### Permission Guards

```typescript
// Permission-based conditional rendering
export const PermissionGuard: React.FC<{
  agent: string
  operation: string
  children: React.ReactNode
  fallback?: React.ReactNode
}> = ({ agent, operation, children, fallback = null }) => {
  const { hasAgentPermission } = useUserPermissions()
  
  if (!hasAgentPermission(agent, operation)) {
    return <>{fallback}</>
  }
  
  return <>{children}</>
}

// Usage in components
<PermissionGuard agent="client_management" operation="create">
  <Button onClick={() => createClient()}>
    New Client
  </Button>
</PermissionGuard>
```

### Permission Component UX

The permission system includes specialized UX components designed to enhance the administrative experience while maintaining user clarity about access restrictions.

#### Permission Status Dashboard

```typescript
export const PermissionStatusDashboard: React.FC<{ userId: string }> = ({ userId }) => {
  const { data: permissions } = useUserPermissions(userId)
  const { data: user } = useUser(userId)

  const permissionSummary = useMemo(() => {
    if (!permissions) return { total: 0, granted: 0, restricted: 0 }
    
    let granted = 0
    let total = 0
    
    Object.entries(permissions).forEach(([agent, ops]) => {
      Object.entries(ops).forEach(([operation, hasPermission]) => {
        total++
        if (hasPermission) granted++
      })
    })
    
    return { total, granted, restricted: total - granted }
  }, [permissions])

  return (
    <Card className="p-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="h-5 w-5" />
          Status de Permissões - {user?.full_name}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{permissionSummary.granted}</div>
            <div className="text-sm text-gray-600">Permissões Ativas</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{permissionSummary.restricted}</div>
            <div className="text-sm text-gray-600">Restrições</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{permissionSummary.total}</div>
            <div className="text-sm text-gray-600">Total</div>
          </div>
        </div>
        
        <div className="space-y-3">
          {Object.entries(permissions || {}).map(([agent, operations]) => (
            <PermissionAgentSummary
              key={agent}
              agent={agent}
              operations={operations}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

#### Interactive Permission Editor

```typescript
export const InteractivePermissionEditor: React.FC<{
  userId: string
  onPermissionChange: (agent: string, operation: string, value: boolean) => void
}> = ({ userId, onPermissionChange }) => {
  const { data: permissions, isLoading } = useUserPermissions(userId)
  const [pendingChanges, setPendingChanges] = useState<Record<string, Record<string, boolean>>>({})

  const handleToggle = (agent: string, operation: string, currentValue: boolean) => {
    const newValue = !currentValue
    setPendingChanges(prev => ({
      ...prev,
      [agent]: { ...prev[agent], [operation]: newValue }
    }))
    onPermissionChange(agent, operation, newValue)
  }

  if (isLoading) {
    return <PermissionEditorSkeleton />
  }

  return (
    <div className="space-y-6">
      {AGENTS.map(agent => (
        <Card key={agent.name} className="overflow-hidden">
          <CardHeader className="bg-gray-50">
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <agent.icon className="h-5 w-5" />
                <span>{agent.display_name}</span>
              </div>
              <PermissionContextIndicator
                agent={agent.name}
                operations={['create', 'read', 'update', 'delete']}
              />
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="grid grid-cols-4 divide-x">
              {['create', 'read', 'update', 'delete'].map(operation => {
                const currentValue = permissions?.[agent.name]?.[operation] || false
                const hasPendingChange = pendingChanges[agent.name]?.[operation] !== undefined
                const displayValue = hasPendingChange 
                  ? pendingChanges[agent.name][operation]
                  : currentValue

                return (
                  <div key={operation} className="p-4 text-center">
                    <Label className="text-sm font-medium capitalize mb-2 block">
                      {operation}
                    </Label>
                    <Switch
                      checked={displayValue}
                      onCheckedChange={() => handleToggle(agent.name, operation, displayValue)}
                      className={cn(
                        hasPendingChange && "ring-2 ring-blue-500 ring-offset-2"
                      )}
                    />
                    {hasPendingChange && (
                      <div className="text-xs text-blue-600 mt-1">
                        Pendente
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
```

#### Permission Change Impact Analysis

```typescript
export const PermissionImpactAnalysis: React.FC<{
  userId: string
  proposedChanges: Record<string, Record<string, boolean>>
}> = ({ userId, proposedChanges }) => {
  const { data: currentPermissions } = useUserPermissions(userId)
  const { data: user } = useUser(userId)

  const impactAnalysis = useMemo(() => {
    const changes = []
    
    Object.entries(proposedChanges).forEach(([agent, operations]) => {
      Object.entries(operations).forEach(([operation, newValue]) => {
        const currentValue = currentPermissions?.[agent]?.[operation] || false
        
        if (currentValue !== newValue) {
          changes.push({
            agent,
            operation,
            from: currentValue,
            to: newValue,
            impact: getOperationImpact(agent, operation, newValue)
          })
        }
      })
    })
    
    return changes
  }, [proposedChanges, currentPermissions])

  const securityRiskLevel = impactAnalysis.reduce((risk, change) => {
    if (change.to && ['delete', 'update'].includes(change.operation)) {
      return Math.max(risk, change.operation === 'delete' ? 3 : 2)
    }
    return risk
  }, 1)

  return (
    <Card className="border-l-4 border-l-blue-500">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          Análise de Impacto das Mudanças
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium">Nível de Risco:</span>
            <Badge variant={securityRiskLevel > 2 ? 'destructive' : securityRiskLevel > 1 ? 'default' : 'secondary'}>
              {securityRiskLevel > 2 ? 'Alto' : securityRiskLevel > 1 ? 'Médio' : 'Baixo'}
            </Badge>
          </div>
        </div>

        <div className="space-y-3">
          {impactAnalysis.map((change, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                {change.to ? (
                  <Plus className="h-4 w-4 text-green-600" />
                ) : (
                  <Minus className="h-4 w-4 text-red-600" />
                )}
                <div>
                  <div className="font-medium">
                    {AGENTS.find(a => a.name === change.agent)?.display_name} - {change.operation}
                  </div>
                  <div className="text-sm text-gray-600">{change.impact}</div>
                </div>
              </div>
              <div className="text-sm">
                <span className={change.from ? 'text-green-600' : 'text-red-600'}>
                  {change.from ? 'Ativo' : 'Inativo'}
                </span>
                <ArrowRight className="h-4 w-4 mx-2 inline" />
                <span className={change.to ? 'text-green-600' : 'text-red-600'}>
                  {change.to ? 'Ativo' : 'Inativo'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

### Real-time Permission Updates

The system implements sophisticated UX patterns for handling real-time permission changes, ensuring users understand when their access levels change without disrupting their current workflow.

#### Live Permission Update Notification System

```typescript
export const LivePermissionUpdates: React.FC = () => {
  const { user } = useAuth()
  const [permissionUpdates, setPermissionUpdates] = useState<PermissionUpdate[]>([])
  const { toast } = useToast()

  useEffect(() => {
    if (!user?.user_id) return

    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/permissions/${user.user_id}`)
    
    ws.onmessage = (event) => {
      const update: PermissionUpdate = JSON.parse(event.data)
      
      setPermissionUpdates(prev => [update, ...prev.slice(0, 9)]) // Keep latest 10
      
      // Show contextual notification based on update type
      if (update.type === 'permission_granted') {
        toast({
          title: "Nova Permissão Concedida",
          description: `Você agora pode ${update.operation} em ${update.agent_display_name}`,
          action: (
            <ToastAction altText="Ver detalhes" onClick={() => showPermissionDetails(update)}>
              Ver Detalhes
            </ToastAction>
          ),
        })
      } else if (update.type === 'permission_revoked') {
        toast({
          title: "Permissão Removida",
          description: `Acesso para ${update.operation} em ${update.agent_display_name} foi removido`,
          variant: "destructive",
        })
      }
    }

    return () => ws.close()
  }, [user?.user_id, toast])

  return (
    <PermissionUpdatesList updates={permissionUpdates} />
  )
}
```

#### Contextual Permission Change Handling

```typescript
export const useContextualPermissionHandling = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { toast } = useToast()

  const handlePermissionChange = useCallback((update: PermissionUpdate) => {
    // Invalidate relevant queries
    queryClient.invalidateQueries(['user-permissions', update.user_id])
    
    // Handle navigation if user loses access to current page
    if (update.type === 'permission_revoked') {
      const currentPath = window.location.pathname
      const affectedPaths = getAffectedPaths(update.agent, update.operation)
      
      if (affectedPaths.some(path => currentPath.startsWith(path))) {
        toast({
          title: "Redirecionamento Necessário",
          description: "Você será redirecionado pois não tem mais acesso a esta página",
          action: (
            <ToastAction altText="Entendi" onClick={() => navigate('/dashboard')}>
              Entendi
            </ToastAction>
          ),
        })
        
        // Redirect after 3 seconds to allow user to save work
        setTimeout(() => navigate('/dashboard'), 3000)
      }
    }

    // Update UI state for permission-aware components
    broadcastPermissionUpdate(update)
  }, [queryClient, navigate, toast])

  return { handlePermissionChange }
}
```

#### Permission-Aware Route Protection

```typescript
export const PermissionRoute: React.FC<{
  agent: string
  operation: string
  children: React.ReactNode
  fallback?: React.ReactNode
}> = ({ agent, operation, children, fallback }) => {
  const { hasAgentPermission, isLoading } = useUserPermissions()
  const [permissionLost, setPermissionLost] = useState(false)

  // Listen for real-time permission changes
  useEffect(() => {
    const handlePermissionUpdate = (update: PermissionUpdate) => {
      if (update.agent === agent && update.operation === operation && !update.value) {
        setPermissionLost(true)
      }
    }

    window.addEventListener('permission-update', handlePermissionUpdate)
    return () => window.removeEventListener('permission-update', handlePermissionUpdate)
  }, [agent, operation])

  if (isLoading) {
    return <PermissionLoadingSkeleton />
  }

  if (!hasAgentPermission(agent, operation) || permissionLost) {
    return fallback || (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <Lock className="h-16 w-16 text-gray-400" />
        <h2 className="text-xl font-semibold text-gray-600">Acesso Restrito</h2>
        <p className="text-gray-500 text-center max-w-md">
          Você não tem permissão para acessar esta área. Entre em contato com um administrador 
          se precisar de acesso.
        </p>
        <Button variant="outline" onClick={() => window.history.back()}>
          Voltar
        </Button>
      </div>
    )
  }

  return <>{children}</>
}
```

#### Real-time Permission Status Indicator

```typescript
export const RealTimePermissionIndicator: React.FC<{
  agent: string
  operation: string
  className?: string
}> = ({ agent, operation, className }) => {
  const { hasAgentPermission } = useUserPermissions()
  const [status, setStatus] = useState<'checking' | 'granted' | 'denied'>('checking')
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  useEffect(() => {
    const checkPermission = async () => {
      setStatus('checking')
      const hasPermission = hasAgentPermission(agent, operation)
      setStatus(hasPermission ? 'granted' : 'denied')
      setLastUpdate(new Date())
    }

    checkPermission()

    // Listen for permission updates
    const handleUpdate = (update: PermissionUpdate) => {
      if (update.agent === agent && update.operation === operation) {
        setStatus(update.value ? 'granted' : 'denied')
        setLastUpdate(new Date())
      }
    }

    window.addEventListener('permission-update', handleUpdate)
    return () => window.removeEventListener('permission-update', handleUpdate)
  }, [agent, operation, hasAgentPermission])

  const statusConfig = {
    checking: { color: 'text-yellow-500', icon: Clock, text: 'Verificando...' },
    granted: { color: 'text-green-500', icon: CheckCircle, text: 'Permitido' },
    denied: { color: 'text-red-500', icon: XCircle, text: 'Negado' }
  }

  const config = statusConfig[status]

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn('flex items-center gap-2', className)}>
            <config.icon className={cn('h-4 w-4', config.color)} />
            <span className={cn('text-sm', config.color)}>{config.text}</span>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <div className="space-y-1">
            <p>{agent} - {operation}</p>
            {lastUpdate && (
              <p className="text-xs text-gray-500">
                Última atualização: {lastUpdate.toLocaleTimeString()}
              </p>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
```

### Real-time Permission Updates

```typescript
export const usePermissionUpdates = () => {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const permissionStore = usePermissionStore()

  useEffect(() => {
    if (!user?.user_id) return

    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/permissions`)
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'permission_update') {
        // Invalidate permission queries for updated user
        queryClient.invalidateQueries(['user-permissions', data.user_id])
        
        // Update local permission store
        if (data.user_id === user.user_id) {
          permissionStore.setPermissions(data.permissions)
          toast.info('Suas permissões foram atualizadas')
        }
      }
    }

    return () => ws.close()
  }, [user?.user_id, queryClient, permissionStore])
}
```

## Administrative Interface

### Permission Matrix Component

```typescript
export const PermissionMatrix: React.FC = () => {
  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: usersAPI.getUsers
  })

  const { data: permissionMatrix } = useQuery({
    queryKey: ['permission-matrix'],
    queryFn: permissionsAPI.getPermissionMatrix
  })

  const updatePermission = useMutation({
    mutationFn: ({ userId, agent, operation, value }: {
      userId: string
      agent: string
      operation: string
      value: boolean
    }) => permissionsAPI.updateSinglePermission(userId, agent, operation, value),
    onSuccess: () => {
      queryClient.invalidateQueries(['permission-matrix'])
    }
  })

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th>Usuário</th>
            {AGENTS.map(agent => (
              <th key={agent.name}>{agent.display_name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {users?.map(user => (
            <tr key={user.user_id}>
              <td>{user.full_name}</td>
              {AGENTS.map(agent => (
                <td key={agent.name}>
                  <PermissionCell
                    user={user}
                    agent={agent.name}
                    permissions={permissionMatrix?.[user.user_id]?.[agent.name] || {}}
                    onToggle={updatePermission.mutate}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

### Bulk Permission Operations

```typescript
export const BulkPermissionDialog: React.FC = () => {
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])
  const [permissionChanges, setPermissionChanges] = useState<UserPermissions>({})

  const bulkUpdate = useMutation({
    mutationFn: (data: BulkPermissionRequest) => 
      permissionsAPI.bulkUpdatePermissions(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['permission-matrix'])
      toast.success('Permissões atualizadas em lote com sucesso')
    }
  })

  const handleBulkUpdate = () => {
    bulkUpdate.mutate({
      user_ids: selectedUsers,
      permissions: permissionChanges
    })
  }

  return (
    <Dialog>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>Atualização em Lote de Permissões</DialogTitle>
        </DialogHeader>
        
        {/* User selection interface */}
        <UserSelectionGrid 
          selectedUsers={selectedUsers}
          onSelectionChange={setSelectedUsers}
        />
        
        {/* Permission modification interface */}
        <PermissionModificationPanel
          permissions={permissionChanges}
          onChange={setPermissionChanges}
        />
        
        <DialogFooter>
          <Button 
            onClick={handleBulkUpdate}
            disabled={selectedUsers.length === 0 || bulkUpdate.isLoading}
          >
            {bulkUpdate.isLoading ? 'Processando...' : `Atualizar ${selectedUsers.length} usuários`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

## Permission Templates System

The permission template system addresses the critical administrative challenge of managing consistent permissions across similar roles. It reduces permission configuration time from hours to minutes and ensures standardized access patterns throughout the organization.

### Business Benefits

- **Administrative Efficiency**: Reduce new user onboarding from 30 minutes to 2 minutes through template application
- **Consistent Access Patterns**: Eliminate permission inconsistencies across similar job roles
- **Scalable Permission Management**: Support organizational growth without proportional administrative overhead
- **Reduced Configuration Errors**: Pre-validated permission combinations prevent security gaps and access issues
- **Organizational Standardization**: Enable consistent role definitions across multiple client implementations

### Template Definition

```typescript
interface PermissionTemplate {
  template_id: string
  template_name: string
  description: string
  permissions: UserPermissions
  is_system_template: boolean
  template_category: 'system' | 'custom' | 'organizational'
  usage_count: number
  last_applied: string
  created_by_user_id: string
  created_at: string
  updated_at: string
}

// System templates aligned with PRD FR18 requirements
const SYSTEM_TEMPLATES: PermissionTemplate[] = [
  {
    template_name: "Client Specialist",
    description: "Full client management access for customer service representatives",
    template_category: "system",
    permissions: {
      client_management: {
        create: true,
        read: true,
        update: true,
        delete: false  // Security boundary: no client deletion
      }
    },
    business_use_case: "Customer service representatives who handle daily client interactions"
  },
  {
    template_name: "Report Analyst", 
    description: "Analysis and reporting access with read-only client data",
    template_category: "system",
    permissions: {
      client_management: {
        create: false,
        read: true,
        update: false,
        delete: false
      },
      reports_analysis: {
        create: true,
        read: true,
        update: true,
        delete: false
      }
    },
    business_use_case: "Business analysts who create reports but don't modify client data"
  },
  {
    template_name: "Document Processor",
    description: "PDF processing and client data reading for document workflows",
    template_category: "system",
    permissions: {
      client_management: {
        create: false,
        read: true,
        update: false,
        delete: false
      },
      pdf_processing: {
        create: true,
        read: true,
        update: true,
        delete: true  // Document management requires deletion capability
      }
    },
    business_use_case: "Operations staff who process and manage client documents"
  },
  {
    template_name: "Audio Specialist",
    description: "Audio recording and transcription with client access",
    template_category: "system",
    permissions: {
      client_management: {
        create: false,
        read: true,
        update: false,
        delete: false
      },
      audio_recording: {
        create: true,
        read: true,
        update: true,
        delete: true
      }
    },
    business_use_case: "Support specialists who record and analyze client consultations"
  }
]
```

### Template Application

```python
async def apply_permission_template(
    user_id: UUID,
    template_id: UUID,
    applied_by_user_id: UUID
):
    """Apply permission template to user"""
    template = await get_permission_template(template_id)
    
    for agent_name, agent_permissions in template.permissions.items():
        await permission_service.assign_agent_permissions(
            user_id=user_id,
            agent_name=agent_name,
            permissions=agent_permissions,
            assigned_by=applied_by_user_id
        )
        
        # Log template application
        await log_permission_change(
            user_id, 
            agent_name, 
            'TEMPLATE_APPLIED',
            None,
            agent_permissions,
            applied_by_user_id,
            f'Applied template: {template.template_name}'
        )
```

## Performance Optimization

### Caching Strategy

- **Permission Cache TTL**: 5 minutes (300 seconds) for active users to balance performance and consistency
- **Cache Invalidation**: Immediate invalidation on permission changes to maintain data accuracy
- **Cache Warming**: Proactive loading for admin interface and bulk operations
- **Cache Size Limits**: Maximum 10,000 cached permission sets with LRU eviction
- **Performance Targets**: 90%+ cache hit ratio for active users, <10ms permission check response time
- **Failure Handling**: Graceful degradation to database queries with <50ms fallback response time
- **Monitoring**: Real-time cache hit ratio monitoring with alerting for performance degradation

### Database Optimization

- **Composite Indexes**: (user_id, agent_name) for O(1) lookups
- **JSONB Indexes**: GIN indexes for operation-specific queries
- **Connection Pooling**: Optimized for high-concurrency permission checks
- **Query Optimization**: Permission checks add <10ms overhead

### Frontend Optimization

- **Optimistic Updates**: Immediate UI feedback with server validation
- **Virtualized Tables**: Handle 500+ users in permission matrix
- **Debounced Updates**: Batch permission changes to reduce API calls
- **Lazy Loading**: Load permission dialogs on demand

## Security Considerations

### Security Boundaries

- **API Protection**: All endpoints protected by default with explicit decorators
- **Input Validation**: Comprehensive validation of permission structures
- **Rate Limiting**: Prevent abuse of permission check endpoints
- **Audit Logging**: Complete trail of all permission changes

### Security Implementation

```python
# Secure permission validation
async def validate_permission_safely(
    user_id: UUID,
    agent_name: str,
    operation: str,
    request_context: Optional[Dict] = None
) -> Tuple[bool, Optional[str]]:
    """Secure permission validation with context logging"""
    
    # Input validation
    if not _validate_inputs(user_id, agent_name, operation):
        return False, "Invalid permission parameters"
    
    # Rate limiting
    if await _check_rate_limit(user_id):
        return False, "Permission check rate limit exceeded"
    
    # Active user check
    user = await _get_active_user(user_id)
    if not user:
        return False, "User not found or inactive"
    
    # Permission logic with audit logging
    # ... implementation details
```

## Migration Strategy

### Database Migration

```python
# Alembic migration for permission system
def upgrade():
    # Create user_agent_permissions table
    op.create_table('user_agent_permissions', ...)
    
    # Create permission_templates table
    op.create_table('permission_templates', ...)
    
    # Create audit table
    op.create_table('permission_audit_log', ...)
    
    # Create indexes
    op.create_index('idx_user_agent_permissions_composite', ...)
    
    # Insert system templates
    op.execute("""
        INSERT INTO permission_templates (template_name, description, permissions, is_system_template, created_by_user_id)
        VALUES ('Client Specialist', 'Full client management access', '{"client_management": {"create": true, "read": true, "update": true, "delete": false}}', true, 
                (SELECT user_id FROM users WHERE role = 'sysadmin' LIMIT 1))
    """)
```

### Data Migration

- **Existing Users**: Maintain current role-based access during transition
- **Permission Assignment**: Bulk assign permissions based on current roles
- **Gradual Rollout**: Enable new permission system per agent progressively
- **Rollback Plan**: Database rollback scripts for emergency reversion

## Testing Strategy

### Unit Tests

```python
# Permission service tests
def test_has_agent_permission_sysadmin_bypass():
    """Test that sysadmin always has access"""
    assert permission_service.has_agent_permission(
        sysadmin_user.user_id, "client_management", "delete"
    ) == True

def test_has_agent_permission_user_explicit_grant():
    """Test explicit permission grants for users"""
    # Grant permission
    permission_service.assign_agent_permissions(
        user.user_id, "client_management", {"create": True, "read": True}
    )
    
    assert permission_service.has_agent_permission(
        user.user_id, "client_management", "create"
    ) == True
    
    assert permission_service.has_agent_permission(
        user.user_id, "client_management", "delete"
    ) == False
```

### Integration Tests

```python
# API endpoint protection tests
def test_client_creation_requires_permission():
    """Test that client creation requires proper permissions"""
    # User without permission
    response = client.post("/clients", json=client_data, headers=user_headers)
    assert response.status_code == 403
    
    # User with permission
    permission_service.assign_agent_permissions(
        user.user_id, "client_management", {"create": True}
    )
    response = client.post("/clients", json=client_data, headers=user_headers)
    assert response.status_code == 201
```

### Frontend Tests

```typescript
// Permission guard tests
describe('PermissionGuard', () => {
  it('should render children when user has permission', () => {
    mockUseUserPermissions.mockReturnValue({
      hasAgentPermission: () => true
    })
    
    render(
      <PermissionGuard agent="client_management" operation="create">
        <button>Create Client</button>
      </PermissionGuard>
    )
    
    expect(screen.getByText('Create Client')).toBeInTheDocument()
  })
  
  it('should render fallback when user lacks permission', () => {
    mockUseUserPermissions.mockReturnValue({
      hasAgentPermission: () => false
    })
    
    render(
      <PermissionGuard 
        agent="client_management" 
        operation="create"
        fallback={<div>Access Denied</div>}
      >
        <button>Create Client</button>
      </PermissionGuard>
    )
    
    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.queryByText('Create Client')).not.toBeInTheDocument()
  })
})
```

## Monitoring and Observability

### Key Metrics

- **Permission Check Duration**: <10ms average (aligns with NFR11), <50ms 95th percentile
- **Cache Hit Rate**: >90% for active users (aligns with performance assumptions)
- **Permission Matrix Load Time**: <2s for 100 users
- **Bulk Operations**: <5s for 50 users
- **WebSocket Message Latency**: <100ms
- **Cache Performance**: <5ms Redis response time average
- **Database Fallback**: <50ms when cache unavailable

### Alerting Thresholds

- Permission check >10ms: Performance degradation alert (immediate attention)
- Permission check >50ms: Critical performance alert (escalation required)
- Cache hit rate <90%: Cache efficiency warning
- Cache hit rate <70%: Cache efficiency critical alert
- Bulk operation failure rate >5%: System health alert
- WebSocket disconnection rate >10%: Connection stability alert
- Redis unavailable >30 seconds: Cache infrastructure critical alert

### Audit Reporting

```sql
-- Permission usage analytics
SELECT 
    agent_name,
    operation,
    COUNT(*) as check_count,
    AVG(duration_ms) as avg_duration
FROM permission_check_log 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY agent_name, operation
ORDER BY check_count DESC;

-- Permission change frequency
SELECT 
    user_id,
    agent_name,
    COUNT(*) as change_count,
    MAX(timestamp) as last_change
FROM permission_audit_log
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY user_id, agent_name
ORDER BY change_count DESC;
```

## Future Enhancements

### Planned Features

1. **Time-based Permissions**: Temporary access grants with automatic expiration
2. **Conditional Permissions**: Context-aware permissions based on data ownership
3. **Permission Inheritance**: Team-based permission inheritance models
4. **Advanced Analytics**: Machine learning for permission usage optimization
5. **External Integration**: LDAP/Active Directory synchronization

### Scalability Considerations

- **Horizontal Scaling**: Redis cluster for permission caching
- **Database Sharding**: Partition permission data by client/tenant
- **CDN Integration**: Cache permission matrices at edge locations
- **Microservice Split**: Dedicated permission service for multi-tenant deployments

This comprehensive permission system architecture transforms the IAM Dashboard from a rigid role-based system into a flexible, performant, and secure platform that enables 90% of employees to access the tools they need while maintaining enterprise-grade security and auditability.