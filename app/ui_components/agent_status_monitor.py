"""Agent status monitoring component for real-time display."""

from datetime import datetime
from typing import Any

import requests
from nicegui import ui

from app.core.config import config


class AgentStatusMonitor:
    """Real-time agent status monitoring and display."""

    def __init__(self) -> None:
        """Initialize the agent status monitor."""
        self.agents_data: list[dict[str, Any]] = []
        self.system_health: dict[str, Any] = {}
        self.refresh_timer: ui.timer | None = None
        self.websocket_connected: bool = False
        self.status_cards: dict[str, Any] = {}
        self.agent_table: ui.table | None = None
        self.last_update: str = "Nunca"

    def create(self) -> None:
        """Create the agent status monitoring UI."""
        with ui.column().classes("w-full gap-6"):
            # Real-time status indicator
            self.create_real_time_status_indicator()

            # System health overview
            with ui.card().classes("w-full p-4"):
                ui.label("Status do Sistema").classes("text-xl font-bold mb-4")

                with ui.grid().classes("row q-gutter-md"):
                    # Active agents card with icon
                    with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md text-center"):
                        ui.icon("check_circle", size="2rem", color="green").classes("q-mb-sm")
                        ui.label("Agentes Ativos").classes("text-subtitle1 text-grey-7")
                        status_active = ui.label("0").classes("text-h4 text-green text-weight-bold")
                        status_active.bind_text_from(
                            self,
                            "system_health",
                            lambda x: str(x.get("healthy_agents", 0)),
                        )

                    # Total agents card with icon
                    with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md text-center"):
                        ui.icon("smart_toy", size="2rem", color="blue").classes("q-mb-sm")
                        ui.label("Total de Agentes").classes("text-subtitle1 text-grey-7")
                        status_total = ui.label("0").classes("text-h4 text-blue text-weight-bold")
                        status_total.bind_text_from(
                            self,
                            "system_health",
                            lambda x: str(x.get("total_agents", 0)),
                        )

                    # System status card with dynamic icon
                    with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md text-center"):
                        status_icon = ui.icon("help", size="2rem", color="grey").classes("q-mb-sm")
                        ui.label("Status do Sistema").classes("text-subtitle1 text-grey-7")
                        status_label = ui.label("Verificando...").classes("text-h6 text-weight-bold")

                        def update_status_display(health_data):
                            status = health_data.get("system_status", "unknown")
                            if status == "healthy":
                                status_icon.props("name=health_and_safety color=green")
                                status_label.props("class=text-h6 text-weight-bold text-green")
                                return "Saudável"
                            elif status == "degraded":
                                status_icon.props("name=warning color=orange")
                                status_label.props("class=text-h6 text-weight-bold text-orange")
                                return "Degradado"
                            elif status == "error":
                                status_icon.props("name=error color=red")
                                status_label.props("class=text-h6 text-weight-bold text-red")
                                return "Erro"
                            else:
                                status_icon.props("name=help color=grey")
                                status_label.props("class=text-h6 text-weight-bold text-grey")
                                return "Desconhecido"

                        status_label.bind_text_from(self, "system_health", update_status_display)

                    # Response time card
                    with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md text-center"):
                        ui.icon("speed", size="2rem", color="purple").classes("q-mb-sm")
                        ui.label("Tempo de Resposta").classes("text-subtitle1 text-grey-7")
                        response_time = ui.label("--ms").classes("text-h6 text-purple text-weight-bold")
                        response_time.bind_text_from(
                            self,
                            "system_health",
                            lambda x: f"{x.get('avg_response_time', '--')}ms",
                        )

            # Performance summary
            self._create_performance_summary()

            # Agents table
            with ui.card().classes("w-full p-4"):
                with ui.row().classes("w-full justify-between items-center mb-4"):
                    ui.label("Agentes Disponíveis").classes("text-xl font-bold")

                    with ui.row().classes("gap-2"):
                        ui.button(
                            "Atualizar",
                            on_click=self._refresh_data,
                            icon="refresh",
                        ).classes("bg-blue-500 text-white")

                        ui.button(
                            "Reiniciar Todos",
                            on_click=self._restart_all_agents,
                            icon="restart_alt",
                        ).classes("bg-orange-500 text-white")

                # Agents table container
                with ui.column().classes("w-full") as self.agents_container:
                    ui.label("Carregando dados dos agentes...").classes(
                        "text-center py-8"
                    )

    def load_initial_data(self) -> None:
        """Load initial data for the status monitor."""
        ui.timer(0.1, self._load_initial_data, once=True)
        # Setup WebSocket connection for real-time updates
        self.setup_websocket_connection()

    def _load_initial_data(self) -> None:
        """Load initial system and agent data."""
        self._refresh_data()

        # Set up auto-refresh timer (every 30 seconds)
        if self.refresh_timer:
            self.refresh_timer.cancel()

        self.refresh_timer = ui.timer(30.0, self._refresh_data)

    def _refresh_data(self) -> None:
        """Refresh system health and agents data."""
        try:
            # Load system health
            self._load_system_health()

            # Load agents data
            self._load_agents_data()

        except Exception as e:
            # Only show UI notifications if UI is available
            if hasattr(ui, "notify"):
                ui.notify(f"Erro ao carregar dados: {str(e)}", type="negative")

    def _load_system_health(self) -> None:
        """Load system health data."""
        try:
            response = requests.get(
                config.get_agent_endpoint("/admin/system/health"), timeout=10
            )
            if response.status_code == 200:
                self.system_health = response.json()
            else:
                self.system_health = {
                    "healthy_agents": 0,
                    "total_agents": 0,
                    "system_status": "error",
                }
        except Exception as e:
            # Only show UI notifications if UI is available
            if hasattr(ui, "notify"):
                ui.notify(f"Erro de conexão com API: {str(e)}", type="negative")
            self.system_health = {
                "healthy_agents": 0,
                "total_agents": 0,
                "system_status": "disconnected",
            }

    def _load_agents_data(self) -> None:
        """Load agents data from API."""
        try:
            response = requests.get(
                config.get_agent_endpoint("/admin/agents"), timeout=10
            )
            if response.status_code == 200:
                self.agents_data = response.json()
                # Only update UI table if agents_container exists (not in tests)
                if hasattr(self, "agents_container") and self.agents_container:
                    self._update_agents_table()
            else:
                self.agents_data = []
                # Only show UI notifications if UI is available
                if hasattr(ui, "notify"):
                    ui.notify("Erro ao carregar dados dos agentes", type="warning")
        except Exception as e:
            # Only show UI notifications if UI is available
            if hasattr(ui, "notify"):
                ui.notify(f"Erro de conexão com API: {str(e)}", type="negative")
            self.agents_data = []

    def _update_agents_table(self) -> None:
        """Update the agents table display."""
        # Clear existing content
        self.agents_container.clear()

        if not self.agents_data:
            with self.agents_container:
                ui.label("Nenhum agente encontrado").classes(
                    "text-center py-8 text-gray-500"
                )
            return

        # Create table header
        with self.agents_container:
            with ui.row().classes("w-full bg-gray-100 p-3 rounded font-bold"):
                ui.label("Agente").classes("flex-1")
                ui.label("Status").classes("w-24")
                ui.label("Saúde").classes("w-24")
                ui.label("Ações").classes("w-48")

            # Create rows for each agent
            for agent in self.agents_data:
                self._create_agent_row(agent)

    def _create_performance_summary(self) -> None:
        """Create performance summary cards."""
        with ui.card().classes("w-full p-4"):
            ui.label("Resumo de Performance").classes("text-xl font-bold mb-4")

            with ui.row().classes("w-full gap-4"):
                # Processing metrics
                with ui.card().classes("flex-1 p-3"):
                    ui.label("Tempo Médio de Processamento").classes(
                        "text-sm text-gray-600"
                    )
                    ui.label("~2.3s").classes("text-lg font-bold")

                with ui.card().classes("flex-1 p-3"):
                    ui.label("Taxa de Sucesso").classes("text-sm text-gray-600")
                    ui.label("94.2%").classes("text-lg font-bold text-green-600")

                with ui.card().classes("flex-1 p-3"):
                    ui.label("Uso de Memória").classes("text-sm text-gray-600")
                    ui.label("156MB").classes("text-lg font-bold")

                with ui.card().classes("flex-1 p-3"):
                    ui.label("Documentos Processados (24h)").classes(
                        "text-sm text-gray-600"
                    )
                    ui.label("847").classes("text-lg font-bold text-blue-600")

    def _create_agent_row(self, agent: dict[str, Any]) -> None:
        """Create a row for an agent in the table."""
        with ui.row().classes("w-full p-3 border-b border-gray-200 hover:bg-gray-50"):
            # Agent info
            with ui.column().classes("flex-1"):
                ui.label(agent.get("name", "Unknown")).classes("font-semibold")
                ui.label(agent.get("description", "No description")).classes(
                    "text-sm text-gray-600"
                )

            # Status badge
            status = agent.get("status", "unknown")
            status_color = {
                "active": "bg-green-100 text-green-800",
                "inactive": "bg-gray-100 text-gray-800",
                "error": "bg-red-100 text-red-800",
                "starting": "bg-yellow-100 text-yellow-800",
            }.get(status, "bg-gray-100 text-gray-800")

            ui.badge(status.title()).classes(f"{status_color} w-24")

            # Health status
            health = agent.get("health_status", "unknown")
            health_color = {
                "healthy": "bg-green-100 text-green-800",
                "unhealthy": "bg-red-100 text-red-800",
                "warning": "bg-yellow-100 text-yellow-800",
            }.get(health, "bg-gray-100 text-gray-800")

            ui.badge(health.title()).classes(f"{health_color} w-24")

            # Action buttons
            with ui.row().classes("w-48 gap-1"):
                agent_id = agent.get("agent_id", "")

                if status == "active":
                    ui.button(
                        "",
                        icon="stop",
                        on_click=lambda aid=agent_id: self._stop_agent(aid),
                    ).classes("bg-red-500 text-white w-8 h-8").tooltip("Parar")
                else:
                    ui.button(
                        "",
                        icon="play_arrow",
                        on_click=lambda aid=agent_id: self._start_agent(aid),
                    ).classes("bg-green-500 text-white w-8 h-8").tooltip("Iniciar")

                ui.button(
                    "",
                    icon="refresh",
                    on_click=lambda aid=agent_id: self._restart_agent(aid),
                ).classes("bg-orange-500 text-white w-8 h-8").tooltip("Reiniciar")

                ui.button(
                    "",
                    icon="info",
                    on_click=lambda aid=agent_id: self._show_agent_details(aid),
                ).classes("bg-blue-500 text-white w-8 h-8").tooltip("Detalhes")

                ui.button(
                    "",
                    icon="settings",
                    on_click=lambda aid=agent_id: self._show_agent_config(aid),
                ).classes("bg-purple-500 text-white w-8 h-8").tooltip("Configurar")

    def _start_agent(self, agent_id: str) -> None:
        """Start an agent."""
        try:
            ui.notify(f"Iniciando agente {agent_id}...", type="info")

            response = requests.post(
                config.get_agent_endpoint(f"/admin/agents/{agent_id}/start"), timeout=30
            )

            if response.status_code == 200:
                ui.notify(f"Agente {agent_id} iniciado com sucesso!", type="positive")
                self._refresh_data()
            else:
                error_msg = response.json().get("detail", "Erro desconhecido")
                ui.notify(f"Erro ao iniciar agente: {error_msg}", type="negative")

        except Exception as e:
            ui.notify(f"Erro de conexão: {str(e)}", type="negative")

    def _stop_agent(self, agent_id: str) -> None:
        """Stop an agent."""
        try:
            ui.notify(f"Parando agente {agent_id}...", type="info")

            response = requests.post(
                config.get_agent_endpoint(f"/admin/agents/{agent_id}/stop"), timeout=30
            )

            if response.status_code == 200:
                ui.notify(f"Agente {agent_id} parado com sucesso!", type="positive")
                self._refresh_data()
            else:
                error_msg = response.json().get("detail", "Erro desconhecido")
                ui.notify(f"Erro ao parar agente: {error_msg}", type="negative")

        except Exception as e:
            ui.notify(f"Erro de conexão: {str(e)}", type="negative")

    def _restart_agent(self, agent_id: str) -> None:
        """Restart an agent."""
        try:
            ui.notify(f"Reiniciando agente {agent_id}...", type="info")

            response = requests.post(
                config.get_agent_endpoint(f"/admin/agents/{agent_id}/restart"),
                timeout=30,
            )

            if response.status_code == 200:
                ui.notify(f"Agente {agent_id} reiniciado com sucesso!", type="positive")
                self._refresh_data()
            else:
                error_msg = response.json().get("detail", "Erro desconhecido")
                ui.notify(f"Erro ao reiniciar agente: {error_msg}", type="negative")

        except Exception as e:
            ui.notify(f"Erro de conexão: {str(e)}", type="negative")

    def _restart_all_agents(self) -> None:
        """Restart all agents with confirmation."""
        with ui.dialog() as confirm_dialog:
            with ui.card().classes("w-96"):
                ui.label("Confirmar Reinicialização").classes("text-lg font-bold mb-4")
                ui.label("Tem certeza que deseja reiniciar todos os agentes?").classes(
                    "mb-4"
                )
                ui.label(
                    "Esta operação pode interromper processamentos em andamento."
                ).classes("text-sm text-red-600 mb-4")

                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Cancelar", on_click=confirm_dialog.close).classes(
                        "bg-gray-500 text-white"
                    )

                    def confirm_restart() -> None:
                        confirm_dialog.close()
                        ui.timer(0.1, self._perform_restart_all, once=True)

                    ui.button("Reiniciar Todos", on_click=confirm_restart).classes(
                        "bg-red-500 text-white"
                    )

        confirm_dialog.open()

    def _perform_restart_all(self) -> None:
        """Perform the actual restart of all agents."""
        try:
            ui.notify("Iniciando reinicialização de todos os agentes...", type="info")

            response = requests.post(
                config.get_agent_endpoint("/admin/system/restart-all"), timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                successful = sum(
                    1 for r in result.get("results", []) if r.get("success")
                )
                total = len(result.get("results", []))

                ui.notify(
                    f"Reinicialização concluída. {successful}/{total} agentes reiniciados com sucesso.",
                    type="positive" if successful == total else "warning",
                )
                self._refresh_data()
            else:
                error_msg = response.json().get("detail", "Erro desconhecido")
                ui.notify(f"Erro na reinicialização: {error_msg}", type="negative")

        except Exception as e:
            ui.notify(f"Erro de conexão: {str(e)}", type="negative")

    def _show_agent_details(self, agent_id: str) -> None:
        """Show detailed information about an agent."""
        agent = next(
            (a for a in self.agents_data if a.get("agent_id") == agent_id), None
        )

        if not agent:
            ui.notify("Agente não encontrado", type="warning")
            return

        with ui.dialog() as details_dialog:
            with ui.card().classes("w-[600px] max-h-[80vh] overflow-auto"):
                ui.label(f"Detalhes do Agente: {agent.get('name', 'Unknown')}").classes(
                    "text-xl font-bold mb-4"
                )

                # Basic info
                with ui.expansion("Informações Básicas", icon="info").classes(
                    "w-full mb-2"
                ):
                    with ui.column().classes("gap-2 p-2"):
                        ui.label(f"ID: {agent.get('agent_id', 'N/A')}")
                        ui.label(f"Tipo: {agent.get('type', 'N/A')}")
                        ui.label(f"Versão: {agent.get('version', 'N/A')}")
                        ui.label(f"Status: {agent.get('status', 'N/A')}")
                        ui.label(f"Saúde: {agent.get('health_status', 'N/A')}")

                # Capabilities
                capabilities = agent.get("capabilities", [])
                if capabilities:
                    with ui.expansion("Capacidades", icon="build").classes(
                        "w-full mb-2"
                    ):
                        with ui.column().classes("gap-1 p-2"):
                            for capability in capabilities:
                                ui.label(f"• {capability}")

                # Performance metrics
                with ui.expansion("Métricas de Performance", icon="analytics").classes(
                    "w-full mb-2"
                ):
                    with ui.column().classes("gap-2 p-2"):
                        ui.label(
                            f"Última verificação: {agent.get('last_health_check', 'N/A')}"
                        )
                        ui.label(
                            f"Documentos processados: {agent.get('documents_processed', 0)}"
                        )
                        ui.label(
                            f"Tempo médio de processamento: {agent.get('avg_processing_time', 'N/A')}"
                        )
                        ui.label(f"Taxa de sucesso: {agent.get('success_rate', 'N/A')}")

                ui.button("Fechar", on_click=details_dialog.close).classes(
                    "w-full mt-4 bg-blue-500 text-white"
                )

        details_dialog.open()

    def _show_agent_config(self, agent_id: str) -> None:
        """Show agent configuration (delegated to config manager)."""
        # This will be handled by the AgentConfigManager in the tabs
        ui.notify(
            "Use a aba 'Configuração' para gerenciar configurações dos agentes.",
            type="info",
        )

    def setup_websocket_connection(self) -> None:
        """Setup WebSocket connection for real-time updates."""
        ui.run_javascript("""
            const connectWebSocket = () => {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/agents/status`;

                const ws = new WebSocket(wsUrl);

                ws.onopen = function(event) {
                    console.log('WebSocket connected to agent status');
                    window.agentStatusWS = ws;

                    // Send ping every 30 seconds to keep connection alive
                    setInterval(() => {
                        if (ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({type: 'ping'}));
                        }
                    }, 30000);
                };

                ws.onmessage = function(event) {
                    const message = JSON.parse(event.data);

                    if (message.type === 'agent_status_update' || message.type === 'initial_status') {
                        // Update Python side with received data
                        window.pywebview.api.update_agent_status_from_websocket(message.data);
                    }
                };

                ws.onclose = function(event) {
                    console.log('WebSocket disconnected, attempting to reconnect...');
                    setTimeout(connectWebSocket, 3000);
                };

                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            };

            connectWebSocket();
        """)

    def update_status_from_websocket(self, status_data: dict[str, Any]) -> None:
        """Update status display from WebSocket data."""
        try:
            self.websocket_connected = True

            # Update system health data
            if "system_health" in status_data:
                self.system_health = status_data["system_health"]

            # Update agents data
            if "agents" in status_data:
                self.agents_data = status_data["agents"]

            # Update last update time
            if "timestamp" in status_data:
                try:
                    timestamp = datetime.fromisoformat(status_data["timestamp"].replace('Z', '+00:00'))
                    self.last_update = timestamp.strftime("%H:%M:%S")
                except Exception:
                    self.last_update = "Agora"

            # Update UI components if they exist
            self._update_status_display()

        except Exception as e:
            print(f"Error updating from WebSocket: {e}")
            self.websocket_connected = False

    def _update_status_display(self) -> None:
        """Update the status display with current data."""
        try:
            # Update agents table if it exists
            if hasattr(self, "agents_container") and self.agents_container:
                self._update_agents_table()

            # Trigger UI refresh
            ui.update()

        except Exception as e:
            print(f"Error updating status display: {e}")

    def create_real_time_status_indicator(self) -> None:
        """Create a real-time status indicator showing WebSocket connection."""
        with ui.row().classes("w-full justify-between items-center mb-4"):
            ui.label("Status dos Agentes em Tempo Real").classes("text-xl font-bold")

            # Connection status indicator
            with ui.row().classes("items-center gap-2"):
                connection_icon = ui.icon("wifi", size="sm")
                connection_label = ui.label("Conectando...")

                # Update connection status periodically
                def update_connection_status():
                    if self.websocket_connected:
                        connection_icon.props("name=wifi color=green")
                        connection_label.text = f"Conectado - Última atualização: {self.last_update}"
                    else:
                        connection_icon.props("name=wifi_off color=red")
                        connection_label.text = "Desconectado"

                # Timer to update connection status every 2 seconds
                ui.timer(2.0, update_connection_status)
