"""Unit tests for template management tools."""

import uuid
from unittest.mock import mock_open, patch

import pytest

from app.models.client import Client
from app.tools.template_tools import TemplateManagerTool


class TestTemplateManagerTool:
    """Test suite for TemplateManagerTool."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        return Client(id=uuid.uuid4(), name="Ana Costa", cpf="11122233344")

    @pytest.fixture
    def template_tool(self):
        """Create TemplateManagerTool instance for testing."""
        return TemplateManagerTool()

    @pytest.fixture
    def template_tool_with_directory(self, tmp_path):
        """Create TemplateManagerTool with templates directory."""
        return TemplateManagerTool(templates_directory=str(tmp_path))

    def test_initialization_without_directory(self):
        """Test tool initialization without templates directory."""
        tool = TemplateManagerTool()

        assert tool.templates_directory is None
        assert "medical_examination" in tool._default_templates
        assert "occupational_disease" in tool._default_templates

    def test_initialization_with_directory(self, tmp_path):
        """Test tool initialization with templates directory."""
        tool = TemplateManagerTool(templates_directory=str(tmp_path))

        assert tool.templates_directory == tmp_path
        assert tool._default_templates is not None

    def test_get_questionnaire_template_default(self, template_tool):
        """Test getting default questionnaire template."""
        result = template_tool.get_questionnaire_template(
            template_type="medical_examination"
        )

        assert result["success"] is True
        assert result["source"] == "default"
        assert result["template_type"] == "medical_examination"
        assert "name" in result["template"]
        assert "required_sections" in result["template"]

    def test_get_questionnaire_template_occupational(self, template_tool):
        """Test getting occupational disease template."""
        result = template_tool.get_questionnaire_template(
            template_type="occupational_disease"
        )

        assert result["success"] is True
        assert result["template"]["name"] == "Occupational Disease Questionnaire"
        assert "HISTÓRICO OCUPACIONAL" in result["template"]["required_sections"]

    def test_get_questionnaire_template_unknown_type(self, template_tool):
        """Test getting unknown template type falls back to default."""
        result = template_tool.get_questionnaire_template(template_type="unknown_type")

        assert result["success"] is True
        assert result["template"]["name"] == "Medical Examination Questionnaire"

    def test_get_questionnaire_template_from_file(self, template_tool_with_directory):
        """Test loading template from file system."""
        # Create a mock template file
        template_data = {
            "name": "Custom Template",
            "description": "Custom template from file",
            "required_sections": ["CUSTOM_SECTION"],
        }

        template_tool_with_directory.templates_directory / "custom_template.json"

        with (
            patch("builtins.open", mock_open(read_data='{"name": "Custom Template"}')),
            patch("json.load", return_value=template_data),
        ):
            result = template_tool_with_directory.get_questionnaire_template(
                template_type="custom_template"
            )

            assert result["success"] is True
            assert result["source"] == "file_system"
            assert result["template"]["name"] == "Custom Template"

    def test_apply_template_formatting_success(self, template_tool, mock_client):
        """Test successful template formatting application."""
        questionnaire_text = "Raw questionnaire content"
        case_data = {
            "profession": "Advogada",
            "disease": "Síndrome do Pânico",
            "incident_date": "10/04/2023",
            "medical_date": "12/04/2023",
        }

        result = template_tool.apply_template_formatting(
            questionnaire_text=questionnaire_text,
            client=mock_client,
            case_data=case_data,
        )

        assert result["success"] is True
        assert "formatted_questionnaire" in result
        assert result["original_length"] == len(questionnaire_text)
        assert "template_applied" in result

    def test_apply_template_formatting_with_config(self, template_tool, mock_client):
        """Test template formatting with custom config."""
        questionnaire_text = "Content without header"
        case_data = {"profession": "Engineer", "disease": "RSI"}

        template_config = {
            "name": "custom_template",
            "header_template": "CUSTOM HEADER\n\n",
            "footer_template": "\n\nCUSTOM FOOTER",
            "formatting_rules": ["rule1", "rule2"],
        }

        result = template_tool.apply_template_formatting(
            questionnaire_text=questionnaire_text,
            client=mock_client,
            case_data=case_data,
            template_config=template_config,
        )

        assert result["success"] is True
        assert result["formatting_rules_applied"] == 2

    def test_apply_template_formatting_adds_header(self, template_tool, mock_client):
        """Test that formatting adds header to questionnaire without one."""
        questionnaire_text = "Simple questionnaire content"
        case_data = {"profession": "Teacher", "disease": "Stress"}

        result = template_tool.apply_template_formatting(
            questionnaire_text=questionnaire_text,
            client=mock_client,
            case_data=case_data,
        )

        formatted_text = result["formatted_questionnaire"]
        assert "QUESITOS PARA PERÍCIA MÉDICA" in formatted_text

    def test_apply_template_formatting_preserves_existing_header(
        self, template_tool, mock_client
    ):
        """Test that formatting preserves existing header."""
        questionnaire_text = "QUESITOS PARA PERÍCIA MÉDICA\n\nExisting content"
        case_data = {"profession": "Doctor", "disease": "Burnout"}

        result = template_tool.apply_template_formatting(
            questionnaire_text=questionnaire_text,
            client=mock_client,
            case_data=case_data,
        )

        formatted_text = result["formatted_questionnaire"]
        # Should not duplicate header
        header_count = formatted_text.count("QUESITOS PARA PERÍCIA MÉDICA")
        assert header_count == 1

    def test_apply_template_formatting_exception(self, template_tool, mock_client):
        """Test template formatting with exception."""
        with patch.object(
            template_tool,
            "_apply_header_formatting",
            side_effect=Exception("Format error"),
        ):
            result = template_tool.apply_template_formatting(
                questionnaire_text="test", client=mock_client, case_data={}
            )

            assert result["success"] is False
            assert "error" in result
            assert (
                result["formatted_questionnaire"] == "test"
            )  # Returns original on error

    def test_validate_questionnaire_format_success(self, template_tool):
        """Test successful questionnaire format validation."""
        questionnaire_text = """QUESITOS PARA PERÍCIA MÉDICA

DADOS DO EXAMINANDO:
Nome: Test

QUESITOS:

1. First question
2. Second question
3. Third question
4. Fourth question
5. Fifth question"""

        result = template_tool.validate_questionnaire_format(questionnaire_text)

        assert result["success"] is True
        assert result["validation_results"]["is_valid"] is True
        assert result["question_count"] >= 5

    def test_validate_questionnaire_format_missing_sections(self, template_tool):
        """Test validation with missing required sections."""
        questionnaire_text = "Just some text without proper sections"

        result = template_tool.validate_questionnaire_format(questionnaire_text)

        assert result["success"] is True
        assert result["validation_results"]["is_valid"] is False
        assert len(result["validation_results"]["errors"]) > 0

    def test_validate_questionnaire_format_insufficient_questions(self, template_tool):
        """Test validation with insufficient questions."""
        questionnaire_text = """QUESITOS PARA PERÍCIA MÉDICA

DADOS DO EXAMINANDO:
Nome: Test

QUESITOS:

1. Only one question"""

        result = template_tool.validate_questionnaire_format(questionnaire_text)

        assert result["success"] is True
        assert result["validation_results"]["is_valid"] is False
        assert any(
            "Insufficient questions" in error
            for error in result["validation_results"]["errors"]
        )

    def test_validate_questionnaire_format_with_custom_config(self, template_tool):
        """Test validation with custom template configuration."""
        questionnaire_text = """CUSTOM SECTION

QUESITOS:

1. Question one
2. Question two"""

        template_config = {
            "required_sections": ["CUSTOM SECTION"],
            "min_questions": 2,
            "required_legal_terms": ["legal_term"],
        }

        result = template_tool.validate_questionnaire_format(
            questionnaire_text, template_config
        )

        assert result["success"] is True
        assert result["validation_results"]["is_valid"] is True
        assert (
            len(result["validation_results"]["suggestions"]) > 0
        )  # Missing legal terms

    def test_validate_questionnaire_format_exception(self, template_tool):
        """Test validation with exception."""
        with patch.object(
            template_tool, "_count_questions", side_effect=Exception("Count error")
        ):
            result = template_tool.validate_questionnaire_format("test text")

            assert result["success"] is False
            assert "error" in result

    def test_validate_question_numbering_valid(self, template_tool):
        """Test question numbering validation with valid numbering."""
        text = """QUESITOS:

1. First question
2. Second question
3. Third question"""

        is_valid = template_tool._validate_question_numbering(text)
        assert is_valid is True

    def test_validate_question_numbering_invalid(self, template_tool):
        """Test question numbering validation with invalid numbering."""
        text = """QUESITOS:

1. First question
3. Third question (skipped 2)
4. Fourth question"""

        is_valid = template_tool._validate_question_numbering(text)
        assert is_valid is False

    def test_validate_question_numbering_no_questions(self, template_tool):
        """Test question numbering validation with no numbered questions."""
        text = "Just some text without numbered questions"

        is_valid = template_tool._validate_question_numbering(text)
        assert is_valid is False

    def test_count_questions(self, template_tool):
        """Test question counting functionality."""
        text = """Some preamble

1. First question
2. Second question
3. Third question

Some conclusion text

4. Fourth question"""

        count = template_tool._count_questions(text)
        assert count == 4

    def test_count_questions_no_questions(self, template_tool):
        """Test question counting with no questions."""
        text = "Text without any numbered questions"

        count = template_tool._count_questions(text)
        assert count == 0

    def test_load_default_templates_structure(self, template_tool):
        """Test that default templates have expected structure."""
        templates = template_tool._default_templates

        # Check medical examination template
        medical_template = templates["medical_examination"]
        assert "name" in medical_template
        assert "required_sections" in medical_template
        assert "min_questions" in medical_template
        assert "formatting_rules" in medical_template

        # Check occupational disease template
        occupational_template = templates["occupational_disease"]
        assert "name" in occupational_template
        assert "HISTÓRICO OCUPACIONAL" in occupational_template["required_sections"]

    def test_get_default_template_selection(self, template_tool):
        """Test default template selection logic."""
        # Test with known template type
        template = template_tool._get_default_template(
            "occupational_disease", None, None
        )
        assert template["name"] == "Occupational Disease Questionnaire"

        # Test with unknown template type (should fallback)
        template = template_tool._get_default_template("unknown", None, None)
        assert template["name"] == "Medical Examination Questionnaire"

    def test_load_template_from_file_not_exists(self, template_tool_with_directory):
        """Test loading template from non-existent file."""
        result = template_tool_with_directory._load_template_from_file(
            "nonexistent", None, None
        )

        assert result is None

    def test_load_template_from_file_json_error(self, template_tool_with_directory):
        """Test loading template with JSON parsing error."""
        template_file = template_tool_with_directory.templates_directory / "broken.json"
        template_file.write_text("invalid json content")

        result = template_tool_with_directory._load_template_from_file(
            "broken", None, None
        )

        assert result is None
