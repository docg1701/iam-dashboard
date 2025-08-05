"""
Test integration between old role-based system and new permission system.

This module tests backward compatibility and ensures that:
1. Sysadmin users bypass all permission checks
2. Admin users inherit full access to client_management and reports_analysis
3. Regular users require explicit permission grants
4. Existing role-based endpoints still work correctly
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.security import check_user_agent_permission
from src.models.permissions import AgentName, UserAgentPermission, UserAgentPermissionCreate
from src.models.user import UserRole
from src.services.permission_service import PermissionService
from src.tests.factories import UserFactory


class TestPermissionSystemIntegration:
    """Test integration between role system and permission system."""

    async def test_sysadmin_bypasses_permission_checks(self, test_session: Session):
        """Test that sysadmin users bypass all permission checks."""
        # Create sysadmin user
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        test_session.add(sysadmin)
        test_session.commit()
        test_session.refresh(sysadmin)

        # Test all agents and operations
        for agent_name in AgentName:
            for operation in ["create", "read", "update", "delete"]:
                has_permission = await check_user_agent_permission(
                    sysadmin.user_id, agent_name.value, operation, test_session
                )
                assert has_permission, (
                    f"Sysadmin should have {operation} access to {agent_name.value}"
                )

    async def test_admin_inherits_client_management_access(self, test_session: Session):
        """Test that admin users inherit full access to client_management."""
        # Create admin user
        admin = UserFactory(role=UserRole.ADMIN)
        test_session.add(admin)
        test_session.commit()
        test_session.refresh(admin)

        # Test client_management access (should inherit)
        for operation in ["create", "read", "update", "delete"]:
            has_permission = await check_user_agent_permission(
                admin.user_id, "client_management", operation, test_session
            )
            assert has_permission, f"Admin should have {operation} access to client_management"

    async def test_admin_inherits_reports_analysis_access(self, test_session: Session):
        """Test that admin users inherit full access to reports_analysis."""
        # Create admin user
        admin = UserFactory(role=UserRole.ADMIN)
        test_session.add(admin)
        test_session.commit()
        test_session.refresh(admin)

        # Test reports_analysis access (should inherit)
        for operation in ["create", "read", "update", "delete"]:
            has_permission = await check_user_agent_permission(
                admin.user_id, "reports_analysis", operation, test_session
            )
            assert has_permission, f"Admin should have {operation} access to reports_analysis"

    async def test_admin_no_access_to_other_agents_without_permissions(self, test_session: Session):
        """Test that admin users don't have access to other agents without explicit permissions."""
        # Create admin user
        admin = UserFactory(role=UserRole.ADMIN)
        test_session.add(admin)
        test_session.commit()
        test_session.refresh(admin)

        # Test pdf_processing access (should not inherit)
        for operation in ["create", "read", "update", "delete"]:
            has_permission = await check_user_agent_permission(
                admin.user_id, "pdf_processing", operation, test_session
            )
            assert not has_permission, (
                f"Admin should not have {operation} access to pdf_processing without explicit grant"
            )

        # Test audio_recording access (should not inherit)
        for operation in ["create", "read", "update", "delete"]:
            has_permission = await check_user_agent_permission(
                admin.user_id, "audio_recording", operation, test_session
            )
            assert not has_permission, (
                f"Admin should not have {operation} access to audio_recording without explicit grant"
            )

    async def test_regular_user_requires_explicit_permissions(self, test_session: Session):
        """Test that regular users require explicit permission grants."""
        # Create regular user
        user = UserFactory(role=UserRole.USER)
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        # Test that user has no access without explicit permissions
        for agent_name in AgentName:
            for operation in ["create", "read", "update", "delete"]:
                has_permission = await check_user_agent_permission(
                    user.user_id, agent_name.value, operation, test_session
                )
                assert not has_permission, (
                    f"Regular user should not have {operation} access to {agent_name.value} without explicit grant"
                )

    async def test_explicit_permission_grants_work(self, test_session: Session):
        """Test that explicit permission grants work for all user types."""
        # Create regular user
        user = UserFactory(role=UserRole.USER)
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        # Grant explicit permission for client_management read
        permission_data = UserAgentPermissionCreate(
            user_id=user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"create": False, "read": True, "update": False, "delete": False},
            created_by_user_id=user.user_id,
        )
        permission = UserAgentPermission.model_validate(permission_data)
        test_session.add(permission)
        test_session.commit()

        # Test that user now has read access
        has_read_permission = await check_user_agent_permission(
            user.user_id, "client_management", "read", test_session
        )
        assert has_read_permission, "User should have read access after explicit grant"

        # Test that user still doesn't have other permissions
        for operation in ["create", "update", "delete"]:
            has_permission = await check_user_agent_permission(
                user.user_id, "client_management", operation, test_session
            )
            assert not has_permission, (
                f"User should not have {operation} access without explicit grant"
            )

    async def test_permission_service_check_matches_database_function(self, test_session: Session):
        """Test that PermissionService results match database function results."""
        # Create users with different roles
        sysadmin = UserFactory(role=UserRole.SYSADMIN)
        admin = UserFactory(role=UserRole.ADMIN)
        user = UserFactory(role=UserRole.USER)

        for user_obj in [sysadmin, admin, user]:
            test_session.add(user_obj)
        test_session.commit()

        # Test a few specific cases
        test_cases = [
            (
                sysadmin.user_id,
                "client_management",
                "create",
                True,
            ),  # Sysadmin should always have access
            (
                admin.user_id,
                "client_management",
                "read",
                True,
            ),  # Admin should inherit client_management
            (
                admin.user_id,
                "reports_analysis",
                "update",
                True,
            ),  # Admin should inherit reports_analysis
            (
                admin.user_id,
                "pdf_processing",
                "create",
                False,
            ),  # Admin should NOT inherit pdf_processing
            (
                user.user_id,
                "client_management",
                "read",
                False,
            ),  # User should NOT have access without explicit grant
        ]

        for user_id, agent_name, operation, expected in test_cases:
            # Check using our security function
            security_result = await check_user_agent_permission(
                user_id, agent_name, operation, test_session
            )

            # Check using permission service
            service = PermissionService()
            try:
                service_result = await service.check_user_permission(
                    user_id, AgentName(agent_name), operation
                )
            finally:
                await service.close()

            assert security_result == expected, (
                f"Security function mismatch for {user_id}, {agent_name}, {operation}"
            )
            assert service_result == expected, (
                f"Permission service mismatch for {user_id}, {agent_name}, {operation}"
            )
            assert security_result == service_result, (
                f"Results don't match for {user_id}, {agent_name}, {operation}"
            )

    def test_client_api_permission_integration(
        self, client: TestClient, authenticated_sysadmin_headers
    ):
        """Test that client API endpoints work with new permission system."""
        # Test that sysadmin can access client endpoints
        response = client.get("/api/v1/clients", headers=authenticated_sysadmin_headers)
        assert response.status_code == status.HTTP_200_OK

        # Test client creation
        client_data = {
            "full_name": "John Doe",
            "ssn": "123-45-6789",
            "birth_date": "1990-01-01",
            "notes": "Test client",
        }
        response = client.post(
            "/api/v1/clients", json=client_data, headers=authenticated_sysadmin_headers
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_user_api_backward_compatibility(self, client: TestClient, authenticated_admin_headers):
        """Test that user API endpoints maintain backward compatibility."""
        # Test that admin can list users (existing behavior)
        response = client.get("/api/v1/users", headers=authenticated_admin_headers)
        assert response.status_code == status.HTTP_200_OK

    async def test_fallback_mechanism_when_permission_service_fails(self, test_session: Session):
        """Test that role-based fallback works when permission service is unavailable."""
        # Create admin user
        admin = UserFactory(role=UserRole.ADMIN)
        test_session.add(admin)
        test_session.commit()
        test_session.refresh(admin)

        # Even if we can't create a proper PermissionService (like in testing scenarios),
        # the fallback mechanism should still work for role-based access
        has_permission = await check_user_agent_permission(
            admin.user_id, "client_management", "read", test_session
        )

        # Should still work due to role-based fallback
        assert has_permission, "Admin should have access via role-based fallback"


class TestBackwardCompatibility:
    """Test that existing role-based code continues to work."""

    def test_require_role_with_fallback_sysadmin(self, authenticated_sysadmin_token_data):
        """Test that sysadmin role check works with fallback."""
        from src.core.security import require_role_with_fallback

        check_role_func = require_role_with_fallback("admin")
        result = check_role_func(authenticated_sysadmin_token_data)
        assert result == authenticated_sysadmin_token_data

    def test_require_role_with_fallback_admin_accessing_user_endpoint(
        self, authenticated_admin_token_data
    ):
        """Test that admin can access user-level endpoints."""
        from src.core.security import require_role_with_fallback

        check_role_func = require_role_with_fallback("user")
        result = check_role_func(authenticated_admin_token_data)
        assert result == authenticated_admin_token_data

    def test_require_role_with_fallback_insufficient_permissions(
        self, authenticated_user_token_data
    ):
        """Test that insufficient permissions are properly rejected."""
        from fastapi import HTTPException

        from src.core.security import require_role_with_fallback

        check_role_func = require_role_with_fallback("admin")

        with pytest.raises(HTTPException) as exc_info:
            check_role_func(authenticated_user_token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
