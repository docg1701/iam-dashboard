"""Unit tests for ClientRepository."""

from datetime import date

import pytest

from app.repositories.client_repository import ClientRepository


@pytest.mark.asyncio
async def test_create_client(client_repository: ClientRepository):
    """Test creating a new client."""
    # Arrange
    name = "Maria Silva"
    cpf = "98765432100"
    birth_date = date(1985, 3, 20)

    # Act
    client = await client_repository.create(name, cpf, birth_date)

    # Assert
    assert client.id is not None
    assert client.name == name
    assert client.cpf == cpf
    assert client.birth_date == birth_date
    assert client.created_at is not None
    assert client.updated_at is not None


@pytest.mark.asyncio
async def test_create_client_duplicate_cpf(client_repository: ClientRepository):
    """Test creating client with duplicate CPF raises error."""
    # Arrange
    cpf = "12345678901"
    await client_repository.create("Client 1", cpf, date(1980, 1, 1))

    # Act & Assert
    with pytest.raises(ValueError, match="CPF '12345678901' already exists"):
        await client_repository.create("Client 2", cpf, date(1985, 1, 1))


@pytest.mark.asyncio
async def test_get_by_id(client_repository: ClientRepository):
    """Test getting client by ID."""
    # Arrange
    created_client = await client_repository.create(
        "Test Client", "11111111111", date(1990, 1, 1)
    )

    # Act
    found_client = await client_repository.get_by_id(created_client.id)

    # Assert
    assert found_client is not None
    assert found_client.id == created_client.id
    assert found_client.name == "Test Client"
    assert found_client.cpf == "11111111111"


@pytest.mark.asyncio
async def test_get_by_id_not_found(client_repository: ClientRepository):
    """Test getting client by non-existent ID returns None."""
    # Arrange
    import uuid

    non_existent_id = uuid.uuid4()

    # Act
    client = await client_repository.get_by_id(non_existent_id)

    # Assert
    assert client is None


@pytest.mark.asyncio
async def test_get_by_cpf(client_repository: ClientRepository):
    """Test getting client by CPF."""
    # Arrange
    cpf = "98765432100"  # Valid CPF
    await client_repository.create("Test Client", cpf, date(1990, 1, 1))

    # Act
    client = await client_repository.get_by_cpf(cpf)

    # Assert
    assert client is not None
    assert client.cpf == cpf
    assert client.name == "Test Client"


@pytest.mark.asyncio
async def test_get_by_cpf_not_found(client_repository: ClientRepository):
    """Test getting client by non-existent CPF returns None."""
    # Act
    client = await client_repository.get_by_cpf("99999999999")

    # Assert
    assert client is None


@pytest.mark.asyncio
async def test_get_all_empty(client_repository: ClientRepository):
    """Test getting all clients when none exist."""
    # Act
    clients = await client_repository.get_all()

    # Assert
    assert clients == []


@pytest.mark.asyncio
async def test_get_all_with_clients(client_repository: ClientRepository):
    """Test getting all clients when some exist."""
    # Arrange
    client1 = await client_repository.create(
        "Client 1", "11144477735", date(1980, 1, 1)
    )
    client2 = await client_repository.create(
        "Client 2", "98765432100", date(1985, 1, 1)
    )

    # Act
    clients = await client_repository.get_all()

    # Assert
    assert len(clients) == 2
    client_ids = [c.id for c in clients]
    assert client1.id in client_ids
    assert client2.id in client_ids


@pytest.mark.asyncio
async def test_update_client(client_repository: ClientRepository):
    """Test updating a client."""
    # Arrange
    client = await client_repository.create(
        "Original Name", "11144477735", date(1980, 1, 1)
    )
    original_updated_at = client.updated_at

    # Act
    client.name = "Updated Name"
    updated_client = await client_repository.update(client)

    # Assert
    assert updated_client.name == "Updated Name"
    assert updated_client.updated_at >= original_updated_at


@pytest.mark.asyncio
async def test_delete_client(client_repository: ClientRepository):
    """Test deleting a client."""
    # Arrange
    client = await client_repository.create(
        "To Delete", "11144477735", date(1980, 1, 1)
    )
    client_id = client.id

    # Act
    await client_repository.delete(client)

    # Assert
    deleted_client = await client_repository.get_by_id(client_id)
    assert deleted_client is None


@pytest.mark.asyncio
async def test_is_cpf_taken_true(client_repository: ClientRepository):
    """Test is_cpf_taken returns True for existing CPF."""
    # Arrange
    cpf = "11144477735"
    await client_repository.create("Test Client", cpf, date(1980, 1, 1))

    # Act
    is_taken = await client_repository.is_cpf_taken(cpf)

    # Assert
    assert is_taken is True


@pytest.mark.asyncio
async def test_is_cpf_taken_false(client_repository: ClientRepository):
    """Test is_cpf_taken returns False for non-existent CPF."""
    # Act
    is_taken = await client_repository.is_cpf_taken("99999999999")

    # Assert
    assert is_taken is False
