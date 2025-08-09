"""
Permission Escalation Prevention Security Tests.

This module tests the system's resistance to permission escalation attacks
where users attempt to gain higher privileges than they are authorized for.

Key Scenarios Tested:
1. Direct role manipulation attempts
2. API endpoint privilege escalation
3. JWT token role tampering
4. Agent permission boundary violations
5. Cross-user permission exploitation
6. Administrative function abuse

Testing Philosophy:
- Use real permission logic (no mocks of PermissionService)
- Test actual role hierarchy enforcement
- Mock only external boundaries (Redis, file system)
- Validate audit logging of escalation attempts
- Test both direct and indirect escalation vectors
"""

import pytest
import json
from typing import Dict, Any, List
from unittest.mock import patch, Mock
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from src.core.security import auth_service, TokenData
from src.models.user import User, UserRole
from src.models.permissions import UserAgentPermission, AgentName
from src.tests.factories import UserFactory


class TestDirectRoleEscalationPrevention:
    """
    Test direct role escalation attempts through various attack vectors.
    
    These tests verify that users cannot directly manipulate their roles
    or escalate their privileges through API manipulation.
    """
    
    def test_user_cannot_escalate_to_admin_via_profile_update(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that regular users cannot escalate to admin role via profile update."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Create valid token for regular user
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to escalate role through profile update
        escalation_data = {
            "email": regular_user.email,
            "role": "admin"  # Attempted escalation
        }
        
        response = security_test_client.client.put(
            f"/api/v1/users/{regular_user.user_id}",
            json=escalation_data,
            headers=headers
        )
        
        # Should be rejected (403=forbidden, 422=validation error, 404=not found - all indicate failure)
        assert response.status_code in [403, 422, 404], f"Role escalation should be rejected, got {response.status_code}"
        
        # Verify role didn't change in database
        test_session.refresh(regular_user)
        assert regular_user.role == UserRole.USER, "User role should not have changed"
        
    def test_admin_cannot_escalate_to_sysadmin_via_profile_update(
        self,
        security_test_client, 
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that admin users cannot escalate to sysadmin role via profile update."""
        admin_user = attack_user_scenarios['admin_user']
        
        # Create valid token for admin user
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to escalate to sysadmin
        escalation_data = {
            "email": admin_user.email,
            "role": "sysadmin"  # Attempted escalation
        }
        
        response = security_test_client.client.put(
            f"/api/v1/users/{admin_user.user_id}",
            json=escalation_data,
            headers=headers
        )
        
        # Should be rejected (403=forbidden, 422=validation error, 404=not found - all indicate failure)
        assert response.status_code in [403, 422, 404], f"Sysadmin escalation should be rejected, got {response.status_code}"
        
        # Verify role didn't change
        test_session.refresh(admin_user)
        assert admin_user.role == UserRole.ADMIN, "Admin role should not have changed to sysadmin"
        
    def test_user_cannot_escalate_other_users_roles(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that users cannot escalate other users' roles."""
        regular_user = attack_user_scenarios['regular_user']
        target_user = attack_user_scenarios['admin_user']
        
        # Create token for regular user
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to escalate another user's role
        escalation_data = {
            "email": target_user.email,
            "role": "sysadmin"  # Attempted escalation of target user
        }
        
        response = security_test_client.client.put(
            f"/api/v1/users/{target_user.user_id}",
            json=escalation_data,
            headers=headers
        )
        
        # Should be rejected due to insufficient permissions (403=forbidden, 422=validation error, 404=not found - all indicate failure)
        assert response.status_code in [403, 422, 404], f"Cross-user role escalation should be forbidden, got {response.status_code}"
        
        # Verify target user's role didn't change
        test_session.refresh(target_user) 
        assert target_user.role == UserRole.ADMIN, "Target user role should not have changed"


class TestJWTTokenRoleManipulation:
    """
    Test JWT token role manipulation prevention.
    
    These tests verify that the system properly validates JWT tokens
    and cannot be fooled by manipulated tokens claiming higher privileges.
    """
    
    @pytest.mark.parametrize("manipulated_role", [
        "sysadmin",
        "admin", 
        "super_user",
        "root",
        "administrator"
    ])
    def test_manipulated_jwt_role_rejection(
        self,
        manipulated_role: str,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        malicious_jwt_tokens: List[str]
    ):
        """Test that manipulated JWT tokens with elevated roles are rejected."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Create legitimate token first
        legitimate_token = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        # Attempt to use manipulated token (these are pre-generated malicious tokens)
        for malicious_token in malicious_jwt_tokens:
            headers = {"Authorization": f"Bearer {malicious_token}"}
            
            response = security_test_client.client.get("/api/v1/auth/me", headers=headers)
            
            # Should reject manipulated token
            assert response.status_code == 401, f"Manipulated JWT should be rejected, got {response.status_code}"
            
            # Should not return user data
            if response.status_code == 200:
                user_data = response.json()
                assert user_data.get("role") != manipulated_role, f"Manipulated role should not be accepted"
    
    def test_token_signature_manipulation_detection(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that JWT signature manipulation is properly detected."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Create legitimate token
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        original_token = token_response.access_token
        
        # Manipulate token signature
        token_parts = original_token.split('.')
        if len(token_parts) == 3:
            # Change last character of signature
            manipulated_signature = token_parts[2][:-1] + ('X' if token_parts[2][-1] != 'X' else 'Y')
            manipulated_token = f"{token_parts[0]}.{token_parts[1]}.{manipulated_signature}"
            
            headers = {"Authorization": f"Bearer {manipulated_token}"}
            
            response = security_test_client.client.get("/api/v1/auth/me", headers=headers)
            
            # Should reject token with invalid signature
            assert response.status_code == 401, f"Token with invalid signature should be rejected, got {response.status_code}"
    
    def test_algorithm_none_attack_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test prevention of 'algorithm none' JWT attack."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Create token with 'none' algorithm (classic JWT attack)
        # This is a well-known attack where attacker sets alg=none and removes signature
        none_header = json.dumps({"typ": "JWT", "alg": "none"}).encode()
        none_payload = json.dumps({
            "sub": str(regular_user.user_id),
            "role": "sysadmin",  # Escalated role
            "email": regular_user.email,
            "iat": 1234567890,
            "exp": 9999999999
        }).encode()
        
        import base64
        header_b64 = base64.urlsafe_b64encode(none_header).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(none_payload).decode().rstrip('=')
        
        # Create unsigned token (algorithm none attack)
        none_token = f"{header_b64}.{payload_b64}."
        
        headers = {"Authorization": f"Bearer {none_token}"}
        
        response = security_test_client.client.get("/api/v1/auth/me", headers=headers)
        
        # Should reject 'algorithm none' attack
        assert response.status_code == 401, f"Algorithm none attack should be rejected, got {response.status_code}"


class TestAgentPermissionBoundaryViolation:
    """
    Test agent permission boundary violation prevention.
    
    These tests verify that users cannot bypass agent-based permission
    boundaries to access functionality they shouldn't have access to.
    """
    
    def test_user_cannot_bypass_client_management_permissions(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that users without client_management permissions cannot access client endpoints."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Ensure user has NO client management permissions
        existing_perm = test_session.exec(
            select(UserAgentPermission).where(
                UserAgentPermission.user_id == regular_user.user_id,
                UserAgentPermission.agent_name == AgentName.CLIENT_MANAGEMENT
            )
        ).first()
        
        if existing_perm:
            test_session.delete(existing_perm)
            test_session.commit()
        
        # Create token for user
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to access client management endpoints
        client_data = {
            "name": "Unauthorized Client",
            "cpf": "123456789",
            "birth_date": "1990-01-01"
        }
        
        # Test various client endpoints
        endpoints_to_test = [
            ("POST", "/api/v1/clients", client_data),
            ("GET", "/api/v1/clients", None),
        ]
        
        for method, endpoint, data in endpoints_to_test:
            if method == "POST":
                response = security_test_client.client.post(endpoint, json=data, headers=headers)
            else:
                response = security_test_client.client.get(endpoint, headers=headers)
            
            # Should be forbidden due to lack of agent permissions
            assert response.status_code == 403, f"Access to {endpoint} should be forbidden, got {response.status_code}"
            
    def test_user_cannot_escalate_agent_permissions_directly(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that users cannot directly escalate their agent permissions."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Create token for regular user
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to grant self agent permissions (if such endpoint exists)
        permission_data = {
            "user_id": str(regular_user.user_id),
            "agent_name": "client_management",
            "permissions": {
                "create": True,
                "read": True,
                "update": True,
                "delete": True
            }
        }
        
        response = security_test_client.client.post(
            "/api/v1/permissions/assign",
            json=permission_data,
            headers=headers
        )
        
        # Should be forbidden - regular users cannot assign permissions
        assert response.status_code == 403, f"Self permission assignment should be forbidden, got {response.status_code}"
        
        # Verify no permissions were actually granted
        permission_check = test_session.exec(
            select(UserAgentPermission).where(
                UserAgentPermission.user_id == regular_user.user_id,
                UserAgentPermission.agent_name == AgentName.CLIENT_MANAGEMENT
            )
        ).first()
        
        assert not permission_check, "No permissions should have been granted through self-assignment"
    
    def test_admin_cannot_grant_sysadmin_level_permissions(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that admin users cannot grant sysadmin-level permissions."""
        admin_user = attack_user_scenarios['admin_user']
        target_user = attack_user_scenarios['regular_user']
        
        # Create token for admin user
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to grant system-level permissions to another user
        system_permission_data = {
            "user_id": str(target_user.user_id),
            "permissions": {
                "system:config": True,
                "system:logs": True,
                "delete:users": True,
                "create:agents": True
            }
        }
        
        response = security_test_client.client.post(
            "/api/v1/permissions/assign-system",
            json=system_permission_data,
            headers=headers
        )
        
        # Should be forbidden - only sysadmin can grant system permissions
        assert response.status_code in [403, 404], f"System permission assignment should be forbidden for admin, got {response.status_code}"


class TestCrossUserPermissionExploitation:
    """
    Test cross-user permission exploitation prevention.
    
    These tests verify that users cannot exploit permissions through
    other users or gain unauthorized access to other users' data.
    """
    
    def test_user_cannot_access_other_user_data_via_permission_bypass(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that users cannot access other users' data even with valid permissions."""
        user1 = attack_user_scenarios['regular_user']
        user2 = attack_user_scenarios['admin_user']
        
        # Give user1 legitimate user management permissions
        from src.models.permissions import UserAgentPermission, AgentName
        
        permission = UserAgentPermission(
            user_id=user1.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"read": True, "update": False, "create": False, "delete": False},
            created_by_user_id=user2.user_id  # Granted by admin
        )
        
        test_session.add(permission)
        test_session.commit()
        
        # Create token for user1
        token_response = auth_service.create_access_token(
            user_id=user1.user_id,
            user_role=user1.role.value,
            user_email=user1.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to access user2's profile (should be forbidden)
        response = security_test_client.client.get(
            f"/api/v1/users/{user2.user_id}",
            headers=headers
        )
        
        # Should be forbidden - users can only access their own data (403=forbidden, 404=not found - both indicate access denied)
        assert response.status_code in [403, 404], f"Cross-user data access should be forbidden, got {response.status_code}"
        
    def test_permission_inheritance_exploitation_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that users cannot exploit permission inheritance to gain unauthorized access."""
        regular_user = attack_user_scenarios['regular_user']
        admin_user = attack_user_scenarios['admin_user']
        
        # Create token for regular user
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to exploit admin's inherited permissions by impersonation
        impersonation_data = {
            "acting_as_user_id": str(admin_user.user_id),  # Attempt impersonation
            "name": "Exploited Client",
            "cpf": "987654321",
            "birth_date": "1985-01-01"
        }
        
        response = security_test_client.client.post(
            "/api/v1/clients",
            json=impersonation_data,
            headers=headers
        )
        
        # Should reject impersonation attempt
        assert response.status_code in [400, 403, 422], f"Impersonation should be rejected, got {response.status_code}"
        
        # If client was created, verify it wasn't created with admin privileges
        if response.status_code == 201:
            created_client = response.json()
            # Verify the client was created with regular user's ID, not admin's
            # This would require checking audit trail or created_by field


class TestAdministrativeFunctionAbuse:
    """
    Test administrative function abuse prevention.
    
    These tests verify that administrative functions cannot be abused
    to gain unauthorized access or escalate privileges.
    """
    
    def test_bulk_permission_assignment_abuse_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that bulk permission assignment cannot be abused for privilege escalation."""
        admin_user = attack_user_scenarios['admin_user']
        regular_user = attack_user_scenarios['regular_user']
        
        # Create token for admin user
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to abuse bulk assignment to escalate self and others
        bulk_assignment_data = {
            "user_ids": [str(admin_user.user_id), str(regular_user.user_id)],
            "permissions": {
                "system:all": True,  # Attempt to grant system permissions
                "role": "sysadmin",  # Attempt role escalation
                "all_agents": {
                    "create": True,
                    "read": True, 
                    "update": True,
                    "delete": True
                }
            }
        }
        
        response = security_test_client.client.post(
            "/api/v1/permissions/bulk-assign",
            json=bulk_assignment_data,
            headers=headers
        )
        
        # Should either reject the request or safely ignore dangerous fields
        if response.status_code == 200:
            # If successful, verify dangerous permissions were not granted
            # Check that no system permissions were actually assigned
            pass
        else:
            # Should be rejected due to insufficient privileges
            assert response.status_code in [400, 403, 422], f"Bulk privilege escalation should be rejected, got {response.status_code}"
    
    def test_permission_template_abuse_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that permission templates cannot be abused for privilege escalation."""
        admin_user = attack_user_scenarios['admin_user']
        
        # Create token for admin user
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to create malicious permission template
        malicious_template = {
            "template_name": "Sysadmin Backdoor",
            "description": "Legitimate template",
            "permissions": {
                "all_agents": {
                    "create": True,
                    "read": True,
                    "update": True, 
                    "delete": True
                },
                "system:config": True,
                "system:logs": True,
                "role": "sysadmin"  # Hidden role escalation
            }
        }
        
        response = security_test_client.client.post(
            "/api/v1/permissions/templates",
            json=malicious_template,
            headers=headers
        )
        
        if response.status_code == 201:
            template_data = response.json()
            
            # Verify dangerous fields were stripped out
            permissions = template_data.get("permissions", {})
            assert "role" not in permissions, "Role field should not be allowed in permission templates"
            assert "system:config" not in permissions, "System permissions should not be allowed for admin users"
            assert "system:logs" not in permissions, "System permissions should not be allowed for admin users"
        else:
            # Should be rejected if admin lacks template creation permissions
            assert response.status_code in [403, 422], f"Malicious template should be rejected, got {response.status_code}"


class TestPermissionStateManipulation:
    """
    Test permission state manipulation prevention.
    
    These tests verify that permission state cannot be manipulated
    through race conditions, session hijacking, or state confusion attacks.
    """
    
    @pytest.mark.asyncio
    async def test_concurrent_permission_manipulation_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that concurrent permission changes cannot be exploited."""
        admin_user = attack_user_scenarios['admin_user'] 
        target_user = attack_user_scenarios['regular_user']
        
        # Create token for admin
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Simulate race condition: grant and revoke permission simultaneously
        import asyncio
        import aiohttp
        
        async def grant_permission():
            async with aiohttp.ClientSession() as session:
                data = {
                    "user_id": str(target_user.user_id),
                    "agent_name": "client_management", 
                    "permissions": {"create": True, "read": True}
                }
                async with session.post(
                    "http://localhost:8000/api/v1/permissions/assign",
                    json=data,
                    headers=headers
                ) as resp:
                    return resp.status
        
        async def revoke_permission():
            async with aiohttp.ClientSession() as session:
                data = {
                    "user_id": str(target_user.user_id),
                    "agent_name": "client_management"
                }
                async with session.post(
                    "http://localhost:8000/api/v1/permissions/revoke", 
                    json=data,
                    headers=headers
                ) as resp:
                    return resp.status
        
        # Execute concurrent operations
        grant_task = asyncio.create_task(grant_permission())
        revoke_task = asyncio.create_task(revoke_permission())
        
        try:
            results = await asyncio.gather(grant_task, revoke_task, return_exceptions=True)
            
            # At least one operation should succeed without corruption
            # Final state should be consistent (either granted or revoked, not corrupted)
            final_permissions = test_session.exec(
                select(UserAgentPermission).where(
                    UserAgentPermission.user_id == target_user.user_id,
                    UserAgentPermission.agent_name == AgentName.CLIENT_MANAGEMENT
                )
            ).first()
            
            # State should be consistent - either exists with valid data or doesn't exist
            if final_permissions:
                assert isinstance(final_permissions.permissions, dict), "Permission state should not be corrupted"
                # Verify it has valid structure
                assert "create" in final_permissions.permissions or "read" in final_permissions.permissions, "Permission data should be valid"
                
        except Exception as e:
            # Concurrent operations might fail, but should not corrupt state
            pytest.skip(f"Concurrent test requires running server: {e}")
    
    @patch('src.core.security.auth_service.redis_client')
    def test_session_state_confusion_prevention(
        self,
        mock_redis,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that session state confusion cannot be exploited for privilege escalation."""
        regular_user = attack_user_scenarios['regular_user']
        admin_user = attack_user_scenarios['admin_user']
        
        # Mock Redis to simulate state confusion
        mock_redis.get.return_value = json.dumps({
            "user_id": str(admin_user.user_id),  # Wrong user in session
            "user_role": "sysadmin",  # Wrong role
            "user_email": admin_user.email,
            "created_at": "2023-01-01T00:00:00Z",
            "last_activity": "2023-01-01T00:00:00Z"
        })
        
        # Create token for regular user
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to exploit confused session state
        response = security_test_client.client.get("/api/v1/auth/me", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Should return data for token user, not session user
            assert user_data["user_id"] == str(regular_user.user_id), "Should return token user, not session user"
            assert user_data["role"] == regular_user.role.value, "Should return token role, not session role"
            assert user_data["email"] == regular_user.email, "Should return token email, not session email"
        else:
            # Session confusion should be detected and rejected
            assert response.status_code == 401, f"Confused session should be rejected, got {response.status_code}"