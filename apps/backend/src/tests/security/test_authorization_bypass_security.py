"""
Authorization Bypass Prevention Security Tests.

This module tests the system's resistance to authorization bypass attacks
where attackers attempt to access resources or perform actions without
proper authorization through various attack vectors.

Key Attack Scenarios Tested:
1. Direct API endpoint access without proper roles
2. Agent permission boundary violations
3. Resource access without ownership validation
4. Batch operation authorization bypasses
5. HTTP method manipulation bypasses
6. Parameter pollution authorization bypasses
7. API versioning authorization bypasses
8. Middleware bypass attempts

Testing Philosophy:
- Test real authorization logic (no mocks of permission checking)
- Mock only external boundaries (Redis, file system, network calls)
- Validate proper error responses with minimal information leakage
- Ensure all protected endpoints are properly secured
- Test both direct and indirect bypass techniques
"""

import pytest
import json
from typing import Dict, Any, List, Tuple
from unittest.mock import patch, Mock
from uuid import uuid4, UUID
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.security import auth_service, TokenData
from src.models.user import User, UserRole
from src.models.client import Client
from src.models.permissions import UserAgentPermission, AgentName
from src.tests.factories import UserFactory, ClientFactory


class TestDirectAPIEndpointBypass:
    """
    Test direct API endpoint access bypass prevention.
    
    These tests verify that protected API endpoints cannot be accessed
    without proper authentication and authorization.
    """
    
    def test_unauthenticated_access_to_protected_endpoints(
        self,
        security_test_client,
        test_session: Session
    ):
        """Test that protected endpoints reject unauthenticated requests."""
        # List of protected endpoints that should require authentication
        protected_endpoints = [
            ("GET", "/api/v1/users"),
            ("POST", "/api/v1/users"),
            ("GET", "/api/v1/users/me"),
            ("GET", "/api/v1/clients"),
            ("POST", "/api/v1/clients"),
            ("GET", "/api/v1/permissions"),
            ("POST", "/api/v1/permissions/assign"),
            ("GET", "/api/v1/auth/me"),
        ]
        
        for method, endpoint in protected_endpoints:
            try:
                if method == "GET":
                    response = security_test_client.client.get(endpoint)
                elif method == "POST":
                    response = security_test_client.client.post(endpoint, json={"dummy": "data"})
                elif method == "PUT":
                    response = security_test_client.client.put(endpoint, json={"dummy": "data"})
                elif method == "DELETE":
                    response = security_test_client.client.delete(endpoint)
                
                # Should require authentication (security working correctly)
                assert response.status_code == 401, f"{method} {endpoint} should require authentication, got {response.status_code}"
            except Exception as e:
                # If an HTTPException is raised, that's the correct security behavior
                # The middleware is properly rejecting unauthenticated requests
                assert "401" in str(e) or "Authorization" in str(e) or "Unauthorized" in str(e), f"Unexpected error for {method} {endpoint}: {e}"
            
                # Should not leak information about endpoint existence  
                if response.status_code == 401:
                    response_data = response.json()
                    detail = response_data.get("detail", "").lower()
                    assert "not found" not in detail, f"Should not leak endpoint existence: {endpoint}"
    
    def test_invalid_token_access_to_protected_endpoints(
        self,
        security_test_client,
        malicious_jwt_tokens: List[str]
    ):
        """Test that endpoints properly reject invalid authentication tokens."""
        # Test various invalid tokens
        invalid_tokens = malicious_jwt_tokens + [
            "Bearer invalid_token",
            "invalid_format_token",
            "",
            "Bearer ",
            "Basic dXNlcjpwYXNzd29yZA==",  # Wrong auth type
        ]
        
        protected_endpoint = "/api/v1/users/me"
        
        for token in invalid_tokens:
            if token and not token.startswith("Bearer "):
                headers = {"Authorization": f"Bearer {token}"}
            else:
                headers = {"Authorization": token} if token else {}
            
            response = security_test_client.client.get(protected_endpoint, headers=headers)
            
            # Should reject invalid token
            assert response.status_code == 401, f"Invalid token should be rejected: {token[:30]}..."
    
    def test_role_based_endpoint_access_control(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that role-based endpoints properly enforce role requirements."""
        regular_user = attack_user_scenarios['regular_user']
        admin_user = attack_user_scenarios['admin_user']
        
        # Create tokens for different user roles
        user_token = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        admin_token = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        user_headers = {"Authorization": f"Bearer {user_token.access_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token.access_token}"}
        
        # Test admin-only endpoints
        admin_only_endpoints = [
            ("GET", "/api/v1/users"),
            ("POST", "/api/v1/users"),
            ("GET", "/api/v1/permissions"),
        ]
        
        for method, endpoint in admin_only_endpoints:
            # Regular user should be forbidden
            if method == "GET":
                response = security_test_client.client.get(endpoint, headers=user_headers)
            elif method == "POST":
                response = security_test_client.client.post(
                    endpoint, 
                    json={"dummy": "data"},
                    headers=user_headers
                )
            
            assert response.status_code == 403, f"Regular user should be forbidden from {method} {endpoint}, got {response.status_code}"
            
            # Admin user should have access (or proper validation error)
            if method == "GET":
                admin_response = security_test_client.client.get(endpoint, headers=admin_headers)
            elif method == "POST":
                admin_response = security_test_client.client.post(
                    endpoint,
                    json={"email": "test@example.com", "full_name": "Test User", "role": "user", "password": "Test123!"},
                    headers=admin_headers
                )
            
            # Admin should get access or proper validation (not forbidden)
            assert admin_response.status_code != 403, f"Admin should not be forbidden from {method} {endpoint}"


class TestAgentPermissionBoundaryBypass:
    """
    Test agent permission boundary bypass prevention.
    
    These tests verify that users cannot bypass agent-specific
    permission boundaries to access unauthorized functionality.
    """
    
    def test_client_management_permission_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that client management endpoints properly enforce agent permissions."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Ensure user has NO client management permissions
        from sqlmodel import select, delete
        from src.models.permissions import UserAgentPermission, AgentName
        
        # Delete any existing permissions for this user and agent
        statement = delete(UserAgentPermission).where(
            UserAgentPermission.user_id == regular_user.user_id,
            UserAgentPermission.agent_name == AgentName.CLIENT_MANAGEMENT
        )
        test_session.exec(statement)
        test_session.commit()
        
        # Create token for user without permissions
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Test client management operations
        client_operations = [
            ("POST", "/api/v1/clients", {"name": "Test Client", "cpf": "123456789", "birth_date": "1990-01-01"}),
            ("GET", "/api/v1/clients", None),
        ]
        
        for method, endpoint, data in client_operations:
            if method == "POST":
                response = security_test_client.client.post(endpoint, json=data, headers=headers)
            else:
                response = security_test_client.client.get(endpoint, headers=headers)
            
            # Should be forbidden due to lack of agent permissions
            assert response.status_code == 403, f"Should be forbidden without client_management permission: {method} {endpoint}"
    
    def test_mixed_agent_permission_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that users cannot bypass permission checks by mixing agent operations."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Grant only read permission for client_management
        permission = UserAgentPermission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"read": True, "create": False, "update": False, "delete": False},
            created_by_user_id=regular_user.user_id
        )
        
        test_session.add(permission)
        test_session.commit()
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Should be able to read
        read_response = security_test_client.client.get("/api/v1/clients", headers=headers)
        assert read_response.status_code != 403, "Read operation should be allowed"
        
        # Should NOT be able to create
        create_response = security_test_client.client.post(
            "/api/v1/clients",
            json={"name": "Unauthorized Client", "cpf": "987654321", "birth_date": "1985-01-01"},
            headers=headers
        )
        assert create_response.status_code == 403, "Create operation should be forbidden without create permission"
    
    def test_agent_permission_escalation_via_api_manipulation(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that API manipulation cannot be used to escalate agent permissions."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Grant limited permissions
        permission = UserAgentPermission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"read": True},
            created_by_user_id=regular_user.user_id
        )
        
        test_session.add(permission)
        test_session.commit()
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to escalate permissions through API manipulation
        escalation_attempts = [
            # Attempt to modify request to claim higher permissions
            {"name": "Client", "cpf": "123456789", "birth_date": "1990-01-01", "_permission_override": "admin"},
            {"name": "Client", "cpf": "123456789", "birth_date": "1990-01-01", "force_create": True},
            {"name": "Client", "cpf": "123456789", "birth_date": "1990-01-01", "bypass_auth": True},
            # Attempt to claim admin role in request
            {"name": "Client", "cpf": "123456789", "birth_date": "1990-01-01", "user_role": "admin"},
        ]
        
        for attempt_data in escalation_attempts:
            response = security_test_client.client.post(
                "/api/v1/clients",
                json=attempt_data,
                headers=headers
            )
            
            # Should be forbidden regardless of manipulation attempts
            assert response.status_code == 403, f"Permission escalation should be prevented: {attempt_data}"


class TestResourceOwnershipBypass:
    """
    Test resource ownership bypass prevention.
    
    These tests verify that users cannot access or modify resources
    they don't own through various bypass techniques.
    """
    
    def test_cross_user_resource_access_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that users cannot access other users' resources."""
        user1 = attack_user_scenarios['regular_user']
        user2 = attack_user_scenarios['admin_user']
        
        # Create clients for each user
        client1 = ClientFactory(name="User1 Client", created_by_user_id=user1.user_id)
        client2 = ClientFactory(name="User2 Client", created_by_user_id=user2.user_id)
        
        test_session.add(client1)
        test_session.add(client2)
        test_session.commit()
        test_session.refresh(client1)
        test_session.refresh(client2)
        
        # Create token for user1
        token_response = auth_service.create_access_token(
            user_id=user1.user_id,
            user_role=user1.role.value,
            user_email=user1.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # User1 attempts to access User2's client
        cross_access_response = security_test_client.client.get(
            f"/api/v1/clients/{client2.client_id}",
            headers=headers
        )
        
        # Should be forbidden or not found (but not return the data)
        assert cross_access_response.status_code in [403, 404], f"Cross-user resource access should be prevented, got {cross_access_response.status_code}"
        
        # User1 should be able to access their own client
        own_access_response = security_test_client.client.get(
            f"/api/v1/clients/{client1.client_id}",
            headers=headers
        )
        
        # Should succeed or at least not be forbidden
        assert own_access_response.status_code != 403, "User should be able to access their own resources"
    
    def test_resource_id_manipulation_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that resource ID manipulation cannot bypass ownership checks."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Create legitimate client
        legitimate_client = ClientFactory(name="Legitimate Client", created_by_user_id=regular_user.user_id)
        test_session.add(legitimate_client)
        test_session.commit()
        test_session.refresh(legitimate_client)
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to manipulate resource IDs to access unauthorized resources
        manipulated_ids = [
            "00000000-0000-0000-0000-000000000001",  # Sequential ID guess
            "11111111-1111-1111-1111-111111111111",  # Pattern ID guess
            str(uuid4()),  # Random UUID
            "../admin/clients",  # Path traversal attempt in ID
            "'; DROP TABLE clients; --",  # SQL injection in ID
            "admin",  # Non-UUID string
            "null",  # Null value attempt
            "",  # Empty ID
        ]
        
        for manipulated_id in manipulated_ids:
            response = security_test_client.client.get(
                f"/api/v1/clients/{manipulated_id}",
                headers=headers
            )
            
            # Should properly handle invalid IDs without crashing or leaking data
            assert response.status_code in [400, 404, 422], f"Invalid ID should be handled properly: {manipulated_id}"
            
            # Should not return sensitive data
            if response.status_code == 200:
                data = response.json()
                assert data.get("client_id") != manipulated_id or data.get("created_by_user_id") == str(regular_user.user_id), "Should not return unauthorized data"
    
    def test_batch_operation_ownership_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that batch operations properly enforce ownership for all resources."""
        user1 = attack_user_scenarios['regular_user']
        user2 = attack_user_scenarios['admin_user']
        
        # Create clients for different users
        client1 = ClientFactory(name="User1 Client", created_by_user_id=user1.user_id)
        client2 = ClientFactory(name="User2 Client", created_by_user_id=user2.user_id)
        
        test_session.add_all([client1, client2])
        test_session.commit()
        test_session.refresh(client1)
        test_session.refresh(client2)
        
        token_response = auth_service.create_access_token(
            user_id=user1.user_id,
            user_role=user1.role.value,
            user_email=user1.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt batch operation including both owned and unowned resources
        batch_data = {
            "client_ids": [str(client1.client_id), str(client2.client_id)],  # Mix of owned and unowned
            "operation": "update",
            "data": {"name": "Batch Updated"}
        }
        
        response = security_test_client.client.post(
            "/api/v1/clients/batch",
            json=batch_data,
            headers=headers
        )
        
        # Should either:
        # 1. Reject entire batch due to unauthorized resource
        # 2. Process only authorized resources and report unauthorized ones
        assert response.status_code in [200, 403, 207], f"Batch operation should handle authorization properly, got {response.status_code}"
        
        if response.status_code == 200:
            # If successful, verify only authorized resources were affected
            result = response.json()
            if "processed" in result:
                assert str(client2.client_id) not in result.get("processed", []), "Unauthorized resource should not be processed"
        elif response.status_code == 207:  # Partial success
            # Should report which resources were unauthorized
            result = response.json()
            assert "unauthorized" in result or "failed" in result, "Should report unauthorized resources"


class TestHTTPMethodManipulationBypass:
    """
    Test HTTP method manipulation bypass prevention.
    
    These tests verify that HTTP method manipulation cannot be used
    to bypass authorization controls.
    """
    
    def test_method_override_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that HTTP method override headers cannot bypass authorization."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Create client for testing
        test_client = ClientFactory(name="Test Client", created_by_user_id=regular_user.user_id)
        test_session.add(test_client)
        test_session.commit()
        test_session.refresh(test_client)
        
        # Grant only read permission
        permission = UserAgentPermission(
            user_id=regular_user.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"read": True, "update": False, "delete": False},
            created_by_user_id=regular_user.user_id
        )
        
        test_session.add(permission)
        test_session.commit()
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt method override to bypass permissions
        method_override_attempts = [
            {"X-HTTP-Method-Override": "DELETE"},
            {"X-Method-Override": "PUT"},
            {"_method": "DELETE"},
            {"X-HTTP-Method": "PUT"},
        ]
        
        for override_header in method_override_attempts:
            # Combine auth header with method override
            test_headers = {**headers, **override_header}
            
            # Make GET request but try to override to dangerous method
            response = security_test_client.client.get(
                f"/api/v1/clients/{test_client.client_id}",
                headers=test_headers
            )
            
            # Should not allow method override bypass
            # Either ignore override and process as GET (success) or reject override
            if response.status_code == 200:
                # Should return client data (GET processed normally)
                assert "client_id" in response.json(), "Should process as normal GET"
            else:
                # Should not crash or return method not allowed due to override
                assert response.status_code != 405, "Method override should not change actual HTTP method processing"
    
    def test_verb_tampering_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that HTTP verb tampering cannot bypass authorization."""
        regular_user = attack_user_scenarios['regular_user']
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,  
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt unauthorized operations using different HTTP verbs
        # These should all be forbidden for regular user without permissions
        verb_attempts = [
            ("POST", "/api/v1/clients", {"name": "Test", "cpf": "123456789", "birth_date": "1990-01-01"}),
            ("PUT", "/api/v1/users/me", {"role": "admin"}),  # Role escalation attempt
            ("DELETE", "/api/v1/clients/00000000-0000-0000-0000-000000000001", None),
            ("PATCH", "/api/v1/users/me", {"role": "sysadmin"}),
        ]
        
        for method, endpoint, data in verb_attempts:
            if method == "POST":
                response = security_test_client.client.post(endpoint, json=data, headers=headers)
            elif method == "PUT":
                response = security_test_client.client.put(endpoint, json=data, headers=headers)
            elif method == "DELETE":
                response = security_test_client.client.delete(endpoint, headers=headers)
            elif method == "PATCH":
                response = security_test_client.client.patch(endpoint, json=data, headers=headers)
            
            # Should be properly authorized regardless of HTTP method
            assert response.status_code in [400, 403, 404, 422], f"{method} {endpoint} should require proper authorization"


class TestParameterPollutionBypass:
    """
    Test parameter pollution bypass prevention.
    
    These tests verify that parameter pollution attacks cannot be used
    to bypass authorization controls.
    """
    
    def test_query_parameter_pollution_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that query parameter pollution cannot bypass authorization."""
        regular_user = attack_user_scenarios['regular_user']
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt parameter pollution to bypass authorization
        pollution_attempts = [
            "/api/v1/clients?user_id={}&user_id=admin".format(regular_user.user_id),
            "/api/v1/clients?role=user&role=admin",
            "/api/v1/clients?permission=read&permission=admin",
            f"/api/v1/users/{regular_user.user_id}?user_id={regular_user.user_id}&user_id=admin",
        ]
        
        for polluted_url in pollution_attempts:
            response = security_test_client.client.get(polluted_url, headers=headers)
            
            # Should handle parameter pollution gracefully
            # Should not grant elevated privileges due to pollution
            if response.status_code == 200:
                data = response.json()
                # Should not return admin-level data
                assert not any(
                    item.get("role") == "admin" or item.get("user_id") == "admin"
                    for item in (data if isinstance(data, list) else [data])
                ), f"Parameter pollution should not grant admin access: {polluted_url}"
    
    def test_json_parameter_pollution_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that JSON parameter pollution cannot bypass authorization."""
        regular_user = attack_user_scenarios['regular_user']
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt JSON pollution in client creation
        polluted_json_attempts = [
            {
                "name": "Test Client",
                "cpf": "123456789",
                "birth_date": "1990-01-01",
                "role": "user",
                "role": "admin",  # Duplicate key with different value
            },
            {
                "name": "Test Client",
                "cpf": "123456789", 
                "birth_date": "1990-01-01",
                "permissions": ["read"],
                "permissions": ["admin", "all"],  # Pollution attempt
            },
        ]
        
        for polluted_data in polluted_json_attempts:
            response = security_test_client.client.post(
                "/api/v1/clients",
                json=polluted_data,
                headers=headers
            )
            
            # Should handle gracefully - either reject or process safely
            if response.status_code == 201:
                created_client = response.json()
                # Should not have admin privileges from pollution
                assert "role" not in created_client or created_client["role"] != "admin", "JSON pollution should not grant admin privileges"
                assert "permissions" not in created_client or "admin" not in created_client.get("permissions", []), "Should not grant admin permissions via pollution"
    
    def test_header_pollution_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that HTTP header pollution cannot bypass authorization."""
        regular_user = attack_user_scenarios['regular_user']
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        # Attempt header pollution for privilege escalation
        polluted_headers = {
            "Authorization": f"Bearer {token_response.access_token}",
            "X-User-Role": "user",
            "X-User-Role": "admin",  # Duplicate header with escalated role
            "X-Permission": "read",
            "X-Permission": "admin",  # Duplicate permission header
            "User-Agent": "normal_client",
            "User-Agent": "admin_override_client",  # Duplicate user agent
        }
        
        response = security_test_client.client.get("/api/v1/auth/me", headers=polluted_headers)
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Should return actual user role, not polluted role
            assert user_data.get("role") == regular_user.role.value, "Header pollution should not change user role"
            assert user_data.get("user_id") == str(regular_user.user_id), "Header pollution should not change user identity"


class TestMiddlewareBypassAttempts:
    """
    Test middleware bypass attempt prevention.
    
    These tests verify that security middleware cannot be bypassed
    through various manipulation techniques.
    """
    
    def test_cors_bypass_attempt_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that CORS restrictions cannot be bypassed for unauthorized origins."""
        regular_user = attack_user_scenarios['regular_user']
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        # Attempt CORS bypass with malicious origins
        malicious_origins = [
            "http://evil.com",
            "https://attacker.example.com",
            "null",  # Null origin attack
            "*",  # Wildcard origin
            "http://localhost:3000.evil.com",  # Subdomain attack
        ]
        
        for origin in malicious_origins:
            headers = {
                "Authorization": f"Bearer {token_response.access_token}",
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type",
            }
            
            # Test preflight request
            preflight_response = security_test_client.client.options("/api/v1/users/me", headers=headers)
            
            # Should not allow malicious origins
            if preflight_response.status_code == 200:
                cors_headers = preflight_response.headers
                allowed_origin = cors_headers.get("Access-Control-Allow-Origin", "")
                assert allowed_origin != origin or origin in ["http://localhost:3000"], f"Should not allow malicious origin: {origin}"
    
    def test_content_type_manipulation_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that content type manipulation cannot bypass security controls."""
        regular_user = attack_user_scenarios['regular_user']
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        # Attempt to bypass JSON validation with different content types
        content_type_attacks = [
            "application/x-www-form-urlencoded",
            "text/plain",
            "application/xml",
            "multipart/form-data",
            "text/html",
        ]
        
        malicious_data = '{"name": "Evil Client", "role": "admin"}'
        
        for content_type in content_type_attacks:
            headers = {
                "Authorization": f"Bearer {token_response.access_token}",
                "Content-Type": content_type,
            }
            
            response = security_test_client.client.post(
                "/api/v1/clients",
                data=malicious_data,
                headers=headers
            )
            
            # Should properly validate content type and reject malformed requests
            assert response.status_code in [400, 415, 422], f"Should reject inappropriate content type: {content_type}"
    
    def test_user_agent_spoofing_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that user agent spoofing cannot bypass security restrictions."""
        regular_user = attack_user_scenarios['regular_user']
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        # Attempt to spoof privileged user agents
        spoofed_agents = [
            "AdminBot/1.0",
            "InternalServiceAgent/2.0",
            "SystemHealthCheck/1.0",
            "DatabaseMigration/1.0",
            "SecurityScanner/1.0",
        ]
        
        for user_agent in spoofed_agents:
            headers = {
                "Authorization": f"Bearer {token_response.access_token}",
                "User-Agent": user_agent,
            }
            
            response = security_test_client.client.get("/api/v1/users", headers=headers)
            
            # Should not grant elevated privileges based on user agent
            # Regular user should still be forbidden regardless of user agent
            assert response.status_code == 403, f"User agent spoofing should not bypass authorization: {user_agent}"
    
    def test_encoding_manipulation_bypass_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that encoding manipulation cannot bypass input validation."""
        regular_user = attack_user_scenarios['regular_user']
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt encoding manipulation to bypass validation
        encoding_attacks = [
            # URL encoding
            {"name": "Test%20Client", "role": "%61%64%6D%69%6E"},  # "admin" in URL encoding
            # Unicode escapes
            {"name": "Test Client", "role": "\\u0061\\u0064\\u006D\\u0069\\u006E"},  # "admin" in unicode
            # HTML entities  
            {"name": "Test Client", "role": "&#97;&#100;&#109;&#105;&#110;"},  # "admin" in HTML entities
            # Base64
            {"name": "Test Client", "role": "YWRtaW4="},  # "admin" in base64
        ]
        
        for encoded_data in encoding_attacks:
            # Add required fields
            full_data = {
                **encoded_data,
                "cpf": "123456789",
                "birth_date": "1990-01-01"
            }
            
            response = security_test_client.client.post(
                "/api/v1/clients",
                json=full_data,
                headers=headers
            )
            
            # Should handle encoded data safely
            if response.status_code == 201:
                created_client = response.json()
                # Should not interpret encoded admin role
                assert "role" not in created_client or created_client["role"] != "admin", f"Encoding manipulation should not grant admin role: {encoded_data}"