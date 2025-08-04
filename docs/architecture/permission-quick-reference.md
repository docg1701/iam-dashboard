# Permission System Quick Reference

**Developer implementation guide for the enhanced agent-based permission system**

> ๐ **Quick Links**: [Permission Architecture](./permissions-architecture.md) | [Integration Guide](./permission-integration-guide.md) | [Backend Architecture](./backend-architecture.md#permission-service-layer) | [Frontend Architecture](./frontend-architecture.md#permission-hooks)

---

## ๐ฏ Core Concepts

### Permission Model
```typescript
interface AgentPermissions {
  create: boolean
  read: boolean  
  update: boolean
  delete: boolean
}

interface UserPermissions {
  client_management?: AgentPermissions
  pdf_processing?: AgentPermissions
  reports_analysis?: AgentPermissions
  audio_recording?: AgentPermissions
}
```

### Role Hierarchy
```
sysadmin โ All permissions (bypass)
โ
admin โ client_management + reports_analysis + user management
โ
user โ Explicit agent permissions only
```

---

## ๐ก Frontend Implementation

### 1. Permission Hooks

```typescript
// Check permissions in components
const { hasAgentPermission, isLoading } = useUserPermissions()

// Usage
const canCreateClient = hasAgentPermission('client_management', 'create')
const canDeleteClient = hasAgentPermission('client_management', 'delete')
```

### 2. Permission Guards

```typescript
// Conditional rendering
<PermissionGuard agent="client_management" operation="create">
  <Button onClick={() => createClient()}>
    New Client
  </Button>
</PermissionGuard>

// With fallback
<PermissionGuard 
  agent="client_management" 
  operation="create"
  fallback={<div>Access Denied</div>}
>
  <CreateClientForm />
</PermissionGuard>
```

### 3. Route Protection

```typescript
// Page-level protection
export default function ClientsPage() {
  const { hasAgentPermission } = useUserPermissions()
  
  if (!hasAgentPermission('client_management', 'read')) {
    return <AccessDeniedPage />
  }
  
  return <ClientManagement />
}
```

### 4. Real-time Updates

```typescript
// Automatic permission sync
export function App() {
  usePermissionUpdates() // Handles WebSocket updates
  
  return <YourApp />
}
```

---

## ๐  Backend Implementation

### 1. API Protection Decorator

```python
# Protect endpoints with permissions
@router.post("/clients")
@require_agent_permission("client_management", "create")
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user)
):
    return await client_service.create_client(client_data, current_user.user_id)
```

### 2. Service Layer Validation

```python
class ClientService:
    async def update_client(self, client_id: UUID, updates: ClientUpdate, user_id: UUID):
        # Check permission in service layer
        if not await permission_service.has_agent_permission(
            user_id, "client_management", "update"
        ):
            raise PermissionDeniedError("Cannot update clients")
        
        # Business logic continues...
```

### 3. Permission Checks

```python
# Check permissions programmatically
permission_service = get_permission_service()

has_permission = await permission_service.has_agent_permission(
    user_id=current_user.user_id,
    agent_name="client_management", 
    operation="create"
)

if not has_permission:
    raise HTTPException(status_code=403, detail="Insufficient permissions")
```

---

## ๐ฏ Database Operations

### 1. Grant Permissions

```python
# Grant single permission
await permission_service.assign_agent_permissions(
    user_id=user_id,
    agent_name="client_management",
    permissions={
        "create": True,
        "read": True,
        "update": True,
        "delete": False
    },
    assigned_by=admin_user_id
)
```

### 2. Bulk Operations

```python
# Bulk grant permissions
await permission_service.bulk_assign_permissions(
    user_ids=[user1_id, user2_id, user3_id],
    permissions={
        "client_management": {
            "create": True,
            "read": True,
            "update": False,
            "delete": False
        }
    },
    assigned_by=admin_user_id
)
```

### 3. Permission Templates

```python
# Apply template to user
await permission_service.apply_permission_template(
    user_id=user_id,
    template_id=template_id,
    applied_by=admin_user_id
)
```

---

## ๐ Common Patterns

### 1. Check Multiple Permissions

```typescript
// Frontend
const permissions = ['create', 'update', 'delete']
const hasAnyPermission = permissions.some(op => 
  hasAgentPermission('client_management', op)
)
```

```python
# Backend
async def has_any_client_permission(user_id: UUID) -> bool:
    operations = ['create', 'read', 'update', 'delete']
    for operation in operations:
        if await permission_service.has_agent_permission(user_id, "client_management", operation):
            return True
    return False
```

### 2. Permission-based UI States

```typescript
const { hasAgentPermission } = useUserPermissions()

const tableActions = useMemo(() => {
  const actions = []
  
  if (hasAgentPermission('client_management', 'update')) {
    actions.push({ label: 'Edit', onClick: editClient })
  }
  
  if (hasAgentPermission('client_management', 'delete')) {
    actions.push({ label: 'Delete', onClick: deleteClient })
  }
  
  return actions
}, [hasAgentPermission])
```

### 3. Conditional Form Fields

```typescript
<Form>
  <Input name="name" required />
  <Input name="email" required />
  
  <PermissionGuard agent="client_management" operation="update">
    <Select name="status">
      <option value="active">Active</option>
      <option value="inactive">Inactive</option>
    </Select>
  </PermissionGuard>
  
  <PermissionGuard agent="client_management" operation="delete">
    <Button variant="destructive" onClick={deleteClient}>
      Delete Client
    </Button>
  </PermissionGuard>
</Form>
```

---

## ๐ Permission Debugging

### 1. Debug User Permissions

```typescript
// Frontend debugging
const { permissions, user } = useUserPermissions()

console.log('User role:', user?.role)
console.log('User permissions:', permissions)
console.log('Has client create:', hasAgentPermission('client_management', 'create'))
```

```python
# Backend debugging
async def debug_user_permissions(user_id: UUID):
    permissions = await permission_service.get_user_permissions(user_id)
    print(f"User permissions: {permissions}")
    
    for agent_name in ["client_management", "pdf_processing", "reports_analysis", "audio_recording"]:
        for operation in ["create", "read", "update", "delete"]:
            has_perm = await permission_service.has_agent_permission(user_id, agent_name, operation)
            print(f"{agent_name}.{operation}: {has_perm}")
```

### 2. Check Permission Cache

```python
# Check Redis cache state
cache_key = f"permissions:{user_id}:client_management"
cached_permissions = await redis.get(cache_key)
print(f"Cached permissions: {cached_permissions}")
```

---

## โ ๏ธ Common Pitfalls

### 1. **Don't Skip Permission Checks**
```python
# โ Wrong - missing permission check
@router.delete("/clients/{client_id}")
async def delete_client(client_id: UUID):
    return await client_service.delete_client(client_id)

# โ Correct - with permission check
@router.delete("/clients/{client_id}")
@require_agent_permission("client_management", "delete")
async def delete_client(client_id: UUID):
    return await client_service.delete_client(client_id)
```

### 2. **Don't Hardcode Role Checks**
```typescript
// โ Wrong - hardcoded role check
if (user.role === 'admin') {
  return <CreateButton />
}

// โ Correct - permission-based check
<PermissionGuard agent="client_management" operation="create">
  <CreateButton />
</PermissionGuard>
```

### 3. **Don't Forget Cache Invalidation**
```python
# โ Wrong - permission granted but cache not invalidated
await db.execute("UPDATE user_agent_permissions SET permissions = ?", new_permissions)

# โ Correct - cache invalidated after permission change
await permission_service.assign_agent_permissions(user_id, agent_name, permissions)
# Cache is automatically invalidated in the service
```

---

## ๐ Performance Tips

### 1. **Batch Permission Checks**
```python
# Instead of multiple individual checks
# has_create = await permission_service.has_agent_permission(user_id, "client_management", "create")
# has_update = await permission_service.has_agent_permission(user_id, "client_management", "update")

# Use single permission fetch
permissions = await permission_service.get_agent_permissions(user_id, "client_management")
has_create = permissions.get("create", False)
has_update = permissions.get("update", False)
```

### 2. **Use Permission Store**
```typescript
// Frontend - use permission store to avoid re-fetching
const permissionStore = usePermissionStore()

// Cache permissions locally
useEffect(() => {
  if (permissions) {
    permissionStore.setPermissions(permissions)
  }
}, [permissions])
```

### 3. **Optimize Permission Matrix**
```typescript
// Use virtualization for large user lists
import { FixedSizeGrid as Grid } from 'react-window'

const PermissionMatrix = ({ users, permissions }) => (
  <Grid
    height={600}
    width={1200}
    rowCount={users.length}
    columnCount={4} // agents
    rowHeight={50}
    columnWidth={200}
    itemData={{ users, permissions }}
  >
    {PermissionCell}
  </Grid>
)
```

---

## ๐งช Testing Patterns

### 1. **Test Permission Guards**
```typescript
describe('PermissionGuard', () => {
  it('renders children when user has permission', () => {
    mockUseUserPermissions.mockReturnValue({
      hasAgentPermission: jest.fn(() => true)
    })
    
    render(
      <PermissionGuard agent="client_management" operation="create">
        <button>Create Client</button>
      </PermissionGuard>
    )
    
    expect(screen.getByText('Create Client')).toBeInTheDocument()
  })
})
```

### 2. **Test API Protection**
```python
def test_client_creation_requires_permission():
    # User without permission
    response = client.post("/clients", json=client_data, headers=user_headers)
    assert response.status_code == 403
    
    # Grant permission
    permission_service.assign_agent_permissions(
        user.user_id, "client_management", {"create": True}
    )
    
    # User with permission
    response = client.post("/clients", json=client_data, headers=user_headers)
    assert response.status_code == 201
```

---

## ๐ Migration Checklist

When implementing permission system in existing code:

- [ ] **Backend**: Add `@require_agent_permission` decorators to all protected endpoints
- [ ] **Frontend**: Replace role-based checks with `hasAgentPermission` calls
- [ ] **Components**: Wrap protected UI elements with `<PermissionGuard>`
- [ ] **Routes**: Add permission checks to page components
- [ ] **Tests**: Update tests to mock permission responses
- [ ] **Database**: Run permission system migration
- [ ] **Cache**: Configure Redis for permission caching
- [ ] **WebSocket**: Set up real-time permission updates

---

*This quick reference covers the most common permission system implementation patterns. For comprehensive details, see the [Permissions Architecture](./permissions-architecture.md) document.*