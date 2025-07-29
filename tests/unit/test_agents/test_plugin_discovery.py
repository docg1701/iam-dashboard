"""Tests for plugin discovery system."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.agents.base_agent import AgentPlugin
from app.agents.plugin_discovery import PluginDiscovery


class MockPlugin(AgentPlugin):
    """Mock plugin for testing discovery."""

    PLUGIN_NAME = "MockPlugin"
    VERSION = "1.0.0"

    async def initialize(self) -> bool:
        return True

    async def process(self, data):
        return {"processed": True}

    async def health_check(self) -> bool:
        return True

    def get_capabilities(self):
        return ["mock_capability"]


class InvalidPlugin:
    """Invalid plugin that doesn't inherit from AgentPlugin."""

    PLUGIN_NAME = "InvalidPlugin"


class TestPluginDiscovery:
    """Test suite for PluginDiscovery class."""

    @pytest.fixture
    def discovery(self):
        """Create PluginDiscovery instance for testing."""
        return PluginDiscovery(plugin_dirs=["test.plugins"])

    @pytest.fixture
    def temp_plugin_dir(self):
        """Create temporary directory with plugin files."""
        temp_dir = Path(tempfile.mkdtemp())

        # Create a valid plugin file
        plugin_file = temp_dir / "test_plugin.py"
        plugin_code = """
from app.agents.base_agent import AgentPlugin

class TestPlugin(AgentPlugin):
    PLUGIN_NAME = "TestPlugin"
    VERSION = "1.0.0"

    async def initialize(self):
        return True

    async def process(self, data):
        return {"result": "test"}

    async def health_check(self):
        return True

    def get_capabilities(self):
        return ["test"]
"""
        plugin_file.write_text(plugin_code)

        # Create an invalid plugin file
        invalid_file = temp_dir / "invalid_plugin.py"
        invalid_code = """
class NotAPlugin:
    pass
"""
        invalid_file.write_text(invalid_code)

        yield temp_dir

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir)

    def test_discovery_initialization(self):
        """Test PluginDiscovery initialization."""
        discovery = PluginDiscovery()
        assert discovery.plugin_dirs == ["app.plugins"]
        assert discovery._discovered_plugins == {}

        # With custom dirs
        custom_discovery = PluginDiscovery(["custom.plugins", "other.plugins"])
        assert custom_discovery.plugin_dirs == ["custom.plugins", "other.plugins"]

    @pytest.mark.asyncio
    @patch("app.agents.plugin_discovery.importlib.import_module")
    async def test_discover_plugins_success(self, mock_import, discovery):
        """Test successful plugin discovery."""
        # Mock module with plugin class - note discovery uses "test.plugins"
        mock_module = Mock()
        mock_module.__path__ = ["/fake/path"]
        mock_import.return_value = mock_module

        # Track if our mock function was called
        mock_load_called = False

        # Mock Path.glob to return plugin file
        with patch("pathlib.Path.glob") as mock_glob:
            mock_file = Mock()
            mock_file.name = "mock_plugin.py"
            mock_glob.return_value = [mock_file]

            # Mock the file loading to add our plugin after clear()
            async def mock_load_plugin_side_effect(file_path):
                nonlocal mock_load_called
                mock_load_called = True
                discovery._discovered_plugins["MockPlugin"] = MockPlugin

            with patch.object(
                discovery,
                "_load_plugin_from_file",
                side_effect=mock_load_plugin_side_effect,
            ) as mock_load:
                result = await discovery.discover_plugins()

                # Debug information
                print(f"Mock load called: {mock_load_called}")
                print(f"Mock load call count: {mock_load.call_count}")
                print(f"Import called with: {mock_import.call_args_list}")
                print(f"Discovered plugins: {discovery._discovered_plugins}")
                print(f"Result: {result}")

                # Verify the import was called with the fixture's plugin dir
                mock_import.assert_called_with("test.plugins")
                assert mock_load_called, "Load plugin function should have been called"
                assert "MockPlugin" in result
                assert result["MockPlugin"] == MockPlugin

    @pytest.mark.asyncio
    async def test_discover_plugins_import_error(self, discovery):
        """Test plugin discovery with import error."""
        with patch(
            "app.agents.plugin_discovery.importlib.import_module"
        ) as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            result = await discovery.discover_plugins()

            # Should handle the error gracefully
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    @patch("app.agents.plugin_discovery.plugin_registry")
    async def test_load_plugins_success(self, mock_registry, discovery):
        """Test successful plugin loading."""
        # Setup discovered plugins
        discovery._discovered_plugins = {"MockPlugin": MockPlugin}

        # Mock registry register method
        mock_registry.register_plugin = Mock()

        result = await discovery.load_plugins()

        assert result == 1
        mock_registry.register_plugin.assert_called_once_with(MockPlugin)

    @pytest.mark.asyncio
    @patch("app.agents.plugin_discovery.plugin_registry")
    async def test_load_plugins_with_error(self, mock_registry, discovery):
        """Test plugin loading with registry error."""
        # Setup discovered plugins
        discovery._discovered_plugins = {
            "MockPlugin": MockPlugin,
            "ErrorPlugin": MockPlugin,  # Will cause error
        }

        # Mock registry to raise error on second call
        mock_registry.register_plugin = Mock(
            side_effect=[None, Exception("Registration failed")]
        )

        result = await discovery.load_plugins()

        assert result == 1  # Only one successful
        assert mock_registry.register_plugin.call_count == 2

    @pytest.mark.asyncio
    @patch("app.agents.plugin_discovery.importlib")
    @patch("app.agents.plugin_discovery.plugin_registry")
    async def test_reload_plugin_success(
        self, mock_registry, mock_importlib, discovery
    ):
        """Test successful plugin reload."""
        # Setup discovered plugin
        discovery._discovered_plugins = {"MockPlugin": MockPlugin}

        # Mock importlib functions
        mock_module = Mock()
        mock_module.MockPlugin = MockPlugin
        mock_importlib.import_module.return_value = mock_module
        mock_importlib.reload.return_value = mock_module

        result = await discovery.reload_plugin("MockPlugin")

        assert result is True
        mock_registry.register_plugin.assert_called_once_with(MockPlugin)

    @pytest.mark.asyncio
    async def test_reload_plugin_not_found(self, discovery):
        """Test reloading non-existent plugin."""
        result = await discovery.reload_plugin("NonExistent")
        assert result is False

    def test_get_plugin_validation_errors_valid(self, discovery):
        """Test validation of valid plugin."""
        errors = discovery.get_plugin_validation_errors(MockPlugin)
        assert len(errors) == 0

    def test_get_plugin_validation_errors_invalid(self, discovery):
        """Test validation of invalid plugin."""
        errors = discovery.get_plugin_validation_errors(InvalidPlugin)

        assert len(errors) > 0
        assert any("inherit from AgentPlugin" in error for error in errors)

    def test_get_plugin_validation_errors_missing_methods(self, discovery):
        """Test validation of plugin with missing methods."""

        class IncompletePlugin(AgentPlugin):
            PLUGIN_NAME = "IncompletePlugin"

            # Missing required method implementations
            pass

        errors = discovery.get_plugin_validation_errors(IncompletePlugin)
        assert len(errors) > 0
        # Check for specific missing methods
        assert any("not implemented" in error for error in errors)

    def test_get_plugin_validation_errors_missing_plugin_name(self, discovery):
        """Test validation of plugin without PLUGIN_NAME."""

        class NoNamePlugin(AgentPlugin):
            # Missing PLUGIN_NAME

            async def initialize(self):
                return True

            async def process(self, data):
                return {}

            async def health_check(self):
                return True

            def get_capabilities(self):
                return []

        errors = discovery.get_plugin_validation_errors(NoNamePlugin)
        assert any("missing PLUGIN_NAME" in error for error in errors)

    @pytest.mark.asyncio
    async def test_discover_plugins_in_directory_module_path(self, discovery):
        """Test discovering plugins in module path."""
        with patch(
            "app.agents.plugin_discovery.importlib.import_module"
        ) as mock_import:
            mock_module = Mock()
            mock_module.__path__ = ["/fake/path"]
            mock_import.return_value = mock_module

            with patch.object(discovery, "_scan_directory_for_plugins") as mock_scan:
                await discovery._discover_plugins_in_directory("app.plugins")

                mock_import.assert_called_once_with("app.plugins")
                mock_scan.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_plugins_in_directory_file_path(
        self, discovery, temp_plugin_dir
    ):
        """Test discovering plugins in file path."""
        with patch.object(discovery, "_scan_directory_for_plugins") as mock_scan:
            await discovery._discover_plugins_in_directory(str(temp_plugin_dir))

            # Should call scan_directory since import fails
            mock_scan.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_directory_for_plugins(self, discovery, temp_plugin_dir):
        """Test scanning directory for plugin files."""
        with patch.object(discovery, "_load_plugin_from_file") as mock_load:
            await discovery._scan_directory_for_plugins(temp_plugin_dir)

            # Should call load for each .py file (excluding __init__.py, etc.)
            assert mock_load.call_count >= 1

    @pytest.mark.asyncio
    async def test_scan_directory_for_plugins_error(self, discovery):
        """Test scanning directory with error."""
        # Non-existent directory
        fake_dir = Path("/nonexistent/directory")

        # Should handle error gracefully
        await discovery._scan_directory_for_plugins(fake_dir)
        # No exception should be raised

    @pytest.mark.asyncio
    @patch("app.agents.plugin_discovery.importlib.import_module")
    async def test_load_plugin_from_file_success(self, mock_import, discovery):
        """Test loading plugin from file successfully."""
        # Create a mock module with a valid plugin
        mock_module = MagicMock()
        mock_module.TestPlugin = MockPlugin
        mock_import.return_value = mock_module

        # Mock the dir() function to return our test plugin
        with patch("builtins.dir", return_value=["TestPlugin", "other_attr"]):
            # Mock file path
            mock_file = Mock()
            mock_file.relative_to.return_value = Path("test/plugin.py")

            await discovery._load_plugin_from_file(mock_file)

            # Should discover the plugin
            assert "MockPlugin" in discovery._discovered_plugins

    @pytest.mark.asyncio
    @patch("app.agents.plugin_discovery.importlib.import_module")
    async def test_load_plugin_from_file_import_error(self, mock_import, discovery):
        """Test handling import error when loading plugin."""
        mock_import.side_effect = ImportError("Cannot import module")

        mock_file = Mock()
        mock_file.relative_to.return_value = Path("test/plugin.py")

        # Should handle error gracefully
        await discovery._load_plugin_from_file(mock_file)

        # No plugins should be discovered
        assert len(discovery._discovered_plugins) == 0

    @pytest.mark.asyncio
    @patch("app.agents.plugin_discovery.importlib.import_module")
    async def test_load_plugin_from_file_invalid_plugin(self, mock_import, discovery):
        """Test loading file with invalid plugin."""
        # Mock module with invalid plugin
        mock_module = MagicMock()
        mock_module.InvalidPlugin = InvalidPlugin
        mock_import.return_value = mock_module

        # Mock the dir() function to return our invalid plugin
        with patch("builtins.dir", return_value=["InvalidPlugin"]):
            mock_file = Mock()
            mock_file.relative_to.return_value = Path("test/plugin.py")

            await discovery._load_plugin_from_file(mock_file)

            # Invalid plugin should not be discovered
            assert len(discovery._discovered_plugins) == 0
