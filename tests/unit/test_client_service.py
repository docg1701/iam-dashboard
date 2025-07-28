"""Unit tests for ClientService."""

from datetime import date

import pytest

from app.models.client import Client
from app.services.client_service import ClientService


@pytest.mark.asyncio
async def test_create_client_success(client_service: ClientService):
    """Test creating a client successfully."""
    # Arrange
    name = "João Silva"
    cpf = "111.444.777-35"  # Valid CPF with formatting
    birth_date = date(1980, 5, 15)

    # Act
    client = await client_service.create_client(name, cpf, birth_date)

    # Assert
    assert client.name == "João Silva"
    assert client.cpf == "11144477735"  # Should be cleaned
    assert client.birth_date == birth_date


@pytest.mark.asyncio
async def test_create_client_invalid_cpf(client_service: ClientService):
    """Test creating client with invalid CPF."""
    # Arrange
    name = "João Silva"
    invalid_cpf = "123.456.789-00"  # Invalid check digits
    birth_date = date(1980, 5, 15)

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid CPF format"):
        await client_service.create_client(name, invalid_cpf, birth_date)


@pytest.mark.asyncio
async def test_create_client_duplicate_cpf(client_service: ClientService, test_client: Client):
    """Test creating client with duplicate CPF."""
    # Arrange
    name = "Another Client"
    duplicate_cpf = "111.444.777-35"  # Same as test_client
    birth_date = date(1985, 3, 20)

    # Act & Assert
    with pytest.raises(ValueError, match="CPF .* is already registered"):
        await client_service.create_client(name, duplicate_cpf, birth_date)


@pytest.mark.asyncio
async def test_create_client_empty_name(client_service: ClientService):
    """Test creating client with empty name."""
    # Arrange
    name = "  "  # Only whitespace
    cpf = "111.444.777-35"  # Valid CPF
    birth_date = date(1980, 5, 15)

    # Act & Assert
    with pytest.raises(ValueError, match="Name must have at least 2 characters"):
        await client_service.create_client(name, cpf, birth_date)


@pytest.mark.asyncio
async def test_create_client_short_name(client_service: ClientService):
    """Test creating client with too short name."""
    # Arrange
    name = "A"  # Only 1 character
    cpf = "111.444.777-35"  # Valid CPF
    birth_date = date(1980, 5, 15)

    # Act & Assert
    with pytest.raises(ValueError, match="Name must have at least 2 characters"):
        await client_service.create_client(name, cpf, birth_date)


@pytest.mark.asyncio
async def test_get_client_by_id_existing(client_service: ClientService, test_client: Client):
    """Test getting existing client by ID."""
    # Act
    client = await client_service.get_client_by_id(test_client.id)

    # Assert
    assert client is not None
    assert client.id == test_client.id
    assert client.name == test_client.name


@pytest.mark.asyncio
async def test_get_client_by_id_non_existent(client_service: ClientService):
    """Test getting non-existent client by ID."""
    # Arrange
    import uuid
    non_existent_id = uuid.uuid4()

    # Act
    client = await client_service.get_client_by_id(non_existent_id)

    # Assert
    assert client is None


@pytest.mark.asyncio
async def test_get_client_by_cpf_existing(client_service: ClientService, test_client: Client):
    """Test getting existing client by CPF."""
    # Act
    client = await client_service.get_client_by_cpf("111.444.777-35")  # Formatted CPF

    # Assert
    assert client is not None
    assert client.cpf == test_client.cpf


@pytest.mark.asyncio
async def test_get_client_by_cpf_non_existent(client_service: ClientService):
    """Test getting non-existent client by CPF."""
    # Act
    client = await client_service.get_client_by_cpf("999.999.999-99")

    # Assert
    assert client is None


@pytest.mark.asyncio
async def test_get_all_clients_empty(client_service: ClientService):
    """Test getting all clients when none exist."""
    # Act
    clients = await client_service.get_all_clients()

    # Assert
    assert clients == []


@pytest.mark.asyncio
async def test_get_all_clients_with_data(client_service: ClientService, test_client: Client):
    """Test getting all clients when some exist."""
    # Act
    clients = await client_service.get_all_clients()

    # Assert
    assert len(clients) == 1
    assert clients[0].id == test_client.id


@pytest.mark.asyncio
async def test_update_client_success(client_service: ClientService, test_client: Client):
    """Test updating client successfully."""
    # Arrange
    new_name = "Updated Name"
    new_cpf = "987.654.321-00"  # Valid CPF
    new_birth_date = date(1985, 10, 25)

    # Act
    updated_client = await client_service.update_client(
        test_client.id,
        name=new_name,
        cpf=new_cpf,
        birth_date=new_birth_date
    )

    # Assert
    assert updated_client is not None
    assert updated_client.name == new_name
    assert updated_client.cpf == "98765432100"  # Cleaned CPF
    assert updated_client.birth_date == new_birth_date


@pytest.mark.asyncio
async def test_update_client_non_existent(client_service: ClientService):
    """Test updating non-existent client."""
    # Arrange
    import uuid
    non_existent_id = uuid.uuid4()

    # Act
    result = await client_service.update_client(non_existent_id, name="New Name")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_client_duplicate_cpf(client_service: ClientService, test_client: Client):
    """Test updating client with CPF that belongs to another client."""
    # Arrange - Create another client
    await client_service.create_client(
        "Another Client", "987.654.321-00", date(1985, 1, 1)  # Valid CPF
    )

    # Act & Assert - Try to update test_client with another_client's CPF
    with pytest.raises(ValueError, match="CPF .* is already registered"):
        await client_service.update_client(
            test_client.id,
            cpf="987.654.321-00"
        )


@pytest.mark.asyncio
async def test_delete_client_success(client_service: ClientService, test_client: Client):
    """Test deleting client successfully."""
    # Act
    result = await client_service.delete_client(test_client.id)

    # Assert
    assert result is True

    # Verify client is deleted
    deleted_client = await client_service.get_client_by_id(test_client.id)
    assert deleted_client is None


@pytest.mark.asyncio
async def test_delete_client_non_existent(client_service: ClientService):
    """Test deleting non-existent client."""
    # Arrange
    import uuid
    non_existent_id = uuid.uuid4()

    # Act
    result = await client_service.delete_client(non_existent_id)

    # Assert
    assert result is False


def test_clean_cpf():
    """Test CPF cleaning functionality."""
    # Arrange
    service = ClientService(None)  # Repository not needed for this test

    # Act & Assert
    assert service._clean_cpf("111.444.777-35") == "11144477735"
    assert service._clean_cpf("111 444 777 35") == "11144477735"
    assert service._clean_cpf("11144477735") == "11144477735"
    assert service._clean_cpf("111-444-777-35") == "11144477735"


def test_is_valid_cpf():
    """Test CPF validation functionality."""
    # Arrange
    service = ClientService(None)  # Repository not needed for this test

    # Act & Assert - Valid CPFs
    assert service._is_valid_cpf("11144477735") is True
    assert service._is_valid_cpf("98765432100") is True

    # Invalid CPFs
    assert service._is_valid_cpf("12345678901") is False  # Invalid check digits
    assert service._is_valid_cpf("11111111111") is False  # All same digits
    assert service._is_valid_cpf("123456789") is False    # Too short
    assert service._is_valid_cpf("123456789012") is False # Too long
    assert service._is_valid_cpf("") is False             # Empty
    assert service._is_valid_cpf("abcdefghijk") is False  # Non-numeric
