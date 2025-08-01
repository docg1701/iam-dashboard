"""E2E test for login functionality using MCP Playwright."""

import pytest


class TestLogin:
    """E2E test for login page access."""

    @pytest.mark.e2e
    def test_access_login_page(self):
        """Test accessing the login page."""
        import requests
        
        try:
            # Test homepage first
            response = requests.get("http://localhost:8080", timeout=10)
            assert response.status_code == 200, f"Homepage not accessible: {response.status_code}"
            
            # Test login page access
            response = requests.get("http://localhost:8080/login", timeout=10)
            assert response.status_code == 200, f"Login page not accessible: {response.status_code}"
            
            print("✓ Login page is accessible for MCP Playwright testing")
            
        except Exception as e:
            pytest.fail(f"Login page access failed: {e}")
        
        assert True, "Login page access validated"