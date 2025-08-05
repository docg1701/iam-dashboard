"""
Tests for Permission API endpoints.

This module tests all permission-related API routes including
validation, authorization, error handling, and response formatting.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.core.security import TokenData
from src.models.permissions import AgentName
from src.models.user import UserRole
from src.services.permission_service import PermissionService
from src.tests.factories import (
    create_test_permission,
    create_test_template,
)


class TestPermissionAPI:
    """Tests for permission API endpoints."""

    @pytest.fixture
    def mock_permission_service(self) -> MagicMock:
        """Create a mock permission service."""
        service = MagicMock(spec=PermissionService)

        # Set up async methods
        service.check_user_permission = AsyncMock()
        service.get_user_permissions = AsyncMock()
        service.assign_permission = AsyncMock()
        service.revoke_permission = AsyncMock()
        service.bulk_assign_permissions = AsyncMock()
        service.apply_template_to_users = AsyncMock()
        service.list_templates = AsyncMock()
        service.create_template = AsyncMock()
        service.update_template = AsyncMock()
        service.delete_template = AsyncMock()
        service.get_audit_log = AsyncMock()
        service.get_permission_stats = AsyncMock()

        return service

    @pytest.fixture
    def sysadmin_user(self) -> TokenData:
        """Create a sysadmin user token for testing."""
        return TokenData(
            user_id=uuid4(),
            email="sysadmin@example.com",
            role=UserRole.SYSADMIN.value,
            session_id="test_session",
            jti="test_jti",
        )

    @pytest.fixture
    def admin_user(self) -> TokenData:
        """Create an admin user token for testing."""
        return TokenData(
            user_id=uuid4(),
            email="admin@example.com",
            role=UserRole.ADMIN.value,
            session_id="test_session",
            jti="test_jti",
        )

    @pytest.fixture
    def regular_user(self) -> TokenData:
        """Create a regular user token for testing."""
        return TokenData(
            user_id=uuid4(),
            email="user@example.com",
            role=UserRole.USER.value,
            session_id="test_session",
            jti="test_jti",
        )

    def test_check_permission_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
        regular_user: TokenData,
    ) -> None:
        """Test successful permission check."""
        user_id = regular_user.user_id
        mock_permission_service.check_user_permission.return_value = True

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.get(
                f"/api/v1/permissions/check?user_id={user_id}&agent_name=client_management&operation=create",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["granted"] is True
        assert data["user_id"] == str(user_id)
        assert data["agent_name"] == "client_management"
        assert data["operation"] == "create"

        mock_permission_service.check_user_permission.assert_called_once_with(
            user_id, AgentName.CLIENT_MANAGEMENT, "create"
        )

    def test_check_permission_invalid_agent(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        regular_user: TokenData,
    ) -> None:
        """Test permission check with invalid agent name."""
        user_id = regular_user.user_id

        response = client.get(
            f"/api/v1/permissions/check?user_id={user_id}&agent_name=invalid_agent&operation=create",
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert "input should be" in data["detail"][0]["msg"].lower()

    def test_check_permission_invalid_operation(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        regular_user: TokenData,
    ) -> None:
        """Test permission check with invalid operation."""
        user_id = regular_user.user_id

        response = client.get(
            f"/api/v1/permissions/check?user_id={user_id}&agent_name=client_management&operation=invalid_operation",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid operation" in data["detail"]

    def test_get_user_permissions_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
        sysadmin_user: TokenData,
    ) -> None:
        """Test successful user permissions retrieval."""
        user_id = uuid4()
        expected_permissions = {
            "client_management": {"create": True, "read": True, "update": False, "delete": False},
            "pdf_processing": {"create": False, "read": True, "update": False, "delete": False},
        }
        mock_permission_service.get_user_permissions.return_value = expected_permissions

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.get(
                f"/api/v1/permissions/user/{user_id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(user_id)
        assert data["permissions"] == expected_permissions

        mock_permission_service.get_user_permissions.assert_called_once_with(user_id)

    def test_get_user_permissions_unauthorized(
        self,
        client: TestClient,
        regular_user: TokenData,
    ) -> None:
        """Test user permissions retrieval without proper authorization."""
        user_id = uuid4()

        # Override with regular user who shouldn't have access
        with patch("src.core.security.get_current_user_token", return_value=regular_user):
            response = client.get(f"/api/v1/permissions/user/{user_id}")

        # Should get 403 due to role-based access control
        assert response.status_code == 403

    def test_assign_permission_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
        sysadmin_user: TokenData,
    ) -> None:
        """Test successful permission assignment."""
        user_id = uuid4()
        permission_data = {
            "user_id": str(user_id),
            "agent_name": "client_management",
            "permissions": {"create": True, "read": True, "update": False, "delete": False},
            "change_reason": "Initial setup",
        }

        created_permission = create_test_permission(
            user_id=user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions=permission_data["permissions"],
            created_by_user_id=sysadmin_user.user_id,
        )
        mock_permission_service.assign_permission.return_value = created_permission

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.post(
                "/api/v1/permissions/assign",
                headers=auth_headers,
                json=permission_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(user_id)
        assert data["agent_name"] == "client_management"
        assert data["permissions"] == permission_data["permissions"]

        # Check that assign_permission was called with correct parameters
        mock_permission_service.assign_permission.assert_called_once()
        call_args = mock_permission_service.assign_permission.call_args
        assert call_args.kwargs["user_id"] == user_id
        assert call_args.kwargs["agent_name"] == AgentName.CLIENT_MANAGEMENT
        assert call_args.kwargs["permissions"] == permission_data["permissions"]
        assert call_args.kwargs["change_reason"] == "Initial setup"
        # created_by_user_id will be the mocked user, so we don't check the exact value

    def test_assign_permission_validation_error(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test permission assignment with invalid data."""
        user_id = uuid4()
        invalid_data = {
            "user_id": str(user_id),
            "agent_name": "client_management",
            "permissions": {"create": True, "read": True},  # Missing required keys
        }

        response = client.post(
            "/api/v1/permissions/assign",
            headers=auth_headers,
            json=invalid_data,
        )

        assert response.status_code == 422
        data = response.json()
        assert "validation error" in str(data).lower()

    def test_revoke_permission_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
        sysadmin_user: TokenData,
    ) -> None:
        """Test successful permission revocation."""
        user_id = uuid4()
        agent_name = "client_management"
        change_reason = "Security audit"

        mock_permission_service.revoke_permission.return_value = True

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.delete(
                f"/api/v1/permissions/user/{user_id}/agent/{agent_name}",
                headers=auth_headers,
                params={"change_reason": change_reason},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Permission revoked successfully"

        mock_permission_service.revoke_permission.assert_called_once_with(
            user_id=user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            revoked_by_user_id=sysadmin_user.user_id,
            change_reason="Security audit",
        )

    def test_revoke_permission_not_found(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
        sysadmin_user: TokenData,
    ) -> None:
        """Test revoking non-existent permission."""
        user_id = uuid4()
        agent_name = "client_management"

        mock_permission_service.revoke_permission.return_value = False

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.delete(
                f"/api/v1/permissions/user/{user_id}/agent/{agent_name}",
                headers=auth_headers,
            )

        assert response.status_code == 404
        data = response.json()
        assert "Permission not found" in data["detail"]

    def test_bulk_assign_permissions_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
        sysadmin_user: TokenData,
    ) -> None:
        """Test successful bulk permission assignment."""
        user_ids = [uuid4(), uuid4()]
        bulk_data = {
            "user_ids": [str(uid) for uid in user_ids],
            "agent_permissions": {
                "client_management": {
                    "create": True,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "reports_analysis": {
                    "create": False,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
            },
            "change_reason": "Bulk assignment",
        }

        mock_result = {
            user_ids[0]: {
                AgentName.CLIENT_MANAGEMENT: create_test_permission(),
                AgentName.REPORTS_ANALYSIS: create_test_permission(),
            },
            user_ids[1]: {
                AgentName.CLIENT_MANAGEMENT: create_test_permission(),
                AgentName.REPORTS_ANALYSIS: create_test_permission(),
            },
        }
        mock_permission_service.bulk_assign_permissions.return_value = mock_result

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.post(
                "/api/v1/permissions/bulk-assign",
                headers=auth_headers,
                json=bulk_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["users_updated"] == 2
        assert data["permissions_created"] == 4

    def test_bulk_assign_permissions_empty_users(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test bulk assignment with empty user list."""
        bulk_data = {
            "user_ids": [],
            "agent_permissions": {
                "client_management": {
                    "create": True,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
            },
        }

        response = client.post(
            "/api/v1/permissions/bulk-assign",
            headers=auth_headers,
            json=bulk_data,
        )

        assert response.status_code == 422
        data = response.json()
        assert "at least 1 item" in data["detail"][0]["msg"]

    def test_apply_template_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
        sysadmin_user: TokenData,
    ) -> None:
        """Test successful template application."""
        template_id = uuid4()
        user_ids = [uuid4(), uuid4()]
        apply_data = {
            "user_ids": [str(uid) for uid in user_ids],
            "change_reason": "Role update",
        }

        mock_result = {
            "successful": 2,
            "failed": 0,
            "errors": [],
        }
        mock_permission_service.apply_template_to_users.return_value = mock_result

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.post(
                f"/api/v1/permissions/templates/{template_id}/apply",
                headers=auth_headers,
                json=apply_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["successful"] == 2
        assert data["failed"] == 0
        assert len(data["errors"]) == 0

        mock_permission_service.apply_template_to_users.assert_called_once_with(
            template_id=template_id,
            user_ids=user_ids,
            applied_by_user_id=sysadmin_user.user_id,
            change_reason="Role update",
        )

    def test_list_templates_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        """Test successful template listing."""
        templates = [create_test_template() for _ in range(3)]
        mock_permission_service.list_templates.return_value = (templates, 3)

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.get(
                "/api/v1/permissions/templates",
                headers=auth_headers,
                params={"page": 1, "page_size": 10},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["templates"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 10

        mock_permission_service.list_templates.assert_called_once_with(
            page=1, page_size=10, system_only=False
        )

    def test_list_templates_system_only(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        """Test listing system templates only."""
        system_templates = [create_test_template(is_system=True) for _ in range(2)]
        mock_permission_service.list_templates.return_value = (system_templates, 2)

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.get(
                "/api/v1/permissions/templates",
                headers=auth_headers,
                params={"system_only": True},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["templates"]) == 2

        mock_permission_service.list_templates.assert_called_once_with(
            page=1, page_size=20, system_only=True
        )

    def test_create_template_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
        sysadmin_user: TokenData,
    ) -> None:
        """Test successful template creation."""
        template_data = {
            "template_name": "New Template",
            "description": "Test template",
            "permissions": {
                "client_management": {
                    "create": True,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "reports_analysis": {
                    "create": False,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
            },
        }

        created_template = create_test_template(
            template_name=template_data["template_name"], permissions=template_data["permissions"]
        )
        mock_permission_service.create_template.return_value = created_template

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.post(
                "/api/v1/permissions/templates",
                headers=auth_headers,
                json=template_data,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["template_name"] == template_data["template_name"]
        assert data["description"] == template_data["description"]

        mock_permission_service.create_template.assert_called_once_with(
            template_name=template_data["template_name"],
            description=template_data["description"],
            permissions=template_data["permissions"],
            created_by_user_id=sysadmin_user.user_id,
        )

    def test_create_template_validation_error(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test template creation with invalid data."""
        invalid_data = {
            "template_name": "",  # Empty name
            "permissions": {},  # Empty permissions
        }

        response = client.post(
            "/api/v1/permissions/templates",
            headers=auth_headers,
            json=invalid_data,
        )

        assert response.status_code == 422
        data = response.json()
        assert "validation error" in str(data).lower()

    def test_update_template_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
        sysadmin_user: TokenData,
    ) -> None:
        """Test successful template update."""
        template_id = uuid4()
        update_data = {
            "template_name": "Updated Template",
            "description": "Updated description",
        }

        updated_template = create_test_template(
            template_name=update_data["template_name"],
        )
        updated_template.template_id = template_id
        mock_permission_service.update_template.return_value = updated_template

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.put(
                f"/api/v1/permissions/templates/{template_id}",
                headers=auth_headers,
                json=update_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["template_name"] == update_data["template_name"]

        mock_permission_service.update_template.assert_called_once_with(
            template_id=template_id,
            template_name=update_data["template_name"],
            description=update_data["description"],
            permissions=None,
            updated_by_user_id=sysadmin_user.user_id,
        )

    def test_update_template_not_found(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
        sysadmin_user: TokenData,
    ) -> None:
        """Test updating non-existent template."""
        template_id = uuid4()
        update_data = {"template_name": "Updated Template"}

        mock_permission_service.update_template.return_value = None

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.put(
                f"/api/v1/permissions/templates/{template_id}",
                headers=auth_headers,
                json=update_data,
            )

        assert response.status_code == 404
        data = response.json()
        assert "Template not found" in data["detail"]

    def test_delete_template_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        """Test successful template deletion."""
        template_id = uuid4()

        mock_permission_service.delete_template.return_value = True

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.delete(
                f"/api/v1/permissions/templates/{template_id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        mock_permission_service.delete_template.assert_called_once_with(template_id)

    def test_delete_template_not_found(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        """Test deleting non-existent template."""
        template_id = uuid4()

        mock_permission_service.delete_template.return_value = False

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.delete(
                f"/api/v1/permissions/templates/{template_id}",
                headers=auth_headers,
            )

        assert response.status_code == 404
        data = response.json()
        assert "Template not found" in data["detail"]

    def test_get_audit_log_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        """Test successful audit log retrieval."""
        from src.tests.factories import create_test_permission_audit_log

        audit_logs = [create_test_permission_audit_log() for _ in range(5)]
        mock_permission_service.get_audit_log.return_value = (audit_logs, 5)

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.get(
                "/api/v1/permissions/audit",
                headers=auth_headers,
                params={
                    "page": 1,
                    "page_size": 10,
                    "action": "CREATE",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["audit_entries"]) == 5
        assert data["total"] == 5

        mock_permission_service.get_audit_log.assert_called_once_with(
            user_id=None,
            agent_name=None,
            action="CREATE",
            page=1,
            page_size=10,
        )

    def test_get_audit_log_with_filters(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        """Test audit log retrieval with filters."""
        user_id = uuid4()
        from src.tests.factories import create_test_permission_audit_log

        audit_logs = [create_test_permission_audit_log(user_id=user_id)]
        mock_permission_service.get_audit_log.return_value = (audit_logs, 1)

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.get(
                "/api/v1/permissions/audit",
                headers=auth_headers,
                params={
                    "user_id": str(user_id),
                    "agent_name": "client_management",
                    "action": "UPDATE",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["audit_entries"]) == 1

        mock_permission_service.get_audit_log.assert_called_once_with(
            user_id=user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            action="UPDATE",
            page=1,
            page_size=50,
        )

    def test_get_permission_stats_success(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        """Test successful permission statistics retrieval."""
        expected_stats = {
            "total_users": 100,
            "users_with_permissions": 75,
            "templates_in_use": 5,
            "recent_changes": 20,
            "agent_usage": {
                "client_management": 50,
                "pdf_processing": 25,
                "reports_analysis": 30,
                "audio_recording": 15,
            },
        }
        mock_permission_service.get_permission_stats.return_value = expected_stats

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.get(
                "/api/v1/permissions/stats",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data == expected_stats

        mock_permission_service.get_permission_stats.assert_called_once()

    def test_admin_role_restrictions(
        self,
        client: TestClient,
        admin_user: TokenData,
    ) -> None:
        """Test that admin users have restricted access to certain operations."""
        user_id = uuid4()
        permission_data = {
            "user_id": str(user_id),
            "agent_name": "pdf_processing",  # Admin can't assign this
            "permissions": {"create": True, "read": True, "update": False, "delete": False},
        }

        # Override with admin user
        with patch("src.core.security.get_current_user_token", return_value=admin_user):
            with patch("src.core.security.require_admin_or_above", return_value=admin_user):
                response = client.post(
                    "/api/v1/permissions/assign",
                    json=permission_data,
                )

        # Should get authorization error from the service layer
        assert response.status_code in [403, 400]  # May vary based on service implementation

    def test_invalid_uuid_handling(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test handling of invalid UUID parameters."""
        response = client.get(
            "/api/v1/permissions/user/invalid-uuid",
            headers=auth_headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert "validation error" in str(data).lower()

    def test_request_validation_missing_required_fields(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test request validation with missing required fields."""
        user_id = uuid4()
        incomplete_data = {
            "user_id": str(user_id),
            "agent_name": "client_management",
            # Missing permissions field
        }

        response = client.post(
            "/api/v1/permissions/assign",
            headers=auth_headers,
            json=incomplete_data,
        )

        assert response.status_code == 422
        data = response.json()
        assert "field required" in str(data).lower()

    def test_error_response_format(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that error responses follow consistent format."""
        from src.core.exceptions import NotFoundError

        user_id = uuid4()
        mock_permission_service.get_user_permissions.side_effect = NotFoundError("User not found")

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            response = client.get(
                f"/api/v1/permissions/user/{user_id}",
                headers=auth_headers,
            )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_pagination_parameters(
        self,
        client: TestClient,
        mock_permission_service: MagicMock,
        auth_headers: dict[str, str],
    ) -> None:
        """Test pagination parameter validation."""
        mock_permission_service.list_templates.return_value = ([], 0)

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            # Test invalid page number
            response = client.get(
                "/api/v1/permissions/templates",
                headers=auth_headers,
                params={"page": 0},  # Invalid - should be >= 1
            )

        assert response.status_code == 422

        with patch("src.api.v1.permissions.PermissionService", return_value=mock_permission_service):
            # Test invalid page size
            response = client.get(
                "/api/v1/permissions/templates",
                headers=auth_headers,
                params={"page_size": 0},  # Invalid - should be >= 1
            )

        assert response.status_code == 422
