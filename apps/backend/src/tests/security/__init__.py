"""
Security testing module for IAM Dashboard.

This module contains comprehensive security tests covering:
- Input validation security (SQL injection, XSS, path traversal)
- Permission escalation prevention
- Authentication attack scenarios
- Authorization bypass prevention  
- Data leakage protection

All tests follow the "Mock the boundaries, not the behavior" principle,
testing real security logic while only mocking external dependencies.
"""