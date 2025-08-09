"""
Integration tests for Permission API endpoints to improve coverage.

This module tests the actual API endpoints with real services to achieve better
coverage of the API layer code.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.api.v1.permissions import get_permission_service
from src.core.database import get_session
from src.main import app
from src.models.user import User, UserRole
from src.services.permission_service import PermissionService
from src.tests.factories import create_test_template, create_test_user


class TestPermissionAPIIntegration:
    """Integration tests for permission API endpoints with real services."""

    @pytest.fixture
    def real_permission_service(self, test_session: Session) -> PermissionService:
        """Create a real PermissionService for integration testing."""
        return PermissionService(session=test_session)

    @pytest.fixture
    def test_admin(self, test_engine) -> User:
        """Create an admin user for testing."""
        user = create_test_user(role=UserRole.ADMIN)
        # Create a separate session to commit the user to the database
        with Session(test_engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

    @pytest.fixture
    def test_regular_user(self, test_engine) -> User:
        """Create a regular user for testing."""
        user = create_test_user(role=UserRole.USER)
        # Create a separate session to commit the user to the database
        with Session(test_engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

    @pytest.fixture(autouse=True)
    def setup_real_service(self, test_engine, test_admin: User) -> None:
        """Setup real permission service for tests."""

        def get_real_permission_service() -> PermissionService:
            # Don't inject session - let it use the dependency system
            service = PermissionService()
            service._is_testing = True  # Enable test mode
            return service

        def get_mock_current_user() -> User:
            # Return the actual test admin user instead of a random mock user
            return test_admin

        def get_test_session_for_service():
            # Create a session from the test engine
            session = Session(test_engine)
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_permission_service] = get_real_permission_service
        # E2E tests should use real authentication - NO AUTH BYPASS
        # Use real JWT tokens from authenticated_admin_headers fixture
        app.dependency_overrides[get_session] = get_test_session_for_service

    @pytest.mark.usefixtures("test_admin")
    def test_check_permission_endpoint_success(
        self,
        client: TestClient,
        test_regular_user: User,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test check permission endpoint with real service."""
        user_id = test_regular_user.user_id

        # Test sysadmin user (should have all permissions)
        response = client.get(
            f"/api/v1/permissions/check?user_id={user_id}&agent_name=client_management&operation=create",
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "granted" in data
        assert data["user_id"] == str(user_id)
        assert data["agent_name"] == "client_management"
        assert data["operation"] == "create"

    def test_check_permission_invalid_uuid(
        self,
        client: TestClient,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test check permission with invalid UUID format."""
        response = client.get(
            "/api/v1/permissions/check?user_id=invalid-uuid&agent_name=client_management&operation=create",
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_get_user_permissions_endpoint(
        self,
        client: TestClient,
        test_regular_user: User,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test get user permissions endpoint."""
        user_id = test_regular_user.user_id

        response = client.get(
            f"/api/v1/permissions/user/{user_id}",
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "permissions" in data
        assert data["user_id"] == str(user_id)

    def test_assign_permission_endpoint(
        self,
        client: TestClient,
        test_regular_user: User,
        test_session: Session,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test assign permission endpoint."""
        user_id = test_regular_user.user_id

        # Ensure all data is flushed and available
        test_session.flush()

        request_data = {
            "user_id": str(user_id),
            "agent_name": "client_management",
            "permissions": {"create": True, "read": True, "update": False, "delete": False},
            # assigned_by_user_id comes from current_user in the API, not the request
            "change_reason": "Test assignment",
        }

        response = client.post(
            "/api/v1/permissions/assign",
            json=request_data,
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Check that the permission was created successfully
        assert "user_id" in data
        assert data["user_id"] == str(user_id)
        assert data["agent_name"] == "client_management"
        assert "permissions" in data

    def test_revoke_permission_endpoint(
        self,
        client: TestClient,
        test_regular_user: User,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test revoke permission endpoint."""
        user_id = test_regular_user.user_id

        # First assign a permission to revoke
        request_data = {
            "user_id": str(user_id),
            "agent_name": "client_management",
            "permissions": {"create": True, "read": True, "update": False, "delete": False},
            "change_reason": "Test assignment",
        }

        assign_response = client.post(
            "/api/v1/permissions/assign",
            json=request_data,
            headers=authenticated_admin_headers,
        )
        assert assign_response.status_code == 200

        # Now revoke it using the correct endpoint
        response = client.delete(
            f"/api/v1/permissions/user/{user_id}/agent/client_management",
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Check that the revocation was successful
        assert "message" in data
        assert "successfully" in data["message"].lower()

    def test_bulk_assign_permissions_endpoint(
        self,
        client: TestClient,
        test_regular_user: User,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test bulk assign permissions endpoint."""
        user_ids = [str(test_regular_user.user_id)]

        request_data = {
            "user_ids": user_ids,
            "agent_name": "client_management",
            "permissions": {"create": True, "read": True, "update": False, "delete": False},
            "change_reason": "Bulk test assignment",
        }

        response = client.post(
            "/api/v1/permissions/bulk-assign",
            json=request_data,
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Check bulk operation response structure
        assert "operation_id" in data
        assert "completed_at" in data
        assert "errors" in data

    def test_list_templates_endpoint(
        self,
        client: TestClient,
        test_session: Session,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test list templates endpoint."""
        # Create a test template
        template = create_test_template(template_name="Test Template", is_system=False)
        test_session.add(template)
        test_session.commit()

        response = client.get(
            "/api/v1/permissions/templates",
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Check pagination structure
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert "total" in data

    def test_create_template_endpoint(
        self,
        client: TestClient,
        test_admin: User,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test create template endpoint."""
        request_data = {
            "template_name": "New Test Template",
            "description": "A template for testing",
            "permissions": {
                "client_management": {
                    "create": True,
                    "read": True,
                    "update": False,
                    "delete": False,
                }
            },
            "is_system": False,
            "created_by_user_id": str(test_admin.user_id),
        }

        response = client.post(
            "/api/v1/permissions/templates",
            json=request_data,
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["template_name"] == "New Test Template"
        assert data["description"] == "A template for testing"

    def test_update_template_endpoint(
        self,
        client: TestClient,
        test_session: Session,
        test_admin: User,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test update template endpoint."""
        # Create a template to update
        template = create_test_template(template_name="Update Test Template", is_system=False)
        test_session.add(template)
        test_session.commit()
        test_session.refresh(template)

        request_data = {
            "template_name": "Updated Template Name",
            "description": "Updated description",
            "permissions": {
                "client_management": {
                    "create": False,
                    "read": True,
                    "update": True,
                    "delete": False,
                }
            },
            "updated_by_user_id": str(test_admin.user_id),
        }

        response = client.put(
            f"/api/v1/permissions/templates/{template.template_id}",
            json=request_data,
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["template_name"] == "Updated Template Name"
        assert data["description"] == "Updated description"

    def test_delete_template_endpoint(
        self,
        client: TestClient,
        test_session: Session,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test delete template endpoint."""
        # Create a template to delete
        template = create_test_template(template_name="Delete Test Template", is_system=False)
        test_session.add(template)
        test_session.commit()
        test_session.refresh(template)

        response = client.delete(
            f"/api/v1/permissions/templates/{template.template_id}?reason=Test+deletion",
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_audit_log_endpoint(
        self,
        client: TestClient,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test get audit log endpoint."""
        response = client.get(
            "/api/v1/permissions/audit",
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Check pagination structure
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert "total" in data

    def test_get_permission_stats_endpoint(
        self,
        client: TestClient,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test get permission stats endpoint."""
        response = client.get(
            "/api/v1/permissions/stats",
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Check expected stats fields
        assert "total_users" in data
        assert "agent_usage" in data
        assert "recent_changes" in data
        # Check what fields are actually returned
        # print(data.keys())  # For debugging

    def test_validation_errors(
        self,
        client: TestClient,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test validation error handling."""
        # Test with missing required fields
        response = client.post(
            "/api/v1/permissions/assign",
            json={},  # Empty request
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 422

    def test_invalid_agent_name_handling(
        self,
        client: TestClient,
        test_regular_user: User,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test handling of invalid agent names."""
        user_id = test_regular_user.user_id

        response = client.get(
            f"/api/v1/permissions/check?user_id={user_id}&agent_name=invalid_agent&operation=create",
            headers=authenticated_admin_headers,
        )

        # Should return 422 for invalid enum value
        assert response.status_code == 422

    def test_pagination_parameters(
        self,
        client: TestClient,
        authenticated_admin_headers: dict[str, str],
    ) -> None:
        """Test pagination parameters in list endpoints."""
        # Test templates list with pagination
        response = client.get(
            "/api/v1/permissions/templates?page=1&page_size=5",
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200

        # Test audit log with pagination
        response = client.get(
            "/api/v1/permissions/audit?page=1&page_size=10",
            headers=authenticated_admin_headers,
        )

        assert response.status_code == 200
