# Data Models

Based on the PRD requirements and multi-agent architecture, here are the core data models that will be shared between frontend and backend:

## User Model

**Purpose:** Manages authentication, roles, and agent-specific permissions for the flexible permission system

**Key Attributes:**
- id: UUID - Primary identifier with UUID4 generation
- email: EmailStr - Unique email address for authentication  
- password_hash: str - Bcrypt hashed password with salt
- role: UserRole - Enum (sysadmin, admin, user) for backward compatibility
- is_active: bool - Account status for deactivation capability
- totp_secret: Optional[str] - TOTP secret for 2FA implementation
- created_at: datetime - Account creation timestamp
- updated_at: datetime - Last modification timestamp

### TypeScript Interface
```typescript
interface User {
  id: string;
  email: string;
  role: 'sysadmin' | 'admin' | 'user';
  isActive: boolean;
  totpEnabled: boolean;
  createdAt: string;
  updatedAt: string;
  permissions?: UserAgentPermission[];
}
```

### Relationships
- Has many UserAgentPermissions (one-to-many)
- Creates many AuditLogs as actor (one-to-many)

## Client Model

**Purpose:** Core business entity for client management across all agents with comprehensive validation

**Key Attributes:**
- id: UUID - Primary identifier for cross-agent references
- name: str - Client full name with length validation (2-100 chars)
- cpf: str - Brazilian CPF with format validation and uniqueness
- birth_date: date - Birth date for age calculations and filtering
- created_by: UUID - Foreign key to User who created the record
- created_at: datetime - Registration timestamp
- updated_at: datetime - Last modification timestamp
- is_active: bool - Soft delete flag for data retention

### TypeScript Interface
```typescript
interface Client {
  id: string;
  name: string;
  cpf: string;
  birthDate: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  isActive: boolean;
}
```

### Relationships
- Belongs to User as creator (many-to-one)
- Has many AuditLogs (one-to-many)
- Referenced by agent-specific tables (one-to-many across agents)

## UserAgentPermission Model

**Purpose:** Revolutionary permission system enabling flexible agent-based access control instead of rigid roles

**Key Attributes:**
- id: UUID - Primary identifier for permission records
- user_id: UUID - Foreign key to User receiving permissions
- agent_name: AgentName - Enum (client_management, pdf_processing, reports_analysis, audio_recording)
- can_create: bool - Permission to create new records
- can_read: bool - Permission to view records (always true if any permission granted)
- can_update: bool - Permission to modify existing records
- can_delete: bool - Permission to remove records (typically restricted)
- granted_by: UUID - Foreign key to admin User who granted permissions
- granted_at: datetime - Permission grant timestamp
- expires_at: Optional[datetime] - Optional permission expiration

### TypeScript Interface
```typescript
interface UserAgentPermission {
  id: string;
  userId: string;
  agentName: 'client_management' | 'pdf_processing' | 'reports_analysis' | 'audio_recording';
  canCreate: boolean;
  canRead: boolean;
  canUpdate: boolean;
  canDelete: boolean;
  grantedBy: string;
  grantedAt: string;
  expiresAt?: string;
}
```

### Relationships
- Belongs to User (many-to-one)
- Granted by User as admin (many-to-one)
- Tracked in AuditLogs (one-to-many)

## AuditLog Model

**Purpose:** Comprehensive audit trail for compliance and troubleshooting across all system operations

**Key Attributes:**
- id: UUID - Primary identifier for log entries
- actor_id: UUID - Foreign key to User who performed the action
- action: AuditAction - Enum (create, read, update, delete, login, permission_change)
- resource_type: str - Type of resource affected (User, Client, Permission)
- resource_id: Optional[UUID] - ID of specific resource if applicable
- old_values: Optional[JSON] - Previous values for update operations
- new_values: Optional[JSON] - New values for create/update operations
- ip_address: str - Client IP address for security tracking
- user_agent: str - Browser/client information
- timestamp: datetime - Precise action timestamp
- session_id: Optional[str] - Session identifier for correlation

### TypeScript Interface
```typescript
interface AuditLog {
  id: string;
  actorId: string;
  action: 'create' | 'read' | 'update' | 'delete' | 'login' | 'permission_change';
  resourceType: string;
  resourceId?: string;
  oldValues?: Record<string, any>;
  newValues?: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  timestamp: string;
  sessionId?: string;
}
```

### Relationships
- Belongs to User as actor (many-to-one)
- References any resource by type and ID (polymorphic)

---
