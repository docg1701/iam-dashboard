"""Integration tests for client management flow."""

import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.services.client_service import ClientService


@pytest.mark.asyncio
async def test_complete_client_flow(async_session: AsyncSession):
    """Test complete client management flow."""
    # Arrange
    client_repository = ClientRepository(async_session)
    client_service = ClientService(client_repository)
    
    # Test 1: Create client
    client = await client_service.create_client(
        name="Maria Silva",
        cpf="123.456.789-09",  # Valid CPF
        birth_date=date(1985, 3, 20)
    )
    
    assert client.name == "Maria Silva"
    assert client.cpf == "12345678909"
    assert client.birth_date == date(1985, 3, 20)
    assert client.id is not None
    
    # Test 2: Retrieve client by ID
    retrieved_client = await client_service.get_client_by_id(client.id)
    assert retrieved_client is not None
    assert retrieved_client.name == "Maria Silva"
    
    # Test 3: Retrieve client by CPF
    cpf_client = await client_service.get_client_by_cpf("123.456.789-09")
    assert cpf_client is not None
    assert cpf_client.id == client.id
    
    # Test 4: Update client
    updated_client = await client_service.update_client(
        client.id,
        name="Maria Silva Santos",
        birth_date=date(1985, 3, 21)
    )
    assert updated_client.name == "Maria Silva Santos"
    assert updated_client.birth_date == date(1985, 3, 21)
    assert updated_client.cpf == "12345678909"  # CPF should remain the same
    
    # Test 5: List all clients
    all_clients = await client_service.get_all_clients()
    assert len(all_clients) == 1
    assert all_clients[0].id == client.id
    
    # Test 6: Create another client
    second_client = await client_service.create_client(
        name="João Santos",
        cpf="987.654.321-00",  # Valid CPF
        birth_date=date(1980, 12, 15)
    )
    
    # Test 7: List all clients again
    all_clients = await client_service.get_all_clients()
    assert len(all_clients) == 2
    client_names = [c.name for c in all_clients]
    assert "Maria Silva Santos" in client_names
    assert "João Santos" in client_names
    
    # Test 8: Delete first client
    delete_result = await client_service.delete_client(client.id)
    assert delete_result is True
    
    # Test 9: Verify deletion
    deleted_client = await client_service.get_client_by_id(client.id)
    assert deleted_client is None
    
    # Test 10: List clients after deletion
    remaining_clients = await client_service.get_all_clients()
    assert len(remaining_clients) == 1
    assert remaining_clients[0].name == "João Santos"


@pytest.mark.asyncio
async def test_client_validation_flow(async_session: AsyncSession):
    """Test client validation during the complete flow."""
    # Arrange
    client_repository = ClientRepository(async_session)
    client_service = ClientService(client_repository)
    
    # Test 1: Create client with invalid CPF should fail
    with pytest.raises(ValueError, match="Invalid CPF format"):
        await client_service.create_client(
            name="Invalid Client",
            cpf="123.456.789-00",  # Invalid check digits
            birth_date=date(1980, 1, 1)
        )
    
    # Test 2: Create client with invalid name should fail
    with pytest.raises(ValueError, match="Name must have at least 2 characters"):
        await client_service.create_client(
            name="A",  # Too short
            cpf="123.456.789-09",
            birth_date=date(1980, 1, 1)
        )
    
    # Test 3: Create valid client
    client = await client_service.create_client(
        name="Valid Client",
        cpf="123.456.789-09",
        birth_date=date(1980, 1, 1)
    )
    
    # Test 4: Try to create another client with same CPF should fail
    with pytest.raises(ValueError, match="CPF .* is already registered"):
        await client_service.create_client(
            name="Duplicate CPF Client",
            cpf="123.456.789-09",  # Same CPF
            birth_date=date(1985, 1, 1)
        )
    
    # Test 5: Update client with invalid data should fail
    with pytest.raises(ValueError, match="Name must have at least 2 characters"):
        await client_service.update_client(client.id, name="")
    
    # Test 6: Update client with invalid CPF should fail
    with pytest.raises(ValueError, match="Invalid CPF format"):
        await client_service.update_client(client.id, cpf="invalid-cpf")


@pytest.mark.asyncio
async def test_client_cpf_formatting_flow(async_session: AsyncSession):
    """Test CPF formatting and cleaning throughout the flow."""
    # Arrange
    client_repository = ClientRepository(async_session)
    client_service = ClientService(client_repository)
    
    # Test 1: Create client with formatted CPF
    client1 = await client_service.create_client(
        name="Client 1",
        cpf="111.444.777-35",
        birth_date=date(1980, 1, 1)
    )
    
    # Verify CPF is stored clean
    assert client1.cpf == "11144477735"
    assert client1.formatted_cpf == "111.444.777-35"
    
    # Test 2: Find by different formats of the same CPF
    found_client1 = await client_service.get_client_by_cpf("111.444.777-35")
    assert found_client1 is not None
    assert found_client1.id == client1.id
    
    found_client2 = await client_service.get_client_by_cpf("111 444 777 35")
    assert found_client2 is not None
    assert found_client2.id == client1.id
    
    found_client3 = await client_service.get_client_by_cpf("11144477735")
    assert found_client3 is not None
    assert found_client3.id == client1.id
    
    # Test 3: Create another client with different CPF format
    client2 = await client_service.create_client(
        name="Client 2",
        cpf="987 654 321 00",  # Space-separated format
        birth_date=date(1985, 1, 1)
    )
    
    # Verify second client
    assert client2.cpf == "98765432100"
    assert client2.formatted_cpf == "987.654.321-00"


@pytest.mark.asyncio
async def test_sequential_client_operations(async_session: AsyncSession):
    """Test handling of sequential client operations."""
    # Arrange
    client_repository = ClientRepository(async_session)
    client_service = ClientService(client_repository)
    
    # Test sequential creation of different clients
    client1 = await client_service.create_client(
        name="Client 1",
        cpf="111.444.777-35",
        birth_date=date(1980, 1, 1)
    )
    
    client2 = await client_service.create_client(
        name="Client 2", 
        cpf="987.654.321-00",
        birth_date=date(1985, 1, 1)
    )
    
    client3 = await client_service.create_client(
        name="Client 3",
        cpf="12345678909",
        birth_date=date(1990, 1, 1)
    )
    
    # Verify all clients were created
    clients = [client1, client2, client3]
    assert len(clients) == 3
    assert all(c.id is not None for c in clients)
    
    # Verify all clients are in database
    all_clients = await client_service.get_all_clients()
    assert len(all_clients) == 3
    
    client_names = [c.name for c in all_clients]
    assert "Client 1" in client_names
    assert "Client 2" in client_names
    assert "Client 3" in client_names