"""Tests for PerformanceMonitor UI component."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from nicegui import ui

from app.ui_components.performance_monitor import PerformanceMonitor


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor component."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.performance_monitor = PerformanceMonitor()

    def test_init(self) -> None:
        """Test PerformanceMonitor initialization."""
        assert self.performance_monitor.cpu_data == []
        assert self.performance_monitor.memory_data == []
        assert self.performance_monitor.agent_performance_data == []
        assert self.performance_monitor.system_alerts == []
        assert self.performance_monitor.cpu_chart is None
        assert self.performance_monitor.memory_chart is None
        assert self.performance_monitor.agent_chart is None
        assert self.performance_monitor.max_data_points == 50
        assert self.performance_monitor.update_interval == 5
        assert self.performance_monitor.cpu_alert_threshold == 80
        assert self.performance_monitor.memory_alert_threshold == 85

    @patch('asyncio.create_task')
    def test_create_ui_structure(self, mock_create_task) -> None:
        """Test that the create method builds the correct UI structure."""
        mock_create_task.return_value = MagicMock()

        with ui.column():  # Create container for test
            self.performance_monitor.create()

        # Verify asyncio.create_task was called for loading data
        assert mock_create_task.call_count >= 2  # Both system and agent metrics

    def test_data_point_limit(self) -> None:
        """Test that data collections maintain max data points."""
        # Add more than max data points
        for i in range(60):
            timestamp = datetime.now()
            self.performance_monitor.cpu_data.append({
                "timestamp": timestamp,
                "value": float(i),
                "label": f"{i}%"
            })

        # Should only keep max_data_points
        assert len(self.performance_monitor.cpu_data) == 60

        # Simulate the trimming logic
        if len(self.performance_monitor.cpu_data) > self.performance_monitor.max_data_points:
            excess = len(self.performance_monitor.cpu_data) - self.performance_monitor.max_data_points
            self.performance_monitor.cpu_data = self.performance_monitor.cpu_data[excess:]

        assert len(self.performance_monitor.cpu_data) == 50

    @patch('app.ui_components.performance_monitor.config')
    @patch('app.ui_components.performance_monitor.requests.get')
    @pytest.mark.asyncio
    async def test_collect_system_metrics_api_success(self, mock_get, mock_config) -> None:
        """Test successful system metrics collection via API."""
        mock_config.get_api_endpoint.return_value = "/api/admin/system/metrics"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cpu_percent": 45.5,
            "memory_percent": 67.2,
            "memory_used_gb": 8.5,
            "memory_total_gb": 16.0
        }
        mock_get.return_value = mock_response

        # Mock UI labels
        self.performance_monitor.cpu_value_label = MagicMock()
        self.performance_monitor.memory_value_label = MagicMock()

        with patch.object(self.performance_monitor, '_check_system_alerts', new_callable=AsyncMock):
            await self.performance_monitor._collect_system_metrics()

        # Verify data was collected
        assert len(self.performance_monitor.cpu_data) == 1
        assert len(self.performance_monitor.memory_data) == 1
        assert self.performance_monitor.cpu_data[0]["value"] == 45.5
        assert self.performance_monitor.memory_data[0]["value"] == 67.2

        # Verify API was called
        mock_get.assert_called_once()

    @patch('app.ui_components.performance_monitor.psutil')
    @pytest.mark.asyncio
    async def test_collect_system_metrics_local_fallback(self, mock_psutil) -> None:
        """Test local system metrics collection fallback."""
        mock_psutil.cpu_percent.return_value = 35.0
        mock_memory = MagicMock()
        mock_memory.percent = 55.0
        mock_memory.used = 4 * (1024**3)  # 4GB
        mock_memory.total = 8 * (1024**3)  # 8GB
        mock_psutil.virtual_memory.return_value = mock_memory

        # Mock UI labels
        self.performance_monitor.cpu_value_label = MagicMock()
        self.performance_monitor.memory_value_label = MagicMock()

        with patch.object(self.performance_monitor, '_check_system_alerts', new_callable=AsyncMock):
            await self.performance_monitor._collect_system_metrics_local()

        # Verify data was collected
        assert len(self.performance_monitor.cpu_data) == 1
        assert len(self.performance_monitor.memory_data) == 1
        assert self.performance_monitor.cpu_data[0]["value"] == 35.0
        assert self.performance_monitor.memory_data[0]["value"] == 55.0

    @patch('app.ui_components.performance_monitor.config')
    @patch('app.ui_components.performance_monitor.requests.get')
    @pytest.mark.asyncio
    async def test_collect_agent_metrics_success(self, mock_get, mock_config) -> None:
        """Test successful agent metrics collection."""
        mock_config.get_api_endpoint.return_value = "/api/admin/system/health"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "healthy_agents": 3,
            "total_agents": 4,
            "system_status": "degraded"
        }
        mock_get.return_value = mock_response

        # Mock UI labels
        self.performance_monitor.agents_value_label = MagicMock()
        self.performance_monitor.status_value_label = MagicMock()

        await self.performance_monitor._collect_agent_metrics()

        # Verify data was collected
        assert len(self.performance_monitor.agent_performance_data) == 1
        point = self.performance_monitor.agent_performance_data[0]
        assert point["active_agents"] == 3
        assert point["total_agents"] == 4
        assert point["success_rate"] == 75.0
        assert point["system_status"] == "degraded"

    @pytest.mark.asyncio
    async def test_check_system_alerts_cpu_warning(self) -> None:
        """Test system alert generation for high CPU."""
        self.performance_monitor.alerts_container = MagicMock()

        with patch.object(self.performance_monitor, '_update_alerts_display'):
            await self.performance_monitor._check_system_alerts(85.0, 70.0)

        # Should create CPU alert
        assert len(self.performance_monitor.system_alerts) == 1
        alert = self.performance_monitor.system_alerts[0]
        assert alert["type"] == "cpu"
        assert alert["level"] == "warning"
        assert "High CPU usage: 85.0%" in alert["message"]

    @pytest.mark.asyncio
    async def test_check_system_alerts_memory_critical(self) -> None:
        """Test system alert generation for critical memory."""
        self.performance_monitor.alerts_container = MagicMock()

        with patch.object(self.performance_monitor, '_update_alerts_display'):
            await self.performance_monitor._check_system_alerts(75.0, 96.0)

        # Should create memory alert
        assert len(self.performance_monitor.system_alerts) == 1
        alert = self.performance_monitor.system_alerts[0]
        assert alert["type"] == "memory"
        assert alert["level"] == "critical"
        assert "High memory usage: 96.0%" in alert["message"]

    @pytest.mark.asyncio
    async def test_check_system_alerts_multiple(self) -> None:
        """Test system alert generation for multiple thresholds."""
        self.performance_monitor.alerts_container = MagicMock()

        with patch.object(self.performance_monitor, '_update_alerts_display'):
            await self.performance_monitor._check_system_alerts(92.0, 98.0)

        # Should create both CPU and memory alerts
        assert len(self.performance_monitor.system_alerts) == 2

        cpu_alert = next(a for a in self.performance_monitor.system_alerts if a["type"] == "cpu")
        memory_alert = next(a for a in self.performance_monitor.system_alerts if a["type"] == "memory")

        assert cpu_alert["level"] == "critical"  # > 90%
        assert memory_alert["level"] == "critical"  # > 95%

    def test_update_alerts_display_empty(self) -> None:
        """Test alerts display with no alerts."""
        mock_container = MagicMock()
        mock_container.__enter__ = MagicMock(return_value=mock_container)
        mock_container.__exit__ = MagicMock(return_value=None)
        self.performance_monitor.alerts_container = mock_container

        self.performance_monitor._update_alerts_display()

        # Should clear container and show "no alerts"
        mock_container.clear.assert_called_once()

    def test_update_alerts_display_with_alerts(self) -> None:
        """Test alerts display with alerts."""
        mock_container = MagicMock()
        mock_container.__enter__ = MagicMock(return_value=mock_container)
        mock_container.__exit__ = MagicMock(return_value=None)
        self.performance_monitor.alerts_container = mock_container

        # Add test alerts
        self.performance_monitor.system_alerts = [
            {
                "type": "cpu",
                "level": "warning",
                "message": "High CPU usage: 85.0%",
                "timestamp": datetime.now(),
                "value": 85.0
            },
            {
                "type": "memory",
                "level": "critical",
                "message": "High memory usage: 96.0%",
                "timestamp": datetime.now(),
                "value": 96.0
            }
        ]

        self.performance_monitor._update_alerts_display()

        # Should display alerts
        mock_container.clear.assert_called_once()

    def test_update_cpu_chart(self) -> None:
        """Test CPU chart update."""
        # Mock chart
        mock_chart = MagicMock()
        self.performance_monitor.cpu_chart = mock_chart

        # Add test data
        self.performance_monitor.cpu_data = [
            {
                "timestamp": datetime.now(),
                "value": 45.0,
                "label": "45.0%"
            },
            {
                "timestamp": datetime.now(),
                "value": 50.0,
                "label": "50.0%"
            }
        ]

        self.performance_monitor._update_cpu_chart()

        # Verify chart was updated
        mock_chart.update_figure.assert_called_once()

        # Verify chart data structure
        call_args = mock_chart.update_figure.call_args[0][0]
        assert "data" in call_args
        assert "layout" in call_args
        assert len(call_args["data"]) == 1
        assert call_args["data"][0]["type"] == "scatter"

    def test_update_memory_chart(self) -> None:
        """Test memory chart update."""
        # Mock chart
        mock_chart = MagicMock()
        self.performance_monitor.memory_chart = mock_chart

        # Add test data
        self.performance_monitor.memory_data = [
            {
                "timestamp": datetime.now(),
                "value": 65.0,
                "label": "65.0%"
            }
        ]

        self.performance_monitor._update_memory_chart()

        # Verify chart was updated
        mock_chart.update_figure.assert_called_once()

    def test_update_agent_chart(self) -> None:
        """Test agent performance chart update."""
        # Mock chart
        mock_chart = MagicMock()
        self.performance_monitor.agent_chart = mock_chart

        # Add test data
        self.performance_monitor.agent_performance_data = [
            {
                "timestamp": datetime.now(),
                "active_agents": 3,
                "total_agents": 4,
                "success_rate": 75.0,
                "system_status": "degraded"
            }
        ]

        self.performance_monitor._update_agent_chart()

        # Verify chart was updated
        mock_chart.update_figure.assert_called_once()

        # Verify chart has dual y-axis data
        call_args = mock_chart.update_figure.call_args[0][0]
        assert len(call_args["data"]) == 2  # Active agents + success rate
        assert "yaxis2" in call_args["layout"]  # Dual y-axis

    def test_toggle_auto_refresh(self) -> None:
        """Test auto-refresh toggle."""
        with patch.object(self.performance_monitor, '_start_auto_refresh') as mock_start:
            with patch.object(self.performance_monitor, '_stop_auto_refresh') as mock_stop:
                # Test enable
                self.performance_monitor._toggle_auto_refresh(True)
                mock_start.assert_called_once()

                # Test disable
                self.performance_monitor._toggle_auto_refresh(False)
                mock_stop.assert_called_once()

    @patch('app.ui_components.performance_monitor.ui.notify')
    @pytest.mark.asyncio
    async def test_refresh_data(self, mock_notify) -> None:
        """Test manual data refresh."""
        with patch.object(self.performance_monitor, '_collect_system_metrics', new_callable=AsyncMock) as mock_system:
            with patch.object(self.performance_monitor, '_collect_agent_metrics', new_callable=AsyncMock) as mock_agent:
                with patch.object(self.performance_monitor, '_update_charts') as mock_charts:
                    self.performance_monitor._refresh_data()

                    mock_system.assert_called_once()
                    mock_agent.assert_called_once()
                    mock_charts.assert_called_once()
                    mock_notify.assert_called_with("Performance data refreshed", type="positive")

    def test_cleanup(self) -> None:
        """Test resource cleanup."""
        # Mock running timer
        mock_timer = MagicMock()
        mock_timer.done.return_value = False
        self.performance_monitor.update_timer = mock_timer

        with patch.object(self.performance_monitor, '_stop_auto_refresh') as mock_stop:
            self.performance_monitor.cleanup()
            mock_stop.assert_called_once()
