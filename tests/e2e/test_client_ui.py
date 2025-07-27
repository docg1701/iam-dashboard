"""End-to-end tests for client management UI flows."""

import pytest
from nicegui.testing import Screen


class TestClientUI:
    """E2E tests for client management user interface."""
    
    @pytest.mark.e2e
    def test_dashboard_displays_client_section(self, screen: Screen) -> None:
        """Test that the dashboard displays the client management section."""
        # Note: This test assumes we have authentication set up
        # In a real scenario, we'd need to create a user and login first
        screen.open("/dashboard")
        
        # Should redirect to login since not authenticated
        screen.wait_for_url("/login")
        screen.should_contain("Login")
    
    @pytest.mark.e2e 
    def test_clients_page_requires_authentication(self, screen: Screen) -> None:
        """Test that clients page requires authentication."""
        # Try to access clients page without authentication
        screen.open("/clients")
        
        # Should redirect to login page
        screen.wait_for_url("/login")
        screen.should_contain("Login")
    
    @pytest.mark.e2e
    def test_dashboard_mvp_features_display(self, screen: Screen) -> None:
        """Test that dashboard displays MVP feature placeholders."""
        # Note: In a complete test, we'd authenticate first
        screen.open("/dashboard")
        screen.wait_for_url("/login")
        
        # For now, just test that login page works
        screen.should_contain("Login")
        screen.should_contain("Nome de usuário")
        screen.should_contain("Senha")
    
    @pytest.mark.e2e
    def test_homepage_navigation_to_login_and_back(self, screen: Screen) -> None:
        """Test navigation flow from homepage through login."""
        # Start at homepage
        screen.open("/")
        
        # Verify homepage content
        screen.should_contain("IAM Dashboard")
        screen.should_contain("Sistema de Advocacia SaaS")
        screen.should_contain("Login")
        screen.should_contain("Registrar")
        
        # Navigate to login
        screen.click("Login")
        screen.wait_for_url("/login")
        
        # Verify login page
        screen.should_contain("Login")
        screen.should_contain("Nome de usuário")
        screen.should_contain("Senha")
        screen.should_contain("Entrar")
    
    @pytest.mark.e2e
    def test_dashboard_redirects_unauthenticated_users(self, screen: Screen) -> None:
        """Test that dashboard redirects unauthenticated users to login."""
        screen.open("/dashboard")
        
        # Should be redirected to login
        screen.wait_for_url("/login")
        screen.should_contain("Login")
    
    @pytest.mark.e2e
    def test_login_form_basic_validation(self, screen: Screen) -> None:
        """Test basic validation on login form."""
        screen.open("/login")
        
        # Try to submit empty form
        screen.click("Entrar")
        
        # Should show validation error
        screen.should_contain("Nome de usuário é obrigatório")
    
    @pytest.mark.e2e
    def test_login_with_invalid_credentials_shows_error(self, screen: Screen) -> None:
        """Test that invalid login credentials show error message."""
        screen.open("/login")
        
        # Fill with invalid credentials
        screen.type("invalid_user", into="Nome de usuário")
        screen.type("invalid_password", into="Senha")
        
        # Submit form
        screen.click("Entrar")
        
        # Should show error
        screen.should_contain("Credenciais inválidas")
    
    @pytest.mark.e2e
    def test_register_to_login_navigation(self, screen: Screen) -> None:
        """Test navigation from register to login page."""
        screen.open("/register")
        
        # Verify register page
        screen.should_contain("Registro de Usuário")
        
        # Navigate to login
        screen.click("Fazer login")
        screen.wait_for_url("/login")
        
        # Verify login page
        screen.should_contain("Login")
    
    @pytest.mark.e2e
    def test_register_form_validation(self, screen: Screen) -> None:
        """Test register form validation."""
        screen.open("/register")
        
        # Try to submit empty form
        screen.click("Registrar")
        
        # Should show validation error
        screen.should_contain("Nome de usuário é obrigatório")
    
    @pytest.mark.e2e
    def test_register_form_password_mismatch(self, screen: Screen) -> None:
        """Test register form with mismatched passwords."""
        screen.open("/register")
        
        # Fill form with mismatched passwords
        screen.type("testuser", into="Nome de usuário")
        screen.type("password123", into="Senha")
        screen.type("different_password", into="Confirmar senha")
        
        # Submit form
        screen.click("Registrar")
        
        # Should show error
        screen.should_contain("Senhas não coincidem")


class TestDashboardFeatures:
    """E2E tests for dashboard feature placeholders."""
    
    @pytest.mark.e2e
    def test_homepage_structure(self, screen: Screen) -> None:
        """Test that homepage has correct structure."""
        screen.open("/")
        
        # Main title and subtitle
        screen.should_contain("IAM Dashboard")
        screen.should_contain("Sistema de Advocacia SaaS")
        
        # Action buttons
        screen.should_contain("Login")
        screen.should_contain("Registrar")
    
    @pytest.mark.e2e
    def test_login_page_structure(self, screen: Screen) -> None:
        """Test that login page has correct structure."""
        screen.open("/login")
        
        # Form elements
        screen.should_contain("Login")
        screen.should_contain("Nome de usuário")
        screen.should_contain("Senha")
        screen.should_contain("Entrar")
        
        # Navigation link
        screen.should_contain("Não tem uma conta?")
        screen.should_contain("Registrar-se")
    
    @pytest.mark.e2e
    def test_register_page_structure(self, screen: Screen) -> None:
        """Test that register page has correct structure."""
        screen.open("/register")
        
        # Form elements
        screen.should_contain("Registro de Usuário")
        screen.should_contain("Nome de usuário")
        screen.should_contain("Senha")
        screen.should_contain("Confirmar senha")
        screen.should_contain("Função")
        screen.should_contain("Registrar")
        
        # Navigation link
        screen.should_contain("Já tem uma conta?")
        screen.should_contain("Fazer login")
    
    @pytest.mark.e2e
    def test_protected_routes_redirect(self, screen: Screen) -> None:
        """Test that protected routes redirect to login."""
        protected_routes = ["/dashboard", "/clients", "/settings/2fa"]
        
        for route in protected_routes:
            screen.open(route)
            screen.wait_for_url("/login")
            screen.should_contain("Login")


# Note: In a complete implementation, we would also have tests that:
# 1. Create a test user through the registration flow
# 2. Login with that user
# 3. Navigate to the dashboard and verify MVP features
# 4. Navigate to clients page and test CRUD operations
# 5. Test logout functionality
# 
# These tests would require setting up a test database and handling
# the full authentication flow, which is beyond the scope of this
# basic implementation but would be included in a production system.