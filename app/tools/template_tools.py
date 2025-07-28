"""Template management tools for accessing and applying questionnaire templates."""

import json
import logging
from pathlib import Path
from typing import Any

from app.models.client import Client

logger = logging.getLogger(__name__)


class TemplateManagerTool:
    """Tool for managing questionnaire templates and legal formatting requirements."""

    def __init__(self, templates_directory: str | None = None):
        """Initialize the template manager tool.

        Args:
            templates_directory: Directory containing questionnaire templates
        """
        self.templates_directory = Path(templates_directory) if templates_directory else None
        self._default_templates = self._load_default_templates()

    def get_questionnaire_template(
        self,
        template_type: str = "medical_examination",
        profession: str | None = None,
        disease_category: str | None = None
    ) -> dict[str, Any]:
        """Get questionnaire template based on case characteristics.

        Args:
            template_type: Type of questionnaire template
            profession: Client's profession for template selection
            disease_category: Disease category for specialized templates

        Returns:
            Dictionary containing template structure and formatting
        """
        try:
            logger.info(f"Retrieving template: {template_type}")

            # Try to load from file system first
            if self.templates_directory:
                template = self._load_template_from_file(template_type, profession, disease_category)
                if template:
                    return {
                        "success": True,
                        "template": template,
                        "source": "file_system",
                        "template_type": template_type
                    }

            # Fall back to default templates
            template = self._get_default_template(template_type, profession, disease_category)

            return {
                "success": True,
                "template": template,
                "source": "default",
                "template_type": template_type
            }

        except Exception as e:
            error_msg = f"Error retrieving template {template_type}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "template": {},
                "template_type": template_type
            }

    def apply_template_formatting(
        self,
        questionnaire_text: str,
        client: Client,
        case_data: dict[str, Any],
        template_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Apply template formatting to generated questionnaire text.

        Args:
            questionnaire_text: Raw questionnaire text
            client: Client information
            case_data: Case-specific data
            template_config: Template configuration and formatting rules

        Returns:
            Dictionary containing formatted questionnaire
        """
        try:
            logger.info(f"Applying template formatting for client {client.name}")

            # Use default template config if none provided
            if not template_config:
                template_config = self._get_default_template(
                    "medical_examination",
                    case_data.get("profession"),
                    case_data.get("disease")
                )

            # Apply header formatting
            formatted_text = self._apply_header_formatting(
                questionnaire_text, client, case_data, template_config
            )

            # Apply section formatting
            formatted_text = self._apply_section_formatting(
                formatted_text, template_config
            )

            # Apply footer formatting
            formatted_text = self._apply_footer_formatting(
                formatted_text, template_config
            )

            # Apply legal compliance formatting
            formatted_text = self._apply_legal_formatting(
                formatted_text, template_config
            )

            result = {
                "success": True,
                "formatted_questionnaire": formatted_text,
                "original_length": len(questionnaire_text),
                "formatted_length": len(formatted_text),
                "template_applied": template_config.get("name", "default"),
                "formatting_rules_applied": len(template_config.get("formatting_rules", []))
            }

            logger.info("Successfully applied template formatting")
            return result

        except Exception as e:
            error_msg = f"Error applying template formatting: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "formatted_questionnaire": questionnaire_text,  # Return original on error
                "original_length": len(questionnaire_text),
                "template_applied": "none"
            }

    def validate_questionnaire_format(
        self,
        questionnaire_text: str,
        template_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Validate questionnaire format against template requirements.

        Args:
            questionnaire_text: Questionnaire text to validate
            template_config: Template configuration with validation rules

        Returns:
            Dictionary containing validation results
        """
        try:
            logger.info("Validating questionnaire format")

            # Use default template config if none provided
            if not template_config:
                template_config = self._get_default_template("medical_examination", None, None)

            validation_results = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }

            # Check required sections
            required_sections = template_config.get("required_sections", [])
            for section in required_sections:
                if section.lower() not in questionnaire_text.lower():
                    validation_results["errors"].append(f"Missing required section: {section}")
                    validation_results["is_valid"] = False

            # Check question numbering
            if not self._validate_question_numbering(questionnaire_text):
                validation_results["warnings"].append("Question numbering may be inconsistent")

            # Check minimum question count
            min_questions = template_config.get("min_questions", 5)
            question_count = self._count_questions(questionnaire_text)
            if question_count < min_questions:
                validation_results["errors"].append(
                    f"Insufficient questions: {question_count} (minimum: {min_questions})"
                )
                validation_results["is_valid"] = False

            # Check legal language requirements
            legal_terms = template_config.get("required_legal_terms", [])
            missing_terms: list[str] = []
            for term in legal_terms:
                if term.lower() not in questionnaire_text.lower():
                    missing_terms.append(term)

            if missing_terms:
                validation_results["suggestions"].append(
                    f"Consider including legal terms: {', '.join(missing_terms)}"
                )

            result = {
                "success": True,
                "validation_results": validation_results,
                "question_count": question_count,
                "text_length": len(questionnaire_text),
                "template_used": template_config.get("name", "default")
            }

            logger.info(f"Validation completed: {'PASSED' if validation_results['is_valid'] else 'FAILED'}")
            return result

        except Exception as e:
            error_msg = f"Error validating questionnaire format: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "validation_results": {"is_valid": False, "errors": [error_msg]}
            }

    def _load_default_templates(self) -> dict[str, Any]:
        """Load default questionnaire templates."""
        return {
            "medical_examination": {
                "name": "Medical Examination Questionnaire",
                "description": "Standard template for medical examination questionnaires",
                "required_sections": [
                    "DADOS DO EXAMINANDO",
                    "QUESITOS"
                ],
                "min_questions": 5,
                "max_questions": 20,
                "required_legal_terms": [
                    "perícia médica",
                    "incapacidade laboral",
                    "nexo causal"
                ],
                "formatting_rules": [
                    "numbered_questions",
                    "legal_header",
                    "client_data_section",
                    "professional_language"
                ],
                "header_template": "QUESITOS PARA PERÍCIA MÉDICA\n\n",
                "footer_template": "",
                "sections": {
                    "client_data": {
                        "title": "DADOS DO EXAMINANDO:",
                        "required_fields": ["Nome", "CPF", "Profissão"]
                    },
                    "questions": {
                        "title": "QUESITOS:",
                        "format": "numbered_list"
                    }
                }
            },
            "occupational_disease": {
                "name": "Occupational Disease Questionnaire",
                "description": "Specialized template for occupational disease cases",
                "required_sections": [
                    "DADOS DO EXAMINANDO",
                    "HISTÓRICO OCUPACIONAL",
                    "QUESITOS"
                ],
                "min_questions": 8,
                "max_questions": 25,
                "required_legal_terms": [
                    "doença ocupacional",
                    "atividade profissional",
                    "agente causador"
                ],
                "formatting_rules": [
                    "numbered_questions",
                    "legal_header",
                    "occupational_history",
                    "exposure_analysis"
                ]
            }
        }

    def _load_template_from_file(
        self,
        template_type: str,
        profession: str | None,
        disease_category: str | None
    ) -> dict[str, Any] | None:
        """Load template from file system."""
        if not self.templates_directory or not self.templates_directory.exists():
            return None

        # Try specific template file first
        template_file = self.templates_directory / f"{template_type}.json"
        if not template_file.exists():
            return None

        try:
            with open(template_file, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load template from file {template_file}: {str(e)}")
            return None

    def _get_default_template(
        self,
        template_type: str,
        profession: str | None,
        disease_category: str | None
    ) -> dict[str, Any]:
        """Get default template based on case characteristics."""
        # Simple template selection logic
        if template_type in self._default_templates:
            return self._default_templates[template_type]

        # Default to medical examination template
        return self._default_templates["medical_examination"]

    def _apply_header_formatting(
        self,
        text: str,
        client: Client,
        case_data: dict[str, Any],
        template_config: dict[str, Any]
    ) -> str:
        """Apply header formatting to questionnaire."""
        header_template = template_config.get("header_template", "")

        # If text already has proper header, return as is
        if text.strip().startswith("QUESITOS PARA PERÍCIA MÉDICA"):
            return text

        # Add header if missing
        return header_template + text

    def _apply_section_formatting(self, text: str, template_config: dict[str, Any]) -> str:
        """Apply section formatting to questionnaire."""
        # This would implement section formatting logic
        # For now, return text as is
        return text

    def _apply_footer_formatting(self, text: str, template_config: dict[str, Any]) -> str:
        """Apply footer formatting to questionnaire."""
        footer_template = template_config.get("footer_template", "")
        if footer_template:
            return text + "\n\n" + footer_template
        return text

    def _apply_legal_formatting(self, text: str, template_config: dict[str, Any]) -> str:
        """Apply legal compliance formatting."""
        # This would implement legal formatting requirements
        # For now, return text as is
        return text

    def _validate_question_numbering(self, text: str) -> bool:
        """Validate that questions are properly numbered."""
        import re

        # Look for numbered questions pattern
        numbered_questions = re.findall(r'^\d+\.', text, re.MULTILINE)

        if not numbered_questions:
            return False

        # Check if numbering is sequential
        expected_number = 1
        for match in numbered_questions:
            number = int(match.replace('.', ''))
            if number != expected_number:
                return False
            expected_number += 1

        return True

    def _count_questions(self, text: str) -> int:
        """Count the number of questions in the questionnaire."""
        import re

        # Count numbered questions
        numbered_questions = re.findall(r'^\d+\.', text, re.MULTILINE)
        return len(numbered_questions)

