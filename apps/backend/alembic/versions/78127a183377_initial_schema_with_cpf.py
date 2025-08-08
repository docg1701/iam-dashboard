"""initial_schema_with_cpf - Complete IAM Dashboard schema with CPF format

Single consolidated migration for development environment.
Creates all tables with final schema including CPF format for clients.

Revision ID: 78127a183377
Revises: 
Create Date: 2025-08-08 06:55:15.061191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '78127a183377'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complete IAM Dashboard schema with CPF format."""
    
    # Enable required extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('password_hash', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('role', sa.Enum('SYSADMIN', 'ADMIN', 'USER', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('totp_secret', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('totp_backup_codes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'", name='users_email_format'),
        sa.CheckConstraint("length(password_hash) >= 60", name='users_password_length')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create clients table with CPF format
    op.create_table(
        'agent1_clients',
        sa.Column('client_id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('cpf', sqlmodel.sql.sqltypes.AutoString(length=14), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'ARCHIVED', name='clientstatus'), nullable=False, server_default='ACTIVE'),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('updated_by', sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint('client_id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name='fk_clients_created_by'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], name='fk_clients_updated_by'),
        sa.CheckConstraint("cpf ~ '^\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}$'", name='clients_cpf_format'),
        sa.CheckConstraint("length(trim(full_name)) >= 2", name='clients_name_length'),
        sa.CheckConstraint("birth_date >= '1900-01-01' AND birth_date <= CURRENT_DATE - INTERVAL '13 years'", name='clients_birth_date_range')
    )
    op.create_index('ix_agent1_clients_cpf_unique', 'agent1_clients', ['cpf'], unique=True)
    op.create_index('ix_agent1_clients_full_name', 'agent1_clients', ['full_name'])
    op.create_index('ix_agent1_clients_status', 'agent1_clients', ['status'])
    op.create_index('ix_agent1_clients_created_at', 'agent1_clients', ['created_at'])

    # Create user agent permissions table  
    op.create_table(
        'user_agent_permissions',
        sa.Column('permission_id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('agent_name', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_by_user_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('permission_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.user_id']),
        sa.UniqueConstraint('user_id', 'agent_name'),
        sa.CheckConstraint("agent_name IN ('client_management', 'pdf_processing', 'reports_analysis', 'audio_recording')", name='valid_agent_name'),
        sa.CheckConstraint("""
            jsonb_typeof(permissions::jsonb) = 'object' AND
            permissions::jsonb ? 'create' AND jsonb_typeof(permissions::jsonb->'create') = 'boolean' AND
            permissions::jsonb ? 'read' AND jsonb_typeof(permissions::jsonb->'read') = 'boolean' AND
            permissions::jsonb ? 'update' AND jsonb_typeof(permissions::jsonb->'update') = 'boolean' AND
            permissions::jsonb ? 'delete' AND jsonb_typeof(permissions::jsonb->'delete') = 'boolean'
        """, name='permissions_jsonb_structure')
    )
    op.create_index('ix_user_agent_permissions_user_id', 'user_agent_permissions', ['user_id'])
    op.create_index('ix_user_agent_permissions_agent_name', 'user_agent_permissions', ['agent_name'])
    op.create_index('ix_user_agent_permissions_composite', 'user_agent_permissions', ['user_id', 'agent_name'])

    # Create permission templates table
    op.create_table(
        'permission_templates',
        sa.Column('template_id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('template_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=False),
        sa.Column('is_system_template', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_by_user_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('template_id'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.user_id']),
        sa.UniqueConstraint('template_name'),
        sa.CheckConstraint("length(trim(template_name)) >= 3", name='template_name_length')
    )
    op.create_index('ix_permission_templates_name', 'permission_templates', ['template_name'])
    op.create_index('ix_permission_templates_system', 'permission_templates', ['is_system_template'])

    # Create audit log table
    op.create_table(
        'audit_log',
        sa.Column('audit_id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('table_name', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('record_id', sa.Uuid(), nullable=False),
        sa.Column('action', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('audit_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.CheckConstraint("action IN ('CREATE', 'UPDATE', 'DELETE', 'VIEW')", name='audit_action_valid'),
        sa.CheckConstraint("table_name IN ('users', 'agent1_clients', 'user_agent_permissions', 'permission_templates')", name='audit_table_name_valid')
    )
    op.create_index('ix_audit_table_name', 'audit_log', ['table_name'])
    op.create_index('ix_audit_timestamp', 'audit_log', ['timestamp'])
    op.create_index('ix_audit_user_id', 'audit_log', ['user_id'])

    # Create permission audit log table
    op.create_table(
        'permission_audit_log',
        sa.Column('audit_id', sa.Uuid(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('agent_name', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('action', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('old_permissions', sa.JSON(), nullable=True),
        sa.Column('new_permissions', sa.JSON(), nullable=True),
        sa.Column('changed_by_user_id', sa.Uuid(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('audit_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['changed_by_user_id'], ['users.user_id']),
        sa.CheckConstraint("action IN ('GRANT', 'REVOKE', 'UPDATE', 'BULK_GRANT', 'BULK_REVOKE', 'TEMPLATE_APPLIED')", name='permission_audit_action_valid'),
        sa.CheckConstraint("agent_name IN ('client_management', 'pdf_processing', 'reports_analysis', 'audio_recording')", name='permission_audit_agent_valid')
    )
    op.create_index('ix_permission_audit_user_id', 'permission_audit_log', ['user_id'])
    op.create_index('ix_permission_audit_agent', 'permission_audit_log', ['agent_name'])
    op.create_index('ix_permission_audit_timestamp', 'permission_audit_log', ['timestamp'])
    op.create_index('ix_permission_audit_changed_by', 'permission_audit_log', ['changed_by_user_id'])

    # Create trigger functions for automatic timestamp updates
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)
    
    # Create triggers
    op.execute("CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER update_agent1_clients_updated_at BEFORE UPDATE ON agent1_clients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER update_user_agent_permissions_updated_at BEFORE UPDATE ON user_agent_permissions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")
    op.execute("CREATE TRIGGER update_permission_templates_updated_at BEFORE UPDATE ON permission_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();")

    # Create permission checking functions
    op.execute("""
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
        IF user_role = 'SYSADMIN' THEN
            RETURN true;
        END IF;
        
        -- Admin has access to client_management and reports_analysis
        IF user_role = 'ADMIN' AND p_agent_name IN ('client_management', 'reports_analysis') THEN
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
    """)

    op.execute("""
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
    """)


def downgrade() -> None:
    """Drop all tables and functions."""
    op.drop_table('permission_audit_log')
    op.drop_table('audit_log')
    op.drop_table('permission_templates')
    op.drop_table('user_agent_permissions')
    op.drop_table('agent1_clients')
    op.drop_table('users')
    
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;')
    op.execute('DROP FUNCTION IF EXISTS check_user_agent_permission(UUID, VARCHAR(50), VARCHAR(10)) CASCADE;')
    op.execute('DROP FUNCTION IF EXISTS get_user_permission_matrix(UUID) CASCADE;')
    
    op.execute('DROP TYPE IF EXISTS userrole CASCADE;')
    op.execute('DROP TYPE IF EXISTS clientstatus CASCADE;')