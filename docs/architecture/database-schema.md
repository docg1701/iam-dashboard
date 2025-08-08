# Database Schema

**Complete PostgreSQL >=17.5 + pgvector schema with proper indexing, constraints, and relationships optimized for the multi-agent architecture**

> ๐ **Quick Navigation**: [Permission Tables](./permissions-architecture.md#database-architecture) | [Migration Guide](./developer-reference.md#database-operations) | [Data Models](./data-models.md) | [Backend Architecture](./backend-architecture.md#database-architecture)

---

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Users table for authentication and authorization
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('sysadmin', 'admin', 'user')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    totp_secret VARCHAR(32), -- Base32 encoded TOTP secret
    totp_enabled BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_password_length CHECK (length(password_hash) >= 60)
);

-- User agent permissions table for granular access control
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
    
    UNIQUE(user_id, agent_name),
    CONSTRAINT permissions_jsonb_structure CHECK (
        jsonb_typeof(permissions) = 'object' AND
        permissions ? 'create' AND jsonb_typeof(permissions->'create') = 'boolean' AND
        permissions ? 'read' AND jsonb_typeof(permissions->'read') = 'boolean' AND
        permissions ? 'update' AND jsonb_typeof(permissions->'update') = 'boolean' AND
        permissions ? 'delete' AND jsonb_typeof(permissions->'delete') = 'boolean'
    )
);

-- Permission templates for common role patterns
CREATE TABLE permission_templates (
    template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    permissions JSONB NOT NULL,
    is_system_template BOOLEAN NOT NULL DEFAULT false,
    created_by_user_id UUID NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT template_name_length CHECK (length(trim(template_name)) >= 3),
    CONSTRAINT template_permissions_structure CHECK (
        jsonb_typeof(permissions) = 'object' AND
        (NOT permissions ? 'client_management' OR 
         (jsonb_typeof(permissions->'client_management') = 'object' AND
          permissions->'client_management' ? 'create' AND
          permissions->'client_management' ? 'read' AND
          permissions->'client_management' ? 'update' AND
          permissions->'client_management' ? 'delete'))
    )
);

-- Clients table (Agent 1 primary responsibility)
CREATE TABLE clients (
    client_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE, -- Format: XXX.XXX.XXX-XX
    birth_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    notes TEXT,
    created_by UUID NOT NULL REFERENCES users(user_id),
    updated_by UUID NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT clients_cpf_format CHECK (cpf ~ '^\d{3}\.\d{3}\.\d{3}-\d{2}$'),
    CONSTRAINT clients_name_length CHECK (length(trim(full_name)) >= 2),
    CONSTRAINT clients_birth_date_range CHECK (
        birth_date >= '1900-01-01' AND 
        birth_date <= CURRENT_DATE - INTERVAL '13 years'
    )
);

-- Documents table (Agent 2 primary responsibility)
CREATE TABLE agent2_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0),
    mime_type VARCHAR(100) NOT NULL,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    vector_chunks JSONB, -- Array of {text, embedding, metadata} objects
    extraction_metadata JSONB, -- PDF metadata, page count, etc.
    uploaded_by UUID NOT NULL REFERENCES users(user_id),
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT documents_filename_length CHECK (length(original_filename) <= 255),
    CONSTRAINT documents_mime_type_pdf CHECK (mime_type = 'application/pdf'),
    CONSTRAINT documents_file_size_limit CHECK (file_size <= 52428800) -- 50MB limit
);

-- Comprehensive audit log table
CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE', 'VIEW')),
    old_values JSONB,
    new_values JSONB,
    user_id UUID REFERENCES users(user_id),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT audit_table_name_valid CHECK (
        table_name IN ('users', 'clients', 'agent2_documents', 'agent3_reports', 'agent4_recordings', 'user_agent_permissions', 'permission_templates')
    )
);

-- Permission audit log for detailed permission change tracking
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
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT permission_audit_agent_valid CHECK (
        agent_name IN ('client_management', 'pdf_processing', 'reports_analysis', 'audio_recording')
    )
);

-- Performance indexes
CREATE INDEX idx_clients_full_name ON clients USING gin(to_tsvector('english', full_name));
CREATE INDEX idx_clients_cpf ON clients(cpf);
CREATE INDEX idx_clients_status ON clients(status);
CREATE INDEX idx_clients_created_at ON clients(created_at DESC);

CREATE INDEX idx_documents_client_id ON agent2_documents(client_id);
CREATE INDEX idx_documents_status ON agent2_documents(processing_status);
CREATE INDEX idx_documents_vector_chunks ON agent2_documents USING gin(vector_chunks);

-- Permission system indexes for optimal performance
CREATE INDEX idx_user_agent_permissions_user_id ON user_agent_permissions(user_id);
CREATE INDEX idx_user_agent_permissions_agent_name ON user_agent_permissions(agent_name);
CREATE INDEX idx_user_agent_permissions_composite ON user_agent_permissions(user_id, agent_name);
CREATE INDEX idx_user_agent_permissions_jsonb ON user_agent_permissions USING gin(permissions);

CREATE INDEX idx_permission_templates_name ON permission_templates(template_name);
CREATE INDEX idx_permission_templates_system ON permission_templates(is_system_template);

-- Audit indexes
CREATE INDEX idx_audit_table_name ON audit_log(table_name);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_user_id ON audit_log(user_id);

CREATE INDEX idx_permission_audit_user_id ON permission_audit_log(user_id);
CREATE INDEX idx_permission_audit_agent ON permission_audit_log(agent_name);
CREATE INDEX idx_permission_audit_timestamp ON permission_audit_log(timestamp DESC);
CREATE INDEX idx_permission_audit_changed_by ON permission_audit_log(changed_by_user_id);

-- Automated timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_agent_permissions_updated_at BEFORE UPDATE ON user_agent_permissions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_permission_templates_updated_at BEFORE UPDATE ON permission_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Audit logging function
CREATE OR REPLACE FUNCTION log_audit_trail(
    p_table_name VARCHAR(50),
    p_record_id UUID,
    p_action VARCHAR(10),
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL,
    p_user_id UUID DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    audit_id UUID;
BEGIN
    INSERT INTO audit_log (
        table_name, record_id, action, old_values, new_values,
        user_id, ip_address, user_agent
    ) VALUES (
        p_table_name, p_record_id, p_action, p_old_values, p_new_values,
        p_user_id, p_ip_address, p_user_agent
    ) RETURNING audit_log.audit_id INTO audit_id;
    
    RETURN audit_id;
END;
$$ language 'plpgsql';

-- Permission management functions
CREATE OR REPLACE FUNCTION log_permission_change(
    p_user_id UUID,
    p_agent_name VARCHAR(50),
    p_action VARCHAR(20),
    p_old_permissions JSONB DEFAULT NULL,
    p_new_permissions JSONB DEFAULT NULL,
    p_changed_by_user_id UUID,
    p_change_reason TEXT DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    audit_id UUID;
BEGIN
    INSERT INTO permission_audit_log (
        user_id, agent_name, action, old_permissions, new_permissions,
        changed_by_user_id, change_reason, ip_address, user_agent
    ) VALUES (
        p_user_id, p_agent_name, p_action, p_old_permissions, p_new_permissions,
        p_changed_by_user_id, p_change_reason, p_ip_address, p_user_agent
    ) RETURNING permission_audit_log.audit_id INTO audit_id;
    
    RETURN audit_id;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION check_user_agent_permission(
    p_user_id UUID,
    p_agent_name VARCHAR(50),
    p_operation VARCHAR(10)
)
RETURNS BOOLEAN AS $$
DECLARE
    user_role VARCHAR(20);
    permission_record RECORD;
BEGIN
    -- Get user role
    SELECT role INTO user_role FROM users WHERE user_id = p_user_id AND is_active = true;
    
    -- Sysadmin always has access
    IF user_role = 'sysadmin' THEN
        RETURN true;
    END IF;
    
    -- Admin has access to client_management and reports_analysis
    IF user_role = 'admin' AND p_agent_name IN ('client_management', 'reports_analysis') THEN
        RETURN true;
    END IF;
    
    -- Check specific permissions for users
    SELECT permissions INTO permission_record
    FROM user_agent_permissions 
    WHERE user_id = p_user_id AND agent_name = p_agent_name;
    
    IF permission_record IS NULL THEN
        RETURN false;
    END IF;
    
    -- Check if the specific operation is allowed
    RETURN COALESCE((permission_record.permissions->>p_operation)::boolean, false);
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION get_user_permission_matrix(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}';
    permission_record RECORD;
BEGIN
    FOR permission_record IN 
        SELECT agent_name, permissions 
        FROM user_agent_permissions 
        WHERE user_id = p_user_id
    LOOP
        result := result || jsonb_build_object(permission_record.agent_name, permission_record.permissions);
    END LOOP;
    
    RETURN result;
END;
$$ language 'plpgsql';

-- Function to apply permission template to user
CREATE OR REPLACE FUNCTION apply_permission_template(
    p_user_id UUID,
    p_template_id UUID,
    p_applied_by_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    template_record RECORD;
    agent_name TEXT;
    agent_permissions JSONB;
BEGIN
    -- Get template
    SELECT permissions INTO template_record FROM permission_templates WHERE template_id = p_template_id;
    
    IF template_record IS NULL THEN
        RAISE EXCEPTION 'Template not found';
    END IF;
    
    -- Apply permissions for each agent in template
    FOR agent_name, agent_permissions IN SELECT * FROM jsonb_each(template_record.permissions)
    LOOP
        INSERT INTO user_agent_permissions (user_id, agent_name, permissions, created_by_user_id)
        VALUES (p_user_id, agent_name, agent_permissions, p_applied_by_user_id)
        ON CONFLICT (user_id, agent_name) 
        DO UPDATE SET 
            permissions = EXCLUDED.permissions,
            updated_at = NOW();
        
        -- Log the change
        PERFORM log_permission_change(
            p_user_id, 
            agent_name, 
            'TEMPLATE_APPLIED',
            NULL,
            agent_permissions,
            p_applied_by_user_id,
            'Applied permission template'
        );
    END LOOP;
    
    RETURN true;
END;
$$ language 'plpgsql';

---

## Database Migration Strategy

### Migration Overview

The permission system migration transforms the simple 3-role RBAC system into a flexible agent-based permission system while maintaining backward compatibility and ensuring zero data loss.

### Migration Architecture

#### Current State Analysis
```sql
-- BEFORE: Simple role-based system
users (
    user_id UUID,
    email VARCHAR(255),
    role VARCHAR(20) CHECK (role IN ('sysadmin', 'admin', 'user'))
)

-- Permission checking: Hard-coded role validation
def check_permission(user, action):
    if user.role == 'sysadmin':
        return True
    elif user.role == 'admin' and action in ['client_read', 'client_write']:
        return True
    elif user.role == 'user' and action == 'profile_edit':
        return True
    return False
```

#### Target State Architecture
```sql
-- AFTER: Granular permission system
users (
    user_id UUID,
    email VARCHAR(255),
    role VARCHAR(20) -- Preserved for compatibility
)

user_agent_permissions (
    permission_id UUID,
    user_id UUID REFERENCES users(user_id),
    agent_name VARCHAR(50),
    permissions JSONB,
    created_by_user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
)

-- Permission checking: Database-driven validation
def check_permission(user_id, agent_name, operation):
    return check_user_agent_permission(user_id, agent_name, operation)
```

### Migration Timeline and Dependencies

#### Phase 1: Schema Creation (Day 1)
```sql
-- Migration ID: 2025080401_create_permission_system
-- Dependencies: Existing users table
-- Estimated Time: 30 minutes
-- Rollback Time: 5 minutes

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
    
    UNIQUE(user_id, agent_name),
    CONSTRAINT permissions_jsonb_structure CHECK (
        jsonb_typeof(permissions) = 'object' AND
        permissions ? 'create' AND jsonb_typeof(permissions->'create') = 'boolean' AND
        permissions ? 'read' AND jsonb_typeof(permissions->'read') = 'boolean' AND
        permissions ? 'update' AND jsonb_typeof(permissions->'update') = 'boolean' AND
        permissions ? 'delete' AND jsonb_typeof(permissions->'delete') = 'boolean'
    )
);

-- Performance indexes
CREATE INDEX idx_user_agent_permissions_user_id ON user_agent_permissions(user_id);
CREATE INDEX idx_user_agent_permissions_agent_name ON user_agent_permissions(agent_name);
CREATE INDEX idx_user_agent_permissions_composite ON user_agent_permissions(user_id, agent_name);
CREATE INDEX idx_user_agent_permissions_jsonb ON user_agent_permissions USING gin(permissions);
```

#### Phase 2: Data Migration (Day 1)
```sql
-- Migration logic: Preserve existing role-based permissions
WITH system_user AS (
    INSERT INTO users (user_id, email, password_hash, role, is_active)
    SELECT 
        uuid_generate_v4(),
        'system@migration.local',
        '$2b$12$dummy.hash.for.system.user.migration',
        'sysadmin',
        false
    WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'system@migration.local')
    RETURNING user_id
),
user_permissions AS (
    SELECT 
        u.user_id,
        u.role,
        s.user_id as system_user_id,
        CASE 
            WHEN u.role = 'sysadmin' THEN 
                jsonb_build_object('create', true, 'read', true, 'update', true, 'delete', true)
            WHEN u.role = 'admin' THEN 
                jsonb_build_object('create', true, 'read', true, 'update', true, 'delete', true)
            ELSE 
                jsonb_build_object('create', true, 'read', true, 'update', true, 'delete', false)
        END as permissions
    FROM users u, system_user s
    WHERE u.email != 'system@migration.local'
)
INSERT INTO user_agent_permissions (user_id, agent_name, permissions, created_by_user_id)
SELECT 
    up.user_id,
    agent_name,
    CASE 
        WHEN up.role = 'sysadmin' THEN up.permissions
        WHEN up.role = 'admin' AND agent_name IN ('client_management', 'reports_analysis') THEN up.permissions
        WHEN up.role = 'user' AND agent_name = 'client_management' THEN up.permissions
        ELSE jsonb_build_object('create', false, 'read', false, 'update', false, 'delete', false)
    END as permissions,
    up.system_user_id
FROM user_permissions up
CROSS JOIN (
    VALUES 
        ('client_management'),
        ('pdf_processing'),
        ('reports_analysis'),
        ('audio_recording')
) AS agents(agent_name)
WHERE NOT (
    up.role != 'sysadmin' AND 
    agent_name NOT IN ('client_management', 'reports_analysis') AND 
    up.role = 'admin'
) AND NOT (
    up.role = 'user' AND 
    agent_name != 'client_management'
);
```

#### Phase 3: Permission Template Creation (Day 1)
```sql
-- Create system permission templates
INSERT INTO permission_templates (template_name, description, permissions, is_system_template, created_by_user_id)
VALUES 
    ('Client Specialist', 'Full client management access', 
     '{"client_management": {"create": true, "read": true, "update": true, "delete": false}}', 
     true, 
     (SELECT user_id FROM users WHERE email = 'system@migration.local')),
    ('Report Analyst', 'Read-only access to reports and client data', 
     '{"client_management": {"create": false, "read": true, "update": false, "delete": false}, "reports_analysis": {"create": true, "read": true, "update": true, "delete": false}}', 
     true, 
     (SELECT user_id FROM users WHERE email = 'system@migration.local')),
    ('Document Processor', 'PDF processing and client management', 
     '{"client_management": {"create": false, "read": true, "update": false, "delete": false}, "pdf_processing": {"create": true, "read": true, "update": true, "delete": true}}', 
     true, 
     (SELECT user_id FROM users WHERE email = 'system@migration.local')),
    ('Full Agent Access', 'Complete access to all agents (except system admin functions)', 
     '{"client_management": {"create": true, "read": true, "update": true, "delete": true}, "pdf_processing": {"create": true, "read": true, "update": true, "delete": true}, "reports_analysis": {"create": true, "read": true, "update": true, "delete": true}, "audio_recording": {"create": true, "read": true, "update": true, "delete": true}}', 
     true, 
     (SELECT user_id FROM users WHERE email = 'system@migration.local'))
ON CONFLICT (template_name) DO NOTHING;
```

### Migration Validation and Testing

#### Pre-Migration Validation
```sql
-- Validation queries to run before migration
-- 1. Verify users table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('user_id', 'email', 'role')
ORDER BY ordinal_position;

-- 2. Count existing users by role
SELECT role, COUNT(*) as user_count 
FROM users 
WHERE is_active = true 
GROUP BY role 
ORDER BY role;

-- 3. Check for required extensions
SELECT extname, extversion 
FROM pg_extension 
WHERE extname IN ('uuid-ossp', 'pgcrypto');

-- 4. Verify foreign key constraints will be satisfied
SELECT COUNT(*) as orphaned_records
FROM users u1
LEFT JOIN users u2 ON u1.user_id = u2.user_id
WHERE u2.user_id IS NULL;
```

#### Post-Migration Validation
```sql
-- Validation queries to run after migration
-- 1. Verify all users have permission records
SELECT 
    u.user_id,
    u.email,
    u.role,
    COUNT(uap.permission_id) as permission_count
FROM users u
LEFT JOIN user_agent_permissions uap ON u.user_id = uap.user_id
WHERE u.email != 'system@migration.local'
GROUP BY u.user_id, u.email, u.role
HAVING COUNT(uap.permission_id) = 0;

-- 2. Verify permission structure integrity
SELECT agent_name, COUNT(*) as records_with_invalid_structure
FROM user_agent_permissions
WHERE NOT (
    permissions ? 'create' AND jsonb_typeof(permissions->'create') = 'boolean' AND
    permissions ? 'read' AND jsonb_typeof(permissions->'read') = 'boolean' AND
    permissions ? 'update' AND jsonb_typeof(permissions->'update') = 'boolean' AND
    permissions ? 'delete' AND jsonb_typeof(permissions->'delete') = 'boolean'
)
GROUP BY agent_name;

-- 3. Verify permission inheritance from roles
SELECT 
    u.role,
    uap.agent_name,
    COUNT(*) as permission_count,
    COUNT(CASE WHEN uap.permissions->>'read' = 'true' THEN 1 END) as read_permissions,
    COUNT(CASE WHEN uap.permissions->>'create' = 'true' THEN 1 END) as create_permissions
FROM users u
JOIN user_agent_permissions uap ON u.user_id = uap.user_id
WHERE u.email != 'system@migration.local'
GROUP BY u.role, uap.agent_name
ORDER BY u.role, uap.agent_name;
```

### Rollback Procedures

#### Emergency Rollback (< 5 minutes)
```sql
-- Emergency rollback script
BEGIN;

-- 1. Drop all permission-related constraints and indexes
DROP INDEX IF EXISTS idx_user_agent_permissions_jsonb;
DROP INDEX IF EXISTS idx_user_agent_permissions_composite;
DROP INDEX IF EXISTS idx_user_agent_permissions_agent_name;
DROP INDEX IF EXISTS idx_user_agent_permissions_user_id;

-- 2. Drop permission tables
DROP TABLE IF EXISTS permission_audit_log CASCADE;
DROP TABLE IF EXISTS user_agent_permissions CASCADE;
DROP TABLE IF EXISTS permission_templates CASCADE;

-- 3. Remove system migration user
DELETE FROM users WHERE email = 'system@migration.local';

-- 4. Verify rollback success
SELECT 'Rollback completed successfully' as status;

COMMIT;
```

#### Planned Rollback with Data Preservation
```sql
-- Planned rollback with data backup
-- 1. Create backup tables
CREATE TABLE user_agent_permissions_backup AS 
SELECT * FROM user_agent_permissions;

CREATE TABLE permission_templates_backup AS 
SELECT * FROM permission_templates;

-- 2. Execute rollback
-- (Same as emergency rollback)

-- 3. Verify system functionality
-- Run application test suite
```

### Performance Optimization During Migration

#### Migration Performance Monitoring
```sql
-- Monitor migration progress
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables 
WHERE tablename IN ('user_agent_permissions', 'permission_templates')
ORDER BY tablename;

-- Monitor active connections during migration
SELECT 
    state,
    COUNT(*) as connection_count
FROM pg_stat_activity 
WHERE datname = current_database()
GROUP BY state;
```

#### Index Creation Strategy
```sql
-- Create indexes concurrently to minimize locking
CREATE INDEX CONCURRENTLY idx_user_agent_permissions_user_id 
ON user_agent_permissions(user_id);

CREATE INDEX CONCURRENTLY idx_user_agent_permissions_agent_name 
ON user_agent_permissions(agent_name);

CREATE INDEX CONCURRENTLY idx_user_agent_permissions_composite 
ON user_agent_permissions(user_id, agent_name);

CREATE INDEX CONCURRENTLY idx_user_agent_permissions_jsonb 
ON user_agent_permissions USING gin(permissions);
```

### Migration Success Criteria

#### Technical Success Metrics
- **Zero Data Loss**: All existing user data preserved (100% validation pass rate)
- **Schema Integrity**: All constraints and relationships properly established
- **Performance**: Permission queries execute in <50ms (95th percentile)
- **Rollback Capability**: Complete rollback possible within 5 minutes

#### Business Success Metrics
- **User Access Preservation**: All users retain appropriate access levels
- **Operational Continuity**: No disruption to existing user workflows
- **Enhanced Capabilities**: Regular users can perform client management tasks
- **Admin Efficiency**: Permission management reduces admin workload by >50%

### Migration Monitoring and Alerting

#### Real-time Migration Monitoring
```python
# Migration monitoring service
class MigrationMonitor:
    def __init__(self, db_connection):
        self.db = db_connection
        self.start_time = datetime.utcnow()
    
    async def monitor_progress(self):
        """Monitor migration progress in real-time."""
        stats = await self.db.fetch_one("""
            SELECT 
                (SELECT COUNT(*) FROM users WHERE email != 'system@migration.local') as total_users,
                (SELECT COUNT(DISTINCT user_id) FROM user_agent_permissions) as migrated_users,
                (SELECT COUNT(*) FROM permission_templates WHERE is_system_template = true) as templates_created
        """)
        
        progress = (stats['migrated_users'] / stats['total_users']) * 100
        
        return {
            'progress_percent': progress,
            'total_users': stats['total_users'],
            'migrated_users': stats['migrated_users'],
            'templates_created': stats['templates_created'],
            'elapsed_time': (datetime.utcnow() - self.start_time).total_seconds()
        }
```

#### Migration Health Checks
```sql
-- Health check queries for production monitoring
-- 1. Permission system availability
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 'HEALTHY'
        ELSE 'DEGRADED'
    END as permission_system_status
FROM information_schema.tables 
WHERE table_name = 'user_agent_permissions';

-- 2. Permission data integrity
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN 'HEALTHY'
        ELSE 'DEGRADED'
    END as data_integrity_status
FROM user_agent_permissions
WHERE permissions = '{}'::jsonb;

-- 3. Migration completeness
SELECT 
    CASE 
        WHEN users_without_permissions = 0 THEN 'COMPLETE'
        ELSE 'INCOMPLETE'
    END as migration_status,
    users_without_permissions
FROM (
    SELECT COUNT(*) as users_without_permissions
    FROM users u
    LEFT JOIN user_agent_permissions uap ON u.user_id = uap.user_id
    WHERE uap.user_id IS NULL 
    AND u.email != 'system@migration.local'
    AND u.is_active = true
) stats;
```

---

## Cross-References

### Related Documentation
- **Migration Implementation**: [Story 1.8 - Permission System Database Migration](../stories/1.8.permission-system-database-migration.md)
- **Permission Architecture**: [Permissions Architecture Documentation](./permissions-architecture.md)
- **Permission Requirements**: [FR16-FR18 - Enhanced Permission System](../prd/requirements.md#fr16-enhanced-user-roles-with-agent-permissions)
- **Backend Integration**: [Backend Architecture - Permission Patterns](./backend-architecture.md#permission-validation)

### Implementation Dependencies
- **Alembic Migration**: Requires `apps/backend/alembic/versions/2025080401_create_user_agent_permissions_system.py`
- **Backend Services**: `UserPermissionService`, `AgentAccessService` documented in backend architecture
- **API Endpoints**: Permission management endpoints in [API Specification](./api-specification.md)
- **Frontend Components**: Permission-aware components in [Frontend Architecture](./frontend-architecture.md)

-- Sample permission data insertion
INSERT INTO permission_templates (template_name, description, permissions, is_system_template, created_by_user_id)
VALUES 
    ('Client Specialist', 'Full client management access', 
     '{"client_management": {"create": true, "read": true, "update": true, "delete": false}}', 
     true, 
     (SELECT user_id FROM users WHERE role = 'sysadmin' LIMIT 1)),
    ('Report Analyst', 'Read-only access to reports and client data', 
     '{"client_management": {"create": false, "read": true, "update": false, "delete": false}, "reports_analysis": {"create": true, "read": true, "update": true, "delete": false}}', 
     true, 
     (SELECT user_id FROM users WHERE role = 'sysadmin' LIMIT 1)),
    ('Document Processor', 'PDF processing and client management', 
     '{"client_management": {"create": false, "read": true, "update": false, "delete": false}, "pdf_processing": {"create": true, "read": true, "update": true, "delete": true}}', 
     true, 
     (SELECT user_id FROM users WHERE role = 'sysadmin' LIMIT 1)),
    ('Full Agent Access', 'Complete access to all agents (except system admin functions)', 
     '{"client_management": {"create": true, "read": true, "update": true, "delete": true}, "pdf_processing": {"create": true, "read": true, "update": true, "delete": true}, "reports_analysis": {"create": true, "read": true, "update": true, "delete": true}, "audio_recording": {"create": true, "read": true, "update": true, "delete": true}}', 
     true, 
     (SELECT user_id FROM users WHERE role = 'sysadmin' LIMIT 1))
ON CONFLICT (template_name) DO NOTHING;
```
