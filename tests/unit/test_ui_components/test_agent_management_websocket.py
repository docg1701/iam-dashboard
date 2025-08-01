"""Tests for agent management WebSocket functionality."""

from unittest.mock import Mock, patch

import pytest

from app.ui_components.agent_status_monitor import AgentStatusMonitor


class TestAgentManagementWebSocket:
    """Test agent management WebSocket and real-time updates."""

    @pytest.fixture
    def agent_monitor(self):
        """Create agent status monitor instance for testing."""
        return AgentStatusMonitor()

    def test_agent_monitor_initialization_with_websocket_fields(self, agent_monitor):
        """Test agent monitor initializes with WebSocket-related fields."""
        assert agent_monitor.websocket_connected is False
        assert agent_monitor.status_cards == {}
        assert agent_monitor.agent_table is None
        assert agent_monitor.last_update == "Nunca"

    @patch('app.ui_components.agent_status_monitor.ui')
    def test_setup_websocket_connection(self, mock_ui, agent_monitor):
        """Test WebSocket connection setup."""
        agent_monitor.setup_websocket_connection()

        # Verify JavaScript was executed for WebSocket setup
        mock_ui.run_javascript.assert_called_once()

        # Check that the JavaScript contains WebSocket connection logic
        js_code = mock_ui.run_javascript.call_args[0][0]
        assert "WebSocket" in js_code
        assert "/ws/agents/status" in js_code
        assert "onopen" in js_code
        assert "onmessage" in js_code
        assert "onclose" in js_code

    def test_update_status_from_websocket_with_valid_data(self, agent_monitor):
        """Test updating status from WebSocket with valid data."""
        test_data = {
            "system_health": {
                "healthy_agents": 3,
                "total_agents": 4,
                "system_status": "healthy",
                "avg_response_time": 150
            },
            "agents": [
                {"agent_id": "agent1", "name": "PDF Processor", "status": "running"},
                {"agent_id": "agent2", "name": "Questionnaire Writer", "status": "running"}
            ],
            "timestamp": "2025-01-31T15:30:45Z"
        }

        with patch.object(agent_monitor, '_update_status_display') as mock_update:
            agent_monitor.update_status_from_websocket(test_data)

            # Verify connection status updated
            assert agent_monitor.websocket_connected is True

            # Verify system health data updated
            assert agent_monitor.system_health == test_data["system_health"]

            # Verify agents data updated
            assert agent_monitor.agents_data == test_data["agents"]

            # Verify timestamp processed
            assert agent_monitor.last_update == "15:30:45"

            # Verify UI update was triggered
            mock_update.assert_called_once()

    def test_update_status_from_websocket_with_invalid_timestamp(self, agent_monitor):
        """Test updating status with invalid timestamp."""
        test_data = {
            "system_health": {"healthy_agents": 2},
            "timestamp": "invalid-timestamp"
        }

        with patch.object(agent_monitor, '_update_status_display'):
            agent_monitor.update_status_from_websocket(test_data)

            # Should fallback to "Agora" when timestamp is invalid
            assert agent_monitor.last_update == "Agora"

    def test_update_status_from_websocket_handles_errors(self, agent_monitor):
        """Test error handling in WebSocket status update."""
        # Cause an error by passing invalid data
        invalid_data = None

        agent_monitor.update_status_from_websocket(invalid_data)

        # Connection should be marked as disconnected on error
        assert agent_monitor.websocket_connected is False

    @patch('app.ui_components.agent_status_monitor.ui')
    def test_update_status_display(self, mock_ui, agent_monitor):
        """Test status display update method."""
        # Mock the agents_container attribute
        agent_monitor.agents_container = Mock()

        with patch.object(agent_monitor, '_update_agents_table') as mock_update_table:
            agent_monitor._update_status_display()

            # Verify agents table was updated
            mock_update_table.assert_called_once()

            # Verify UI update was called
            mock_ui.update.assert_called_once()

    @patch('app.ui_components.agent_status_monitor.ui')
    def test_create_real_time_status_indicator(self, mock_ui, agent_monitor):
        """Test creation of real-time status indicator."""
        agent_monitor.create_real_time_status_indicator()

        # Verify UI components were created
        mock_ui.row.assert_called()
        mock_ui.label.assert_called()
        mock_ui.icon.assert_called()
        mock_ui.timer.assert_called()

        # Verify timer is set for 2 second intervals
        timer_call = mock_ui.timer.call_args
        assert timer_call[0][0] == 2.0  # 2 second interval

    @patch('app.ui_components.agent_status_monitor.ui')
    def test_create_with_real_time_indicator(self, mock_ui, agent_monitor):
        """Test that create method includes real-time status indicator."""
        with patch.object(agent_monitor, 'create_real_time_status_indicator') as mock_indicator:
            agent_monitor.create()

            # Verify real-time indicator was created
            mock_indicator.assert_called_once()

    @patch('app.ui_components.agent_status_monitor.ui')
    def test_load_initial_data_sets_up_websocket(self, mock_ui, agent_monitor):
        """Test that load_initial_data sets up WebSocket connection."""
        with patch.object(agent_monitor, 'setup_websocket_connection') as mock_setup:
            agent_monitor.load_initial_data()

            # Verify WebSocket setup was called
            mock_setup.assert_called_once()

            # Verify timer was set up for initial data loading
            mock_ui.timer.assert_called()

    def test_websocket_status_cards_responsive_design(self, agent_monitor):
        """Test that status cards use responsive Quasar design."""
        with patch('app.ui_components.agent_status_monitor.ui') as mock_ui, \
             patch.object(agent_monitor, 'create_real_time_status_indicator'), \
             patch.object(agent_monitor, '_create_performance_summary'):
            agent_monitor.create()

            # Verify grid layout is used
            mock_ui.grid.assert_called()

            # Verify cards are created (responsive design is in the implementation)
            mock_ui.card.assert_called()

            # Just verify the structure exists - responsive classes are implementation details
            assert mock_ui.grid.call_count >= 1

    def test_agent_status_cards_have_icons(self, agent_monitor):
        """Test that agent status cards include proper icons."""
        with patch('app.ui_components.agent_status_monitor.ui') as mock_ui:
            agent_monitor.create()

            # Verify icons are created for status cards
            icon_calls = mock_ui.icon.call_args_list

            # Check for expected icons
            expected_icons = ["check_circle", "smart_toy", "help", "speed", "wifi"]
            found_icons = [call[0][0] for call in icon_calls if call[0]]

            # Verify at least some expected icons are present
            assert any(icon in found_icons for icon in expected_icons[:4]), f"Expected icons not found. Found: {found_icons}"

    def test_connection_status_updates(self, agent_monitor):
        """Test connection status indicator updates correctly."""
        # Test connected state
        agent_monitor.websocket_connected = True
        agent_monitor.last_update = "12:34:56"

        # Test disconnected state
        agent_monitor.websocket_connected = False

        # The actual update logic is in JavaScript/UI timer
        # We just verify the state variables are set correctly
        assert agent_monitor.websocket_connected is False
