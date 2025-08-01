"""Dependency injection container for the application."""

from dependency_injector import containers, providers

from app.agents.plugin_discovery import plugin_discovery
from app.core.agent_config import config_manager
from app.core.agent_manager import AgentManager
from app.core.agent_registry import agent_registry
from app.core.database import get_async_db
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_log_service import AuditLogService
from app.services.client_service import ClientService
from app.services.user_service import UserService


class Container(containers.DeclarativeContainer):
    """Application dependency injection container."""

    # Configuration
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.ui_components.admin_dashboard",
            "app.ui_components.clients_area",
            "app.ui_components.dashboard",
            "app.ui_components.login",
            "app.ui_components.register",
            "app.ui_components.settings_2fa",
            "app.core.agent_manager",
            "app.api.documents",
            "app.api.questionnaire",
            "app.api.admin",
        ]
    )

    # Database session provider
    database_session = providers.Resource(get_async_db)

    # Repositories
    audit_log_repository = providers.Factory(AuditLogRepository, session=database_session)

    client_repository = providers.Factory(ClientRepository, session=database_session)

    user_repository = providers.Factory(UserRepository, session=database_session)

    # Services
    audit_log_service = providers.Factory(
        AuditLogService, audit_log_repository=audit_log_repository
    )

    client_service = providers.Factory(
        ClientService, client_repository=client_repository
    )

    user_service = providers.Factory(UserService, user_repository=user_repository)

    # Agent Management
    agent_config_manager = providers.Object(config_manager)

    agent_registry_service = providers.Object(agent_registry)

    agent_manager = providers.Singleton(AgentManager)

    plugin_discovery_service = providers.Object(plugin_discovery)


# Global container instance
container = Container()
