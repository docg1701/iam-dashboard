"""
Client factory for generating test client data.

Provides realistic test data generation for Client models with valid CPF
numbers and reasonable birth dates.
"""

import uuid
from datetime import date

from src.models.client import Client

from .base_factory import BaseFactory


class ClientFactory(BaseFactory):
    """Factory for creating Client test instances."""

    @classmethod
    def create_client(
        self,
        name: str | None = None,
        cpf: str | None = None,
        birth_date: date | None = None,
        created_by: uuid.UUID | None = None,
        is_active: bool = True,
        **kwargs,
    ) -> Client:
        """
        Create a Client instance with realistic test data.

        Args:
            name: Client name (auto-generated if None)
            cpf: Client CPF (auto-generated valid CPF if None)
            birth_date: Birth date (auto-generated if None)
            created_by: User ID who created the client
            is_active: Active status
            **kwargs: Additional fields to override

        Returns:
            Client instance with test data
        """
        # Generate name if not provided
        if name is None:
            name = self.generate_name()

        # Generate valid CPF if not provided
        if cpf is None:
            cpf = self.generate_cpf()

        # Generate birth date if not provided
        if birth_date is None:
            birth_date = self.generate_birth_date()

        # Generate created_by if not provided
        if created_by is None:
            created_by = self.generate_uuid()

        # Create base client data
        client_data = {
            "name": name,
            "cpf": cpf,
            "birth_date": birth_date,
            "created_by": created_by,
            "is_active": is_active,
            **kwargs,
        }

        return Client(**client_data)

    @classmethod
    def create_young_adult_client(
        self, name: str | None = None, created_by: uuid.UUID | None = None, **kwargs
    ) -> Client:
        """Create a client in the 18-25 age range."""
        birth_date = self.generate_birth_date(min_age=18, max_age=25)
        return self.create_client(
            name=name, birth_date=birth_date, created_by=created_by, **kwargs
        )

    @classmethod
    def create_middle_aged_client(
        self, name: str | None = None, created_by: uuid.UUID | None = None, **kwargs
    ) -> Client:
        """Create a client in the 30-50 age range."""
        birth_date = self.generate_birth_date(min_age=30, max_age=50)
        return self.create_client(
            name=name, birth_date=birth_date, created_by=created_by, **kwargs
        )

    @classmethod
    def create_senior_client(
        self, name: str | None = None, created_by: uuid.UUID | None = None, **kwargs
    ) -> Client:
        """Create a client in the 60-80 age range."""
        birth_date = self.generate_birth_date(min_age=60, max_age=80)
        return self.create_client(
            name=name, birth_date=birth_date, created_by=created_by, **kwargs
        )

    @classmethod
    def create_inactive_client(
        self, name: str | None = None, created_by: uuid.UUID | None = None, **kwargs
    ) -> Client:
        """Create an inactive client."""
        return self.create_client(
            name=name, created_by=created_by, is_active=False, **kwargs
        )

    @classmethod
    def create_client_batch(
        self,
        count: int,
        created_by: uuid.UUID | None = None,
        age_distribution: dict | None = None,
        **kwargs,
    ) -> list[Client]:
        """
        Create multiple clients with specified age distribution.

        Args:
            count: Number of clients to create
            created_by: User ID who created all clients
            age_distribution: Dict mapping age group to percentage
            **kwargs: Additional arguments for client creation

        Returns:
            List of Client instances
        """
        if created_by is None:
            created_by = self.generate_uuid()

        if age_distribution is None:
            age_distribution = {
                "young": 0.3,  # 18-30
                "middle": 0.5,  # 31-55
                "senior": 0.2,  # 56+
            }

        clients = []
        for i in range(count):
            # Determine age group based on distribution
            if i < count * age_distribution.get("young", 0):
                birth_date = self.generate_birth_date(min_age=18, max_age=30)
            elif i < count * (
                age_distribution.get("young", 0) + age_distribution.get("middle", 0)
            ):
                birth_date = self.generate_birth_date(min_age=31, max_age=55)
            else:
                birth_date = self.generate_birth_date(min_age=56, max_age=80)

            client = self.create_client(
                birth_date=birth_date, created_by=created_by, **kwargs
            )
            clients.append(client)

        return clients

    @classmethod
    def create_client_with_specific_cpf(
        self,
        cpf_pattern: str,
        name: str | None = None,
        created_by: uuid.UUID | None = None,
        **kwargs,
    ) -> Client:
        """
        Create a client with a specific CPF pattern.

        Args:
            cpf_pattern: CPF number (will be validated)
            name: Client name
            created_by: User ID who created the client
            **kwargs: Additional arguments

        Returns:
            Client instance with specified CPF
        """
        return self.create_client(
            name=name, cpf=cpf_pattern, created_by=created_by, **kwargs
        )

    @classmethod
    def create_clients_for_user(
        self, user_id: uuid.UUID, count: int = 5, **kwargs
    ) -> list[Client]:
        """
        Create multiple clients associated with a specific user.

        Args:
            user_id: ID of the user who created the clients
            count: Number of clients to create
            **kwargs: Additional arguments for client creation

        Returns:
            List of Client instances created by the specified user
        """
        clients = []
        for _ in range(count):
            client = self.create_client(created_by=user_id, **kwargs)
            clients.append(client)

        return clients

    @classmethod
    def get_sample_cpfs(cls) -> list[str]:
        """Get a list of valid sample CPF numbers for testing."""
        return [
            "11144477735",  # Valid CPF 1 (keep existing valid one)
            "79842946908",  # Valid CPF 2
            "62974875297",  # Valid CPF 3
            "60727800248",  # Valid CPF 4
            "35100788534",  # Valid CPF 5
            "12345678909",  # Valid CPF 6 - common test pattern
            "98765432100",  # Valid CPF 7 - reverse pattern
            "11122233344",  # Valid CPF 8 - sequential pattern
            "55566677788",  # Valid CPF 9 - mid-range pattern
            "99988877766",  # Valid CPF 10 - high-range pattern
        ]

    @classmethod
    def get_invalid_cpfs(cls) -> list[str]:
        """Get a list of invalid CPF numbers for validation testing."""
        return [
            "11111111111",  # All same digits
            "00000000000",  # All zeros
            "22222222222",  # All same digits (2s)
            "33333333333",  # All same digits (3s)
            "44444444444",  # All same digits (4s)
            "123456789",  # Too short
            "1234567890123",  # Too long
            "",  # Empty
            "abc.def.ghi-jk",  # Non-numeric
            "123.456.789-00",  # Formatted but invalid
            "111.444.777-34",  # Formatted but wrong check digits
            "12345678901",  # 11 digits but invalid check
            "98765432101",  # 11 digits but invalid check
            " 11144477735 ",  # Valid CPF with spaces (should be trimmed)
            "111.444.777-35",  # Valid format but invalid CPF
            "000.000.001-91",  # Edge case invalid
        ]

    @classmethod
    def create_client_with_edge_case_data(
        self,
        edge_case_type: str,
        created_by: uuid.UUID | None = None,
        **kwargs,
    ) -> Client:
        """
        Create a client with edge case data for testing validation and handling.

        Args:
            edge_case_type: Type of edge case ('min_age', 'max_name_length', 'special_chars', etc.)
            created_by: User ID who created the client
            **kwargs: Additional arguments

        Returns:
            Client instance with edge case data
        """
        if created_by is None:
            created_by = self.generate_uuid()

        edge_cases = {
            "min_age": {
                "name": "Jovem Adulto Silva",
                "birth_date": self.generate_birth_date(
                    min_age=16, max_age=16
                ),  # Minimum age
            },
            "max_name_length": {
                "name": "João Silva Santos Oliveira Costa Lima Ferreira Rodrigues Almeida Pereira da Silva",  # Long name
                "birth_date": self.generate_birth_date(),
            },
            "min_name_length": {
                "name": "Jo",  # Minimum valid name length
                "birth_date": self.generate_birth_date(),
            },
            "special_chars": {
                "name": "José da Silva-Santos O'Connor",  # Name with special chars
                "birth_date": self.generate_birth_date(),
            },
            "accented_chars": {
                "name": "João José da Conceição",  # Name with accents
                "birth_date": self.generate_birth_date(),
            },
            "senior_citizen": {
                "name": "Idoso Senior Cliente",
                "birth_date": self.generate_birth_date(
                    min_age=80, max_age=90
                ),  # Senior citizen
            },
        }

        if edge_case_type not in edge_cases:
            raise ValueError(f"Unknown edge case type: {edge_case_type}")

        case_data = edge_cases[edge_case_type]

        return self.create_client(
            name=case_data["name"],
            birth_date=case_data["birth_date"],
            created_by=created_by,
            **kwargs,
        )

    @classmethod
    def create_realistic_brazilian_clients(
        self,
        count: int = 10,
        created_by: uuid.UUID | None = None,
        **kwargs,
    ) -> list[Client]:
        """
        Create realistic Brazilian client data for integration testing.

        Args:
            count: Number of clients to create
            created_by: User ID who created all clients
            **kwargs: Additional arguments

        Returns:
            List of Client instances with realistic Brazilian names and data
        """
        if created_by is None:
            created_by = self.generate_uuid()

        # Common Brazilian names and surnames
        first_names = [
            "João",
            "Maria",
            "José",
            "Ana",
            "Pedro",
            "Antônio",
            "Luiz",
            "Francisco",
            "Paulo",
            "Carlos",
            "Manoel",
            "Raimundo",
            "Sebastião",
            "Marcos",
            "Antonia",
            "Francisca",
            "Rita",
            "Rosa",
            "Cláudia",
            "Juliana",
            "Sandra",
            "Cristina",
            "Fernanda",
            "Adriana",
            "Patrícia",
            "Aline",
            "Luciana",
            "Marcia",
        ]

        last_names = [
            "Silva",
            "Santos",
            "Oliveira",
            "Souza",
            "Rodrigues",
            "Ferreira",
            "Alves",
            "Pereira",
            "Lima",
            "Gomes",
            "Costa",
            "Ribeiro",
            "Martins",
            "Carvalho",
            "Araújo",
            "Melo",
            "Barbosa",
            "Machado",
            "Nascimento",
            "Lopes",
            "Moreira",
            "Mendes",
            "Cardoso",
            "Vieira",
            "Monteiro",
            "Rocha",
            "Freitas",
            "Campos",
        ]

        clients = []
        sample_cpfs = self.get_sample_cpfs()

        for i in range(count):
            # Generate realistic name
            first = (
                self.fake.random.choice(first_names)
                if hasattr(self, "fake")
                else first_names[i % len(first_names)]
            )
            middle = (
                self.fake.random.choice(first_names[:10])
                if hasattr(self, "fake")
                else first_names[(i + 5) % 10]
            )  # Shorter list for middle names
            last = (
                self.fake.random.choice(last_names)
                if hasattr(self, "fake")
                else last_names[i % len(last_names)]
            )

            name = f"{first} {middle} {last}"

            # Use cycling through sample CPFs to avoid duplicates
            cpf = sample_cpfs[i % len(sample_cpfs)]

            # Generate realistic age distribution (more adults, fewer seniors)
            if i % 4 == 0:  # 25% young adults
                birth_date = self.generate_birth_date(min_age=18, max_age=30)
            elif i % 4 in [1, 2]:  # 50% middle-aged
                birth_date = self.generate_birth_date(min_age=31, max_age=55)
            else:  # 25% seniors
                birth_date = self.generate_birth_date(min_age=56, max_age=75)

            client = self.create_client(
                name=name,
                cpf=cpf,
                birth_date=birth_date,
                created_by=created_by,
                **kwargs,
            )
            clients.append(client)

        return clients
