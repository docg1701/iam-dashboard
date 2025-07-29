"""LLM processing tools for content generation using Google Gemini API integration."""

import logging
from typing import Any

import google.generativeai as genai

from app.models.client import Client

logger = logging.getLogger(__name__)


class LLMProcessorTool:
    """Tool for generating content using Google Gemini API."""

    def __init__(self, model_name: str = "gemini-1.5-pro", api_key: str | None = None):
        """Initialize the LLM processor tool.

        Args:
            model_name: Gemini model to use for generation
            api_key: Gemini API key (if not provided, assumes already configured)
        """
        self.model_name = model_name

        if api_key:
            genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(model_name)

    def generate_questionnaire(
        self,
        client: Client,
        profession: str,
        disease: str,
        incident_date: str,
        medical_date: str,
        context_chunks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate questionnaire using Gemini API with retrieved context.

        Args:
            client: Client instance
            profession: Client's profession
            disease: Disease/condition
            incident_date: Date of incident
            medical_date: Date of first medical attention
            context_chunks: Retrieved document chunks with context

        Returns:
            Dictionary containing generated questionnaire and metadata
        """
        try:
            logger.info(f"Generating questionnaire for client {client.name}")

            # Prepare context text from chunks
            context_text = self._prepare_context_text(context_chunks)

            # Create detailed prompt for Gemini
            prompt = self._create_questionnaire_prompt(
                client, profession, disease, incident_date, medical_date, context_text
            )

            # Call Gemini API
            response = self.model.generate_content(prompt)

            if response and hasattr(response, "text"):
                generated_text = response.text

                result = {
                    "success": True,
                    "questionnaire": generated_text,
                    "context_chunks_used": len(context_chunks) if context_chunks else 0,
                    "model_used": self.model_name,
                    "client_name": client.name,
                    "has_context": bool(context_chunks),
                }

                logger.info(
                    f"Successfully generated questionnaire with {self.model_name}"
                )
                return result
            else:
                raise ValueError("Gemini API returned empty response")

        except Exception as e:
            error_msg = f"Error generating questionnaire with Gemini: {str(e)}"
            logger.error(error_msg)

            # Return fallback questionnaire
            fallback_text = self._generate_fallback_questionnaire(
                client, profession, disease, incident_date, medical_date
            )

            return {
                "success": True,  # Still successful, just using fallback
                "questionnaire": fallback_text,
                "context_chunks_used": 0,
                "model_used": "fallback",
                "client_name": client.name,
                "has_context": False,
                "fallback_used": True,
                "original_error": error_msg,
            }

    def generate_with_prompt(
        self, prompt: str, max_tokens: int | None = None, temperature: float = 0.7
    ) -> dict[str, Any]:
        """Generate content with a custom prompt.

        Args:
            prompt: Custom prompt for generation
            max_tokens: Maximum tokens to generate (if supported)
            temperature: Temperature for generation randomness

        Returns:
            Dictionary containing generated content and metadata
        """
        try:
            logger.info("Generating content with custom prompt")

            # Note: Gemini API doesn't directly support max_tokens or temperature
            # in the same way as OpenAI, but we can include them in the prompt if needed
            response = self.model.generate_content(prompt)

            if response and hasattr(response, "text"):
                result = {
                    "success": True,
                    "generated_text": response.text,
                    "model_used": self.model_name,
                    "prompt_length": len(prompt),
                }

                logger.info(f"Successfully generated content with {self.model_name}")
                return result
            else:
                raise ValueError("Gemini API returned empty response")

        except Exception as e:
            error_msg = f"Error generating content with custom prompt: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "generated_text": "",
                "model_used": self.model_name,
            }

    def _prepare_context_text(self, context_chunks: list[dict[str, Any]] | None) -> str:
        """Prepare context text from document chunks.

        Args:
            context_chunks: List of context chunks with text and metadata

        Returns:
            Formatted context text
        """
        if not context_chunks:
            return "Nenhum documento disponível para análise."

        # Extract text from chunks and combine
        context_texts = []
        for chunk in context_chunks:
            chunk_text = chunk.get("text", "")
            if chunk_text:
                # Add some metadata if available
                score = chunk.get("score", 0.0)

                # Format chunk with optional metadata
                formatted_chunk = chunk_text
                if score > 0:
                    formatted_chunk = f"[Relevância: {score:.2f}] {chunk_text}"

                context_texts.append(formatted_chunk)

        return "\n\n".join(context_texts)

    def _create_questionnaire_prompt(
        self,
        client: Client,
        profession: str,
        disease: str,
        incident_date: str,
        medical_date: str,
        context_text: str,
    ) -> str:
        """Create detailed prompt for questionnaire generation.

        Args:
            client: Client instance
            profession: Client's profession
            disease: Disease/condition
            incident_date: Date of incident
            medical_date: Date of first medical attention
            context_text: Prepared context from documents

        Returns:
            Formatted prompt for Gemini
        """
        return f"""
Você é um especialista em Direito do Trabalho e Previdenciário. Sua tarefa é gerar quesitos judiciais precisos e detalhados para um caso pericial médica.

DADOS DO CASO:
- Cliente: {client.name}
- CPF: {client.formatted_cpf}
- Profissão: {profession}
- Condição/Doença: {disease}
- Data do Incidente: {incident_date}
- Data do Primeiro Atendimento Médico: {medical_date}

DOCUMENTOS ANALISADOS:
{context_text}

INSTRUÇÕES:
1. Analise cuidadosamente os documentos fornecidos
2. Gere quesitos específicos e objetivos para perícia médica
3. Inclua quesitos sobre:
   - Diagnóstico e estado atual de saúde
   - Nexo causal com atividade profissional
   - Relação com o incidente relatado
   - Grau de incapacidade (parcial/total, temporária/permanente)
   - Necessidade de tratamentos futuros
   - Data de consolidação da lesão (se aplicável)
4. Use linguagem jurídica adequada
5. Numere os quesitos sequencialmente
6. Seja específico sobre as datas e fatos mencionados

FORMATO ESPERADO:
QUESITOS PARA PERÍCIA MÉDICA

[Dados do caso]

QUESITOS:

1. [Primeiro quesito]

2. [Segundo quesito]

[...continue...]

Gere os quesitos agora:
"""

    def _generate_fallback_questionnaire(
        self,
        client: Client,
        profession: str,
        disease: str,
        incident_date: str,
        medical_date: str,
    ) -> str:
        """Generate a basic questionnaire as fallback when Gemini fails.

        Args:
            client: Client instance
            profession: Client's profession
            disease: Disease/condition
            incident_date: Date of incident
            medical_date: Date of first medical attention

        Returns:
            Fallback questionnaire text
        """
        return f"""QUESITOS PARA PERÍCIA MÉDICA

DADOS DO EXAMINANDO:
Nome: {client.name}
CPF: {client.formatted_cpf}
Profissão: {profession}
Condição Relatada: {disease}
Data do Incidente: {incident_date}
Data do Primeiro Atendimento: {medical_date}

QUESITOS:

1. O examinando apresenta a condição denominada {disease}?

2. A condição apresentada pelo examinando tem relação com sua atividade profissional como {profession}?

3. Há evidências de que o incidente ocorrido em {incident_date} contribuiu para o desenvolvimento ou agravamento da condição?

4. O examinando apresenta incapacidade laboral em decorrência da condição diagnosticada?

5. Qual o grau de incapacidade apresentado pelo examinando (parcial ou total, temporária ou permanente)?

6. Há necessidade de tratamento contínuo ou reabilitação?

7. Considerando o primeiro atendimento médico em {medical_date}, qual a data estimada de consolidação da lesão?

8. O examinando apresenta sequelas permanentes decorrentes da condição?

[ATENÇÃO: Quesitos gerados em modo de segurança devido a falha na integração com IA]
"""
