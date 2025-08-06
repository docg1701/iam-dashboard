#!/usr/bin/env python3

import asyncio
import builtins
import contextlib
import sys

from src.core.database import get_session
from src.core.security import check_user_agent_permission
from src.models.permissions import AgentName
from src.models.user import UserRole
from src.tests.factories import UserFactory

# Mock test environment after imports to ensure proper pytest detection
sys.modules["pytest"] = type(sys)("pytest")
sys.argv = ["test"]  # Ensure test mode is detected


async def debug_test_env():
    """Debug the permission system in test environment similar to actual tests."""
    print("=== Test Environment Debug ===")

    # Use same session pattern as tests
    session_gen = get_session()
    session = next(session_gen)

    try:
        # Create a sysadmin user exactly like the test does
        print("1. Creating sysadmin user like in test...")
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        session.add(sysadmin)
        session.commit()
        session.refresh(sysadmin)
        print(f"   Created user: {sysadmin.user_id} with role: {sysadmin.role}")

        # Test just like the integration test does
        print("\n2. Testing exactly like integration test...")
        for agent_name in AgentName:
            for operation in ["create", "read", "update", "delete"]:
                has_permission = await check_user_agent_permission(
                    sysadmin.user_id, agent_name.value, operation, session
                )
                print(f"   {agent_name.value} {operation}: {has_permission}")
                if not has_permission:
                    print(f"   ❌ FAILED: Sysadmin should have {operation} access to {agent_name.value}")
                    return

        print("✅ All permission checks passed!")

    finally:
        with contextlib.suppress(builtins.BaseException):
            session.close()

if __name__ == "__main__":
    asyncio.run(debug_test_env())
