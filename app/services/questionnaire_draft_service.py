"""Questionnaire Draft Service for RAG integration and Gemini generation."""

import logging
import uuid

import google.generativeai as genai
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import QueryBundle

from app.config.llama_index_config import get_llama_index_config
from app.models.client import Client
from app.repositories.document_chunk_repository import DocumentChunkRepository

logger = logging.getLogger(__name__)


class QuestionnaireDraftService:
    """Service for generating judicial questionnaire drafts using RAG + Gemini."""

    def __init__(self, chunk_repository: DocumentChunkRepository):
        """Initialize the questionnaire draft service."""
        self.chunk_repository = chunk_repository
        self.config = get_llama_index_config()
        self.config.setup_global_settings()

        # Initialize Gemini API
        genai.configure(api_key=self.config.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")

    async def generate_questionnaire(
        self,
        client: Client,
        profession: str,
        disease: str,
        incident_date: str,
        medical_date: str,
    ) -> dict[str, str]:
        """
        Generate judicial questionnaire using RAG + Gemini.

        Args:
            client: Client instance
            profession: Client's profession
            disease: Disease/condition
            incident_date: Date of incident
            medical_date: Date of first medical attention

        Returns:
            Dictionary with generated questionnaire and metadata
        """
        try:
            logger.info(f"Generating questionnaire for client {client.id}")

            # Step 1: Retrieve relevant context from client documents
            context = await self._retrieve_client_context(
                client.id, profession, disease, incident_date
            )

            # Step 2: Generate questionnaire using Gemini
            questionnaire = await self._generate_with_gemini(
                client, profession, disease, incident_date, medical_date, context
            )

            return {
                "success": True,
                "questionnaire": questionnaire,
                "context_chunks": len(context),
                "client_name": client.name,
            }

        except Exception as e:
            logger.error(f"Error generating questionnaire: {str(e)}")
            return {"success": False, "error": str(e), "questionnaire": ""}

    async def _retrieve_client_context(
        self, client_id: uuid.UUID, profession: str, disease: str, incident_date: str
    ) -> list[str]:
        """
        Retrieve relevant document chunks for the client using RAG.

        Args:
            client_id: Client UUID
            profession: Client's profession
            disease: Disease/condition
            incident_date: Date of incident

        Returns:
            List of relevant text chunks
        """
        try:
            # Get all chunks for this client
            chunks = await self.chunk_repository.get_chunks_by_client(client_id)

            if not chunks:
                logger.warning(f"No document chunks found for client {client_id}")
                return []

            # Create query combining the form data
            query_text = f"""
            Profissão: {profession}
            Condição médica: {disease}
            Data do incidente: {incident_date}

            Buscar informações sobre diagnósticos, tratamentos, incapacidade laboral,
            relação com atividade profissional e evidências médicas.
            """

            # Use vector store for similarity search
            vector_store = self.config.get_vector_store()
            index = VectorStoreIndex.from_vector_store(vector_store)

            # Create retriever with client filtering
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=10,  # Retrieve top 10 most relevant chunks
            )

            # Perform retrieval
            query_bundle = QueryBundle(query_text)
            retrieved_nodes = retriever.retrieve(query_bundle)

            # Filter nodes by client_id and extract text
            relevant_texts = []
            for node in retrieved_nodes:
                # Check if this chunk belongs to our client
                if hasattr(node, "metadata") and node.metadata.get("client_id") == str(
                    client_id
                ):
                    relevant_texts.append(node.text)
                elif hasattr(node, "node") and hasattr(node.node, "metadata"):
                    if node.node.metadata.get("client_id") == str(client_id):
                        relevant_texts.append(node.node.text)

            logger.info(
                f"Retrieved {len(relevant_texts)} relevant chunks for client {client_id}"
            )
            return relevant_texts

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []

    async def _generate_with_gemini(
        self,
        client: Client,
        profession: str,
        disease: str,
        incident_date: str,
        medical_date: str,
        context: list[str],
    ) -> str:
        """
        Generate questionnaire using Gemini API with retrieved context.

        Args:
            client: Client instance
            profession: Client's profession
            disease: Disease/condition
            incident_date: Date of incident
            medical_date: Date of first medical attention
            context: Retrieved document chunks

        Returns:
            Generated questionnaire text
        """
        try:
            # Prepare context text
            context_text = (
                "\n\n".join(context)
                if context
                else "Nenhum documento disponível para análise."
            )

            # Create detailed prompt for Gemini
            prompt = f"""
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

            # Call Gemini API
            response = self.model.generate_content(prompt)

            if response and hasattr(response, "text"):
                generated_text = response.text
                logger.info("Successfully generated questionnaire with Gemini")
                return generated_text
            else:
                raise ValueError("Gemini API returned empty response")

        except Exception as e:
            logger.error(f"Error generating with Gemini: {str(e)}")
            # Return fallback questionnaire
            return self._generate_fallback_questionnaire(
                client, profession, disease, incident_date, medical_date
            )

    def _generate_fallback_questionnaire(
        self,
        client: Client,
        profession: str,
        disease: str,
        incident_date: str,
        medical_date: str,
    ) -> str:
        """Generate a basic questionnaire as fallback when Gemini fails."""
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


def get_questionnaire_draft_service(
    chunk_repository: DocumentChunkRepository,
) -> QuestionnaireDraftService:
    """Factory function to get questionnaire draft service."""
    return QuestionnaireDraftService(chunk_repository)
