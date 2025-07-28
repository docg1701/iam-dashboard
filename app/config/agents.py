"""Agent configuration management."""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_agent_config() -> dict[str, Any]:
    """Load agent configuration from YAML file.

    Returns:
        Dictionary containing agent configuration
    """
    try:
        config_path = Path(__file__).parent / "agents.yaml"

        if not config_path.exists():
            logger.error(f"Agent configuration file not found: {config_path}")
            return {}

        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)

        logger.info(f"Loaded agent configuration from: {config_path}")
        return config or {}

    except Exception as e:
        logger.error(f"Failed to load agent configuration: {str(e)}")
        return {}


def get_agent_config(agent_id: str) -> dict[str, Any]:
    """Get configuration for a specific agent.

    Args:
        agent_id: ID of the agent

    Returns:
        Dictionary containing agent configuration or empty dict if not found
    """
    try:
        config = load_agent_config()
        agents = config.get("agents", {})

        if agent_id in agents:
            return agents[agent_id]
        else:
            logger.warning(f"Configuration not found for agent: {agent_id}")
            return {}

    except Exception as e:
        logger.error(f"Failed to get agent configuration for {agent_id}: {str(e)}")
        return {}


def is_agent_enabled(agent_id: str) -> bool:
    """Check if an agent is enabled in configuration.

    Args:
        agent_id: ID of the agent

    Returns:
        True if agent is enabled, False otherwise
    """
    try:
        agent_config = get_agent_config(agent_id)
        return agent_config.get("enabled", False)

    except Exception as e:
        logger.error(f"Failed to check if agent {agent_id} is enabled: {str(e)}")
        return False


def get_global_config() -> dict[str, Any]:
    """Get global agent configuration settings.

    Returns:
        Dictionary containing global configuration
    """
    try:
        config = load_agent_config()
        return config.get("global", {})

    except Exception as e:
        logger.error(f"Failed to get global agent configuration: {str(e)}")
        return {}


def get_discovery_config() -> dict[str, Any]:
    """Get plugin discovery configuration.

    Returns:
        Dictionary containing discovery configuration
    """
    try:
        config = load_agent_config()
        return config.get("discovery", {})

    except Exception as e:
        logger.error(f"Failed to get discovery configuration: {str(e)}")
        return {}


def get_security_config() -> dict[str, Any]:
    """Get security configuration for agents.

    Returns:
        Dictionary containing security configuration
    """
    try:
        config = load_agent_config()
        return config.get("security", {})

    except Exception as e:
        logger.error(f"Failed to get security configuration: {str(e)}")
        return {}


def get_monitoring_config() -> dict[str, Any]:
    """Get monitoring configuration for agents.

    Returns:
        Dictionary containing monitoring configuration
    """
    try:
        config = load_agent_config()
        return config.get("monitoring", {})

    except Exception as e:
        logger.error(f"Failed to get monitoring configuration: {str(e)}")
        return {}
