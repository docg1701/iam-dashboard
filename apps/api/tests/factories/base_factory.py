"""
Base factory class for test data generation.

Provides common utilities and patterns for all model factories.
"""

import random
import string
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from validate_docbr import CPF


class BaseFactory:
    """Base factory class with common utilities for test data generation."""

    @staticmethod
    def generate_uuid() -> uuid.UUID:
        """Generate a random UUID for testing."""
        return uuid.uuid4()

    @staticmethod
    def generate_email(domain: str = "example.com") -> str:
        """Generate a random email address."""
        username = "".join(random.choices(string.ascii_lowercase, k=8))
        return f"{username}@{domain}"

    @staticmethod
    def generate_string(length: int = 10, chars: str = string.ascii_letters) -> str:
        """Generate a random string of specified length."""
        return "".join(random.choices(chars, k=length))

    @staticmethod
    def generate_name() -> str:
        """Generate a realistic Brazilian name."""
        first_names = [
            "Ana",
            "Carlos",
            "Maria",
            "João",
            "Luiza",
            "Pedro",
            "Camila",
            "Rafael",
            "Fernanda",
            "Lucas",
            "Juliana",
            "Gabriel",
            "Beatriz",
            "Thiago",
            "Amanda",
        ]
        last_names = [
            "Silva",
            "Santos",
            "Oliveira",
            "Souza",
            "Lima",
            "Pereira",
            "Costa",
            "Rodrigues",
            "Almeida",
            "Nascimento",
            "Carvalho",
            "Ribeiro",
            "Araújo",
        ]

        first = random.choice(first_names)
        last1 = random.choice(last_names)
        last2 = random.choice(last_names)
        return f"{first} {last1} {last2}"

    @staticmethod
    def generate_cpf() -> str:
        """Generate a valid CPF number for testing purposes using validate_docbr."""
        cpf_generator = CPF()
        return cpf_generator.generate()

    @staticmethod
    def generate_birth_date(min_age: int = 18, max_age: int = 80) -> datetime:
        """Generate a realistic birth date."""
        today = datetime.now().date()
        min_birth = today - timedelta(days=max_age * 365)
        max_birth = today - timedelta(days=min_age * 365)

        # Random date between min and max birth dates
        days_diff = (max_birth - min_birth).days
        random_days = random.randint(0, days_diff)

        return min_birth + timedelta(days=random_days)

    @staticmethod
    def generate_datetime(past_days: int = 30, future_days: int = 0) -> datetime:
        """Generate a datetime within specified range."""
        base = datetime.now(UTC)
        start = base - timedelta(days=past_days)
        end = base + timedelta(days=future_days)

        time_range = int((end - start).total_seconds())
        random_seconds = random.randint(0, time_range)

        return start + timedelta(seconds=random_seconds)

    @staticmethod
    def generate_ip_address() -> str:
        """Generate a random IP address."""
        return ".".join(str(random.randint(1, 254)) for _ in range(4))

    @staticmethod
    def generate_user_agent() -> str:
        """Generate a realistic user agent string."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        ]
        return random.choice(user_agents)

    @staticmethod
    def generate_session_id() -> str:
        """Generate a random session ID."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=32))

    @staticmethod
    def pick_random(items: list[Any]) -> Any:
        """Pick a random item from a list."""
        return random.choice(items)

    @staticmethod
    def generate_dict_data(
        keys: list[str], generate_values: bool = True
    ) -> dict[str, Any]:
        """Generate a dictionary with random data."""
        if not generate_values:
            return {}

        data = {}
        for key in keys:
            # Generate different types of values
            value_type = random.choice(["string", "int", "bool", "float"])
            if value_type == "string":
                data[key] = BaseFactory.generate_string(8)
            elif value_type == "int":
                data[key] = random.randint(1, 100)
            elif value_type == "bool":
                data[key] = random.choice([True, False])
            else:  # float
                data[key] = round(random.uniform(1.0, 100.0), 2)

        return data
