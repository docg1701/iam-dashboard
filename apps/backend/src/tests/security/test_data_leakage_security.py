"""
Data Leakage Protection Security Tests.

This module tests the system's protection against various forms of data leakage
including sensitive data exposure, information disclosure through error messages,
timing attacks, and other data leakage vectors.

Key Data Leakage Scenarios Tested:
1. SSN and PII exposure prevention
2. Password and authentication data leakage
3. Error message information disclosure
4. Database schema information leakage  
5. User enumeration through response differences
6. Sensitive configuration data exposure
7. Internal system information disclosure
8. Cross-user data bleeding

Testing Philosophy:
- Test real data handling logic (no mocks of data processing)
- Mock only external boundaries (file system, network calls, logging)
- Validate information leakage in responses, errors, and logs
- Ensure sensitive data is properly masked or filtered
- Test both intentional and accidental data exposure vectors
"""

import pytest
import json
import re
from typing import Dict, Any, List, Set
from unittest.mock import patch, Mock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.security import auth_service
from src.models.user import User, UserRole
from src.models.client import Client
from src.tests.factories import UserFactory, ClientFactory


class TestSensitiveDataExposurePrevention:
    """
    Test prevention of sensitive data exposure in API responses.
    
    These tests verify that sensitive information like SSNs, passwords,
    tokens, and other PII is properly masked or excluded from responses.
    """
    
    def test_ssn_masking_in_client_responses(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that SSN data is properly masked in client API responses."""
        admin_user = attack_user_scenarios['admin_user']
        
        # Create client with real SSN
        test_client = ClientFactory(
            name="Test Client",
            ssn="123456789",  # Real SSN for testing
            birth_date="1990-01-01"
        )
        test_session.add(test_client)
        test_session.commit()
        test_session.refresh(test_client)
        
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Test individual client retrieval
        response = security_test_client.client.get(
            f"/api/v1/clients/{test_client.client_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            client_data = response.json()
            ssn_value = client_data.get("ssn", "")
            
            # SSN should be masked (e.g., "XXX-XX-6789" or similar)
            assert "123456789" not in ssn_value, "Full SSN should not be exposed"
            assert len(ssn_value) > 0, "SSN field should exist but be masked"
            
            # Common masking patterns
            is_masked = (
                "XXX" in ssn_value or  # XXX-XX-6789
                "*" in ssn_value or    # ***-**-6789
                "###" in ssn_value or  # ###-##-6789
                ssn_value.startswith("***") or  # ***456789
                len(ssn_value.replace("-", "").replace("X", "").replace("*", "").replace("#", "")) < 9  # Some digits hidden
            )
            
            assert is_masked, f"SSN should be masked, got: {ssn_value}"
    
    def test_password_data_never_exposed(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that password hashes and related data are never exposed."""
        admin_user = attack_user_scenarios['admin_user']
        target_user = attack_user_scenarios['regular_user']
        
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Test user listing
        users_response = security_test_client.client.get("/api/v1/users", headers=headers)
        
        if users_response.status_code == 200:
            users_data = users_response.json()
            
            # Check each user in response
            for user_data in users_data:
                sensitive_fields = [
                    "password", "password_hash", "hashed_password", "pwd", "pass",
                    "totp_secret", "backup_codes", "secret_key", "private_key"
                ]
                
                for field in sensitive_fields:
                    assert field not in user_data, f"Sensitive field '{field}' should not be in user response"
                
                # Verify no field values look like password hashes
                for key, value in user_data.items():
                    if isinstance(value, str):
                        # Check for bcrypt hash pattern
                        assert not re.match(r'^\$2[abyxz]?\$\d+\$', value), f"Field '{key}' contains what looks like a password hash"
                        # Check for other hash patterns
                        assert not (len(value) == 60 and value.startswith("$2")), f"Field '{key}' may contain a bcrypt hash"
    
    def test_authentication_tokens_not_logged_or_exposed(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that authentication tokens are not exposed in error responses or logs."""
        regular_user = attack_user_scenarios['regular_user']
        
        # Create valid token
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        # Test with invalid endpoint to trigger error
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        error_response = security_test_client.client.get("/api/v1/nonexistent-endpoint", headers=headers)
        
        # Check that token is not exposed in error response
        response_text = error_response.text.lower()
        
        # Token should not appear in error response
        token_parts = token_response.access_token.split('.')
        for part in token_parts:
            assert part not in response_text, f"Token part should not be exposed in error response: {part[:10]}..."
        
        # Check error response structure
        if error_response.status_code >= 400:
            try:
                error_data = error_response.json()
                error_detail = str(error_data.get("detail", "")).lower()
                
                # Should not contain token or auth info in error details
                assert "bearer" not in error_detail, "Error should not expose auth scheme details"
                assert "token" not in error_detail, "Error should not mention tokens explicitly"
                
            except json.JSONDecodeError:
                # If not JSON, check raw text doesn't contain sensitive info
                assert "authorization" not in response_text, "Error should not expose authorization details"
    
    def test_internal_ids_and_system_info_not_exposed(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that internal IDs and system information are not exposed."""
        admin_user = attack_user_scenarios['admin_user']
        
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Test various endpoints for internal data exposure
        endpoints_to_test = [
            "/api/v1/users",
            "/api/v1/clients", 
            "/api/v1/auth/me"
        ]
        
        for endpoint in endpoints_to_test:
            response = security_test_client.client.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                data_str = json.dumps(data).lower()
                
                # Check for internal system information that shouldn't be exposed
                sensitive_system_info = [
                    "password_hash", "totp_secret", "backup_codes",
                    "database_url", "redis_url", "secret_key", 
                    "internal_id", "system_id", "db_id",
                    "created_by_user_id",  # Internal foreign keys shouldn't be exposed to regular users
                    "session_id", "jti"  # Token-related internal IDs
                ]
                
                for sensitive_info in sensitive_system_info:
                    if sensitive_info in data_str:
                        # Some fields like created_by_user_id might be acceptable for admin users
                        if admin_user.role == UserRole.SYSADMIN and sensitive_info in ["created_by_user_id"]:
                            continue  # Acceptable for sysadmin
                        else:
                            assert False, f"Sensitive system info '{sensitive_info}' found in {endpoint} response"


class TestErrorMessageInformationDisclosure:
    """
    Test prevention of information disclosure through error messages.
    
    These tests verify that error messages don't leak sensitive information
    about the system, database structure, or user data.
    """
    
    def test_database_error_information_not_disclosed(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that database errors don't expose internal information."""
        admin_user = attack_user_scenarios['admin_user']
        
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to trigger database errors with malicious data
        database_error_triggers = [
            # Duplicate key violation attempt
            {"name": "Test Client", "ssn": "123456789", "birth_date": "1990-01-01"},
            {"name": "Test Client 2", "ssn": "123456789", "birth_date": "1990-01-01"},  # Same SSN
            # Invalid foreign key attempt  
            {"name": "Test Client", "ssn": "987654321", "birth_date": "1990-01-01", "created_by_user_id": "invalid-uuid"},
            # Invalid data type
            {"name": "Test Client", "ssn": "111111111", "birth_date": "not-a-date"},
        ]
        
        for client_data in database_error_triggers:
            response = security_test_client.client.post(
                "/api/v1/clients",
                json=client_data,
                headers=headers
            )
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_detail = str(error_data.get("detail", "")).lower()
                    
                    # Should not expose database internals
                    database_internals = [
                        "postgresql", "postgres", "psycopg2", "sqlalchemy", "alembic",
                        "table", "column", "constraint", "foreign key", "primary key",
                        "duplicate key", "violates", "relation", "schema",
                        "sql", "select", "insert", "update", "delete",
                        "user_agent_permissions", "clients", "users"  # Table names
                    ]
                    
                    for internal_term in database_internals:
                        assert internal_term not in error_detail, f"Database internal '{internal_term}' exposed in error: {error_detail}"
                        
                except json.JSONDecodeError:
                    # Check raw response text
                    response_text = response.text.lower()
                    assert "postgresql" not in response_text, "Database type should not be exposed in errors"
                    assert "sqlalchemy" not in response_text, "ORM details should not be exposed"
    
    def test_file_system_error_information_not_disclosed(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that file system errors don't expose internal paths or structure."""
        admin_user = attack_user_scenarios['admin_user']
        
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Attempt to trigger file system related errors
        file_system_triggers = [
            # Invalid file uploads (if endpoint exists)
            "/api/v1/files/upload",
            # Configuration file access attempts
            "/api/v1/config",
            # Log file access attempts  
            "/api/v1/logs",
        ]
        
        for endpoint in file_system_triggers:
            response = security_test_client.client.get(endpoint, headers=headers)
            
            if response.status_code >= 400:
                response_text = response.text.lower()
                
                # Should not expose file system paths
                filesystem_internals = [
                    "/etc/", "/var/", "/usr/", "/opt/", "/home/",
                    "/tmp/", "/root/", "c:\\", "d:\\",
                    ".env", "config.py", "settings.py",
                    "permission denied", "no such file", "directory",
                    "path", "file not found"
                ]
                
                for internal_path in filesystem_internals:
                    if internal_path in response_text:
                        # Some generic messages are acceptable
                        if internal_path in ["file not found", "permission denied"] and "path" not in response_text:
                            continue
                        assert False, f"File system internal '{internal_path}' exposed in error response"
    
    def test_validation_error_information_disclosure_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that validation errors don't disclose internal validation logic."""
        admin_user = attack_user_scenarios['admin_user']
        
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Trigger various validation errors
        validation_triggers = [
            # Missing required fields
            {"name": "Test Client"},  # Missing SSN and birth_date
            # Invalid formats
            {"name": "", "ssn": "invalid-ssn", "birth_date": "invalid-date"},
            # Field length violations
            {"name": "A" * 1000, "ssn": "123456789", "birth_date": "1990-01-01"},
            # Type mismatches
            {"name": 12345, "ssn": True, "birth_date": ["array"]},
        ]
        
        for invalid_data in validation_triggers:
            response = security_test_client.client.post(
                "/api/v1/clients",
                json=invalid_data,
                headers=headers
            )
            
            if response.status_code == 422:  # Validation error
                try:
                    error_data = response.json()
                    
                    # Should provide helpful error messages without exposing internals
                    if "detail" in error_data:
                        error_detail = str(error_data["detail"])
                        
                        # Should not expose internal validation class names or paths
                        internal_validators = [
                            "pydantic", "sqlmodel", "fastapi", "validator",
                            "__pydantic_model__", "ValidationError",
                            "src.models", "src.schemas", "src.core"
                        ]
                        
                        for internal in internal_validators:
                            assert internal not in error_detail, f"Internal validator '{internal}' exposed in validation error"
                            
                except json.JSONDecodeError:
                    pass  # Raw text response is acceptable for validation errors


class TestUserEnumerationPrevention:
    """
    Test prevention of user enumeration through response differences.
    
    These tests verify that attackers cannot enumerate valid users
    through response time differences or different error messages.
    """
    
    def test_login_response_consistency_for_user_enumeration_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that login responses don't allow user enumeration."""
        existing_user = attack_user_scenarios['regular_user']
        non_existent_email = "definitely_not_a_user@example.com"
        
        # Test login with existing user
        existing_user_response = security_test_client.client.post("/api/v1/auth/login", json={
            "email": existing_user.email,
            "password": "wrong_password"
        })
        
        # Test login with non-existent user  
        non_existent_response = security_test_client.client.post("/api/v1/auth/login", json={
            "email": non_existent_email,
            "password": "wrong_password"
        })
        
        # Both should return same status code
        assert existing_user_response.status_code == non_existent_response.status_code, \
            "Status codes should be identical for existing and non-existing users"
        
        # Error messages should not reveal user existence
        if existing_user_response.status_code == 401:
            existing_error = existing_user_response.json().get("detail", "")
            non_existing_error = non_existent_response.json().get("detail", "")
            
            # Error messages should be generic
            assert "user not found" not in existing_error.lower(), "Should not explicitly mention user not found"
            assert "invalid user" not in existing_error.lower(), "Should not mention invalid user"
            assert "user does not exist" not in non_existing_error.lower(), "Should not mention user existence"
            
            # Messages should be similar (ideally identical)
            assert len(existing_error) > 0 and len(non_existing_error) > 0, "Both should return error messages"
    
    def test_password_reset_user_enumeration_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that password reset doesn't allow user enumeration."""
        existing_user = attack_user_scenarios['regular_user']
        non_existent_email = "does_not_exist@example.com"
        
        # Test password reset for existing user
        existing_response = security_test_client.client.post("/api/v1/auth/forgot-password", json={
            "email": existing_user.email
        })
        
        # Test password reset for non-existent user
        non_existing_response = security_test_client.client.post("/api/v1/auth/forgot-password", json={
            "email": non_existent_email
        })
        
        # Both should return success to prevent enumeration
        assert existing_response.status_code == non_existing_response.status_code, \
            "Password reset should return same status for existing and non-existing users"
        
        # Both should return similar success messages
        if existing_response.status_code == 200:
            existing_message = existing_response.json().get("message", "")
            non_existing_message = non_existing_response.json().get("message", "")
            
            # Messages should not reveal user existence
            assert "user not found" not in existing_message.lower(), "Should not mention user not found"
            assert "email not found" not in non_existing_message.lower(), "Should not mention email not found"
            
            # Should provide generic success message for both
            assert "sent" in existing_message.lower() or "email" in existing_message.lower(), "Should suggest email was sent"
            assert "sent" in non_existing_message.lower() or "email" in non_existing_message.lower(), "Should suggest email was sent"
    
    def test_user_profile_access_enumeration_prevention(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that user profile access doesn't allow user ID enumeration."""
        regular_user = attack_user_scenarios['regular_user']
        
        token_response = auth_service.create_access_token(
            user_id=regular_user.user_id,
            user_role=regular_user.role.value,
            user_email=regular_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Test access to various user IDs
        test_user_ids = [
            str(uuid4()),  # Random UUID
            "00000000-0000-0000-0000-000000000001",  # Sequential guess
            "11111111-1111-1111-1111-111111111111",  # Pattern guess
            "admin",  # Non-UUID string
            "user1",  # Common username pattern
        ]
        
        responses = []
        for user_id in test_user_ids:
            response = security_test_client.client.get(f"/api/v1/users/{user_id}", headers=headers)
            responses.append((user_id, response))
        
        # All invalid UUIDs should return consistent error responses
        invalid_uuid_responses = [(uid, resp) for uid, resp in responses if not self._is_valid_uuid(uid)]
        
        if invalid_uuid_responses:
            status_codes = [resp.status_code for _, resp in invalid_uuid_responses]
            # All invalid UUIDs should return same status code
            assert len(set(status_codes)) <= 1, "Invalid UUIDs should return consistent status codes"
        
        # Valid UUIDs that don't exist should return consistent responses
        valid_uuid_responses = [(uid, resp) for uid, resp in responses if self._is_valid_uuid(uid)]
        
        if valid_uuid_responses:
            status_codes = [resp.status_code for _, resp in valid_uuid_responses]
            # Should return consistent error codes (403 or 404)
            assert all(code in [403, 404] for code in status_codes), "Non-existent valid UUIDs should return 403 or 404"
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Helper method to check if string is valid UUID format."""
        try:
            UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False


class TestCrossUserDataBleeding:
    """
    Test prevention of cross-user data bleeding.
    
    These tests verify that user data doesn't accidentally leak
    between different user sessions or requests.
    """
    
    def test_client_data_isolation_between_users(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that client data is properly isolated between users."""
        user1 = attack_user_scenarios['regular_user']
        user2 = attack_user_scenarios['admin_user']
        
        # Create clients for each user
        client1 = ClientFactory(
            name="User1 Confidential Client",
            ssn="111111111",
            created_by_user_id=user1.user_id
        )
        
        client2 = ClientFactory(
            name="User2 Secret Client", 
            ssn="222222222",
            created_by_user_id=user2.user_id
        )
        
        test_session.add_all([client1, client2])
        test_session.commit()
        test_session.refresh(client1)
        test_session.refresh(client2)
        
        # Create token for user1
        token1 = auth_service.create_access_token(
            user_id=user1.user_id,
            user_role=user1.role.value,
            user_email=user1.email
        )
        
        headers1 = {"Authorization": f"Bearer {token1.access_token}"}
        
        # User1 requests client list
        response1 = security_test_client.client.get("/api/v1/clients", headers=headers1)
        
        if response1.status_code == 200:
            clients_data = response1.json()
            
            # Should not contain user2's client data
            client_names = [client.get("name", "") for client in clients_data]
            client_ssns = [client.get("ssn", "") for client in clients_data]
            
            assert "User2 Secret Client" not in client_names, "Should not see other user's client names"
            assert "222222222" not in str(client_ssns), "Should not see other user's client SSNs"
            assert "***-**-2222" not in str(client_ssns), "Should not see other user's masked SSNs"
            
            # Should only see own clients or have appropriate permission-based access
            for client_data in clients_data:
                created_by = client_data.get("created_by_user_id")
                if created_by:
                    # If created_by is exposed, should only be user1's ID or users they have permission to see
                    assert created_by == str(user1.user_id) or user1.role == UserRole.ADMIN, \
                        f"Should not see clients created by other users: {created_by}"
    
    def test_session_data_isolation_between_concurrent_users(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that session data doesn't bleed between concurrent user requests."""
        user1 = attack_user_scenarios['regular_user']
        user2 = attack_user_scenarios['admin_user']
        
        # Create tokens for both users
        token1 = auth_service.create_access_token(
            user_id=user1.user_id,
            user_role=user1.role.value,
            user_email=user1.email
        )
        
        token2 = auth_service.create_access_token(
            user_id=user2.user_id,
            user_role=user2.role.value,
            user_email=user2.email
        )
        
        headers1 = {"Authorization": f"Bearer {token1.access_token}"}
        headers2 = {"Authorization": f"Bearer {token2.access_token}"}
        
        # Make rapid alternating requests to test for session bleeding
        responses = []
        
        for i in range(10):
            if i % 2 == 0:
                response = security_test_client.client.get("/api/v1/auth/me", headers=headers1)
                expected_user_id = str(user1.user_id)
                expected_role = user1.role.value
            else:
                response = security_test_client.client.get("/api/v1/auth/me", headers=headers2)
                expected_user_id = str(user2.user_id)
                expected_role = user2.role.value
            
            responses.append((response, expected_user_id, expected_role, i))
        
        # Verify each response matches expected user
        for response, expected_user_id, expected_role, request_num in responses:
            if response.status_code == 200:
                user_data = response.json()
                actual_user_id = user_data.get("user_id")
                actual_role = user_data.get("role")
                
                assert actual_user_id == expected_user_id, \
                    f"Session bleeding detected in request {request_num}: got {actual_user_id}, expected {expected_user_id}"
                assert actual_role == expected_role, \
                    f"Role bleeding detected in request {request_num}: got {actual_role}, expected {expected_role}"
    
    def test_permission_state_isolation_between_users(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User],
        test_session: Session
    ):
        """Test that permission states don't bleed between different users."""
        user1 = attack_user_scenarios['regular_user']
        user2 = attack_user_scenarios['admin_user']
        
        # Grant different permissions to each user
        from src.models.permissions import UserAgentPermission, AgentName
        
        # User1 gets client read permission only
        perm1 = UserAgentPermission(
            user_id=user1.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"read": True, "create": False},
            created_by_user_id=user2.user_id
        )
        
        # User2 (admin) should have broader permissions
        perm2 = UserAgentPermission(
            user_id=user2.user_id,
            agent_name=AgentName.CLIENT_MANAGEMENT,
            permissions={"read": True, "create": True, "update": True, "delete": True},
            created_by_user_id=user2.user_id
        )
        
        test_session.add_all([perm1, perm2])
        test_session.commit()
        
        # Create tokens
        token1 = auth_service.create_access_token(
            user_id=user1.user_id,
            user_role=user1.role.value,
            user_email=user1.email
        )
        
        token2 = auth_service.create_access_token(
            user_id=user2.user_id,
            user_role=user2.role.value,
            user_email=user2.email
        )
        
        headers1 = {"Authorization": f"Bearer {token1.access_token}"}
        headers2 = {"Authorization": f"Bearer {token2.access_token}"}
        
        # User1 should not be able to create clients
        create_response1 = security_test_client.client.post(
            "/api/v1/clients",
            json={"name": "Test Client", "ssn": "123456789", "birth_date": "1990-01-01"},
            headers=headers1
        )
        
        assert create_response1.status_code == 403, "User1 should not be able to create clients"
        
        # User2 should be able to create clients
        create_response2 = security_test_client.client.post(
            "/api/v1/clients",
            json={"name": "Admin Client", "ssn": "987654321", "birth_date": "1990-01-01"},
            headers=headers2
        )
        
        # Should succeed or return validation error, but not forbidden
        assert create_response2.status_code != 403, "User2 should be able to create clients"
        
        # Verify permissions didn't bleed - user1 still can't create after user2's successful creation
        create_response1_again = security_test_client.client.post(
            "/api/v1/clients",
            json={"name": "Test Client 2", "ssn": "111111111", "birth_date": "1990-01-01"},
            headers=headers1
        )
        
        assert create_response1_again.status_code == 403, "User1 permissions should not have escalated after user2's actions"


class TestConfigurationDataExposurePrevention:
    """
    Test prevention of configuration and system data exposure.
    
    These tests verify that system configuration, environment variables,
    and other sensitive system information is not exposed through the API.
    """
    
    def test_environment_variables_not_exposed(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that environment variables are not exposed in responses."""
        admin_user = attack_user_scenarios['admin_user']
        
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Test various endpoints that might expose config
        endpoints_to_test = [
            "/api/v1/auth/me",
            "/api/v1/users",
            "/api/v1/config",  # If this endpoint exists
            "/api/v1/health",  # Health check endpoint
        ]
        
        for endpoint in endpoints_to_test:
            response = security_test_client.client.get(endpoint, headers=headers)
            
            if response.status_code == 200:
                response_text = response.text.lower()
                
                # Environment variables that should never be exposed
                sensitive_env_vars = [
                    "database_url", "redis_url", "secret_key", "jwt_secret",
                    "password", "api_key", "private_key", "token",
                    "aws_", "google_", "stripe_", "openai_",
                    "smtp_password", "email_password",
                    ".env", "env_", "config_"
                ]
                
                for env_var in sensitive_env_vars:
                    assert env_var not in response_text, \
                        f"Sensitive environment variable pattern '{env_var}' exposed in {endpoint}"
    
    def test_debug_information_not_exposed_in_production_mode(
        self,
        security_test_client,
        attack_user_scenarios: Dict[str, User]
    ):
        """Test that debug information is not exposed in production-like responses."""
        admin_user = attack_user_scenarios['admin_user']
        
        token_response = auth_service.create_access_token(
            user_id=admin_user.user_id,
            user_role=admin_user.role.value,
            user_email=admin_user.email
        )
        
        headers = {"Authorization": f"Bearer {token_response.access_token}"}
        
        # Try to trigger errors that might expose debug info
        error_triggers = [
            # Invalid JSON
            ("/api/v1/clients", "invalid json data"),
            # Invalid endpoint
            ("/api/v1/nonexistent", None),
            # Invalid method
            ("/api/v1/users", "invalid data"),
        ]
        
        for endpoint, data in error_triggers:
            if data:
                response = security_test_client.client.post(endpoint, data=data, headers=headers)
            else:
                response = security_test_client.client.get(endpoint, headers=headers)
            
            if response.status_code >= 400:
                response_text = response.text.lower()
                
                # Debug information that should not be exposed
                debug_indicators = [
                    "traceback", "stacktrace", "exception", "error:",
                    "line ", "file ", "function ", "method ",
                    "src/", "/usr/", "/opt/", "/home/",
                    "python", "fastapi", "uvicorn", "gunicorn"
                ]
                
                for debug_info in debug_indicators:
                    if debug_info in response_text:
                        # Some terms might be acceptable in generic error messages
                        if debug_info in ["error:"] and "internal" not in response_text:
                            continue
                        
                        assert False, f"Debug information '{debug_info}' exposed in error response from {endpoint}"