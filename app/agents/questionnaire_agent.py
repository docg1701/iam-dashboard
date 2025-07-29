"""Questionnaire Agent for autonomous legal questionnaire generation."""

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from agno.agent import Agent
from agno.models.google import Gemini

from app.agents.base_agent import AgentPlugin
from app.core.database import get_async_db
from app.models.client import Client
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.tools.llm_tools import LLMProcessorTool
from app.tools.rag_tools import RAGRetrieverTool
from app.tools.template_tools import TemplateManagerTool

logger = logging.getLogger(__name__)


class QuestionnaireAgent(Agent):
    """Autonomous agent for legal questionnaire generation with RAG retrieval and LLM integration."""

    def __init__(
        self,
        model: str = "gemini-1.5-pro",
        instructions: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Questionnaire Agent.

        Args:
            model: The LLM model to use for questionnaire generation
            instructions: Custom instructions for the agent
            **kwargs: Additional agent configuration
        """
        default_instructions = """You are a legal questionnaire generation agent specialized in:
        1. Generating judicial questionnaires for medical examinations
        2. Using RAG retrieval to find relevant client document context
        3. Applying legal templates and formatting requirements
        4. Ensuring questionnaires meet legal quality standards

        Always provide detailed logging for questionnaire generation operations.
        Ensure legal compliance and professional formatting.
        Generate questionnaires that are specific, objective, and legally sound.
        """

        # Extract tool-specific config before passing to parent
        tool_config = {
            "gemini_api_key": kwargs.pop("gemini_api_key", None),
            "similarity_top_k": kwargs.pop("similarity_top_k", 10),
            "templates_directory": kwargs.pop("templates_directory", None),
            "min_context_chunks": kwargs.pop("min_context_chunks", 1),
            "max_context_chunks": kwargs.pop("max_context_chunks", 15),
        }

        # Convert model string to Gemini model object
        model_instance = Gemini(id=model) if isinstance(model, str) else model

        super().__init__(
            model=model_instance,
            instructions=instructions or default_instructions,
            **kwargs,
        )

        # Initialize tools
        self.rag_retriever = RAGRetrieverTool()
        self.llm_processor = LLMProcessorTool(
            model_name=model, api_key=tool_config["gemini_api_key"]
        )
        self.template_manager = TemplateManagerTool(
            templates_directory=tool_config["templates_directory"]
        )

        # Configuration
        self.similarity_top_k = tool_config["similarity_top_k"]
        self.min_context_chunks = tool_config["min_context_chunks"]
        self.max_context_chunks = tool_config["max_context_chunks"]

        # Note: Workflow methods are not tools - they are called directly
        # Tools are initialized as separate objects (rag_retriever, llm_processor, template_manager)

        logger.info(f"Initialized QuestionnaireAgent with model: {model}")

    async def retrieve_client_context(
        self, client_id: str, profession: str, disease: str, incident_date: str
    ) -> dict[str, Any]:
        """Retrieve relevant document context for questionnaire generation.

        Args:
            client_id: Client UUID as string
            profession: Client's profession
            disease: Disease or condition
            incident_date: Date of incident

        Returns:
            Dictionary containing retrieved context and metadata
        """
        try:
            client_uuid = uuid.UUID(client_id)

            # Set up repository for RAG retrieval
            async for db in get_async_db():
                chunk_repository = DocumentChunkRepository(db)
                self.rag_retriever.chunk_repository = chunk_repository

                # Retrieve context using RAG
                context_result = self.rag_retriever.retrieve_client_context(
                    client_id=client_uuid,
                    profession=profession,
                    disease=disease,
                    incident_date=incident_date,
                    similarity_top_k=self.similarity_top_k,
                )

                if context_result["success"]:
                    # Filter to reasonable number of chunks
                    context_chunks = context_result["context_chunks"]
                    if len(context_chunks) > self.max_context_chunks:
                        # Keep top chunks by score
                        context_chunks = sorted(
                            context_chunks,
                            key=lambda x: x.get("score", 0.0),
                            reverse=True,
                        )[: self.max_context_chunks]
                        context_result["context_chunks"] = context_chunks
                        context_result["total_chunks"] = len(context_chunks)

                    logger.info(
                        f"Retrieved {len(context_chunks)} context chunks for client {client_id}"
                    )
                    return context_result
                else:
                    return context_result

            # Fallback in case no database session is available
            return {
                "success": False,
                "error": "No database session available",
                "context_chunks": [],
                "total_chunks": 0,
                "client_id": client_id,
            }

        except Exception as e:
            error_msg = f"Failed to retrieve context for client {client_id}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "context_chunks": [],
                "total_chunks": 0,
                "client_id": client_id,
            }

    def generate_questionnaire_content(
        self,
        client_data: dict[str, Any],
        case_data: dict[str, Any],
        context_chunks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate questionnaire content using LLM with retrieved context.

        Args:
            client_data: Client information dictionary
            case_data: Case-specific data (profession, disease, dates)
            context_chunks: Retrieved document chunks

        Returns:
            Dictionary containing generated questionnaire content
        """
        try:
            # Create Client object for LLM tool
            client = Client(
                id=uuid.UUID(client_data["id"]),
                name=client_data["name"],
                cpf=client_data["cpf"],
            )

            # Generate questionnaire using LLM processor
            generation_result = self.llm_processor.generate_questionnaire(
                client=client,
                profession=case_data["profession"],
                disease=case_data["disease"],
                incident_date=case_data["incident_date"],
                medical_date=case_data["medical_date"],
                context_chunks=context_chunks,
            )

            if generation_result["success"]:
                logger.info(f"Generated questionnaire for client {client.name}")
                return generation_result
            else:
                return generation_result

        except Exception as e:
            error_msg = f"Failed to generate questionnaire content: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "questionnaire": "",
                "model_used": "error",
            }

    def apply_legal_formatting(
        self,
        questionnaire_text: str,
        client_data: dict[str, Any],
        case_data: dict[str, Any],
        template_type: str = "medical_examination",
    ) -> dict[str, Any]:
        """Apply legal formatting and template structure to questionnaire.

        Args:
            questionnaire_text: Raw questionnaire text
            client_data: Client information
            case_data: Case-specific data
            template_type: Type of template to apply

        Returns:
            Dictionary containing formatted questionnaire
        """
        try:
            # Create Client object for template tool
            client = Client(
                id=uuid.UUID(client_data["id"]),
                name=client_data["name"],
                cpf=client_data["cpf"],
            )

            # Get template configuration
            template_result = self.template_manager.get_questionnaire_template(
                template_type=template_type,
                profession=case_data.get("profession"),
                disease_category=case_data.get("disease"),
            )

            if not template_result["success"]:
                logger.warning(
                    f"Failed to get template: {template_result.get('error')}"
                )
                # Continue without template
                template_config = None
            else:
                template_config = template_result["template"]

            # Apply formatting
            formatting_result = self.template_manager.apply_template_formatting(
                questionnaire_text=questionnaire_text,
                client=client,
                case_data=case_data,
                template_config=template_config,
            )

            if formatting_result["success"]:
                logger.info("Applied legal formatting to questionnaire")
                return formatting_result
            else:
                return formatting_result

        except Exception as e:
            error_msg = f"Failed to apply legal formatting: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "formatted_questionnaire": questionnaire_text,  # Return original
                "template_applied": "none",
            }

    def validate_questionnaire(
        self, questionnaire_text: str, template_type: str = "medical_examination"
    ) -> dict[str, Any]:
        """Validate questionnaire format and content quality.

        Args:
            questionnaire_text: Questionnaire text to validate
            template_type: Template type for validation rules

        Returns:
            Dictionary containing validation results
        """
        try:
            # Get template for validation rules
            template_result = self.template_manager.get_questionnaire_template(
                template_type=template_type
            )

            template_config = (
                None if not template_result["success"] else template_result["template"]
            )

            # Validate format
            validation_result = self.template_manager.validate_questionnaire_format(
                questionnaire_text=questionnaire_text, template_config=template_config
            )

            if validation_result["success"]:
                logger.info(
                    f"Questionnaire validation completed: {validation_result['validation_results']['is_valid']}"
                )
                return validation_result
            else:
                return validation_result

        except Exception as e:
            error_msg = f"Failed to validate questionnaire: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "validation_results": {"is_valid": False, "errors": [error_msg]},
            }

    async def save_questionnaire_draft(
        self,
        questionnaire_text: str,
        client_id: str,
        case_data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Save questionnaire draft to database.

        Args:
            questionnaire_text: Generated questionnaire text
            client_id: Client UUID as string
            case_data: Case-specific data
            metadata: Additional metadata to store

        Returns:
            Dictionary containing save results
        """
        try:
            from app.models.questionnaire_draft import QuestionnaireDraft

            async for db in get_async_db():
                # Create questionnaire draft record
                draft = QuestionnaireDraft(
                    client_id=uuid.UUID(client_id),
                    content=questionnaire_text,
                    profession=case_data.get("profession", ""),
                    disease=case_data.get("disease", ""),
                    incident_date=case_data.get("incident_date", ""),
                    medical_date=case_data.get("medical_date", ""),
                    metadata_=json.dumps(metadata or {}),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )

                db.add(draft)
                await db.commit()
                await db.refresh(draft)

                result = {
                    "success": True,
                    "draft_id": draft.id,
                    "client_id": client_id,
                    "text_length": len(questionnaire_text),
                    "created_at": draft.created_at.isoformat(),
                }

                logger.info(f"Saved questionnaire draft with ID: {draft.id}")
                return result

            # Fallback in case no database session is available
            return {
                "success": False,
                "error": "No database session available",
                "draft_id": None,
            }

        except Exception as e:
            error_msg = f"Failed to save questionnaire draft: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "draft_id": None}

    async def generate_questionnaire(
        self,
        client: Client,
        profession: str,
        disease: str,
        incident_date: str,
        medical_date: str,
        save_draft: bool = True,
    ) -> dict[str, Any]:
        """Main workflow for generating a legal questionnaire.

        Args:
            client: Client instance
            profession: Client's profession
            disease: Disease or condition
            incident_date: Date of incident
            medical_date: Date of first medical attention
            save_draft: Whether to save the draft to database

        Returns:
            Dictionary containing complete generation results
        """
        logger.info(
            f"Starting questionnaire generation workflow for client: {client.name}"
        )

        try:
            # Step 1: Retrieve relevant context
            context_result = await self.retrieve_client_context(
                client_id=str(client.id),
                profession=profession,
                disease=disease,
                incident_date=incident_date,
            )

            if not context_result["success"]:
                logger.warning(
                    f"Context retrieval failed: {context_result.get('error')}"
                )
                context_chunks = []
            else:
                context_chunks = context_result["context_chunks"]

            # Step 2: Generate questionnaire content
            client_data = {"id": str(client.id), "name": client.name, "cpf": client.cpf}
            case_data = {
                "profession": profession,
                "disease": disease,
                "incident_date": incident_date,
                "medical_date": medical_date,
            }

            generation_result = self.generate_questionnaire_content(
                client_data=client_data,
                case_data=case_data,
                context_chunks=context_chunks,
            )

            if not generation_result["success"]:
                return generation_result

            questionnaire_text = generation_result["questionnaire"]

            # Step 3: Apply legal formatting
            formatting_result = self.apply_legal_formatting(
                questionnaire_text=questionnaire_text,
                client_data=client_data,
                case_data=case_data,
            )

            if formatting_result["success"]:
                questionnaire_text = formatting_result["formatted_questionnaire"]

            # Step 4: Validate questionnaire
            validation_result = self.validate_questionnaire(questionnaire_text)
            is_valid = validation_result.get("validation_results", {}).get(
                "is_valid", True
            )

            # Step 5: Save draft if requested
            draft_id = None
            if save_draft:
                save_result = await self.save_questionnaire_draft(
                    questionnaire_text=questionnaire_text,
                    client_id=str(client.id),
                    case_data=case_data,
                    metadata={
                        "context_chunks_used": len(context_chunks),
                        "model_used": generation_result.get("model_used"),
                        "template_applied": formatting_result.get(
                            "template_applied", "none"
                        ),
                        "validation_passed": is_valid,
                        "generation_timestamp": datetime.now(UTC).isoformat(),
                        "agent_version": "1.0.0",
                    },
                )

                if save_result["success"]:
                    draft_id = save_result["draft_id"]

            # Compile final result
            final_result = {
                "success": True,
                "questionnaire": questionnaire_text,
                "context_chunks": len(context_chunks),
                "client_name": client.name,
                "processing_summary": {
                    "context_retrieved": context_result["success"],
                    "content_generated": generation_result["success"],
                    "formatting_applied": formatting_result.get("success", False),
                    "validation_passed": is_valid,
                    "draft_saved": draft_id is not None,
                    "draft_id": draft_id,
                    "model_used": generation_result.get("model_used"),
                    "fallback_used": generation_result.get("fallback_used", False),
                },
            }

            logger.info(f"Questionnaire generation completed for client: {client.name}")
            return final_result

        except Exception as e:
            error_msg = (
                f"Questionnaire generation workflow failed for {client.name}: {str(e)}"
            )
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "questionnaire": "",
                "context_chunks": 0,
                "client_name": client.name,
            }


class QuestionnairePlugin(AgentPlugin):
    """Plugin wrapper for QuestionnaireAgent."""

    PLUGIN_NAME = "QuestionnairePlugin"
    VERSION = "1.0.0"
    DEPENDENCIES: list[str] = []

    def __init__(self, agent_id: str, config: dict[str, Any]):
        super().__init__(agent_id, config)
        self._agent_instance: QuestionnaireAgent | None = None

    async def initialize(self) -> bool:
        """Initialize the questionnaire agent."""
        try:
            model = self.config.get("model", "gemini-1.5-pro")
            instructions = self.config.get("instructions")

            # Remove conflicting keys from config
            agent_config = {
                k: v
                for k, v in self.config.items()
                if k not in ["name", "description", "model", "instructions"]
            }

            self._agent_instance = QuestionnaireAgent(
                model=model,
                instructions=instructions,
                name=self.name,
                description=self.description,
                **agent_config,
            )

            self._initialized = True
            logger.info(f"Initialized QuestionnairePlugin: {self.agent_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to initialize QuestionnairePlugin {self.agent_id}: {str(e)}"
            )
            return False

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process questionnaire generation through the agent."""
        if not self._initialized or not self._agent_instance:
            return {"success": False, "error": "Agent not initialized"}

        try:
            # Extract required parameters
            client_data = data.get("client")
            profession = data.get("profession")
            disease = data.get("disease")
            incident_date = data.get("incident_date")
            medical_date = data.get("medical_date")
            save_draft = data.get("save_draft", True)

            if not all([client_data, profession, disease, incident_date, medical_date]):
                return {
                    "success": False,
                    "error": "Missing required parameters: client, profession, disease, incident_date, medical_date",
                }

            # Validate client_data structure
            if not isinstance(client_data, dict) or not all(
                key in client_data for key in ["id", "name", "cpf"]
            ):
                return {
                    "success": False,
                    "error": "Invalid client data structure",
                }

            # Create Client object
            client = Client(
                id=uuid.UUID(str(client_data["id"])),
                name=str(client_data["name"]),
                cpf=str(client_data["cpf"]),
            )

            # Process questionnaire generation
            result = await self._agent_instance.generate_questionnaire(
                client=client,
                profession=str(profession),
                disease=str(disease),
                incident_date=str(incident_date),
                medical_date=str(medical_date),
                save_draft=save_draft,
            )

            return result

        except Exception as e:
            error_msg = f"Processing failed in QuestionnairePlugin: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def health_check(self) -> bool:
        """Perform health check on the questionnaire agent."""
        if not self._initialized or not self._agent_instance:
            return False

        try:
            # Simple health check - verify agent tools are available
            return hasattr(self._agent_instance, "generate_questionnaire_content")
        except Exception:
            return False

    def get_capabilities(self) -> list[str]:
        """Get the capabilities of the questionnaire agent."""
        return [
            "questionnaire_generation",
            "rag_document_retrieval",
            "legal_template_formatting",
            "content_validation",
            "draft_management",
        ]
