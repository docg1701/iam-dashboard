"""add_user_agent_permissions_system

Revision ID: 9b632b3132c3
Revises: 5522e7954293
Create Date: 2025-08-04 14:19:32.997221

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9b632b3132c3"
down_revision: str | Sequence[str] | None = "5522e7954293"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create user_agent_permissions table
    op.create_table(
        "user_agent_permissions",
        sa.Column(
            "permission_id",
            sa.UUID(),
            nullable=False,
            primary_key=True,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("agent_name", sa.VARCHAR(50), nullable=False),
        sa.Column(
            "permissions",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            default=sa.text(
                '\'{"create": false, "read": false, "update": false, "delete": false}\''
            ),
        ),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, default=sa.text("NOW()")
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"], name="fk_user_agent_permissions_user_id"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.user_id"], name="fk_user_agent_permissions_created_by"
        ),
        sa.CheckConstraint(
            "agent_name IN ('client_management', 'pdf_processing', 'reports_analysis', 'audio_recording')",
            name="check_agent_name_valid",
        ),
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
        sa.UniqueConstraint("user_id", "agent_name", name="uq_user_agent_permissions_user_agent"),
    )

    # Create indexes for user_agent_permissions
    op.create_index("ix_user_agent_permissions_user_id", "user_agent_permissions", ["user_id"])
    op.create_index(
        "ix_user_agent_permissions_agent_name", "user_agent_permissions", ["agent_name"]
    )
    op.create_index(
        "ix_user_agent_permissions_created_at", "user_agent_permissions", ["created_at"]
    )

    # Create permission_templates table
    op.create_table(
        "permission_templates",
        sa.Column(
            "template_id",
            sa.UUID(),
            nullable=False,
            primary_key=True,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("template_name", sa.VARCHAR(100), nullable=False, unique=True),
        sa.Column("description", sa.TEXT(), nullable=True),
        sa.Column("permissions", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("is_system_template", sa.BOOLEAN(), nullable=False, default=False),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, default=sa.text("NOW()")
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.user_id"], name="fk_permission_templates_created_by"
        ),
    )

    # Create indexes for permission_templates
    op.create_index(
        "ix_permission_templates_name", "permission_templates", ["template_name"], unique=True
    )
    op.create_index(
        "ix_permission_templates_system", "permission_templates", ["is_system_template"]
    )
    op.create_index("ix_permission_templates_created_at", "permission_templates", ["created_at"])

    # Create permission_audit_log table
    op.create_table(
        "permission_audit_log",
        sa.Column(
            "audit_id",
            sa.UUID(),
            nullable=False,
            primary_key=True,
            default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("agent_name", sa.VARCHAR(50), nullable=False),
        sa.Column("action", sa.VARCHAR(50), nullable=False),
        sa.Column("old_permissions", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("new_permissions", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("changed_by_user_id", sa.UUID(), nullable=False),
        sa.Column("change_reason", sa.VARCHAR(255), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_permission_audit_user_id"),
        sa.ForeignKeyConstraint(
            ["changed_by_user_id"], ["users.user_id"], name="fk_permission_audit_changed_by"
        ),
        sa.CheckConstraint(
            "agent_name IN ('client_management', 'pdf_processing', 'reports_analysis', 'audio_recording')",
            name="check_audit_agent_name_valid",
        ),
    )

    # Create indexes for permission_audit_log
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

    # Create database functions for permission checking
    op.execute("""
        CREATE OR REPLACE FUNCTION check_user_agent_permission(
            p_user_id UUID,
            p_agent_name VARCHAR,
            p_operation VARCHAR
        ) RETURNS BOOLEAN AS $$
        DECLARE
            user_role VARCHAR;
            permission_granted BOOLEAN := FALSE;
        BEGIN
            -- Get user role
            SELECT role INTO user_role FROM users WHERE user_id = p_user_id;

            -- Sysadmin bypasses all permission checks
            IF user_role = 'SYSADMIN' THEN
                RETURN TRUE;
            END IF;

            -- Admin inherits full access to client_management and reports_analysis
            IF user_role = 'ADMIN' AND p_agent_name IN ('client_management', 'reports_analysis') THEN
                RETURN TRUE;
            END IF;

            -- Check explicit permission grants
            SELECT COALESCE((permissions->>p_operation)::BOOLEAN, FALSE)
            INTO permission_granted
            FROM user_agent_permissions
            WHERE user_id = p_user_id AND agent_name = p_agent_name;

            RETURN COALESCE(permission_granted, FALSE);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION get_user_permission_matrix(p_user_id UUID)
        RETURNS TABLE(
            agent_name VARCHAR,
            create_permission BOOLEAN,
            read_permission BOOLEAN,
            update_permission BOOLEAN,
            delete_permission BOOLEAN
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT
                agent.agent_name,
                check_user_agent_permission(p_user_id, agent.agent_name, 'create') as create_permission,
                check_user_agent_permission(p_user_id, agent.agent_name, 'read') as read_permission,
                check_user_agent_permission(p_user_id, agent.agent_name, 'update') as update_permission,
                check_user_agent_permission(p_user_id, agent.agent_name, 'delete') as delete_permission
            FROM (VALUES
                ('client_management'::VARCHAR),
                ('pdf_processing'::VARCHAR),
                ('reports_analysis'::VARCHAR),
                ('audio_recording'::VARCHAR)
            ) AS agent(agent_name);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    # Note: Permission templates will be created by the application service
    # when users are available to assign as creators


def downgrade() -> None:
    """Downgrade schema."""
    # Drop database functions
    op.execute("DROP FUNCTION IF EXISTS get_user_permission_matrix(UUID);")
    op.execute("DROP FUNCTION IF EXISTS check_user_agent_permission(UUID, VARCHAR, VARCHAR);")

    # Drop tables in reverse order
    op.drop_table("permission_audit_log")
    op.drop_table("permission_templates")
    op.drop_table("user_agent_permissions")
