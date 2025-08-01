"""Performance monitoring component with real-time charts and system metrics."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import psutil
import requests
from nicegui import ui

from app.core.config import config


class PerformanceMonitor:
    """Performance monitoring component with real-time metrics and charts."""

    def __init__(self) -> None:
        """Initialize the performance monitor."""
        self.cpu_data: list[dict[str, Any]] = []
        self.memory_data: list[dict[str, Any]] = []
        self.agent_performance_data: list[dict[str, Any]] = []
        self.system_alerts: list[dict[str, Any]] = []

        # Chart containers
        self.cpu_chart: ui.plotly | None = None
        self.memory_chart: ui.plotly | None = None
        self.agent_chart: ui.plotly | None = None
        self.alerts_container: ui.element | None = None

        # Configuration
        self.max_data_points = 50
        self.update_interval = 5  # seconds
        self.cpu_alert_threshold = 80
        self.memory_alert_threshold = 85

        # Update timer
        self.update_timer: asyncio.Task | None = None

    def _update_metric_card(self, label: ui.label, value: float, threshold: float, normal_color: str) -> None:
        """Update a metric card with value and threshold-based coloring."""
        label.text = f"{value:.1f}%"
        color = "red" if value > threshold else normal_color
        label.classes(f"text-h6 text-{color}")

    def create(self) -> None:
        """Create the performance monitoring UI."""
        with ui.column().classes("w-full q-gutter-md"):
            # Header with controls
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("Monitoramento de Performance").classes("text-h5 text-weight-bold")

                with ui.row().classes("q-gutter-sm"):
                    # Refresh controls
                    ui.button(
                        icon="refresh",
                        on_click=self._refresh_data,
                    ).classes("bg-primary text-white").props("size=sm")

                    # Auto-refresh toggle
                    auto_refresh = ui.switch("Auto-refresh", value=True).classes("text-body2")
                    auto_refresh.on('update:model-value', self._toggle_auto_refresh)

            # System metrics overview cards
            with ui.row().classes("w-full q-gutter-md"):
                # CPU usage card
                with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                    ui.icon("memory", size="2rem", color="blue").classes("q-mb-sm")
                    ui.label("CPU Usage").classes("text-subtitle1")
                    self.cpu_value_label = ui.label("---%").classes("text-h6 text-blue")

                # Memory usage card
                with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                    ui.icon("storage", size="2rem", color="green").classes("q-mb-sm")
                    ui.label("Memory Usage").classes("text-subtitle1")
                    self.memory_value_label = ui.label("---%").classes("text-h6 text-green")

                # Active agents card
                with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                    ui.icon("smart_toy", size="2rem", color="orange").classes("q-mb-sm")
                    ui.label("Active Agents").classes("text-subtitle1")
                    self.agents_value_label = ui.label("---").classes("text-h6 text-orange")

                # System status card
                with ui.card().classes("col-xs-12 col-sm-6 col-md-3 q-pa-md"):
                    ui.icon("health_and_safety", size="2rem", color="red").classes("q-mb-sm")
                    ui.label("System Status").classes("text-subtitle1")
                    self.status_value_label = ui.label("---").classes("text-h6")

            # Performance charts
            with ui.row().classes("w-full q-gutter-md"):
                # CPU usage chart
                with ui.card().classes("col-xs-12 col-md-6 q-pa-md"):
                    ui.label("CPU Usage Over Time").classes("text-h6 q-mb-md")
                    self.cpu_chart = ui.plotly({}).classes("w-full h-64")

                # Memory usage chart
                with ui.card().classes("col-xs-12 col-md-6 q-pa-md"):
                    ui.label("Memory Usage Over Time").classes("text-h6 q-mb-md")
                    self.memory_chart = ui.plotly({}).classes("w-full h-64")

            # Agent performance chart
            with ui.card().classes("w-full q-pa-md"):
                ui.label("Agent Performance Metrics").classes("text-h6 q-mb-md")
                self.agent_chart = ui.plotly({}).classes("w-full h-80")

            # System alerts
            with ui.card().classes("w-full q-pa-md"):
                ui.label("System Alerts").classes("text-h6 q-mb-md")
                with ui.column().classes("w-full") as alerts_container:
                    self.alerts_container = alerts_container
                    ui.label("No alerts").classes("text-center q-pa-lg text-grey-6")

        # Load initial data and start auto-refresh
        self._load_initial_data()
        self._start_auto_refresh()

    def _load_initial_data(self) -> None:
        """Load initial performance data."""
        ui.timer(0.1, self._collect_system_metrics, once=True)
        ui.timer(0.1, self._collect_agent_metrics, once=True)

    def _start_auto_refresh(self) -> None:
        """Start automatic data refresh."""
        if self.update_timer is None:
            self.update_timer = ui.timer(5.0, self._refresh_data)

    def _stop_auto_refresh(self) -> None:
        """Stop automatic data refresh."""
        if self.update_timer:
            self.update_timer.cancel()

    async def _auto_refresh_loop(self) -> None:
        """Auto-refresh loop for performance data."""
        while True:
            try:
                await asyncio.sleep(self.update_interval)
                await self._collect_system_metrics()
                await self._collect_agent_metrics()
                self._update_charts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                ui.notify(f"Error updating performance data: {str(e)}", type="warning")

    def _toggle_auto_refresh(self, enabled: bool) -> None:
        """Toggle auto-refresh on/off."""
        if enabled:
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()

    def _refresh_data(self) -> None:
        """Manually refresh performance data."""
        self._collect_system_metrics()
        self._collect_agent_metrics()
        self._update_charts()
        ui.notify("Performance data refreshed", type="positive")

    def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            # Get system metrics from admin API
            response = requests.get(
                config.get_api_endpoint("/admin/system/metrics"),
                timeout=10
            )

            if response.status_code != 200:
                # Fallback to local collection if API fails
                self._collect_system_metrics_local()
                return

            metrics = response.json()
            timestamp = datetime.now()

            cpu_percent = metrics["cpu_percent"]
            memory_percent = metrics["memory_percent"]

            # Add to data collections
            cpu_point = {
                "timestamp": timestamp,
                "value": cpu_percent,
                "label": f"{cpu_percent:.1f}%"
            }

            memory_point = {
                "timestamp": timestamp,
                "value": memory_percent,
                "label": f"{memory_percent:.1f}%",
                "used_gb": metrics["memory_used_gb"],
                "total_gb": metrics["memory_total_gb"]
            }

            # Maintain max data points
            self.cpu_data.append(cpu_point)
            self.memory_data.append(memory_point)

            if len(self.cpu_data) > self.max_data_points:
                self.cpu_data.pop(0)
            if len(self.memory_data) > self.max_data_points:
                self.memory_data.pop(0)

            # Update overview cards
            self._update_metric_card(self.cpu_value_label, cpu_percent, self.cpu_alert_threshold, "blue")
            self._update_metric_card(self.memory_value_label, memory_percent, self.memory_alert_threshold, "green")

            # Check for alerts
            self._check_system_alerts(cpu_percent, memory_percent)

        except Exception as e:
            ui.notify(f"Error collecting system metrics: {str(e)}", type="warning")
            # Fallback to local collection
            self._collect_system_metrics_local()

    def _collect_system_metrics_local(self) -> None:
        """Fallback method to collect system metrics locally."""
        try:
            timestamp = datetime.now()

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Add to data collections
            cpu_point = {
                "timestamp": timestamp,
                "value": cpu_percent,
                "label": f"{cpu_percent:.1f}%"
            }

            memory_point = {
                "timestamp": timestamp,
                "value": memory_percent,
                "label": f"{memory_percent:.1f}%",
                "used_gb": memory.used / (1024**3),
                "total_gb": memory.total / (1024**3)
            }

            # Maintain max data points
            self.cpu_data.append(cpu_point)
            self.memory_data.append(memory_point)

            if len(self.cpu_data) > self.max_data_points:
                self.cpu_data.pop(0)
            if len(self.memory_data) > self.max_data_points:
                self.memory_data.pop(0)

            # Update overview cards
            self._update_metric_card(self.cpu_value_label, cpu_percent, self.cpu_alert_threshold, "blue")
            self._update_metric_card(self.memory_value_label, memory_percent, self.memory_alert_threshold, "green")

            # Check for alerts
            self._check_system_alerts(cpu_percent, memory_percent)

        except Exception as e:
            ui.notify(f"Error collecting local system metrics: {str(e)}", type="negative")

    def _collect_agent_metrics(self) -> None:
        """Collect agent performance metrics."""
        try:
            # Get agent status from admin API
            response = requests.get(
                config.get_api_endpoint("/admin/system/health"),
                timeout=10
            )

            if response.status_code == 200:
                health_data = response.json()

                active_agents = health_data.get("healthy_agents", 0)
                total_agents = health_data.get("total_agents", 0)
                system_status = health_data.get("system_status", "unknown")

                # Update overview cards
                self.agents_value_label.text = f"{active_agents}/{total_agents}"
                self.status_value_label.text = system_status.title()

                # Set status color
                if system_status == "healthy":
                    self.status_value_label.classes("text-h6 text-green")
                elif system_status == "degraded":
                    self.status_value_label.classes("text-h6 text-orange")
                else:
                    self.status_value_label.classes("text-h6 text-red")

                # Collect agent performance data
                timestamp = datetime.now()
                agent_point = {
                    "timestamp": timestamp,
                    "active_agents": active_agents,
                    "total_agents": total_agents,
                    "success_rate": (active_agents / total_agents * 100) if total_agents > 0 else 0,
                    "system_status": system_status
                }

                self.agent_performance_data.append(agent_point)

                if len(self.agent_performance_data) > self.max_data_points:
                    self.agent_performance_data.pop(0)

        except Exception as e:
            ui.notify(f"Error collecting agent metrics: {str(e)}", type="warning")

    def _check_system_alerts(self, cpu_percent: float, memory_percent: float) -> None:
        """Check for system alerts and update alert display."""
        new_alerts = []
        current_time = datetime.now()

        # CPU alert
        if cpu_percent > self.cpu_alert_threshold:
            new_alerts.append({
                "type": "cpu",
                "level": "critical" if cpu_percent > 90 else "warning",
                "message": f"High CPU usage: {cpu_percent:.1f}%",
                "timestamp": current_time,
                "value": cpu_percent
            })

        # Memory alert
        if memory_percent > self.memory_alert_threshold:
            new_alerts.append({
                "type": "memory",
                "level": "critical" if memory_percent > 95 else "warning",
                "message": f"High memory usage: {memory_percent:.1f}%",
                "timestamp": current_time,
                "value": memory_percent
            })

        # Add new alerts
        self.system_alerts.extend(new_alerts)

        # Keep only recent alerts (last hour)
        cutoff_time = current_time - timedelta(hours=1)
        self.system_alerts = [
            alert for alert in self.system_alerts
            if alert["timestamp"] > cutoff_time
        ]

        # Update alerts display
        self._update_alerts_display()

    def _update_alerts_display(self) -> None:
        """Update the alerts display."""
        if not self.alerts_container:
            return

        self.alerts_container.clear()

        if not self.system_alerts:
            with self.alerts_container:
                ui.label("No alerts").classes("text-center q-pa-lg text-grey-6")
            return

        # Group alerts by type for display
        with self.alerts_container:
            for alert in sorted(self.system_alerts, key=lambda x: x["timestamp"], reverse=True)[:10]:
                level_color = {
                    "critical": "red",
                    "warning": "orange",
                    "info": "blue"
                }.get(alert["level"], "grey")

                level_icon = {
                    "critical": "error",
                    "warning": "warning",
                    "info": "info"
                }.get(alert["level"], "circle")

                with ui.row().classes("w-full items-center q-pa-sm border-bottom"):
                    ui.icon(level_icon, color=level_color, size="md").classes("q-mr-md")

                    with ui.column().classes("flex-grow"):
                        ui.label(alert["message"]).classes(f"text-weight-medium text-{level_color}")
                        ui.label(alert["timestamp"].strftime("%H:%M:%S")).classes("text-caption text-grey-6")

    def _update_charts(self) -> None:
        """Update all performance charts."""
        self._update_cpu_chart()
        self._update_memory_chart()
        self._update_agent_chart()

    def _update_cpu_chart(self) -> None:
        """Update CPU usage chart."""
        if not self.cpu_chart or not self.cpu_data:
            return

        timestamps = [point["timestamp"].strftime("%H:%M:%S") for point in self.cpu_data]
        values = [point["value"] for point in self.cpu_data]

        fig = {
            "data": [{
                "x": timestamps,
                "y": values,
                "type": "scatter",
                "mode": "lines+markers",
                "name": "CPU Usage",
                "line": {"color": "#1976d2", "width": 2},
                "marker": {"size": 4}
            }],
            "layout": {
                "title": "",
                "xaxis": {"title": "Time", "showgrid": True},
                "yaxis": {"title": "Usage (%)", "range": [0, 100], "showgrid": True},
                "margin": {"l": 60, "r": 20, "t": 20, "b": 60},
                "height": 200,
                "showlegend": False,
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)"
            }
        }

        self.cpu_chart.update_figure(fig)

    def _update_memory_chart(self) -> None:
        """Update memory usage chart."""
        if not self.memory_chart or not self.memory_data:
            return

        timestamps = [point["timestamp"].strftime("%H:%M:%S") for point in self.memory_data]
        values = [point["value"] for point in self.memory_data]

        fig = {
            "data": [{
                "x": timestamps,
                "y": values,
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Memory Usage",
                "line": {"color": "#388e3c", "width": 2},
                "marker": {"size": 4}
            }],
            "layout": {
                "title": "",
                "xaxis": {"title": "Time", "showgrid": True},
                "yaxis": {"title": "Usage (%)", "range": [0, 100], "showgrid": True},
                "margin": {"l": 60, "r": 20, "t": 20, "b": 60},
                "height": 200,
                "showlegend": False,
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)"
            }
        }

        self.memory_chart.update_figure(fig)

    def _update_agent_chart(self) -> None:
        """Update agent performance chart."""
        if not self.agent_chart or not self.agent_performance_data:
            return

        timestamps = [point["timestamp"].strftime("%H:%M:%S") for point in self.agent_performance_data]
        active_agents = [point["active_agents"] for point in self.agent_performance_data]
        total_agents = [point["total_agents"] for point in self.agent_performance_data]
        success_rates = [point["success_rate"] for point in self.agent_performance_data]

        fig = {
            "data": [
                {
                    "x": timestamps,
                    "y": active_agents,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Active Agents",
                    "line": {"color": "#ff9800", "width": 2},
                    "marker": {"size": 4},
                    "yaxis": "y"
                },
                {
                    "x": timestamps,
                    "y": success_rates,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Success Rate (%)",
                    "line": {"color": "#4caf50", "width": 2},
                    "marker": {"size": 4},
                    "yaxis": "y2"
                }
            ],
            "layout": {
                "title": "",
                "xaxis": {"title": "Time", "showgrid": True},
                "yaxis": {
                    "title": "Active Agents",
                    "side": "left",
                    "showgrid": True,
                    "range": [0, max(max(total_agents) if total_agents else [1], 5)]
                },
                "yaxis2": {
                    "title": "Success Rate (%)",
                    "side": "right",
                    "overlaying": "y",
                    "range": [0, 100]
                },
                "margin": {"l": 60, "r": 60, "t": 20, "b": 60},
                "height": 300,
                "legend": {"x": 0, "y": 1},
                "plot_bgcolor": "rgba(0,0,0,0)",
                "paper_bgcolor": "rgba(0,0,0,0)"
            }
        }

        self.agent_chart.update_figure(fig)

    def cleanup(self) -> None:
        """Cleanup resources when component is destroyed."""
        self._stop_auto_refresh()
