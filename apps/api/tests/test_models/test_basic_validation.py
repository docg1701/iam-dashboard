"""
Basic validation tests for models.

Simple tests that verify model behavior without complex database setup.
"""
import pytest
import uuid
from datetime import date, datetime, timedelta
from pydantic import ValidationError


def test_user_role_enum():
    """Test UserRole enumeration values."""
    from src.models.user import UserRole
    
    assert UserRole.SYSADMIN.value == "sysadmin"
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.USER.value == "user"
    
    # Test iteration
    roles = list(UserRole)
    assert len(roles) == 3
    assert UserRole.SYSADMIN in roles
    assert UserRole.ADMIN in roles
    assert UserRole.USER in roles


def test_agent_name_enum():
    """Test AgentName enumeration values."""
    from src.models.permission import AgentName
    
    assert AgentName.CLIENT_MANAGEMENT.value == "client_management"
    assert AgentName.PDF_PROCESSING.value == "pdf_processing"
    assert AgentName.REPORTS_ANALYSIS.value == "reports_analysis"
    assert AgentName.AUDIO_RECORDING.value == "audio_recording"
    
    # Test iteration
    agents = list(AgentName)
    assert len(agents) == 4
    assert AgentName.CLIENT_MANAGEMENT in agents
    assert AgentName.PDF_PROCESSING in agents
    assert AgentName.REPORTS_ANALYSIS in agents
    assert AgentName.AUDIO_RECORDING in agents


def test_audit_action_enum():
    """Test AuditAction enumeration values."""
    from src.models.audit import AuditAction
    
    assert AuditAction.CREATE.value == "create"
    assert AuditAction.READ.value == "read"
    assert AuditAction.UPDATE.value == "update"
    assert AuditAction.DELETE.value == "delete"
    assert AuditAction.LOGIN.value == "login"
    assert AuditAction.LOGOUT.value == "logout"
    assert AuditAction.PERMISSION_CHANGE.value == "permission_change"
    
    # Test iteration
    actions = list(AuditAction)
    assert len(actions) == 7


def test_client_cpf_validation_function():
    """Test CPF validation logic directly."""
    from src.models.client import Client
    
    # These are the validation rules from the Client model
    valid_cpfs = [
        "11144477735",  # Valid CPF format
        "22233366644",
        "33322211100",
    ]
    
    invalid_cpfs = [
        "11111111111",  # All same digits
        "00000000000",  # All zeros
        "123456789",    # Too short
        "1234567890123", # Too long
        "",             # Empty
    ]
    
    # Test that the validation function catches these cases
    for cpf in invalid_cpfs:
        try:
            Client.validate_cpf(cpf)
            assert False, f"Should have failed for CPF: {cpf}"
        except ValueError:
            pass  # Expected to fail


def test_client_birth_date_validation_function():
    """Test birth date validation logic directly."""
    from src.models.client import Client
    
    today = date.today()
    
    # Valid dates - ensuring exact age calculation
    valid_dates = [
        date(today.year - 16, today.month, min(today.day, 28)),  # Exactly 16 years old
        date(today.year - 25, today.month, min(today.day, 28)),  # 25 years old
        date(today.year - 50, today.month, min(today.day, 28)),  # 50 years old
    ]
    
    for birth_date in valid_dates:
        result = Client.validate_birth_date(birth_date)
        assert result == birth_date
    
    # Invalid dates
    future_date = today + timedelta(days=1)
    too_young = date(today.year - 15, today.month, min(today.day, 28))  # 15 years old
    too_old = date(today.year - 121, today.month, min(today.day, 28))   # 121 years old
    
    # Test future date
    with pytest.raises(ValueError, match="future"):
        Client.validate_birth_date(future_date)
    
    # Test too young
    with pytest.raises(ValueError, match="16 years"):
        Client.validate_birth_date(too_young)
    
    # Test too old  
    with pytest.raises(ValueError, match="unreasonably old"):
        Client.validate_birth_date(too_old)


def test_factory_utilities():
    """Test factory utility functions."""
    from tests.factories.base_factory import BaseFactory
    
    # Test email generation
    email = BaseFactory.generate_email()
    assert "@" in email
    assert email.endswith("example.com")
    
    # Test string generation
    test_string = BaseFactory.generate_string(10)
    assert len(test_string) == 10
    assert test_string.isalpha()
    
    # Test name generation
    name = BaseFactory.generate_name()
    assert len(name.split()) >= 2  # Should have at least first and last name
    
    # Test CPF generation
    cpf = BaseFactory.generate_cpf()
    assert len(cpf) == 11
    assert cpf.isdigit()
    
    # Test birth date generation
    birth_date = BaseFactory.generate_birth_date()
    assert isinstance(birth_date, date)
    today = date.today()
    age_days = (today - birth_date).days
    age_years = age_days / 365
    assert 18 <= age_years <= 80  # Default age range
    
    # Test IP address generation
    ip = BaseFactory.generate_ip_address()
    parts = ip.split(".")
    assert len(parts) == 4
    for part in parts:
        assert 1 <= int(part) <= 254
    
    # Test session ID generation
    session_id = BaseFactory.generate_session_id()
    assert len(session_id) == 32
    assert session_id.isalnum()


def test_sample_cpfs():
    """Test that sample CPFs from factory are valid."""
    from tests.factories.client_factory import ClientFactory
    from src.models.client import Client
    
    sample_cpfs = ClientFactory.get_sample_cpfs()
    assert len(sample_cpfs) >= 5
    
    for cpf in sample_cpfs:
        # Should not raise validation error
        result = Client.validate_cpf(cpf)
        assert result == cpf


def test_invalid_cpfs():
    """Test that invalid CPFs from factory are properly invalid."""
    from tests.factories.client_factory import ClientFactory
    from src.models.client import Client
    
    invalid_cpfs = ClientFactory.get_invalid_cpfs()
    assert len(invalid_cpfs) >= 5
    
    for cpf in invalid_cpfs:
        with pytest.raises(ValueError):
            Client.validate_cpf(cpf)


if __name__ == "__main__":
    # Run basic validation tests
    print("Running basic model validation tests...")
    
    try:
        test_user_role_enum()
        print("✅ UserRole enum tests passed")
        
        test_agent_name_enum()
        print("✅ AgentName enum tests passed")
        
        test_audit_action_enum()
        print("✅ AuditAction enum tests passed")
        
        test_client_cpf_validation_function()
        print("✅ CPF validation tests passed")
        
        test_client_birth_date_validation_function()
        print("✅ Birth date validation tests passed")
        
        test_factory_utilities()
        print("✅ Factory utility tests passed")
        
        test_sample_cpfs()
        print("✅ Sample CPF tests passed")
        
        test_invalid_cpfs()
        print("✅ Invalid CPF tests passed")
        
        print("🎉 All basic validation tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()