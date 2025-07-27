"""Main application entry point for the IAM Dashboard."""

from fastapi import FastAPI
from nicegui import app, ui

from app.api.clients import router as clients_router
from app.api.documents import router as documents_router
from app.core.auth import AuthManager
from app.ui_components.client_details import client_details_page
from app.ui_components.clients_area import clients_area_page
from app.ui_components.dashboard import dashboard_page
from app.ui_components.login import login_page
from app.ui_components.register import register_page
from app.ui_components.settings_2fa import settings_2fa_page

# Create FastAPI app instance that will be wrapped by NiceGUI
fastapi_app: FastAPI = app

# Register API routers
fastapi_app.include_router(documents_router)
fastapi_app.include_router(clients_router)


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
