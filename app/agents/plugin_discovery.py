"""Plugin discovery and loading mechanisms for agent plugins."""

import importlib
import logging
from pathlib import Path

from app.agents.base_agent import AgentPlugin, plugin_registry

logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Handles discovery and loading of agent plugins."""

    def __init__(self, plugin_dirs: list[str] | None = None):
        """Initialize plugin discovery.

        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugin_dirs = plugin_dirs or ["app.plugins"]
        self._discovered_plugins: dict[str, type[AgentPlugin]] = {}

    async def discover_plugins(self) -> dict[str, type[AgentPlugin]]:
        """Discover all available plugins.

        Returns:
            Dictionary mapping plugin names to plugin classes
        """
        logger.info("Starting plugin discovery")
        self._discovered_plugins.clear()

        for plugin_dir in self.plugin_dirs:
            await self._discover_plugins_in_directory(plugin_dir)

        logger.info(f"Discovered {len(self._discovered_plugins)} plugins")
        return self._discovered_plugins.copy()

    async def load_plugins(self) -> int:
        """Load all discovered plugins into the registry.

        Returns:
            Number of plugins successfully loaded
        """
        if not self._discovered_plugins:
            await self.discover_plugins()

        loaded_count = 0
        for plugin_name, plugin_class in self._discovered_plugins.items():
            try:
                plugin_registry.register_plugin(plugin_class)
                loaded_count += 1
                logger.info(f"Loaded plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")

        logger.info(f"Successfully loaded {loaded_count} plugins")
        return loaded_count

    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a specific plugin.

        Args:
            plugin_name: Name of the plugin to reload

        Returns:
            True if reload was successful, False otherwise
        """
        try:
            logger.info(f"Reloading plugin: {plugin_name}")

            # Find and reimport the plugin module
            plugin_class = self._discovered_plugins.get(plugin_name)
            if not plugin_class:
                logger.error(f"Plugin {plugin_name} not found in discovered plugins")
                return False

            module_name = plugin_class.__module__
            module = importlib.import_module(module_name)
            importlib.reload(module)

            # Re-register the plugin
            new_plugin_class = getattr(module, plugin_class.__name__)
            plugin_registry.register_plugin(new_plugin_class)
            self._discovered_plugins[plugin_name] = new_plugin_class

            logger.info(f"Successfully reloaded plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to reload plugin {plugin_name}: {str(e)}")
            return False

    def get_plugin_validation_errors(self, plugin_class: type) -> list[str]:
        """Validate a plugin class and return any errors.

        Args:
            plugin_class: Plugin class to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Check if it inherits from AgentPlugin
        if not issubclass(plugin_class, AgentPlugin):
            errors.append("Plugin must inherit from AgentPlugin")

        # Check required methods
        required_methods = ["initialize", "process", "health_check", "get_capabilities"]
        for method in required_methods:
            if not hasattr(plugin_class, method):
                errors.append(f"Plugin missing required method: {method}")
            elif callable(getattr(plugin_class, method)):
                # Check if method is abstract (not implemented)
                method_obj = getattr(plugin_class, method)
                if (
                    hasattr(method_obj, "__isabstractmethod__")
                    and method_obj.__isabstractmethod__
                ):
                    errors.append(f"Plugin method {method} is not implemented")

        # Check for required class attributes
        if not hasattr(plugin_class, "PLUGIN_NAME"):
            errors.append("Plugin missing PLUGIN_NAME class attribute")

        return errors

    async def _discover_plugins_in_directory(self, plugin_dir: str) -> None:
        """Discover plugins in a specific directory.

        Args:
            plugin_dir: Directory path to search for plugins
        """
        try:
            # Check if it's a module path (contains dots but not file separators)
            if "." in plugin_dir and "/" not in plugin_dir and "\\" not in plugin_dir:
                # Already a module path
                module_path = plugin_dir

                logger.debug(f"Searching for plugins in module: {module_path}")

                try:
                    # Import the module
                    module = importlib.import_module(module_path)

                    # Look for plugin files in the directory
                    if hasattr(module, "__path__"):
                        for module_path_item in module.__path__:
                            await self._scan_directory_for_plugins(
                                Path(module_path_item)
                            )

                except ImportError as e:
                    logger.debug(
                        f"Could not import plugin directory {module_path}: {str(e)}"
                    )

            else:
                # It's a file path, scan directly
                logger.debug(f"Searching for plugins in directory: {plugin_dir}")
                path = Path(plugin_dir)
                if path.exists() and path.is_dir():
                    await self._scan_directory_for_plugins(path)
                else:
                    logger.warning(f"Plugin directory does not exist: {plugin_dir}")

        except Exception as e:
            logger.error(f"Error discovering plugins in {plugin_dir}: {str(e)}")

    async def _scan_directory_for_plugins(self, directory: Path) -> None:
        """Scan a directory for Python plugin files.

        Args:
            directory: Directory path to scan
        """
        try:
            for file_path in directory.glob("*.py"):
                if file_path.name.startswith("__"):
                    continue

                await self._load_plugin_from_file(file_path)

        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {str(e)}")

    async def _load_plugin_from_file(self, file_path: Path) -> None:
        """Load a plugin from a Python file.

        Args:
            file_path: Path to the Python file
        """
        try:
            # Convert file path to module name
            relative_path = file_path.relative_to(Path.cwd())
            module_name = (
                str(relative_path).replace("/", ".").replace("\\", ".")[:-3]
            )  # Remove .py

            logger.debug(f"Loading plugin module: {module_name}")

            # Import the module
            module = importlib.import_module(module_name)

            # Look for plugin classes in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # Check if it's a plugin class
                if (
                    isinstance(attr, type)
                    and issubclass(attr, AgentPlugin)
                    and attr != AgentPlugin
                ):
                    # Validate the plugin
                    errors = self.get_plugin_validation_errors(attr)
                    if errors:
                        logger.warning(
                            f"Plugin {attr.__name__} validation failed: {errors}"
                        )
                        continue

                    # Get plugin name
                    plugin_name = getattr(attr, "PLUGIN_NAME", attr.__name__)

                    # Store the discovered plugin
                    self._discovered_plugins[plugin_name] = attr
                    logger.debug(f"Discovered plugin: {plugin_name}")

        except Exception as e:
            logger.error(f"Error loading plugin from {file_path}: {str(e)}")


# Global discovery instance
plugin_discovery = PluginDiscovery()
