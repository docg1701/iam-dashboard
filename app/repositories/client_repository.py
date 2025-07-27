"""Client repository for database operations."""

import uuid
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.client import Client


class ClientRepository:
    """Repository for Client model database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        self.session = session

    async def create(self, name: str, cpf: str, birth_date: date) -> Client:
        """Create a new client in the database."""
        client = Client(name=name, cpf=cpf, birth_date=birth_date)

        self.session.add(client)
        try:
            await self.session.commit()
            await self.session.refresh(client)
            return client
        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(f"CPF '{cpf}' already exists") from e

    async def get_by_id(self, client_id: uuid.UUID) -> Client | None:
        """Get a client by ID."""
        result = await self.session.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_by_cpf(self, cpf: str) -> Client | None:
        """Get a client by CPF."""
        result = await self.session.execute(select(Client).where(Client.cpf == cpf))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Client]:
        """Get all clients."""
        result = await self.session.execute(select(Client))
        return list(result.scalars().all())

    async def update(self, client: Client) -> Client:
        """Update an existing client."""
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def delete(self, client: Client) -> None:
        """Delete a client from the database."""
        await self.session.delete(client)
        await self.session.commit()

    async def is_cpf_taken(self, cpf: str) -> bool:
        """Check if a CPF is already taken."""
        client = await self.get_by_cpf(cpf)
        return client is not None
