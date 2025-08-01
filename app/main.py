"""Main application entry point for the IAM Dashboard."""

import asyncio
import atexit
import logging

from fastapi import FastAPI
from nicegui import app, ui

from app.api.admin import router as admin_router
from app.api.agents import router as agents_router
from app.api.clients import router as clients_router
from app.api.documents import router as documents_router
from app.api.middleware.agent_error_handler import agent_error_handler
from app.api.middleware.auth_middleware import AuthorizationMiddleware
from app.api.middleware.performance_middleware import performance_middleware
from app.api.questionnaire import router as questionnaire_router
from app.api.websockets import router as websockets_router
from app.core.agent_initialization import initialize_agent_system, shutdown_agent_system
from app.core.auth import AuthManager
from app.ui_components.admin_control_panel import admin_control_panel_page
from app.ui_components.client_details import client_details_page
from app.ui_components.clients_area import clients_area_page
from app.ui_components.dashboard import dashboard_page
from app.ui_components.login import login_page
from app.ui_components.pdf_processor_page import pdf_processor_page
from app.ui_components.questionnaire_writer import questionnaire_writer_page
from app.ui_components.register import register_page
from app.ui_components.settings_2fa import settings_2fa_page

logger = logging.getLogger(__name__)

# Create FastAPI app instance that will be wrapped by NiceGUI
fastapi_app: FastAPI = app

# Add middleware (order matters - performance first, then auth, then error handling)
fastapi_app.middleware("http")(performance_middleware)
fastapi_app.add_middleware(AuthorizationMiddleware)
fastapi_app.middleware("http")(agent_error_handler)


@fastapi_app.on_event("startup")
async def startup_event() -> None:
    """Initialize agent system on application startup."""
    try:
        logger.info("Starting IAM Dashboard application")
        await initialize_agent_system()
        logger.info("Agent system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent system: {str(e)}")
        raise


@fastapi_app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown agent system on application shutdown."""
    try:
        logger.info("Shutting down IAM Dashboard application")
        await shutdown_agent_system()
        logger.info("Agent system shutdown completed")
    except Exception as e:
        logger.error(f"Error during agent system shutdown: {str(e)}")


# Register graceful shutdown handler
atexit.register(lambda: asyncio.run(shutdown_agent_system()))

# Register API routers
fastapi_app.include_router(documents_router)
fastapi_app.include_router(clients_router)
fastapi_app.include_router(questionnaire_router)
fastapi_app.include_router(admin_router)
fastapi_app.include_router(agents_router)
fastapi_app.include_router(websockets_router)


@ui.page("/")
def index() -> None:
    """Home page route."""
    # Check if user is already authenticated
    if AuthManager.is_authenticated():
        ui.navigate.to("/dashboard")
        return

    with ui.column().classes("w-full max-w-md mx-auto mt-10"):
        ui.label("IAM Dashboard").classes("text-2xl font-bold text-center mb-6")
        ui.label("Sistema de Advocacia SaaS").classes(
            "text-lg text-center text-gray-600"
        )

        with ui.row().classes("w-full mt-8 gap-4"):
            ui.button("Login", on_click=lambda: ui.navigate.to("/login")).classes(
                "flex-1"
            )
            ui.button(
                "Registrar", on_click=lambda: ui.navigate.to("/register")
            ).classes("flex-1")


@ui.page("/login")
def login() -> None:
    """Login page route."""
    login_page()


@ui.page("/register")
def register() -> None:
    """Registration page route."""
    register_page()


@ui.page("/dashboard")
def dashboard() -> None:
    """Dashboard page route."""
    dashboard_page()


@ui.page("/settings/2fa")
def settings_2fa() -> None:
    """2FA settings page route."""
    settings_2fa_page()


@ui.page("/clients")
def clients() -> None:
    """Clients management page route."""
    clients_area_page()


@ui.page("/client/{client_id}")
def client_details(client_id: str) -> None:
    """Client details page route."""
    client_details_page(client_id)


@ui.page("/questionnaire-writer")
def questionnaire_writer() -> None:
    """Questionnaire writer page route."""
    questionnaire_writer_page()


@ui.page("/pdf-processor")
def pdf_processor() -> None:
    """PDF processor page route."""
    pdf_processor_page()


@ui.page("/admin")
def admin() -> None:
    """Administrative control panel page route."""
    admin_control_panel_page()


@ui.page("/logout")
def logout() -> None:
    """Logout route."""
    AuthManager.logout_user()
    ui.notify("Saída realizada com sucesso", type="positive")
    ui.navigate.to("/login")


def main() -> None:
    """Initialize and run the application."""
    # Configure NiceGUI settings
    ui.run(
        title="IAM Dashboard - Sistema de Advocacia SaaS",
        port=8080,
        host="0.0.0.0",
        reload=True,
        show=False,  # Don't auto-open browser in production
        favicon="🏛️",
        storage_secret="your-secret-key-change-in-production",  # Required for user sessions
        language="pt-BR",  # Set Portuguese Brazilian locale
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
