# Database Schema

Complete PostgreSQL 16.x + pgvector schema with proper indexing, constraints, and relationships optimized for the multi-agent architecture:

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

-- Clients table (Agent 1 primary responsibility)
CREATE TABLE clients (
    client_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    ssn VARCHAR(11) NOT NULL UNIQUE, -- Format: XXX-XX-XXXX
    birth_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    notes TEXT,
    created_by UUID NOT NULL REFERENCES users(user_id),
    updated_by UUID NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT clients_ssn_format CHECK (ssn ~ '^\d{3}-\d{2}-\d{4}$'),
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
        table_name IN ('users', 'clients', 'agent2_documents', 'agent3_reports', 'agent4_recordings')
    )
);

-- Performance indexes
CREATE INDEX idx_clients_full_name ON clients USING gin(to_tsvector('english', full_name));
CREATE INDEX idx_clients_ssn ON clients(ssn);
CREATE INDEX idx_clients_status ON clients(status);
CREATE INDEX idx_clients_created_at ON clients(created_at DESC);

CREATE INDEX idx_documents_client_id ON agent2_documents(client_id);
CREATE INDEX idx_documents_status ON agent2_documents(processing_status);
CREATE INDEX idx_documents_vector_chunks ON agent2_documents USING gin(vector_chunks);

CREATE INDEX idx_audit_table_name ON audit_log(table_name);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);

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
```
