"""Consolidated IAM Dashboard Schema - Production Ready

Single consolidated migration for production deployment.
Includes complete schema with security fields and JSONB permissions.

Revision ID: 001_consolidated_initial_schema
Revises:
Create Date: 2025-08-09 02:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_consolidated_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create complete IAM Dashboard schema - production ready."""

    # Enable required PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Create custom enum types
    op.execute("CREATE TYPE userrole AS ENUM ('SYSADMIN', 'ADMIN', 'USER')")
    op.execute("CREATE TYPE clientstatus AS ENUM ('ACTIVE', 'INACTIVE', 'ARCHIVED')")
    op.execute(
        "CREATE TYPE agentname AS ENUM ('client_management', 'pdf_processing', 'reports_analysis', 'audio_recording')"
    )
    op.execute("CREATE TYPE auditaction AS ENUM ('CREATE', 'UPDATE', 'DELETE', 'VIEW')")

    # Create users table with security fields
    op.create_table(
        "users",
        sa.Column(
            "user_id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v4()")
        ),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("password_hash", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("role", sa.Enum("SYSADMIN", "ADMIN", "USER", name="userrole"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("totp_secret", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("totp_backup_codes", JSONB(), nullable=True),
        sa.Column(
            "failed_login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("account_locked_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint(
            r"email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'",
            name="users_email_format",
        ),
        sa.CheckConstraint("length(password_hash) >= 60", name="users_password_length"),
        sa.CheckConstraint("failed_login_attempts >= 0", name="users_failed_attempts_positive"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_active", "users", ["is_active"])

    # Create clients table with CPF format
    op.create_table(
        "agent1_clients",
        sa.Column(
            "client_id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v4()")
        ),
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("cpf", sqlmodel.sql.sqltypes.AutoString(length=14), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", "ARCHIVED", name="clientstatus"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("notes", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("client_id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], name="fk_clients_created_by"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.user_id"], name="fk_clients_updated_by"),
        sa.CheckConstraint("cpf ~ '^\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}$'", name="clients_cpf_format"),
        sa.CheckConstraint("length(trim(full_name)) >= 2", name="clients_name_length"),
        sa.CheckConstraint(
            "birth_date >= '1900-01-01' AND birth_date <= CURRENT_DATE - INTERVAL '13 years'",
            name="clients_birth_date_range",
        ),
    )
    op.create_index("ix_agent1_clients_cpf", "agent1_clients", ["cpf"], unique=True)
    op.create_index("ix_agent1_clients_full_name", "agent1_clients", ["full_name"])
    op.create_index("ix_agent1_clients_status", "agent1_clients", ["status"])
    op.create_index("ix_agent1_clients_created_at", "agent1_clients", ["created_at"])

    # Create user agent permissions table with JSONB
    op.create_table(
        "user_agent_permissions",
        sa.Column(
            "permission_id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v4()")
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "agent_name",
            sa.Enum(
                "client_management",
                "pdf_processing",
                "reports_analysis",
                "audio_recording",
                name="agentname",
            ),
            nullable=False,
        ),
        sa.Column(
            "permissions",
            JSONB(),
            nullable=False,
            server_default='{"create": false, "read": false, "update": false, "delete": false}',
        ),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("permission_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.user_id"]),
        sa.UniqueConstraint("user_id", "agent_name", name="uq_user_agent_permissions"),
        sa.CheckConstraint(
            """
            jsonb_typeof(permissions) = 'object' AND
            permissions ? 'create' AND jsonb_typeof(permissions->'create') = 'boolean' AND
            permissions ? 'read' AND jsonb_typeof(permissions->'read') = 'boolean' AND
            permissions ? 'update' AND jsonb_typeof(permissions->'update') = 'boolean' AND
            permissions ? 'delete' AND jsonb_typeof(permissions->'delete') = 'boolean'
        """,
            name="permissions_jsonb_structure",
        ),
    )
    op.create_index("ix_user_agent_permissions_user_id", "user_agent_permissions", ["user_id"])
    op.create_index(
        "ix_user_agent_permissions_agent_name", "user_agent_permissions", ["agent_name"]
    )
    op.create_index(
        "ix_user_agent_permissions_user_agent",
        "user_agent_permissions",
        ["user_id", "agent_name"],
        unique=True,
    )
    op.create_index(
        "ix_user_agent_permissions_created_at", "user_agent_permissions", ["created_at"]
    )

    # Create permission templates table with JSONB
    op.create_table(
        "permission_templates",
        sa.Column(
            "template_id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v4()")
        ),
        sa.Column("template_name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("permissions", JSONB(), nullable=False),
        sa.Column(
            "is_system_template", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("template_id"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.user_id"]),
        sa.UniqueConstraint("template_name"),
        sa.CheckConstraint("length(trim(template_name)) >= 3", name="template_name_length"),
    )
    op.create_index(
        "ix_permission_templates_name", "permission_templates", ["template_name"], unique=True
    )
    op.create_index(
        "ix_permission_templates_system", "permission_templates", ["is_system_template"]
    )
    op.create_index("ix_permission_templates_created_at", "permission_templates", ["created_at"])

    # Create permission audit log table with JSONB
    op.create_table(
        "permission_audit_log",
        sa.Column(
            "audit_id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v4()")
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "agent_name",
            sa.Enum(
                "client_management",
                "pdf_processing",
                "reports_analysis",
                "audio_recording",
                name="agentname",
            ),
            nullable=False,
        ),
        sa.Column("action", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("old_permissions", JSONB(), nullable=True),
        sa.Column("new_permissions", JSONB(), nullable=True),
        sa.Column("changed_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("change_reason", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("audit_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.user_id"]),
        sa.CheckConstraint(
            "action IN ('CREATE', 'UPDATE', 'DELETE', 'BULK_ASSIGN')", name="audit_action_valid"
        ),
    )
    op.create_index("ix_permission_audit_user_id", "permission_audit_log", ["user_id"])
    op.create_index("ix_permission_audit_agent_name", "permission_audit_log", ["agent_name"])
    op.create_index("ix_permission_audit_action", "permission_audit_log", ["action"])
    op.create_index(
        "ix_permission_audit_changed_by", "permission_audit_log", ["changed_by_user_id"]
    )
    op.create_index("ix_permission_audit_created_at", "permission_audit_log", ["created_at"])
    op.create_index(
        "ix_permission_audit_user_agent", "permission_audit_log", ["user_id", "agent_name"]
    )

    # Create trigger function for automatic timestamp updates
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """)

    # Create triggers for automatic updated_at
    op.execute(
        "CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"
    )
    op.execute(
        "CREATE TRIGGER update_agent1_clients_updated_at BEFORE UPDATE ON agent1_clients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"
    )
    op.execute(
        "CREATE TRIGGER update_user_agent_permissions_updated_at BEFORE UPDATE ON user_agent_permissions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"
    )
    op.execute(
        "CREATE TRIGGER update_permission_templates_updated_at BEFORE UPDATE ON permission_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"
    )


def downgrade() -> None:
    """Drop all tables, functions and types."""

    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users;")
    op.execute("DROP TRIGGER IF EXISTS update_agent1_clients_updated_at ON agent1_clients;")
    op.execute(
        "DROP TRIGGER IF EXISTS update_user_agent_permissions_updated_at ON user_agent_permissions;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS update_permission_templates_updated_at ON permission_templates;"
    )

    # Drop tables
    op.drop_table("permission_audit_log")
    op.drop_table("permission_templates")
    op.drop_table("user_agent_permissions")
    op.drop_table("agent1_clients")
    op.drop_table("users")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;")

    # Drop custom enum types
    op.execute("DROP TYPE IF EXISTS userrole CASCADE;")
    op.execute("DROP TYPE IF EXISTS clientstatus CASCADE;")
    op.execute("DROP TYPE IF EXISTS agentname CASCADE;")
    op.execute("DROP TYPE IF EXISTS auditaction CASCADE;")
