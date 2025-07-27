"""Dependency injection container for the application."""

from dependency_injector import containers, providers

from app.core.database import get_async_db
from app.repositories.client_repository import ClientRepository
from app.repositories.user_repository import UserRepository
from app.services.client_service import ClientService
from app.services.user_service import UserService


class Container(containers.DeclarativeContainer):
    """Application dependency injection container."""

    # Configuration
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.ui_components.clients_area",
            "app.ui_components.dashboard",
            "app.ui_components.login",
            "app.ui_components.register",
            "app.ui_components.settings_2fa",
        ]
    )

    # Database session provider
    database_session = providers.Resource(get_async_db)

    # Repositories
    client_repository = providers.Factory(ClientRepository, session=database_session)

    user_repository = providers.Factory(UserRepository, session=database_session)

    # Services
    client_service = providers.Factory(
        ClientService, client_repository=client_repository
    )

    user_service = providers.Factory(UserService, user_repository=user_repository)


# Global container instance
container = Container()
