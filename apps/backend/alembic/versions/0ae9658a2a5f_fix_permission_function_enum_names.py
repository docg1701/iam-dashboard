"""fix_permission_function_enum_names

Revision ID: 0ae9658a2a5f
Revises: b2dee6e21ed0
Create Date: 2025-08-05 14:33:04.525156

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0ae9658a2a5f"
down_revision: str | Sequence[str] | None = "b2dee6e21ed0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Fix the database function to use enum names (SYSADMIN, ADMIN) which is how SQLAlchemy stores them
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

            -- Sysadmin bypasses all permission checks (use enum name as stored by SQLAlchemy)
            IF user_role = 'SYSADMIN' THEN
                RETURN TRUE;
            END IF;

            -- Admin inherits full access to client_management and reports_analysis (use enum name)
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


def downgrade() -> None:
    """Downgrade schema."""
    # Revert to lowercase role values
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
            IF user_role = 'sysadmin' THEN
                RETURN TRUE;
            END IF;

            -- Admin inherits full access to client_management and reports_analysis
            IF user_role = 'admin' AND p_agent_name IN ('client_management', 'reports_analysis') THEN
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
