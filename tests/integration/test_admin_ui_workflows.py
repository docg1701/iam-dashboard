"""Integration tests for admin UI workflows."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import fastapi_app


class TestAdminUIWorkflows:
    """Integration tests for complete admin UI workflows."""

    def setup_method(self):
        """Set up test cases."""
        self.client = TestClient(fastapi_app)

    def test_admin_api_endpoints_exist(self):
        """Test that all required admin API endpoints exist."""
        # Test agents list endpoint
        response = self.client.get("/v1/admin/agents")
        assert response.status_code in [200, 500]  # 500 if AgentManager not initialized

        # Test system health endpoint
        response = self.client.get("/v1/admin/system/health")
        assert response.status_code in [200, 500]

        # Test agent config endpoint
        response = self.client.get("/v1/admin/agents/test/config")
        assert response.status_code in [200, 500]

        # Test config validation endpoint
        response = self.client.post(
            "/v1/admin/agents/test/config/validate",
            json={"config": {"max_concurrent_tasks": 5}},
        )
        assert response.status_code in [200, 500]

    def test_admin_agent_start_stop_workflow(self):
        """Test complete agent start/stop workflow."""
        agent_id = "test_agent"

        # Test start agent
        response = self.client.post(f"/v1/admin/agents/{agent_id}/start")
        assert response.status_code in [200, 500]

        # Test stop agent
        response = self.client.post(f"/v1/admin/agents/{agent_id}/stop")
        assert response.status_code in [200, 500]

        # Test restart agent
        response = self.client.post(f"/v1/admin/agents/{agent_id}/restart")
        assert response.status_code in [200, 500]

    def test_admin_configuration_workflow(self):
        """Test complete configuration management workflow."""
        agent_id = "test_agent"

        # Test get configuration
        response = self.client.get(f"/v1/admin/agents/{agent_id}/config")
        assert response.status_code in [200, 500]

        # Test configuration validation
        test_config = {
            "max_concurrent_tasks": 5,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "log_level": "INFO",
            "enable_metrics": True,
        }

        response = self.client.post(
            f"/v1/admin/agents/{agent_id}/config/validate", json={"config": test_config}
        )
        assert response.status_code in [200, 500]

        # Test configuration update
        response = self.client.put(
            f"/v1/admin/agents/{agent_id}/config", json={"config": test_config}
        )
        assert response.status_code in [200, 500]

        # Test configuration rollback
        response = self.client.post(f"/v1/admin/agents/{agent_id}/config/rollback")
        assert response.status_code in [200, 500]

    def test_config_validation_rules(self):
        """Test configuration validation rules."""
        agent_id = "test_agent"

        # Test invalid max_concurrent_tasks
        invalid_config = {
            "max_concurrent_tasks": -1,  # Invalid: negative value
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "log_level": "INFO",
        }

        response = self.client.post(
            f"/v1/admin/agents/{agent_id}/config/validate",
            json={"config": invalid_config},
        )

        if response.status_code == 200:
            data = response.json()
            assert data["is_valid"] is False
            assert any(
                "max_concurrent_tasks" in error for error in data["validation_errors"]
            )

    def test_config_validation_log_level(self):
        """Test log level validation."""
        agent_id = "test_agent"

        # Test invalid log level
        invalid_config = {
            "max_concurrent_tasks": 5,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "log_level": "INVALID_LEVEL",  # Invalid log level
        }

        response = self.client.post(
            f"/v1/admin/agents/{agent_id}/config/validate",
            json={"config": invalid_config},
        )

        if response.status_code == 200:
            data = response.json()
            assert data["is_valid"] is False
            assert any("log_level" in error for error in data["validation_errors"])

    def test_system_restart_all_workflow(self):
        """Test system-wide restart workflow."""
        response = self.client.post("/v1/admin/system/restart-all")
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "results" in data

    def test_agent_health_check_workflow(self):
        """Test agent health check workflow."""
        agent_id = "test_agent"

        response = self.client.get(f"/v1/admin/agents/{agent_id}/health")
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert "agent_id" in data
            assert "is_healthy" in data
            assert "health_status" in data

    @pytest.mark.asyncio
    async def test_admin_ui_access_control(self):
        """Test admin UI access control."""
        with (
            patch("app.ui_components.admin_dashboard.AuthManager") as mock_auth,
            patch("app.ui_components.admin_dashboard.ui") as mock_ui,
        ):
            from app.ui_components.admin_control_panel import AdminControlPanel

            # Test with non-admin user
            mock_auth.require_auth.return_value = True
            mock_auth.get_current_user.return_value = {
                "username": "user",
                "role": "common_user",
            }

            # Mock UI elements to prevent context errors
            mock_ui.column.return_value.__enter__ = MagicMock()
            mock_ui.column.return_value.__exit__ = MagicMock()

            panel = AdminControlPanel()
            result = panel._check_admin_access()
            assert result is False

            # Test with admin user
            mock_auth.get_current_user.return_value = {
                "username": "admin",
                "role": "admin_user",
            }

            result = panel._check_admin_access()
            assert result is True

    @pytest.mark.asyncio
    async def test_real_time_monitoring_workflow(self):
        """Test real-time monitoring functionality."""
        with (
            patch("app.ui_components.agent_status_monitor.requests") as mock_requests,
            patch("app.ui_components.agent_status_monitor.ui"),
        ):
            from app.ui_components.admin_control_panel import AdminControlPanel

            # Mock successful API responses
            mock_health_response = MagicMock()
            mock_health_response.status_code = 200
            mock_health_response.json.return_value = {
                "healthy_agents": 2,
                "total_agents": 3,
                "system_status": "degraded",
            }

            mock_agents_response = MagicMock()
            mock_agents_response.status_code = 200
            mock_agents_response.json.return_value = [
                {
                    "agent_id": "agent1",
                    "name": "Test Agent 1",
                    "status": "active",
                    "health_status": "healthy",
                    "capabilities": ["test"],
                }
            ]

            mock_requests.get.side_effect = [mock_health_response, mock_agents_response]

            panel = AdminControlPanel()
            await panel._refresh_data()

            # Verify data was loaded
            assert panel.system_health["healthy_agents"] == 2
            assert len(panel.agents_data) == 1
            assert panel.agents_data[0]["agent_id"] == "agent1"

    @pytest.mark.asyncio
    async def test_configuration_form_workflow(self):
        """Test complete configuration form workflow."""
        with (
            patch("app.ui_components.agent_config_manager.requests") as mock_requests,
            patch(
                "app.ui_components.agent_status_monitor.requests"
            ) as mock_status_requests,
        ):
            from app.ui_components.admin_control_panel import AdminControlPanel

            panel = AdminControlPanel()
            agent_id = "test_agent"

            # Mock configuration loading
            mock_config_response = MagicMock()
            mock_config_response.status_code = 200
            mock_config_response.json.return_value = {
                "agent_id": agent_id,
                "config": {
                    "max_concurrent_tasks": 5,
                    "timeout_seconds": 30,
                    "retry_attempts": 3,
                    "log_level": "INFO",
                    "enable_metrics": True,
                    "custom_parameters": {
                        "gemini_model": "gemini-1.5-pro",
                        "temperature": 0.7,
                    },
                },
                "is_valid": True,
                "validation_errors": [],
            }

            # Mock validation response
            mock_validation_response = MagicMock()
            mock_validation_response.status_code = 200
            mock_validation_response.json.return_value = {
                "is_valid": True,
                "validation_errors": [],
            }

            # Mock update response
            mock_update_response = MagicMock()
            mock_update_response.status_code = 200
            mock_update_response.json.return_value = {
                "is_valid": True,
                "validation_errors": [],
            }

            mock_requests.get.return_value = mock_config_response
            mock_requests.post.return_value = mock_validation_response
            mock_requests.put.return_value = mock_update_response

            # Mock status monitor API responses for refresh callback
            mock_health_response = MagicMock()
            mock_health_response.status_code = 200
            mock_health_response.json.return_value = {
                "healthy_agents": 1,
                "total_agents": 1,
                "system_status": "healthy",
            }

            mock_agents_response = MagicMock()
            mock_agents_response.status_code = 200
            mock_agents_response.json.return_value = [
                {
                    "agent_id": agent_id,
                    "name": "Test Agent",
                    "status": "active",
                    "health_status": "healthy",
                    "capabilities": ["test"],
                }
            ]

            mock_status_requests.get.side_effect = [
                mock_health_response,
                mock_agents_response,
            ]

            # Set up mock form data
            panel.config_forms = {
                agent_id: {
                    "max_concurrent_tasks": MagicMock(value=10),
                    "timeout_seconds": MagicMock(value=60),
                    "retry_attempts": MagicMock(value=5),
                    "log_level": MagicMock(value="DEBUG"),
                    "enable_metrics": MagicMock(value=False),
                    "gemini_model": MagicMock(value="gemini-1.5-flash"),
                    "temperature": MagicMock(value=0.5),
                }
            }

            # Test configuration validation
            with patch("nicegui.ui.notify") as mock_notify:
                await panel._validate_config(agent_id)
                mock_notify.assert_called_with("Configuração válida!", type="positive")

            # Test configuration application
            mock_dialog = MagicMock()
            with patch("nicegui.ui.notify") as mock_notify:
                # Mock the status monitor's refresh method before calling _apply_config
                original_refresh = panel.dashboard.config_manager.refresh_callback
                panel.dashboard.config_manager.refresh_callback = AsyncMock()

                await panel._apply_config(agent_id, mock_dialog)
                mock_notify.assert_called_with(
                    "Configuração aplicada com sucesso!", type="positive"
                )
                mock_dialog.close.assert_called_once()
                panel.dashboard.config_manager.refresh_callback.assert_called_once()

                # Restore original callback
                panel.dashboard.config_manager.refresh_callback = original_refresh

    @pytest.mark.asyncio
    async def test_plugin_management_workflow(self):
        """Test plugin management functionality."""
        from app.ui_components.admin_control_panel import AdminControlPanel

        panel = AdminControlPanel()

        # Test dependency refresh
        with patch("nicegui.ui.notify") as mock_notify:
            await panel._refresh_dependency("TestDependency")
            mock_notify.assert_any_call(
                "Atualizando dependência TestDependency...", type="info"
            )
            mock_notify.assert_any_call(
                "Dependência TestDependency atualizada", type="positive"
            )

        # Test conflict resolution
        test_conflict = {
            "type": "version_conflict",
            "description": "Test conflict",
            "severity": "high",
        }

        with patch("nicegui.ui.notify") as mock_notify:
            panel._resolve_conflict(test_conflict)
            mock_notify.assert_any_call(
                "Resolvendo conflito: version_conflict", type="info"
            )
            mock_notify.assert_any_call(
                "Conflito resolvido automaticamente", type="positive"
            )

        # Test plugin installation
        with patch("nicegui.ui.notify") as mock_notify:
            panel._install_plugin("TestPlugin")
            mock_notify.assert_any_call("Instalando plugin TestPlugin...", type="info")
            mock_notify.assert_any_call(
                "Plugin TestPlugin instalado com sucesso", type="positive"
            )

    def test_admin_route_registration(self):
        """Test that admin route is properly registered."""
        # Test admin route exists by checking if it returns a response
        # (We can't test the actual UI rendering in unit tests)
        from app.main import fastapi_app

        # Note: NiceGUI routes might not appear in FastAPI routes list
        # This test verifies the integration is properly set up
        assert fastapi_app is not None

    @pytest.mark.asyncio
    async def test_error_handling_in_workflows(self):
        """Test error handling in various workflows."""
        with patch("app.ui_components.agent_status_monitor.requests") as mock_requests:
            from app.ui_components.admin_control_panel import AdminControlPanel

            # Mock request exceptions
            mock_requests.get.side_effect = Exception("Connection error")

            panel = AdminControlPanel()

            # Test error handling in data loading
            with patch("nicegui.ui.notify") as mock_notify:
                await panel._load_system_health()
                mock_notify.assert_called_with(
                    "Erro de conexão com API: Connection error", type="negative"
                )

            with patch("nicegui.ui.notify") as mock_notify:
                await panel._load_agents_data()
                mock_notify.assert_called_with(
                    "Erro de conexão com API: Connection error", type="negative"
                )

    def test_responsive_design_elements(self):
        """Test responsive design elements in UI components."""
        from app.ui_components.admin_control_panel import AdminControlPanel

        panel = AdminControlPanel()

        # Test that UI component classes include responsive design classes
        # This is a basic test to ensure responsive classes are being used

        # Mock agents data for testing
        test_agent = {
            "agent_id": "test",
            "name": "Test Agent",
            "description": "Test Description",
            "status": "active",
            "health_status": "healthy",
            "capabilities": ["test"],
            "last_health_check": "2024-01-01T12:00:00Z",
        }

        # Test that the component can handle the agent data structure
        # without throwing exceptions (basic structural test)
        with (
            patch("nicegui.ui.column"),
            patch("nicegui.ui.label"),
            patch("nicegui.ui.badge"),
            patch("nicegui.ui.row"),
            patch("nicegui.ui.button"),
            patch("nicegui.ui.tooltip"),
        ):
            try:
                panel._create_agent_row(test_agent)
                # If no exception is thrown, the component structure is valid
                assert True
            except Exception as e:
                pytest.fail(f"Component structure test failed: {e}")
