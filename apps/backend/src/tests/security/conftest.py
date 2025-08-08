"""
Security test fixtures and utilities.

This module provides specialized fixtures for security testing,
including attack vector data, malicious user scenarios, and
security-focused test helpers.
"""

import pytest
from typing import Dict, Any, List
from uuid import UUID
from unittest.mock import Mock
from sqlmodel import Session

from src.core.security import auth_service
from src.models.user import User, UserRole
from src.tests.factories import UserFactory, ClientFactory


@pytest.fixture
def malicious_strings() -> List[str]:
    """
    Comprehensive list of malicious input strings for security testing.
    
    This fixture provides real attack vectors that the system must properly reject.
    These are actual malicious inputs that could cause security vulnerabilities.
    """
    return [
        # SQL Injection attacks
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; DELETE FROM clients WHERE '1'='1'; --",
        "' UNION SELECT password FROM users --",
        "admin'; UPDATE users SET role = 'sysadmin' WHERE email = 'user@test.com'; --",
        
        # XSS attacks  
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "';alert('XSS');//",
        
        # Path traversal attacks
        "../../etc/passwd",
        "../../../etc/shadow", 
        "..\\..\\windows\\system32\\config\\sam",
        "./../.env",
        "../../../../etc/hosts",
        
        # Command injection
        "; rm -rf /",
        "; cat /etc/passwd",
        "&& rm -rf /*",
        "| whoami",
        "`cat /etc/passwd`",
        
        # LDAP injection
        "admin)(&(password=*)",
        "admin)(|(password=*))",
        "admin)(!(&(1=1)))",
        
        # NoSQL injection
        "admin'||'1'=='1",
        "' || 1==1 || '",
        "'; return db.users.find(); var foo='",
        
        # Template injection
        "${7*7}",
        "{{7*7}}",
        "<%= 7*7 %>",
        "#{7*7}",
        
        # XXE attacks
        "<?xml version=\"1.0\"?><!DOCTYPE root [<!ENTITY test SYSTEM 'file:///etc/passwd'>]><root>&test;</root>",
        
        # HTTP parameter pollution
        "name=admin&name=user",
        "role=user&role=sysadmin",
    ]


@pytest.fixture
def malicious_jwt_tokens() -> List[str]:
    """
    Malicious JWT token variations for security testing.
    
    These tokens test various JWT-based attack scenarios including
    token manipulation, signature bypasses, and algorithm confusion.
    """
    return [
        # Malformed tokens
        "invalid.jwt.token",
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.INVALID.signature",
        
        # Algorithm none attack
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.",
        
        # Role manipulation attempts (base64 encoded payloads with tampered roles)
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIiwicm9sZSI6InN5c2FkbWluIn0.invalid_signature",
        
        # Expired token
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjoxfQ.invalid_signature",
        
        # Empty token
        "",
        
        # Non-JWT string
        "this_is_not_a_jwt_token",
        
        # Token with SQL injection in claims
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiInOyBEUk9QIFRBQkxFIHVzZXJzOyAtLSIsInJvbGUiOiJ1c2VyIn0.invalid_signature",
    ]


@pytest.fixture
def attack_user_scenarios(test_session: Session) -> Dict[str, User]:
    """
    Create different user scenarios for attack testing.
    
    These users represent different attack scenarios and privilege levels
    that attackers might attempt to exploit or escalate to.
    """
    users = {}
    
    # Regular user (potential attacker)
    users['regular_user'] = UserFactory(
        role=UserRole.USER,
        email="attacker@test.com",
        full_name="Potential Attacker",
        is_active=True,
        failed_login_attempts=0
    )
    
    # Admin user (escalation target)
    users['admin_user'] = UserFactory(
        role=UserRole.ADMIN,
        email="admin@test.com", 
        full_name="Admin Target",
        is_active=True,
        failed_login_attempts=0
    )
    
    # Sysadmin user (ultimate target)
    users['sysadmin_user'] = UserFactory(
        role=UserRole.SYSADMIN,
        email="sysadmin@test.com",
        full_name="System Administrator",
        is_active=True,
        failed_login_attempts=0
    )
    
    # Disabled user (should never get access)
    users['disabled_user'] = UserFactory(
        role=UserRole.USER,
        email="disabled@test.com",
        full_name="Disabled User",
        is_active=False,
        failed_login_attempts=0
    )
    
    # Locked user (brute force victim)
    users['locked_user'] = UserFactory(
        role=UserRole.USER,
        email="locked@test.com",
        full_name="Locked User", 
        is_active=True,
        failed_login_attempts=6  # Exceeds threshold
    )
    
    # Add all users to session
    for user in users.values():
        test_session.add(user)
    
    test_session.commit()
    
    # Refresh instances to get IDs
    for user in users.values():
        test_session.refresh(user)
    
    return users


@pytest.fixture 
def security_test_client(client):
    """
    Enhanced test client with security testing utilities.
    
    This fixture wraps the standard test client with additional
    security testing methods and attack simulation capabilities.
    """
    class SecurityTestClient:
        def __init__(self, client):
            self.client = client
            
        def attempt_sql_injection(self, endpoint: str, payload: str, method: str = "POST"):
            """Attempt SQL injection attack on endpoint"""
            if method == "POST":
                return self.client.post(endpoint, json={"malicious_input": payload})
            elif method == "GET":
                return self.client.get(f"{endpoint}?param={payload}")
            
        def attempt_xss(self, endpoint: str, payload: str):
            """Attempt XSS attack on endpoint"""
            return self.client.post(endpoint, json={"content": payload})
            
        def attempt_path_traversal(self, endpoint: str, payload: str):
            """Attempt path traversal attack"""
            return self.client.get(f"{endpoint}?file={payload}")
            
        def brute_force_login(self, email: str, password_attempts: List[str]):
            """Simulate brute force login attempts"""
            responses = []
            for password in password_attempts:
                response = self.client.post("/api/v1/auth/login", json={
                    "email": email,
                    "password": password
                })
                responses.append(response)
            return responses
            
        def attempt_privilege_escalation(self, token: str, target_role: str):
            """Attempt to escalate privileges via API manipulation"""
            headers = {"Authorization": f"Bearer {token}"}
            return self.client.post("/api/v1/users/me", 
                                  json={"role": target_role}, 
                                  headers=headers)
    
    return SecurityTestClient(client)


@pytest.fixture
def mock_redis_for_security():
    """
    Mock Redis for security tests that need to test boundaries.
    
    This fixture mocks Redis (external dependency) while allowing
    real security logic to execute.
    """
    mock_redis = Mock()
    mock_redis.get.return_value = None  # Simulate cache miss
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = False  # Not blacklisted
    mock_redis.ping.return_value = True
    
    return mock_redis


@pytest.fixture
def security_headers() -> Dict[str, str]:
    """
    Expected security headers for response validation.
    
    These headers should be present in responses to prevent
    various security vulnerabilities.
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY", 
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }


@pytest.fixture
def rate_limit_test_data():
    """
    Test data for rate limiting security tests.
    
    Provides configuration for testing various rate limiting scenarios
    including normal usage, threshold testing, and attack simulation.
    """
    return {
        "login_rate_limit": {
            "threshold": 5,  # Max login attempts
            "window": 900,   # 15 minutes
            "lockout_duration": 1800  # 30 minutes
        },
        "api_rate_limit": {
            "threshold": 1000,  # Max API calls
            "window": 3600,     # 1 hour  
            "burst_limit": 100   # Max burst requests
        },
        "password_reset_limit": {
            "threshold": 3,   # Max password reset attempts
            "window": 3600    # 1 hour
        }
    }


@pytest.fixture
def security_audit_expectations():
    """
    Expected audit log entries for security events.
    
    This fixture defines what audit log entries should be created
    for various security events and attack attempts.
    """
    return {
        "failed_login": {
            "action": "LOGIN_FAILED",
            "risk_level": "MEDIUM",
            "required_fields": ["user_email", "ip_address", "user_agent", "failure_reason"]
        },
        "account_lockout": {
            "action": "ACCOUNT_LOCKED", 
            "risk_level": "HIGH",
            "required_fields": ["user_id", "lockout_reason", "failed_attempts", "ip_address"]
        },
        "privilege_escalation_attempt": {
            "action": "PRIVILEGE_ESCALATION_ATTEMPTED",
            "risk_level": "CRITICAL",
            "required_fields": ["user_id", "attempted_role", "current_role", "endpoint"]
        },
        "malicious_input_detected": {
            "action": "MALICIOUS_INPUT_DETECTED",
            "risk_level": "HIGH", 
            "required_fields": ["input_type", "payload_sample", "endpoint", "user_id"]
        },
        "jwt_manipulation_attempt": {
            "action": "JWT_MANIPULATION_ATTEMPTED",
            "risk_level": "HIGH",
            "required_fields": ["token_sample", "manipulation_type", "ip_address"]
        }
    }