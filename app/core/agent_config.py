"""Agent configuration management with YAML parsing and validation."""

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class GlobalConfig(BaseModel):
    """Global agent configuration."""

    health_check_interval: int = Field(default=60, ge=1)
    max_retries: int = Field(default=3, ge=0)
    timeout: int = Field(default=30, ge=1)
    log_level: str = Field(default="INFO")


class DiscoveryConfig(BaseModel):
    """Plugin discovery configuration."""

    plugin_directories: list[str] = Field(default=["app.plugins"])
    auto_discovery: bool = Field(default=True)
    reload_on_change: bool = Field(default=False)


class AgentConfig(BaseModel):
    """Individual agent configuration."""

    enabled: bool = Field(default=False)
    plugin_name: str
    name: str
    description: str = Field(default="")
    version: str = Field(default="1.0.0")
    capabilities: list[str] = Field(default=[])
    dependencies: list[str] = Field(default=[])
    config: dict[str, Any] = Field(default={})


class SecurityConfig(BaseModel):
    """Security configuration for agents."""

    validate_plugins: bool = Field(default=True)
    sandbox_plugins: bool = Field(default=False)
    allowed_imports: list[str] = Field(
        default=["agno", "logging", "asyncio", "typing", "datetime", "pathlib"]
    )


class MonitoringConfig(BaseModel):
    """Monitoring and logging configuration."""

    enable_metrics: bool = Field(default=True)
    metrics_endpoint: str = Field(default="/metrics")
    health_check_endpoint: str = Field(default="/health")
    log_agent_actions: bool = Field(default=True)
    log_level: str = Field(default="INFO")


class AgentSystemConfig(BaseModel):
    """Complete agent system configuration."""

    global_config: GlobalConfig = Field(default=GlobalConfig())
    discovery: DiscoveryConfig = Field(default=DiscoveryConfig())
    agents: dict[str, AgentConfig] = Field(default={})
    security: SecurityConfig = Field(default=SecurityConfig())
    monitoring: MonitoringConfig = Field(default=MonitoringConfig())


class ConfigManager:
    """Manages agent configuration with YAML loading and environment overrides."""

    def __init__(self, config_path: str | None = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path or "app/config/agents.yaml"
        self._config: AgentSystemConfig | None = None
        self._file_watcher_task: Any | None = None

    def load_config(self) -> AgentSystemConfig:
        """Load configuration from YAML file with environment variable overrides.

        Returns:
            Loaded and validated configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config validation fails
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            logger.info(f"Loading agent configuration from: {self.config_path}")

            # Load YAML file
            config_path = Path(self.config_path)
            if not config_path.exists():
                logger.warning(
                    f"Config file {self.config_path} not found, using defaults"
                )
                raw_config: dict[str, Any] = {}
            else:
                with open(config_path, encoding="utf-8") as f:
                    raw_config = yaml.safe_load(f) or {}

            # Apply environment variable overrides
            raw_config = self._apply_env_overrides(raw_config)

            # Validate and create configuration
            self._config = self._validate_config(raw_config)

            logger.info("Agent configuration loaded successfully")
            return self._config

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {str(e)}")
            raise
        except ValidationError as e:
            logger.error(f"Configuration validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise

    def get_config(self) -> AgentSystemConfig:
        """Get current configuration, loading if necessary.

        Returns:
            Current configuration
        """
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def get_agent_config(self, agent_id: str) -> AgentConfig | None:
        """Get configuration for a specific agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Agent configuration or None if not found
        """
        config = self.get_config()
        return config.agents.get(agent_id)

    def get_enabled_agents(self) -> dict[str, AgentConfig]:
        """Get all enabled agent configurations.

        Returns:
            Dictionary of enabled agent configurations
        """
        config = self.get_config()
        return {
            agent_id: agent_config
            for agent_id, agent_config in config.agents.items()
            if agent_config.enabled
        }

    def reload_config(self) -> AgentSystemConfig:
        """Reload configuration from file.

        Returns:
            Reloaded configuration
        """
        logger.info("Reloading agent configuration")
        self._config = None
        return self.load_config()

    def validate_agent_config(self, agent_config: dict[str, Any]) -> AgentConfig:
        """Validate an individual agent configuration.

        Args:
            agent_config: Raw agent configuration dictionary

        Returns:
            Validated agent configuration

        Raises:
            ValidationError: If validation fails
        """
        return AgentConfig(**agent_config)

    def _apply_env_overrides(self, config: dict[str, Any]) -> dict[str, Any]:
        """Apply environment variable overrides to configuration.

        Args:
            config: Raw configuration dictionary

        Returns:
            Configuration with environment overrides applied
        """
        # Apply global overrides
        health_check_interval = os.getenv("AGENT_GLOBAL_HEALTH_CHECK_INTERVAL")
        if health_check_interval:
            config.setdefault("global", {})["health_check_interval"] = int(
                health_check_interval
            )

        max_retries = os.getenv("AGENT_GLOBAL_MAX_RETRIES")
        if max_retries:
            config.setdefault("global", {})["max_retries"] = int(max_retries)

        timeout = os.getenv("AGENT_GLOBAL_TIMEOUT")
        if timeout:
            config.setdefault("global", {})["timeout"] = int(timeout)

        log_level = os.getenv("AGENT_GLOBAL_LOG_LEVEL")
        if log_level:
            config.setdefault("global", {})["log_level"] = log_level

        # Apply discovery overrides
        auto_discovery = os.getenv("AGENT_DISCOVERY_AUTO_DISCOVERY")
        if auto_discovery:
            config.setdefault("discovery", {})["auto_discovery"] = (
                auto_discovery.lower() == "true"
            )

        reload_on_change = os.getenv("AGENT_DISCOVERY_RELOAD_ON_CHANGE")
        if reload_on_change:
            config.setdefault("discovery", {})["reload_on_change"] = (
                reload_on_change.lower() == "true"
            )

        # Apply security overrides
        validate_plugins = os.getenv("AGENT_SECURITY_VALIDATE_PLUGINS")
        if validate_plugins:
            config.setdefault("security", {})["validate_plugins"] = (
                validate_plugins.lower() == "true"
            )

        sandbox_plugins = os.getenv("AGENT_SECURITY_SANDBOX_PLUGINS")
        if sandbox_plugins:
            config.setdefault("security", {})["sandbox_plugins"] = (
                sandbox_plugins.lower() == "true"
            )

        # Apply agent-specific overrides (only if agent already exists)
        for env_var, value in os.environ.items():
            if env_var.startswith("AGENT_") and "_CONFIG_" in env_var:
                # Parse agent-specific config: AGENT_{AGENT_ID}_CONFIG_{KEY}
                parts = env_var.replace("AGENT_", "").split("_CONFIG_")
                if len(parts) == 2:
                    agent_id = parts[0].lower()
                    config_key = parts[1].lower()

                    # Only apply override if agent already exists in config
                    if "agents" in config and agent_id in config["agents"]:
                        config["agents"][agent_id].setdefault("config", {})[
                            config_key
                        ] = value

        return config

    def _validate_config(self, raw_config: dict[str, Any]) -> AgentSystemConfig:
        """Validate raw configuration dictionary.

        Args:
            raw_config: Raw configuration dictionary

        Returns:
            Validated configuration object

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Handle nested configuration structure
            config_data = {}

            # Map YAML structure to Pydantic model
            if "global" in raw_config:
                config_data["global_config"] = raw_config["global"]

            if "discovery" in raw_config:
                config_data["discovery"] = raw_config["discovery"]

            if "agents" in raw_config:
                config_data["agents"] = raw_config["agents"]

            if "security" in raw_config:
                config_data["security"] = raw_config["security"]

            if "monitoring" in raw_config:
                config_data["monitoring"] = raw_config["monitoring"]

            return AgentSystemConfig(**config_data)

        except ValidationError as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise

    async def start_file_watcher(self) -> None:
        """Start watching configuration file for changes."""
        # This would implement file watching for hot reload
        # For now, it's a placeholder for future implementation
        logger.info("File watcher not implemented yet")

    def stop_file_watcher(self) -> None:
        """Stop watching configuration file."""
        if self._file_watcher_task:
            self._file_watcher_task.cancel()
            self._file_watcher_task = None


# Global configuration manager instance
config_manager = ConfigManager()
