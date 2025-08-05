# Admin Permission Management Components

This directory contains comprehensive admin interface components for managing user permissions in the IAM Dashboard. These components provide a complete solution for permission management with responsive design, real-time updates, and comprehensive error handling.

## Components Overview

### 1. PermissionMatrix
**File**: `PermissionMatrix.tsx`

Main admin interface component that displays user-agent permissions in a matrix view with inline editing capabilities.

**Features**:
- Responsive matrix view (desktop) and card view (mobile)
- Inline permission editing with quick level selection
- Advanced filtering (search, role, agent, permission level, status)
- Bulk user selection and operations
- Real-time permission updates
- Export functionality
- Comprehensive statistics dashboard

**Props**:
```typescript
interface PermissionMatrixProps {
  users: User[]
  onUserPermissionsChange?: (userId: string) => void
  onBulkAction?: (userIds: string[], action: string) => void
  className?: string
}
```

**Usage**:
```tsx
<PermissionMatrix
  users={users}
  onUserPermissionsChange={(userId) => refetchUser(userId)}
  onBulkAction={(userIds, action) => handleBulkOperation(userIds, action)}
/>
```

### 2. UserPermissionsDialog
**File**: `UserPermissionsDialog.tsx`

Dialog component for detailed management of individual user permissions across all agents.

**Features**:
- Comprehensive user information display
- Agent-specific permission configuration
- Quick permission level selection with detailed CRUD controls
- Permission change history and audit trail
- Form validation with required change reason
- Real-time permission updates via WebSocket
- Loading and error states

**Props**:
```typescript
interface UserPermissionsDialogProps {
  user: User | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onPermissionsChanged?: (userId: string) => void
  className?: string
}
```

**Usage**:
```tsx
<UserPermissionsDialog
  user={selectedUser}
  open={dialogOpen}
  onOpenChange={setDialogOpen}
  onPermissionsChanged={(userId) => refetchPermissions(userId)}
/>
```

### 3. BulkPermissionDialog
**File**: `BulkPermissionDialog.tsx`

Dialog for performing bulk permission operations on multiple users simultaneously.

**Features**:
- Multiple operation types: template application, grant all, revoke all, custom permissions
- Template selection with preview functionality
- Custom permission configuration for all agents
- Progress tracking with real-time updates
- Error handling and retry logic
- Bulk operation results summary
- Export functionality for selected users

**Props**:
```typescript
interface BulkPermissionDialogProps {
  users: User[]
  open: boolean
  onOpenChange: (open: boolean) => void
  onBulkOperationComplete?: (results: BulkPermissionAssignResponse) => void
  className?: string
}
```

**Usage**:
```tsx
<BulkPermissionDialog
  users={selectedUsers}
  open={bulkDialogOpen}
  onOpenChange={setBulkDialogOpen}
  onBulkOperationComplete={(results) => handleResults(results)}
/>
```

### 4. PermissionTemplates
**File**: `PermissionTemplates.tsx`

Component for creating, editing, and managing permission templates for easy reuse.

**Features**:
- Template CRUD operations (Create, Read, Update, Delete)
- Template duplication functionality
- System vs. custom template distinction
- Permission level configuration for each agent
- Template search and filtering
- Template application tracking
- Comprehensive template statistics

**Props**:
```typescript
interface PermissionTemplatesProps {
  onTemplateApplied?: (templateId: string, userCount: number) => void
  className?: string
}
```

**Usage**:
```tsx
<PermissionTemplates
  onTemplateApplied={(templateId, userCount) => handleTemplateApplied(templateId, userCount)}
/>
```

## Dependencies

### Required Hooks
- `useUserPermissions` - Main permission management hook
- `usePermissionMutations` - Permission CRUD operations
- `usePermissionTemplates` - Template management
- `usePermissionAudit` - Audit log functionality

### Required Types
All components use the comprehensive type system from `@/types/permissions.ts`:
- `AgentName` - Enum for agent types
- `PermissionActions` - CRUD permission structure
- `PermissionLevel` - Permission level constants
- `UserPermissionMatrix` - User permission data structure
- `PermissionTemplate` - Template data structure

### UI Components
Components use shadcn/ui components for consistency:
- `Dialog`, `Button`, `Card`, `Table`, `Badge`
- `Input`, `Textarea`, `Select`, `Label`
- `Alert`, `Progress`, `DropdownMenu`

## Features

### 🎨 Responsive Design
- **Mobile (320px-639px)**: Card-based layouts with expandable details
- **Tablet (640px-1023px)**: Horizontal scroll with fixed columns
- **Desktop (1024px+)**: Full matrix view with inline editing

### 🔒 Permission Guards
All components are wrapped with appropriate permission guards:
- `PermissionGuard` - Basic access control
- `CreatePermissionGuard` - Create operation protection
- `UpdatePermissionGuard` - Update operation protection
- `DeletePermissionGuard` - Delete operation protection

### 🌐 Internationalization
- All UI text is in Portuguese (Brazil) as specified in requirements
- Agent names and permission levels have proper Portuguese translations
- Error messages and user feedback in Portuguese

### ⚡ Real-time Updates
- WebSocket integration for permission change notifications
- Automatic cache invalidation and refetching
- Real-time UI updates without page refresh

### 📊 Comprehensive Statistics
- User count by role and status
- Permission distribution analytics
- Template usage statistics
- Activity tracking and audit logs

## Usage Examples

### Complete Admin Interface
```tsx
import {
  PermissionMatrix,
  UserPermissionsDialog,
  BulkPermissionDialog,
  PermissionTemplates,
} from '@/components/admin'

function AdminPermissionPage() {
  const [selectedUser, setSelectedUser] = useState(null)
  const [selectedUsers, setSelectedUsers] = useState([])
  const [activeTab, setActiveTab] = useState('matrix')
  
  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex space-x-2">
        <Button 
          variant={activeTab === 'matrix' ? 'default' : 'outline'}
          onClick={() => setActiveTab('matrix')}
        >
          Matriz de Permissões
        </Button>
        <Button 
          variant={activeTab === 'templates' ? 'default' : 'outline'}
          onClick={() => setActiveTab('templates')}
        >
          Templates
        </Button>
      </div>
      
      {/* Tab Content */}
      {activeTab === 'matrix' && (
        <PermissionMatrix
          users={users}
          onUserPermissionsChange={refetchPermissions}
          onBulkAction={(userIds, action) => {
            setSelectedUsers(userIds)
            setBulkDialogOpen(true)
          }}
        />
      )}
      
      {activeTab === 'templates' && (
        <PermissionTemplates
          onTemplateApplied={handleTemplateApplied}
        />
      )}
      
      {/* Dialogs */}
      <UserPermissionsDialog
        user={selectedUser}
        open={userDialogOpen}
        onOpenChange={setUserDialogOpen}
        onPermissionsChanged={refetchPermissions}
      />
      
      <BulkPermissionDialog
        users={selectedUsers}
        open={bulkDialogOpen}
        onOpenChange={setBulkDialogOpen}
        onBulkOperationComplete={handleBulkComplete}
      />
    </div>
  )
}
```

### Individual Component Usage
```tsx
// Permission Matrix only
<PermissionMatrix
  users={users}
  onUserPermissionsChange={(userId) => {
    toast({ title: 'Permissões atualizadas', variant: 'success' })
    refetchUser(userId)
  }}
/>

// User Dialog for specific user
<UserPermissionsDialog
  user={currentUser}
  open={open}
  onOpenChange={setOpen}
/>

// Template Management
<PermissionTemplates
  onTemplateApplied={(templateId, count) => {
    toast({ 
      title: 'Template aplicado', 
      description: `Aplicado a ${count} usuários` 
    })
  }}
/>
```

## Best Practices

### 1. Error Handling
```tsx
// Always handle errors gracefully
const handlePermissionChange = async (userId, permissions) => {
  try {
    await updatePermissions(userId, permissions)
    toast({ title: 'Sucesso', variant: 'success' })
  } catch (error) {
    toast({ 
      title: 'Erro', 
      description: error.message,
      variant: 'error' 
    })
  }
}
```

### 2. Loading States
```tsx
// Show loading indicators during operations
{isLoading ? (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin h-8 w-8 border-b-2 border-gray-900"></div>
    <span className="ml-2">Carregando permissões...</span>
  </div>
) : (
  <PermissionMatrix users={users} />
)}
```

### 3. Optimistic Updates
```tsx
// Update UI immediately, rollback on error
const handleQuickPermissionChange = async (userId, agent, permissions) => {
  // Optimistic update
  updateLocalState(userId, agent, permissions)
  
  try {
    await updatePermissionAPI(userId, agent, permissions)
  } catch (error) {
    // Rollback on error
    revertLocalState(userId, agent)
    showError(error.message)
  }
}
```

## Testing

### Component Testing
```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { PermissionMatrix } from '../PermissionMatrix'

test('renders permission matrix with users', () => {
  const mockUsers = [
    { user_id: '1', name: 'Test User', email: 'test@example.com' }
  ]
  
  render(<PermissionMatrix users={mockUsers} />)
  
  expect(screen.getByText('Test User')).toBeInTheDocument()
  expect(screen.getByText('test@example.com')).toBeInTheDocument()
})
```

### Integration Testing
```tsx
// Test component interactions
test('opens user dialog when edit button clicked', async () => {
  render(<AdminPermissionPage />)
  
  const editButton = screen.getByRole('button', { name: /editar/i })
  fireEvent.click(editButton)
  
  await waitFor(() => {
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })
})
```

## Architecture Notes

### Data Flow
1. **Parent Component** → Provides user data and handlers
2. **Permission Matrix** → Displays data, handles user interactions
3. **Dialogs** → Handle detailed operations, emit events
4. **Hooks** → Manage API calls and state
5. **API** → Persist changes to backend

### State Management
- Local component state for UI interactions
- TanStack Query for server state and caching
- WebSocket connections for real-time updates
- Optimistic updates for better UX

### Performance Optimizations
- Memoized computations for filtered data
- Virtualized tables for large user lists
- Debounced search inputs
- Cached permission checks
- Lazy loading of audit logs

## Security Considerations

### Permission Guards
All components are protected by appropriate permission guards that check user access rights before rendering sensitive UI elements.

### Input Validation
- All form inputs are validated using Zod schemas
- Server-side validation is always enforced
- XSS prevention through proper data encoding

### Audit Trail
- All permission changes are logged with timestamps
- Change reasons are required for accountability
- User actions are tracked for security monitoring

---

This component library provides a complete solution for admin permission management in the IAM Dashboard, following all security, usability, and architectural requirements specified in the project documentation.