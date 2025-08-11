# Database Schema

Based on the conceptual data models, here's the concrete database schema using PostgreSQL with comprehensive indexes, constraints, and relationships:

## Database Schema (PostgreSQL DDL)

```sql
-- Enable UUID extension for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for password hashing
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable pgvector for future AI capabilities
CREATE EXTENSION IF NOT EXISTS "vector";

-- User roles enumeration
CREATE TYPE user_role AS ENUM ('sysadmin', 'admin', 'user');

-- Agent names enumeration for permission system
CREATE TYPE agent_name AS ENUM (
    'client_management', 
    'pdf_processing', 
    'reports_analysis', 
    'audio_recording'
);

-- Audit action types
CREATE TYPE audit_action AS ENUM (
    'create', 'read', 'update', 'delete', 
    'login', 'logout', 'permission_change'
);

-- Users table with authentication and role management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    totp_secret VARCHAR(32), -- Base32 encoded TOTP secret
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT password_not_empty CHECK (length(password_hash) > 0)
);

-- Clients table with Brazilian CPF validation
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    cpf CHAR(11) UNIQUE NOT NULL,
    birth_date DATE NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Constraints
    CONSTRAINT valid_name CHECK (length(trim(name)) >= 2),
    CONSTRAINT valid_cpf CHECK (cpf ~ '^[0-9]{11}$'),
    CONSTRAINT valid_birth_date CHECK (birth_date <= CURRENT_DATE),
    CONSTRAINT future_birth_date CHECK (birth_date > '1900-01-01')
);

-- User agent permissions table - Core of flexible permission system
CREATE TABLE user_agent_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_name agent_name NOT NULL,
    can_create BOOLEAN NOT NULL DEFAULT false,
    can_read BOOLEAN NOT NULL DEFAULT true,
    can_update BOOLEAN NOT NULL DEFAULT false,
    can_delete BOOLEAN NOT NULL DEFAULT false,
    granted_by UUID NOT NULL REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Unique constraint: one permission record per user per agent
    UNIQUE(user_id, agent_name),
    
    -- Constraint: expires_at must be in the future if specified
    CONSTRAINT valid_expiry CHECK (expires_at IS NULL OR expires_at > granted_at)
);

-- Comprehensive audit logging table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID REFERENCES users(id),
    action audit_action NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET NOT NULL,
    user_agent TEXT,
    session_id VARCHAR(128),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_resource_type CHECK (length(trim(resource_type)) > 0)
);

-- Performance Indexes

-- Users table indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- Clients table indexes
CREATE INDEX idx_clients_cpf ON clients(cpf);
CREATE INDEX idx_clients_created_by ON clients(created_by);
CREATE INDEX idx_clients_birth_date ON clients(birth_date);
CREATE INDEX idx_clients_active ON clients(is_active) WHERE is_active = true;

-- Permission system indexes (Critical for <10ms performance)
CREATE INDEX idx_user_permissions_user_agent ON user_agent_permissions(user_id, agent_name);
CREATE INDEX idx_user_permissions_granted_by ON user_agent_permissions(granted_by);
CREATE INDEX idx_user_permissions_expires ON user_agent_permissions(expires_at) WHERE expires_at IS NOT NULL;

-- Audit logs indexes
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

---
