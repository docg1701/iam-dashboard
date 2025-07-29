"""Agent configuration management component."""

import asyncio
from collections.abc import Callable
from typing import Any

import requests
from nicegui import ui

from app.core.config import config


class AgentConfigManager:
    """Agent configuration management interface."""

    def __init__(self, refresh_callback: Callable[[], Any] | None = None) -> None:
        """Initialize the configuration manager."""
        self.agents_data: list[dict[str, Any]] = []
        self.config_forms: dict[str, dict[str, Any]] = {}
        self.config_backup: dict[str, dict[str, Any]] = {}
        self.refresh_callback = refresh_callback

    def create(self) -> None:
        """Create the configuration management UI."""
        with ui.column().classes("w-full gap-6"):
            ui.label("Gerenciamento de Configuração").classes("text-2xl font-bold")

            # Agent selection
            with ui.card().classes("w-full p-4"):
                ui.label("Selecionar Agente para Configurar").classes(
                    "text-lg font-bold mb-4"
                )

                with ui.row().classes("w-full gap-4 flex-wrap"):
                    # This will be populated with agent cards
                    self._create_agent_selection()

    def _create_agent_selection(self) -> None:
        """Create agent selection interface."""
        with ui.column().classes("w-full gap-4") as self.selection_container:
            ui.label("Carregando agentes disponíveis...").classes(
                "text-center py-8 text-gray-500"
            )

        # Load agents data
        asyncio.create_task(self._load_agents_for_config())

    async def _load_agents_for_config(self) -> None:
        """Load agents data for configuration."""
        try:
            response = requests.get(
                config.get_agent_endpoint("/admin/agents"), timeout=10
            )
            if response.status_code == 200:
                self.agents_data = response.json()
                self._update_agent_selection()
            else:
                self.agents_data = []

        except Exception as e:
            ui.notify(f"Erro ao carregar agentes: {str(e)}", type="negative")
            self.agents_data = []

    def _update_agent_selection(self) -> None:
        """Update the agent selection display."""
        self.selection_container.clear()

        if not self.agents_data:
            with self.selection_container:
                ui.label("Nenhum agente encontrado").classes(
                    "text-center py-8 text-gray-500"
                )
            return

        with self.selection_container:
            with ui.row().classes("w-full gap-4 flex-wrap"):
                for agent in self.agents_data:
                    self._create_agent_config_card(agent)

    def _create_agent_config_card(self, agent: dict[str, Any]) -> None:
        """Create a configuration card for an agent."""
        agent_id = agent.get("agent_id", "")

        with ui.card().classes("w-80 p-4 cursor-pointer hover:shadow-lg"):
            # Agent header
            with ui.row().classes("w-full justify-between items-center mb-2"):
                ui.label(agent.get("name", "Unknown")).classes("text-lg font-bold")

                status = agent.get("status", "unknown")
                status_color = {
                    "active": "bg-green-100 text-green-800",
                    "inactive": "bg-gray-100 text-gray-800",
                    "error": "bg-red-100 text-red-800",
                }.get(status, "bg-gray-100 text-gray-800")

                ui.badge(status.title()).classes(status_color)

            # Agent description
            ui.label(agent.get("description", "No description")).classes(
                "text-sm text-gray-600 mb-4"
            )

            # Configuration button
            ui.button(
                "Configurar",
                on_click=lambda aid=agent_id: self._show_agent_config(aid),
                icon="settings",
            ).classes("w-full bg-blue-500 text-white")

    def _show_agent_config(self, agent_id: str) -> None:
        """Show configuration dialog for an agent."""
        self._create_config_dialog(agent_id)

    def _create_config_dialog(self, agent_id: str) -> None:
        """Create configuration dialog for an agent."""
        agent = next(
            (a for a in self.agents_data if a.get("agent_id") == agent_id), None
        )
        if not agent:
            ui.notify("Agente não encontrado", type="warning")
            return

        with ui.dialog() as config_dialog:
            with ui.card().classes("w-[800px] max-h-[90vh] overflow-auto"):
                # Dialog header
                with ui.row().classes("w-full justify-between items-center mb-4"):
                    ui.label(f"Configuração: {agent.get('name', 'Unknown')}").classes(
                        "text-xl font-bold"
                    )
                    ui.button(
                        "",
                        icon="close",
                        on_click=config_dialog.close,
                    ).classes("text-gray-500 hover:text-gray-700")

                # Configuration tabs
                with ui.tabs().classes("w-full") as config_tabs:
                    basic_tab = ui.tab("basic", label="Básico", icon="settings")
                    advanced_tab = ui.tab("advanced", label="Avançado", icon="tune")
                    security_tab = ui.tab(
                        "security", label="Segurança", icon="security"
                    )

                with ui.tab_panels(config_tabs, value="basic").classes("w-full"):
                    with ui.tab_panel("basic"):
                        self._create_basic_config_form(agent_id)

                    with ui.tab_panel("advanced"):
                        self._create_advanced_config_form(agent_id)

                    with ui.tab_panel("security"):
                        self._create_security_config_form(agent_id)

                # Dialog actions
                with ui.row().classes("w-full justify-end gap-2 mt-6"):
                    ui.button("Cancelar", on_click=config_dialog.close).classes(
                        "bg-gray-500 text-white"
                    )

                    ui.button(
                        "Validar",
                        on_click=lambda: asyncio.create_task(
                            self._validate_config(agent_id)
                        ),
                        icon="check_circle",
                    ).classes("bg-yellow-500 text-white")

                    ui.button(
                        "Aplicar",
                        on_click=lambda: asyncio.create_task(
                            self._apply_config(agent_id, config_dialog)
                        ),
                        icon="save",
                    ).classes("bg-green-500 text-white")

                    ui.button(
                        "Rollback",
                        on_click=lambda: asyncio.create_task(
                            self._rollback_config(agent_id)
                        ),
                        icon="undo",
                    ).classes("bg-red-500 text-white")

        config_dialog.open()

        # Load current configuration
        asyncio.create_task(self._load_agent_config(agent_id, config_dialog))

    def _create_basic_config_form(self, agent_id: str) -> None:
        """Create basic configuration form."""
        if agent_id not in self.config_forms:
            self.config_forms[agent_id] = {}

        with ui.column().classes("w-full gap-4"):
            ui.label("Configurações Básicas").classes("text-lg font-bold mb-2")

            # Basic configuration fields
            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("flex-1"):
                    ui.label("Tarefas Simultâneas Máximas")
                    self.config_forms[agent_id]["max_concurrent_tasks"] = ui.number(
                        label="Max Concurrent Tasks",
                        value=5,
                        min=1,
                        max=20,
                    ).classes("w-full")

                with ui.column().classes("flex-1"):
                    ui.label("Timeout (segundos)")
                    self.config_forms[agent_id]["timeout_seconds"] = ui.number(
                        label="Timeout",
                        value=300,
                        min=30,
                        max=3600,
                    ).classes("w-full")

            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("flex-1"):
                    ui.label("Tentativas de Retry")
                    self.config_forms[agent_id]["retry_attempts"] = ui.number(
                        label="Retry Attempts",
                        value=3,
                        min=0,
                        max=10,
                    ).classes("w-full")

                with ui.column().classes("flex-1"):
                    ui.label("Nível de Log")
                    self.config_forms[agent_id]["log_level"] = ui.select(
                        ["DEBUG", "INFO", "WARNING", "ERROR"],
                        value="INFO",
                        label="Log Level",
                    ).classes("w-full")

            # Enable metrics toggle
            self.config_forms[agent_id]["enable_metrics"] = ui.checkbox(
                "Habilitar Métricas",
                value=True,
            )

    def _create_advanced_config_form(self, agent_id: str) -> None:
        """Create advanced configuration form."""
        with ui.column().classes("w-full gap-4"):
            ui.label("Configurações Avançadas").classes("text-lg font-bold mb-2")

            # Memory limits
            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("flex-1"):
                    ui.label("Limite de Memória (MB)")
                    self.config_forms[agent_id]["memory_limit_mb"] = ui.number(
                        label="Memory Limit",
                        value=512,
                        min=128,
                        max=4096,
                    ).classes("w-full")

                with ui.column().classes("flex-1"):
                    ui.label("Tamanho do Buffer")
                    self.config_forms[agent_id]["buffer_size"] = ui.number(
                        label="Buffer Size",
                        value=1000,
                        min=100,
                        max=10000,
                    ).classes("w-full")

            # Custom parameters
            ui.label("Parâmetros Personalizados").classes("font-semibold mt-4")

            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("flex-1"):
                    ui.label("Modelo Gemini")
                    self.config_forms[agent_id]["gemini_model"] = ui.select(
                        ["gemini-1.5-pro", "gemini-1.5-flash"],
                        value="gemini-1.5-pro",
                        label="Gemini Model",
                    ).classes("w-full")

                with ui.column().classes("flex-1"):
                    ui.label("Temperatura")
                    self.config_forms[agent_id]["temperature"] = ui.number(
                        label="Temperature",
                        value=0.7,
                        min=0.0,
                        max=1.0,
                        step=0.1,
                    ).classes("w-full")

    def _create_security_config_form(self, agent_id: str) -> None:
        """Create security configuration form."""
        with ui.column().classes("w-full gap-4"):
            ui.label("Configurações de Segurança").classes("text-lg font-bold mb-2")

            # API Keys (masked inputs)
            with ui.column().classes("w-full gap-2"):
                ui.label("Chave API Gemini")
                self.config_forms[agent_id]["gemini_api_key"] = ui.input(
                    label="Gemini API Key",
                    password=True,
                    password_toggle_button=True,
                ).classes("w-full")

            # Security toggles
            self.config_forms[agent_id]["enable_rate_limiting"] = ui.checkbox(
                "Habilitar Rate Limiting",
                value=True,
            )

            self.config_forms[agent_id]["enable_audit_log"] = ui.checkbox(
                "Habilitar Log de Auditoria",
                value=True,
            )

            self.config_forms[agent_id]["require_authentication"] = ui.checkbox(
                "Requerer Autenticação",
                value=True,
            )

    async def _load_agent_config(self, agent_id: str, dialog: ui.dialog) -> None:
        """Load current agent configuration."""
        try:
            response = requests.get(
                config.get_agent_endpoint(f"/admin/agents/{agent_id}/config"),
                timeout=10,
            )

            if response.status_code == 200:
                config_data = response.json()
                agent_config = config_data.get("config", {})

                # Populate form fields with current values
                if agent_id in self.config_forms:
                    forms = self.config_forms[agent_id]

                    # Basic config
                    if "max_concurrent_tasks" in forms:
                        forms["max_concurrent_tasks"].value = agent_config.get(
                            "max_concurrent_tasks", 5
                        )
                    if "timeout_seconds" in forms:
                        forms["timeout_seconds"].value = agent_config.get(
                            "timeout_seconds", 300
                        )
                    if "retry_attempts" in forms:
                        forms["retry_attempts"].value = agent_config.get(
                            "retry_attempts", 3
                        )
                    if "log_level" in forms:
                        forms["log_level"].value = agent_config.get("log_level", "INFO")
                    if "enable_metrics" in forms:
                        forms["enable_metrics"].value = agent_config.get(
                            "enable_metrics", True
                        )

                    # Advanced config
                    if "memory_limit_mb" in forms:
                        forms["memory_limit_mb"].value = agent_config.get(
                            "memory_limit_mb", 512
                        )
                    if "buffer_size" in forms:
                        forms["buffer_size"].value = agent_config.get(
                            "buffer_size", 1000
                        )

                    # Custom parameters
                    custom_params = agent_config.get("custom_parameters", {})
                    if "gemini_model" in forms:
                        forms["gemini_model"].value = custom_params.get(
                            "gemini_model", "gemini-1.5-pro"
                        )
                    if "temperature" in forms:
                        forms["temperature"].value = custom_params.get(
                            "temperature", 0.7
                        )

                    # Security config (don't populate sensitive data)
                    if "enable_rate_limiting" in forms:
                        forms["enable_rate_limiting"].value = agent_config.get(
                            "enable_rate_limiting", True
                        )
                    if "enable_audit_log" in forms:
                        forms["enable_audit_log"].value = agent_config.get(
                            "enable_audit_log", True
                        )
                    if "require_authentication" in forms:
                        forms["require_authentication"].value = agent_config.get(
                            "require_authentication", True
                        )

            else:
                ui.notify("Erro ao carregar configuração atual", type="warning")

        except Exception as e:
            ui.notify(f"Erro ao carregar configuração: {str(e)}", type="negative")

    async def _validate_config(self, agent_id: str) -> None:
        """Validate agent configuration."""
        if agent_id not in self.config_forms:
            ui.notify("Formulário de configuração não encontrado", type="warning")
            return

        try:
            # Collect form data
            forms = self.config_forms[agent_id]
            config_data = {
                "max_concurrent_tasks": forms.get("max_concurrent_tasks", {}).value
                if forms.get("max_concurrent_tasks")
                else 5,
                "timeout_seconds": forms.get("timeout_seconds", {}).value
                if forms.get("timeout_seconds")
                else 300,
                "retry_attempts": forms.get("retry_attempts", {}).value
                if forms.get("retry_attempts")
                else 3,
                "log_level": forms.get("log_level", {}).value
                if forms.get("log_level")
                else "INFO",
                "enable_metrics": forms.get("enable_metrics", {}).value
                if forms.get("enable_metrics")
                else True,
                "memory_limit_mb": forms.get("memory_limit_mb", {}).value
                if forms.get("memory_limit_mb")
                else 512,
                "buffer_size": forms.get("buffer_size", {}).value
                if forms.get("buffer_size")
                else 1000,
                "custom_parameters": {
                    "gemini_model": forms.get("gemini_model", {}).value
                    if forms.get("gemini_model")
                    else "gemini-1.5-pro",
                    "temperature": forms.get("temperature", {}).value
                    if forms.get("temperature")
                    else 0.7,
                },
                "enable_rate_limiting": forms.get("enable_rate_limiting", {}).value
                if forms.get("enable_rate_limiting")
                else True,
                "enable_audit_log": forms.get("enable_audit_log", {}).value
                if forms.get("enable_audit_log")
                else True,
                "require_authentication": forms.get("require_authentication", {}).value
                if forms.get("require_authentication")
                else True,
            }

            # Send validation request
            ui.notify("Validando configuração...", type="info")

            response = requests.post(
                config.get_agent_endpoint(f"/admin/agents/{agent_id}/config/validate"),
                json={"config": config_data},
                timeout=15,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("is_valid", False):
                    ui.notify("Configuração válida!", type="positive")
                else:
                    errors = result.get("validation_errors", [])
                    error_msg = "\n".join(errors) if errors else "Configuração inválida"
                    ui.notify(f"Erros de validação:\n{error_msg}", type="negative")
            else:
                ui.notify("Erro na validação da configuração", type="negative")

        except Exception as e:
            ui.notify(f"Erro durante validação: {str(e)}", type="negative")

    async def _apply_config(self, agent_id: str, dialog: ui.dialog) -> None:
        """Apply configuration changes."""
        if agent_id not in self.config_forms:
            ui.notify("Formulário de configuração não encontrado", type="warning")
            return

        try:
            # Collect form data (same as validation)
            forms = self.config_forms[agent_id]
            config_data = {
                "max_concurrent_tasks": forms.get("max_concurrent_tasks", {}).value
                if forms.get("max_concurrent_tasks")
                else 5,
                "timeout_seconds": forms.get("timeout_seconds", {}).value
                if forms.get("timeout_seconds")
                else 300,
                "retry_attempts": forms.get("retry_attempts", {}).value
                if forms.get("retry_attempts")
                else 3,
                "log_level": forms.get("log_level", {}).value
                if forms.get("log_level")
                else "INFO",
                "enable_metrics": forms.get("enable_metrics", {}).value
                if forms.get("enable_metrics")
                else True,
                "memory_limit_mb": forms.get("memory_limit_mb", {}).value
                if forms.get("memory_limit_mb")
                else 512,
                "buffer_size": forms.get("buffer_size", {}).value
                if forms.get("buffer_size")
                else 1000,
                "custom_parameters": {
                    "gemini_model": forms.get("gemini_model", {}).value
                    if forms.get("gemini_model")
                    else "gemini-1.5-pro",
                    "temperature": forms.get("temperature", {}).value
                    if forms.get("temperature")
                    else 0.7,
                },
                "enable_rate_limiting": forms.get("enable_rate_limiting", {}).value
                if forms.get("enable_rate_limiting")
                else True,
                "enable_audit_log": forms.get("enable_audit_log", {}).value
                if forms.get("enable_audit_log")
                else True,
                "require_authentication": forms.get("require_authentication", {}).value
                if forms.get("require_authentication")
                else True,
            }

            # Add API key if provided
            api_key = (
                forms.get("gemini_api_key", {}).value
                if forms.get("gemini_api_key")
                else None
            )
            if api_key and api_key.strip():
                custom_params = config_data.get("custom_parameters", {})
                if isinstance(custom_params, dict):
                    custom_params["gemini_api_key"] = api_key

            # Send update request
            ui.notify("Aplicando configuração...", type="info")

            response = requests.put(
                config.get_agent_endpoint(f"/admin/agents/{agent_id}/config"),
                json={"config": config_data},
                timeout=30,
            )

            if response.status_code == 200:
                ui.notify("Configuração aplicada com sucesso!", type="positive")
                dialog.close()

                # Store backup for rollback
                self.config_backup[agent_id] = config_data

                # Refresh data if callback is available
                if self.refresh_callback:
                    await self.refresh_callback()

            else:
                error_msg = response.json().get("detail", "Erro desconhecido")
                ui.notify(f"Erro ao aplicar configuração: {error_msg}", type="negative")

        except Exception as e:
            ui.notify(f"Erro durante aplicação: {str(e)}", type="negative")

    async def _rollback_config(self, agent_id: str) -> None:
        """Rollback configuration to previous state."""
        with ui.dialog() as rollback_dialog:
            with ui.card().classes("w-96"):
                ui.label("Confirmar Rollback").classes("text-lg font-bold mb-4")
                ui.label("Tem certeza que deseja reverter as configurações?").classes(
                    "mb-4"
                )
                ui.label(
                    "Esta operação irá restaurar a configuração anterior."
                ).classes("text-sm text-yellow-600 mb-4")

                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Cancelar", on_click=rollback_dialog.close).classes(
                        "bg-gray-500 text-white"
                    )

                    def confirm_rollback() -> None:
                        rollback_dialog.close()
                        asyncio.create_task(self._perform_rollback(agent_id))

                    ui.button("Reverter", on_click=confirm_rollback).classes(
                        "bg-red-500 text-white"
                    )

        rollback_dialog.open()

    async def _perform_rollback(self, agent_id: str) -> None:
        """Perform the actual configuration rollback."""
        try:
            ui.notify("Revertendo configuração...", type="info")

            response = requests.post(
                config.get_agent_endpoint(f"/admin/agents/{agent_id}/config/rollback"),
                timeout=15,
            )

            if response.status_code == 200:
                ui.notify("Configuração revertida com sucesso!", type="positive")
            else:
                error_msg = response.json().get("detail", "Erro desconhecido")
                ui.notify(f"Erro no rollback: {error_msg}", type="negative")

        except Exception as e:
            ui.notify(f"Erro durante rollback: {str(e)}", type="negative")
