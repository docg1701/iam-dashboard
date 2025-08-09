"""fix_user_role_case_in_permission_functions

Revision ID: b2dee6e21ed0
Revises: 9b632b3132c3
Create Date: 2025-08-05 14:31:20.695472

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2dee6e21ed0"
down_revision: str | Sequence[str] | None = "9b632b3132c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Fix the database function to use lowercase role values to match the application
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

            -- Sysadmin bypasses all permission checks (lowercase to match UserRole enum)
            IF user_role = 'sysadmin' THEN
                RETURN TRUE;
            END IF;

            -- Admin inherits full access to client_management and reports_analysis (lowercase)
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


def downgrade() -> None:
    """Downgrade schema."""
    # Revert to uppercase role values
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
