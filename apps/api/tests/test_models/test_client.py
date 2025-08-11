"""
Unit tests for Client model.

Tests client creation, CPF validation, birth date validation, and audit fields.
"""
import pytest
import uuid
from datetime import date, datetime, timedelta
from pydantic import ValidationError

from src.models.client import Client
from tests.factories import ClientFactory, UserFactory


class TestClientModel:
    """Test suite for Client model."""
    
    def test_client_creation_with_defaults(self):
        """Test creating a client with default values."""
        client = ClientFactory.create_client()
        
        assert client.id is not None
        assert isinstance(client.id, uuid.UUID)
        assert len(client.name) >= 2
        assert len(client.cpf) == 11
        assert isinstance(client.birth_date, date)
        assert client.created_by is not None
        assert isinstance(client.created_by, uuid.UUID)
        assert isinstance(client.created_at, datetime)
        assert isinstance(client.updated_at, datetime)
        assert client.is_active is True
    
    def test_client_creation_with_custom_values(self):
        """Test creating a client with custom field values."""
        custom_name = "João Silva Santos"
        custom_cpf = "11144477735"
        custom_birth_date = date(1990, 5, 15)
        custom_created_by = uuid.uuid4()
        
        client = ClientFactory.create_client(
            name=custom_name,
            cpf=custom_cpf,
            birth_date=custom_birth_date,
            created_by=custom_created_by
        )
        
        assert client.name == custom_name
        assert client.cpf == custom_cpf
        assert client.birth_date == custom_birth_date
        assert client.created_by == custom_created_by
    
    def test_young_adult_client_creation(self):
        """Test creating a young adult client (18-25)."""
        client = ClientFactory.create_young_adult_client()
        
        today = date.today()
        age = today.year - client.birth_date.year
        if today.month < client.birth_date.month or \
           (today.month == client.birth_date.month and today.day < client.birth_date.day):
            age -= 1
        
        assert 18 <= age <= 25
    
    def test_middle_aged_client_creation(self):
        """Test creating a middle-aged client (30-50)."""
        client = ClientFactory.create_middle_aged_client()
        
        today = date.today()
        age = today.year - client.birth_date.year
        if today.month < client.birth_date.month or \
           (today.month == client.birth_date.month and today.day < client.birth_date.day):
            age -= 1
        
        assert 30 <= age <= 50
    
    def test_senior_client_creation(self):
        """Test creating a senior client (60-80)."""
        client = ClientFactory.create_senior_client()
        
        today = date.today()
        age = today.year - client.birth_date.year
        if today.month < client.birth_date.month or \
           (today.month == client.birth_date.month and today.day < client.birth_date.day):
            age -= 1
        
        assert 60 <= age <= 80
    
    def test_inactive_client_creation(self):
        """Test creating an inactive client."""
        client = ClientFactory.create_inactive_client()
        assert client.is_active is False
    
    def test_client_batch_creation(self):
        """Test creating multiple clients with age distribution."""
        created_by = uuid.uuid4()
        client_count = 15
        
        clients = ClientFactory.create_client_batch(
            count=client_count,
            created_by=created_by,
            age_distribution={
                'young': 0.3,    # ~5 clients
                'middle': 0.5,   # ~7 clients  
                'senior': 0.2,   # ~3 clients
            }
        )
        
        assert len(clients) == client_count
        
        # All clients should have the same creator
        for client in clients:
            assert client.created_by == created_by
        
        # Verify age distribution exists
        ages = []
        today = date.today()
        for client in clients:
            age = today.year - client.birth_date.year
            if today.month < client.birth_date.month or \
               (today.month == client.birth_date.month and today.day < client.birth_date.day):
                age -= 1
            ages.append(age)
        
        # Should have variety in ages
        assert min(ages) >= 16  # Minimum age from validation
        assert max(ages) <= 120  # Maximum age from validation
        assert len(set(ages)) > 1  # Should have variety
    
    def test_clients_for_user(self):
        """Test creating multiple clients for a specific user."""
        user = UserFactory.create_user()
        client_count = 5
        
        clients = ClientFactory.create_clients_for_user(
            user_id=user.id,
            count=client_count
        )
        
        assert len(clients) == client_count
        
        for client in clients:
            assert client.created_by == user.id
            assert client.is_active is True
    
    def test_client_with_specific_cpf(self):
        """Test creating a client with a specific CPF."""
        test_cpf = "11144477735"
        client = ClientFactory.create_client_with_specific_cpf(cpf_pattern=test_cpf)
        
        assert client.cpf == test_cpf
    
    def test_client_repr(self):
        """Test client string representation."""
        client = ClientFactory.create_client(
            name="João Silva",
            cpf="11144477735"
        )
        
        repr_str = repr(client)
        assert "Client(" in repr_str
        assert "João Silva" in repr_str
        assert "111.***." in repr_str  # CPF should be masked
        assert "35" in repr_str  # Last 2 digits should show
        assert str(client.id) in repr_str
    
    def test_client_id_uniqueness(self):
        """Test that client IDs are unique."""
        clients = [ClientFactory.create_client() for _ in range(10)]
        client_ids = [client.id for client in clients]
        
        # All IDs should be unique
        assert len(set(client_ids)) == len(client_ids)
    
    def test_client_timestamps_are_set(self):
        """Test that created_at and updated_at are automatically set."""
        client = ClientFactory.create_client()
        
        assert client.created_at is not None
        assert client.updated_at is not None
        assert isinstance(client.created_at, datetime)
        assert isinstance(client.updated_at, datetime)
        
        # Should be recent timestamps
        now = datetime.utcnow()
        assert (now - client.created_at).total_seconds() < 60
        assert (now - client.updated_at).total_seconds() < 60


class TestClientCPFValidation:
    """Test suite for Client CPF validation."""
    
    def test_valid_cpf_numbers(self):
        """Test that valid CPF numbers are accepted."""
        valid_cpfs = ClientFactory.get_sample_cpfs()
        
        for cpf in valid_cpfs:
            client = ClientFactory.create_client(cpf=cpf)
            assert client.cpf == cpf
    
    def test_invalid_cpf_numbers(self):
        """Test that invalid CPF numbers are rejected."""
        invalid_cpfs = ClientFactory.get_invalid_cpfs()
        
        for cpf in invalid_cpfs:
            with pytest.raises(ValidationError) as exc_info:
                ClientFactory.create_client(cpf=cpf)
            
            # Verify the error message is appropriate
            error_msg = str(exc_info.value)
            assert any(keyword in error_msg.lower() for keyword in 
                      ['cpf', 'digits', 'required', 'invalid'])
    
    def test_cpf_formatting_removal(self):
        """Test that CPF formatting is removed during validation."""
        formatted_cpf = "111.444.777-35"
        expected_cpf = "11144477735"
        
        client = ClientFactory.create_client(cpf=formatted_cpf)
        assert client.cpf == expected_cpf
    
    def test_cpf_all_same_digits_rejection(self):
        """Test that CPFs with all same digits are rejected."""
        invalid_same_digits = ["11111111111", "00000000000", "99999999999"]
        
        for cpf in invalid_same_digits:
            with pytest.raises(ValidationError) as exc_info:
                ClientFactory.create_client(cpf=cpf)
            
            error_msg = str(exc_info.value)
            assert "same digits" in error_msg.lower()
    
    def test_cpf_length_validation(self):
        """Test CPF length validation."""
        # Too short
        with pytest.raises(ValidationError):
            ClientFactory.create_client(cpf="123456789")
        
        # Too long
        with pytest.raises(ValidationError):
            ClientFactory.create_client(cpf="1234567890123")
    
    def test_empty_cpf_rejection(self):
        """Test that empty CPF is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ClientFactory.create_client(cpf="")
        
        error_msg = str(exc_info.value)
        assert "required" in error_msg.lower()
    
    def test_non_numeric_cpf_rejection(self):
        """Test that non-numeric CPF is rejected."""
        with pytest.raises(ValidationError):
            ClientFactory.create_client(cpf="abcdefghijk")


class TestClientBirthDateValidation:
    """Test suite for Client birth date validation."""
    
    def test_valid_birth_dates(self):
        """Test that valid birth dates are accepted."""
        today = date.today()
        
        # Valid dates (16-120 years old)
        valid_dates = [
            today - timedelta(days=16*365),   # 16 years old
            today - timedelta(days=25*365),   # 25 years old
            today - timedelta(days=50*365),   # 50 years old
            today - timedelta(days=80*365),   # 80 years old
        ]
        
        for birth_date in valid_dates:
            client = ClientFactory.create_client(birth_date=birth_date)
            assert client.birth_date == birth_date
    
    def test_future_birth_date_rejection(self):
        """Test that future birth dates are rejected."""
        future_date = date.today() + timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            ClientFactory.create_client(birth_date=future_date)
        
        error_msg = str(exc_info.value)
        assert "future" in error_msg.lower()
    
    def test_too_young_birth_date_rejection(self):
        """Test that birth dates making client too young are rejected."""
        too_recent = date.today() - timedelta(days=15*365)  # 15 years old
        
        with pytest.raises(ValidationError) as exc_info:
            ClientFactory.create_client(birth_date=too_recent)
        
        error_msg = str(exc_info.value)
        assert "16 years" in error_msg.lower()
    
    def test_too_old_birth_date_rejection(self):
        """Test that unreasonably old birth dates are rejected."""
        too_old = date.today() - timedelta(days=121*365)  # 121 years old
        
        with pytest.raises(ValidationError) as exc_info:
            ClientFactory.create_client(birth_date=too_old)
        
        error_msg = str(exc_info.value)
        assert "unreasonably old" in error_msg.lower()
    
    def test_birth_date_required(self):
        """Test that birth date is required."""
        with pytest.raises((ValidationError, TypeError)):
            Client(
                name="Test Client",
                cpf="11144477735",
                created_by=uuid.uuid4()
            )


class TestClientNameValidation:
    """Test suite for Client name validation."""
    
    def test_valid_names(self):
        """Test that valid names are accepted."""
        valid_names = [
            "Ana Silva",
            "João Pedro Santos",
            "Maria Fernanda Oliveira Costa",
            "Carlos Eduardo",
            "Luiza Souza Lima",
            "AB",  # Minimum length
            "A" * 100,  # Maximum length
        ]
        
        for name in valid_names:
            client = ClientFactory.create_client(name=name)
            assert client.name == name
    
    def test_name_too_short_rejection(self):
        """Test that names too short are rejected."""
        with pytest.raises(ValidationError):
            ClientFactory.create_client(name="A")  # Only 1 character
    
    def test_name_too_long_rejection(self):
        """Test that names too long are rejected."""
        long_name = "A" * 101  # 101 characters
        with pytest.raises(ValidationError):
            ClientFactory.create_client(name=long_name)
    
    def test_name_required(self):
        """Test that name is required."""
        with pytest.raises((ValidationError, TypeError)):
            Client(
                cpf="11144477735",
                birth_date=date.today() - timedelta(days=20*365),
                created_by=uuid.uuid4()
            )


class TestClientRequiredFields:
    """Test suite for Client required fields."""
    
    def test_created_by_required(self):
        """Test that created_by is required."""
        with pytest.raises((ValidationError, TypeError)):
            Client(
                name="Test Client",
                cpf="11144477735", 
                birth_date=date.today() - timedelta(days=20*365)
            )
    
    def test_all_required_fields_present(self):
        """Test that client can be created with all required fields."""
        client = Client(
            name="Test Client",
            cpf="11144477735",
            birth_date=date.today() - timedelta(days=20*365),
            created_by=uuid.uuid4()
        )
        
        assert client.name == "Test Client"
        assert client.cpf == "11144477735"
        assert client.created_by is not None
        assert client.is_active is True  # Should default to True