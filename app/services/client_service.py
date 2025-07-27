"""Client service for business logic operations."""

import re
import uuid
from datetime import date

from app.models.client import Client
from app.repositories.client_repository import ClientRepository


class ClientService:
    """Service class for client-related business logic."""

    def __init__(self, client_repository: ClientRepository) -> None:
        """Initialize the service with a client repository."""
        self.client_repository = client_repository

    async def create_client(self, name: str, cpf: str, birth_date: date) -> Client:
        """Create a new client with validation."""
        # Validate CPF format and uniqueness
        cleaned_cpf = self._clean_cpf(cpf)
        if not self._is_valid_cpf(cleaned_cpf):
            raise ValueError("Invalid CPF format")

        if await self.client_repository.is_cpf_taken(cleaned_cpf):
            raise ValueError(f"CPF '{cpf}' is already registered")

        # Validate name
        if not name or len(name.strip()) < 2:
            raise ValueError("Name must have at least 2 characters")

        # Validate birth date
        if not birth_date:
            raise ValueError("Birth date is required")

        # Create client
        client = await self.client_repository.create(
            name=name.strip(), cpf=cleaned_cpf, birth_date=birth_date
        )

        return client

    async def get_client_by_id(self, client_id: uuid.UUID) -> Client | None:
        """Get a client by ID."""
        return await self.client_repository.get_by_id(client_id)

    async def get_client_by_cpf(self, cpf: str) -> Client | None:
        """Get a client by CPF."""
        cleaned_cpf = self._clean_cpf(cpf)
        return await self.client_repository.get_by_cpf(cleaned_cpf)

    async def get_all_clients(self) -> list[Client]:
        """Get all clients."""
        return await self.client_repository.get_all()

    async def update_client(
        self,
        client_id: uuid.UUID,
        name: str | None = None,
        cpf: str | None = None,
        birth_date: date | None = None,
    ) -> Client | None:
        """Update an existing client."""
        client = await self.client_repository.get_by_id(client_id)
        if not client:
            return None

        # Update fields if provided
        if name is not None:
            if not name or len(name.strip()) < 2:
                raise ValueError("Name must have at least 2 characters")
            client.name = name.strip()  # type: ignore[assignment]

        if cpf is not None:
            cleaned_cpf = self._clean_cpf(cpf)
            if not self._is_valid_cpf(cleaned_cpf):
                raise ValueError("Invalid CPF format")

            # Check if CPF is already taken by another client
            existing_client = await self.client_repository.get_by_cpf(cleaned_cpf)
            if existing_client and existing_client.id != client_id:
                raise ValueError(f"CPF '{cpf}' is already registered")

            client.cpf = cleaned_cpf  # type: ignore[assignment]

        if birth_date is not None:
            client.birth_date = birth_date

        return await self.client_repository.update(client)

    async def delete_client(self, client_id: uuid.UUID) -> bool:
        """Delete a client."""
        client = await self.client_repository.get_by_id(client_id)
        if not client:
            return False

        await self.client_repository.delete(client)
        return True

    def _clean_cpf(self, cpf: str) -> str:
        """Remove formatting from CPF, keeping only digits."""
        return re.sub(r"[^\d]", "", cpf)

    def _is_valid_cpf(self, cpf: str) -> bool:
        """Validate CPF format (11 digits) and check digit verification."""
        if not cpf or len(cpf) != 11 or not cpf.isdigit():
            return False

        # Check if all digits are the same (invalid CPF)
        if cpf == cpf[0] * 11:
            return False

        # Calculate first check digit
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = (sum1 * 10) % 11
        if digit1 == 10:
            digit1 = 0

        if int(cpf[9]) != digit1:
            return False

        # Calculate second check digit
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = (sum2 * 10) % 11
        if digit2 == 10:
            digit2 = 0

        return int(cpf[10]) == digit2
