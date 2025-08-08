# Data Models

Based on the PRD requirements and multi-agent architecture, the core data models enable TypeScript interfaces that can be used across the entire stack.

### User Model
**Purpose:** Authentication and authorization management with role-based access control

```typescript
interface User {
  user_id: string;
  email: string;
  role: 'sysadmin' | 'admin' | 'user';
  is_active: boolean;
  totp_enabled: boolean;
  created_at: string; // ISO 8601 timestamp
  updated_at: string; // ISO 8601 timestamp
  last_login?: string; // ISO 8601 timestamp
}

interface UserCreate {
  email: string;
  password: string;
  role: 'sysadmin' | 'admin' | 'user';
}

interface UserUpdate {
  email?: string;
  role?: 'sysadmin' | 'admin' | 'user';
  is_active?: boolean;
}
```

### Client Model  
**Purpose:** Core business entity for client management with comprehensive data validation

```typescript
interface Client {
  client_id: string;
  full_name: string;
  cpf: string; // Format: XXX.XXX.XXX-XX
  birth_date: string; // ISO 8601 date format
  status: 'active' | 'inactive' | 'archived';
  created_by: string; // User ID reference
  updated_by: string; // User ID reference
  created_at: string; // ISO 8601 timestamp
  updated_at: string; // ISO 8601 timestamp
  notes?: string;
}

interface ClientCreate {
  full_name: string;
  cpf: string;
  birth_date: string;
  notes?: string;
}

interface ClientUpdate {
  full_name?: string;
  cpf?: string;
  birth_date?: string;
  status?: 'active' | 'inactive' | 'archived';
  notes?: string;
}

interface ClientSearch {
  query?: string; // Name or CPF search
  status?: 'active' | 'inactive' | 'archived';
  created_after?: string;
  created_before?: string;
  birth_after?: string;
  birth_before?: string;
}
```

### AuditLog Model
**Purpose:** Comprehensive audit trail for all system modifications and access

```typescript
interface AuditLog {
  audit_id: string;
  table_name: string;
  record_id: string;
  action: 'CREATE' | 'UPDATE' | 'DELETE' | 'VIEW';
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  user_id: string;
  ip_address: string;
  user_agent: string;
  timestamp: string; // ISO 8601 timestamp
}
```

### Agent2Document Model
**Purpose:** PDF document management and vector storage for RAG processing

```typescript
interface Agent2Document {
  document_id: string;
  client_id: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  vector_chunks?: Record<string, any>[];
  extraction_metadata?: Record<string, any>;
  uploaded_by: string;
  uploaded_at: string;
  processed_at?: string;
}
```
