"""Audit logs component with filtering and export functionality."""

from datetime import datetime
from typing import Any

from nicegui import ui

from app.models.audit_log import AuditAction, AuditLevel
from app.services.audit_log_service import AuditLogService


class AuditLogs:
    """Audit logs management component."""

    def __init__(self, audit_log_service: AuditLogService) -> None:
        """Initialize the audit logs component."""
        self.audit_log_service = audit_log_service

        # Data
        self.logs_data: list[dict[str, Any]] = []
        self.current_page = 1
        self.page_size = 25
        self.total_pages = 1
        self.total_count = 0

        # Filters
        self.action_filter = "all"
        self.level_filter = "all"
        self.user_filter = ""
        self.search_query = ""
        self.date_from: datetime | None = None
        self.date_to: datetime | None = None

        # UI Components
        self.logs_table: ui.table | None = None
        self.pagination_info: ui.label | None = None
        self.export_button: ui.button | None = None

        # Statistics
        self.stats_data: dict[str, Any] = {}

    def create(self) -> None:
        """Create the audit logs UI."""
        with ui.column().classes("w-full q-gutter-md"):
            # Header with title and export button
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("Logs de Auditoria").classes("text-h5 text-weight-bold")

                self.export_button = ui.button(
                    "Exportar CSV",
                    icon="file_download",
                    on_click=self._export_csv,
                ).classes("bg-primary text-white")

            # Statistics cards
            with ui.row().classes("w-full q-gutter-md"):
                with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                    ui.icon("assignment", size="2rem", color="blue").classes("q-mb-sm")
                    ui.label("Total de Logs").classes("text-subtitle1")
                    self.total_logs_label = ui.label("---").classes("text-h6 text-blue")

                with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                    ui.icon("error", size="2rem", color="red").classes("q-mb-sm")
                    ui.label("Logs Críticos").classes("text-subtitle1")
                    self.critical_logs_label = ui.label("---").classes("text-h6 text-red")

                with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                    ui.icon("warning", size="2rem", color="orange").classes("q-mb-sm")
                    ui.label("Avisos").classes("text-subtitle1")
                    self.warning_logs_label = ui.label("---").classes("text-h6 text-orange")

                with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                    ui.icon("info", size="2rem", color="green").classes("q-mb-sm")
                    ui.label("Informativos").classes("text-subtitle1")
                    self.info_logs_label = ui.label("---").classes("text-h6 text-green")

            # Filters
            with ui.card().classes("w-full q-pa-md"):
                ui.label("Filtros").classes("text-h6 q-mb-md")

                with ui.row().classes("w-full q-gutter-md"):
                    # Action filter
                    with ui.column().classes("col-xs-12 col-sm-6 col-md-3"):
                        ui.label("Ação").classes("text-weight-medium")
                        action_select = ui.select(
                            options=self._get_action_options(),
                            value="all",
                            on_change=lambda e: self._set_action_filter(e.value),
                        ).classes("w-full")
                        action_select.value = "all"  # Ensure default value is set

                    # Level filter
                    with ui.column().classes("col-xs-12 col-sm-6 col-md-3"):
                        ui.label("Nível").classes("text-weight-medium")
                        level_select = ui.select(
                            options=self._get_level_options(),
                            value="all",
                            on_change=lambda e: self._set_level_filter(e.value),
                        ).classes("w-full")
                        level_select.value = "all"  # Ensure default value is set

                    # User filter
                    with ui.column().classes("col-xs-12 col-sm-6 col-md-3"):
                        ui.label("Usuário").classes("text-weight-medium")
                        ui.input(
                            placeholder="Nome do usuário",
                            on_change=lambda e: self._set_user_filter(e.value),
                        ).classes("w-full")

                    # Search query
                    with ui.column().classes("col-xs-12 col-sm-6 col-md-3"):
                        ui.label("Buscar").classes("text-weight-medium")
                        ui.input(
                            placeholder="Buscar em mensagens",
                            on_change=lambda e: self._set_search_query(e.value),
                        ).classes("w-full")

                # Date range filters
                with ui.row().classes("w-full q-gutter-md q-mt-md"):
                    with ui.column().classes("col-xs-12 col-sm-6 col-md-3"):
                        ui.label("Data Início").classes("text-weight-medium")
                        ui.input(
                            placeholder="YYYY-MM-DD",
                            on_change=lambda e: self._set_date_from(e.value),
                        ).classes("w-full")

                    with ui.column().classes("col-xs-12 col-sm-6 col-md-3"):
                        ui.label("Data Fim").classes("text-weight-medium")
                        ui.input(
                            placeholder="YYYY-MM-DD",
                            on_change=lambda e: self._set_date_to(e.value),
                        ).classes("w-full")

                    with ui.column().classes("col-xs-12 col-sm-6 col-md-3"):
                        ui.label(" ").classes("text-weight-medium invisible")
                        ui.button(
                            "Aplicar Filtros",
                            icon="filter_list",
                            on_click=self._apply_filters,
                        ).classes("bg-secondary text-white w-full")

                    with ui.column().classes("col-xs-12 col-sm-6 col-md-3"):
                        ui.label(" ").classes("text-weight-medium invisible")
                        ui.button(
                            "Limpar Filtros",
                            icon="clear",
                            on_click=self._clear_filters,
                        ).classes("bg-grey text-white w-full")

            # Logs table
            with ui.card().classes("w-full q-pa-md"):
                ui.label("Registros de Auditoria").classes("text-h6 q-mb-md")

                self.logs_table = ui.table(
                    columns=[
                        {"name": "timestamp", "label": "Data/Hora", "field": "timestamp", "sortable": True},
                        {"name": "level", "label": "Nível", "field": "level", "sortable": True},
                        {"name": "action", "label": "Ação", "field": "action", "sortable": True},
                        {"name": "user", "label": "Usuário", "field": "user", "sortable": True},
                        {"name": "message", "label": "Mensagem", "field": "message", "sortable": True},
                        {"name": "resource", "label": "Recurso", "field": "resource", "sortable": True},
                    ],
                    rows=[],
                    row_key="id",
                    pagination=0,  # Disable built-in pagination
                ).classes("w-full")

                # Custom pagination
                with ui.row().classes("w-full justify-between items-center q-mt-md"):
                    self.pagination_info = ui.label("").classes("text-body2")

                    with ui.row().classes("q-gutter-sm"):
                        ui.button(
                            icon="first_page",
                            on_click=lambda: self._go_to_page(1),
                        ).classes("bg-grey-3").props("size=sm")

                        ui.button(
                            icon="chevron_left",
                            on_click=self._previous_page,
                        ).classes("bg-grey-3").props("size=sm")

                        self.page_input = ui.input(
                            value=str(self.current_page),
                            on_change=lambda e: self._go_to_page(int(e.value) if e.value.isdigit() else 1),
                        ).classes("text-center").props("size=sm").style("width: 80px")

                        ui.button(
                            icon="chevron_right",
                            on_click=self._next_page,
                        ).classes("bg-grey-3").props("size=sm")

                        ui.button(
                            icon="last_page",
                            on_click=lambda: self._go_to_page(self.total_pages),
                        ).classes("bg-grey-3").props("size=sm")

        # Load initial data
        ui.timer(0.1, self._load_data, once=True)
        ui.timer(0.1, self._load_statistics, once=True)

    def _get_action_options(self) -> dict[str, str]:
        """Get action filter options."""
        options = {"all": "Todas as Ações"}

        action_labels = {
            "user_created": "Usuário Criado",
            "user_updated": "Usuário Atualizado",
            "user_deleted": "Usuário Excluído",
            "user_2fa_reset": "2FA Resetado",
            "user_role_changed": "Papel Alterado",
            "agent_started": "Agente Iniciado",
            "agent_stopped": "Agente Parado",
            "agent_restarted": "Agente Reiniciado",
            "login_success": "Login Bem-sucedido",
            "login_failed": "Login Falhou",
            "logout": "Logout",
            "audit_logs_exported": "Logs Exportados",
        }

        for action in AuditAction:
            label = action_labels.get(action.value, action.value.replace("_", " ").title())
            options[action.value] = label

        return options

    def _get_level_options(self) -> dict[str, str]:
        """Get level filter options."""
        options = {"all": "Todos os Níveis"}

        level_labels = {
            "info": "Informativo",
            "warning": "Aviso",
            "error": "Erro",
            "critical": "Crítico",
        }

        for level in AuditLevel:
            label = level_labels.get(level.value, level.value.title())
            options[level.value] = label

        return options

    def _set_action_filter(self, value: str) -> None:
        """Set action filter."""
        self.action_filter = value

    def _set_level_filter(self, value: str) -> None:
        """Set level filter."""
        self.level_filter = value

    def _set_user_filter(self, value: str) -> None:
        """Set user filter."""
        self.user_filter = value.strip()

    def _set_search_query(self, value: str) -> None:
        """Set search query."""
        self.search_query = value.strip()

    def _set_date_from(self, value: str) -> None:
        """Set date from filter."""
        try:
            self.date_from = datetime.fromisoformat(value) if value else None
        except ValueError:
            ui.notify("Formato de data inválido. Use YYYY-MM-DD", type="warning")

    def _set_date_to(self, value: str) -> None:
        """Set date to filter."""
        try:
            if value:
                # Add end of day time
                date_to = datetime.fromisoformat(value)
                self.date_to = date_to.replace(hour=23, minute=59, second=59)
            else:
                self.date_to = None
        except ValueError:
            ui.notify("Formato de data inválido. Use YYYY-MM-DD", type="warning")

    def _apply_filters(self) -> None:
        """Apply current filters and reload data."""
        self.current_page = 1
        ui.timer(0.1, self._load_data, once=True)

    def _clear_filters(self) -> None:
        """Clear all filters."""
        self.action_filter = "all"
        self.level_filter = "all"
        self.user_filter = ""
        self.search_query = ""
        self.date_from = None
        self.date_to = None
        self.current_page = 1

        # Reset form values
        ui.run_javascript("""
            document.querySelectorAll('input').forEach(input => {
                if (input.placeholder.includes('usuário') || input.placeholder.includes('mensagens') || input.placeholder.includes('YYYY-MM-DD')) {
                    input.value = '';
                }
            });
            document.querySelectorAll('select').forEach(select => {
                select.value = 'all';
            });
        """)

        ui.timer(0.1, self._load_data, once=True)

    async def _load_data(self) -> None:
        """Load audit logs data."""
        try:
            # Prepare filters
            action_filter = self.action_filter if self.action_filter != "all" else None
            level_filter = self.level_filter if self.level_filter != "all" else None
            user_filter = self.user_filter if self.user_filter else None
            search_query = self.search_query if self.search_query else None

            logs, total_count, total_pages = await self.audit_log_service.get_logs_paginated(
                page=self.current_page,
                page_size=self.page_size,
                action_filter=action_filter,
                level_filter=level_filter,
                user_filter=user_filter,
                date_from=self.date_from,
                date_to=self.date_to,
                search_query=search_query,
            )

            self.total_count = total_count
            self.total_pages = total_pages

            # Format data for table
            self.logs_data = []
            for log in logs:
                self.logs_data.append({
                    "id": str(log.id),
                    "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "level": log.level_display,
                    "action": log.action_display,
                    "user": log.username or "Sistema",
                    "message": log.message,
                    "resource": f"{log.resource_type or ''} {log.resource_id or ''}".strip() or "-",
                    "level_color": log.level_color,
                })

            # Update table
            if self.logs_table:
                self.logs_table.rows = self.logs_data

            # Update pagination info
            start_item = (self.current_page - 1) * self.page_size + 1
            end_item = min(self.current_page * self.page_size, total_count)

            if self.pagination_info:
                self.pagination_info.text = f"Mostrando {start_item}-{end_item} de {total_count} registros (Página {self.current_page} de {total_pages})"

            if self.page_input:
                self.page_input.value = str(self.current_page)

        except Exception as e:
            ui.notify(f"Erro ao carregar logs: {str(e)}", type="negative")

    async def _load_statistics(self) -> None:
        """Load audit log statistics."""
        try:
            stats = await self.audit_log_service.get_audit_statistics()
            self.stats_data = stats

            # Update statistics cards
            self.total_logs_label.text = str(stats["total_logs"])
            self.critical_logs_label.text = str(stats["critical_logs"])
            self.warning_logs_label.text = str(stats["warning_logs"])
            self.info_logs_label.text = str(stats["info_logs"])

        except Exception as e:
            ui.notify(f"Erro ao carregar estatísticas: {str(e)}", type="negative")

    def _go_to_page(self, page: int) -> None:
        """Go to specific page."""
        if 1 <= page <= self.total_pages:
            self.current_page = page
            ui.timer(0.1, self._load_data, once=True)

    def _next_page(self) -> None:
        """Go to next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            ui.timer(0.1, self._load_data, once=True)

    def _previous_page(self) -> None:
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            ui.timer(0.1, self._load_data, once=True)

    async def _export_csv(self) -> None:
        """Export audit logs to CSV."""
        try:
            if self.export_button:
                self.export_button.props("loading")

            # Prepare filters for export
            action_filter = self.action_filter if self.action_filter != "all" else None
            level_filter = self.level_filter if self.level_filter != "all" else None
            user_filter = self.user_filter if self.user_filter else None
            search_query = self.search_query if self.search_query else None

            csv_content = await self.audit_log_service.export_logs_csv(
                action_filter=action_filter,
                level_filter=level_filter,
                user_filter=user_filter,
                date_from=self.date_from,
                date_to=self.date_to,
                search_query=search_query,
            )

            # Generate download
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_logs_{timestamp}.csv"

            ui.download(csv_content.encode('utf-8'), filename)
            ui.notify("Logs exportados com sucesso!", type="positive")

            # Log the export action
            await self.audit_log_service.log_action(
                action=AuditAction.AUDIT_LOGS_EXPORTED,
                message=f"Audit logs exported to {filename}",
                level=AuditLevel.INFO,
                details={"filename": filename, "filters_applied": {
                    "action": action_filter,
                    "level": level_filter,
                    "user": user_filter,
                    "search": search_query,
                    "date_from": self.date_from.isoformat() if self.date_from else None,
                    "date_to": self.date_to.isoformat() if self.date_to else None,
                }}
            )

        except Exception as e:
            ui.notify(f"Erro ao exportar logs: {str(e)}", type="negative")
        finally:
            if self.export_button:
                self.export_button.props(remove="loading")

