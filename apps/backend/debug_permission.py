#!/usr/bin/env python3

import asyncio
import sys

from sqlalchemy import text
from sqlmodel import select

from src.core.database import get_session
from src.core.security import check_user_agent_permission
from src.models.permissions import AgentName
from src.models.user import User, UserRole
from src.services.permission_service import PermissionService
from src.tests.factories import UserFactory

# Mock test environment after imports
sys.modules["pytest"] = type(sys)("pytest")  # Mock pytest module


async def debug_permission():
    """Debug the permission system step by step."""
    print("=== Permission System Debug ===")

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

        # Test the database function directly
        print("\n2. Testing database function directly...")
        query = text("SELECT check_user_agent_permission(:user_id, :agent_name, :operation)")
        result = session.execute(query, {
            "user_id": str(sysadmin.user_id),
            "agent_name": "client_management",
            "operation": "create"
        })
        db_result = result.scalar()
        print(f"   Database function result: {db_result}")

        # Test the permission service
        print("\n3. Testing permission service...")
        permission_service = PermissionService(session=session)
        try:
            service_result = await permission_service.check_user_permission(
                sysadmin.user_id, AgentName.CLIENT_MANAGEMENT, "create"
            )
            print(f"   Permission service result: {service_result}")
        finally:
            await permission_service.close()

        # Test the security function
        print("\n4. Testing security function...")
        security_result = await check_user_agent_permission(
            sysadmin.user_id, "client_management", "create", session
        )
        print(f"   Security function result: {security_result}")

        # Check the user's role in the database
        print("\n5. Verifying user role in database...")
        user_from_db = session.exec(select(User).where(User.user_id == sysadmin.user_id)).first()
        print(f"   User from DB role: {user_from_db.role if user_from_db else 'None'}")
        print(f"   User from DB role value: {user_from_db.role.value if user_from_db else 'None'}")

    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(debug_permission())
