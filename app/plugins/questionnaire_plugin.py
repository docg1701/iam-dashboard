"""Plugin registration for QuestionnaireAgent."""

import logging

from app.agents.base_agent import plugin_registry
from app.agents.questionnaire_agent import QuestionnairePlugin

logger = logging.getLogger(__name__)


def register_questionnaire_plugin() -> None:
    """Register the QuestionnairePlugin with the agent registry."""
    try:
        plugin_registry.register_plugin(QuestionnairePlugin)
        logger.info("Successfully registered QuestionnairePlugin")
    except Exception as e:
        logger.error(f"Failed to register QuestionnairePlugin: {str(e)}")


# Auto-register when module is imported
register_questionnaire_plugin()
