"""End-to-end tests for authentication UI flows."""

import pytest
from nicegui.testing import Screen


class TestAuthUI:
    """E2E tests for authentication user interface."""
    
    @pytest.mark.e2e
    def test_homepage_displays_correctly(self, screen: Screen) -> None:
        """Test that the homepage displays correctly."""
        screen.open("/")
        
        # Check if main elements are present
        screen.should_contain("IAM Dashboard")
        screen.should_contain("Sistema de Advocacia SaaS")
        screen.should_contain("Login")
        screen.should_contain("Registrar")
    
    @pytest.mark.e2e
    def test_navigation_to_login_page(self, screen: Screen) -> None:
        """Test navigation from homepage to login page."""
        screen.open("/")
        
        # Click on Login button
        screen.click("Login")
        
        # Should navigate to login page
        screen.wait_for_url("/login")
        screen.should_contain("Login")
        screen.should_contain("Nome de usuário")
        screen.should_contain("Senha")
    
    @pytest.mark.e2e
    def test_navigation_to_register_page(self, screen: Screen) -> None:
        """Test navigation from homepage to register page."""
        screen.open("/")
        
        # Click on Register button
        screen.click("Registrar")
        
        # Should navigate to register page
        screen.wait_for_url("/register")
        screen.should_contain("Registro de Usuário")
        screen.should_contain("Nome de usuário")
        screen.should_contain("Senha")
        screen.should_contain("Confirmar senha")
    
    @pytest.mark.e2e
    def test_login_page_displays_correctly(self, screen: Screen) -> None:
        """Test that the login page displays all required elements."""
        screen.open("/login")
        
        # Check for form elements
        screen.should_contain("Login")
        screen.should_contain("Nome de usuário")
        screen.should_contain("Senha")
        screen.should_contain("Entrar")
        screen.should_contain("Não tem uma conta?")
    
    @pytest.mark.e2e
    def test_register_page_displays_correctly(self, screen: Screen) -> None:
        """Test that the register page displays all required elements."""
        screen.open("/register")
        
        # Check for form elements
        screen.should_contain("Registro de Usuário")
        screen.should_contain("Nome de usuário")
        screen.should_contain("Senha")
        screen.should_contain("Confirmar senha")
        screen.should_contain("Função")
        screen.should_contain("Habilitar Autenticação em Dois Fatores (2FA)")
        screen.should_contain("Registrar")
        screen.should_contain("Já tem uma conta?")
    
    @pytest.mark.e2e
    def test_login_form_validation_empty_fields(self, screen: Screen) -> None:
        """Test login form validation with empty fields."""
        screen.open("/login")
        
        # Try to submit with empty fields
        screen.click("Entrar")
        
        # Should show validation message
        screen.should_contain("Nome de usuário é obrigatório")
    
    @pytest.mark.e2e
    def test_register_form_validation_empty_fields(self, screen: Screen) -> None:
        """Test register form validation with empty fields."""
        screen.open("/register")
        
        # Try to submit with empty fields
        screen.click("Registrar")
        
        # Should show validation message
        screen.should_contain("Nome de usuário é obrigatório")
    
    @pytest.mark.e2e
    def test_register_form_validation_password_mismatch(self, screen: Screen) -> None:
        """Test register form validation with password mismatch."""
        screen.open("/register")
        
        # Fill form with mismatched passwords
        screen.type("testuser", into="Nome de usuário")
        screen.type("password123", into="Senha")
        screen.type("different_password", into="Confirmar senha")
        
        # Submit form
        screen.click("Registrar")
        
        # Should show validation message
        screen.should_contain("Senhas não coincidem")
    
    @pytest.mark.e2e
    def test_register_form_validation_short_password(self, screen: Screen) -> None:
        """Test register form validation with short password."""
        screen.open("/register")
        
        # Fill form with short password
        screen.type("testuser", into="Nome de usuário")
        screen.type("123", into="Senha")
        screen.type("123", into="Confirmar senha")
        
        # Submit form
        screen.click("Registrar")
        
        # Should show validation message
        screen.should_contain("Senha deve ter pelo menos 8 caracteres")
    
    @pytest.mark.e2e
    def test_register_form_validation_short_username(self, screen: Screen) -> None:
        """Test register form validation with short username."""
        screen.open("/register")
        
        # Fill form with short username
        screen.type("ab", into="Nome de usuário")
        screen.type("password123", into="Senha")
        screen.type("password123", into="Confirmar senha")
        
        # Submit form
        screen.click("Registrar")
        
        # Should show validation message
        screen.should_contain("Nome de usuário deve ter pelo menos 3 caracteres")
    
    @pytest.mark.e2e
    def test_login_with_invalid_credentials(self, screen: Screen) -> None:
        """Test login with invalid credentials."""
        screen.open("/login")
        
        # Fill form with invalid credentials
        screen.type("nonexistent_user", into="Nome de usuário")
        screen.type("wrong_password", into="Senha")
        
        # Submit form
        screen.click("Entrar")
        
        # Should show error message
        screen.should_contain("Credenciais inválidas")
    
    @pytest.mark.e2e
    def test_navigation_links_work(self, screen: Screen) -> None:
        """Test that navigation links between login and register work."""
        # Start at login page
        screen.open("/login")
        
        # Click "Registrar-se" link
        screen.click("Registrar-se")
        screen.wait_for_url("/register")
        screen.should_contain("Registro de Usuário")
        
        # Click "Fazer login" link
        screen.click("Fazer login")
        screen.wait_for_url("/login")
        screen.should_contain("Login")
    
    @pytest.mark.e2e
    def test_redirect_to_login_when_accessing_protected_page(self, screen: Screen) -> None:
        """Test that accessing protected pages redirects to login."""
        # Try to access dashboard without authentication
        screen.open("/dashboard")
        
        # Should redirect to login page
        screen.wait_for_url("/login")
        screen.should_contain("Login")
    
    @pytest.mark.e2e
    def test_2fa_settings_page_requires_auth(self, screen: Screen) -> None:
        """Test that 2FA settings page requires authentication."""
        # Try to access 2FA settings without authentication
        screen.open("/settings/2fa")
        
        # Should redirect to login page
        screen.wait_for_url("/login")
        screen.should_contain("Login")