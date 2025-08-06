#!/usr/bin/env python3

import sys

from sqlalchemy import text

from src.core.database import get_session
from src.models.user import UserRole
from src.tests.factories import UserFactory

# Mock test environment after imports
sys.modules["pytest"] = type(sys)("pytest")  # Mock pytest module


def debug_db_function():
    """Debug the database function step by step."""
    print("=== Database Function Debug ===")

    # Get a database session
    session = next(get_session())

    try:
        # Create a sysadmin user
        print("1. Creating sysadmin user...")
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        session.add(sysadmin)
        session.commit()
        session.refresh(sysadmin)
        print(f"   Created user: {sysadmin.user_id} with role: {sysadmin.role}")

        # Test raw SQL query to check the role value
        print("\n2. Testing raw role query...")
        role_query = text("SELECT role FROM users WHERE user_id = :user_id")
        role_result = session.execute(role_query, {"user_id": str(sysadmin.user_id)})
        role_value = role_result.scalar()
        print(f"   Raw role from DB: '{role_value}' (type: {type(role_value)})")

        # Test the condition directly
        print("\n3. Testing role conditions...")
        cond_query = text("SELECT role = 'sysadmin' as sysadmin_match, role = 'SYSADMIN' as upper_match FROM users WHERE user_id = :user_id")
        cond_result = session.execute(cond_query, {"user_id": str(sysadmin.user_id)})
        cond_row = cond_result.fetchone()
        print(f"   role = 'sysadmin': {cond_row.sysadmin_match}")
        print(f"   role = 'SYSADMIN': {cond_row.upper_match}")

        # Test the database function step by step
        print("\n4. Testing DB function manually...")
        manual_query = text("""
            SELECT
                role,
                (role = 'sysadmin') as is_sysadmin_lower,
                (role = 'SYSADMIN') as is_sysadmin_upper,
                CASE
                    WHEN role = 'sysadmin' THEN TRUE
                    WHEN role = 'admin' AND :agent_name IN ('client_management', 'reports_analysis') THEN TRUE
                    ELSE FALSE
                END as manual_result
            FROM users
            WHERE user_id = :user_id
        """)
        manual_result = session.execute(manual_query, {
            "user_id": str(sysadmin.user_id),
            "agent_name": "client_management"
        })
        manual_row = manual_result.fetchone()
        print(f"   Role: '{manual_row.role}'")
        print(f"   Is sysadmin (lower): {manual_row.is_sysadmin_lower}")
        print(f"   Is sysadmin (upper): {manual_row.is_sysadmin_upper}")
        print(f"   Manual result: {manual_row.manual_result}")

        # Test the actual function
        print("\n5. Testing actual database function...")
        func_query = text("SELECT check_user_agent_permission(:user_id, :agent_name, :operation)")
        func_result = session.execute(func_query, {
            "user_id": str(sysadmin.user_id),
            "agent_name": "client_management",
            "operation": "create"
        })
        func_value = func_result.scalar()
        print(f"   Function result: {func_value}")

    finally:
        session.close()

if __name__ == "__main__":
    debug_db_function()
