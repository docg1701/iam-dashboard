# Llama-Index para Sistema RAG de Advocacia

Este guia foca na implementação do Llama-Index 0.12.x como orquestrador RAG para o sistema de agentes autônomos de advocacia, integrando PostgreSQL com pgvector, Gemini API e processamento de documentos legais.

## 1. Instalação para Sistema de Advocacia

```bash
# Instalação completa para integração com nosso stack
pip install llama-index==0.12.x
pip install llama-index-vector-stores-postgres  # pgvector integration
pip install llama-index-embeddings-google     # Gemini embeddings
pip install llama-index-llms-gemini          # Gemini LLM
pip install llama-index-readers-file         # PDF readers
```

## 2. Configuração RAG para Documentos Legais

### Configuração do Vector Store com pgvector

```python
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.embeddings.google import GoogleGenerativeAIEmbedding
from llama_index.llms.gemini import Gemini
import os

# Configurar componentes
embed_model = GoogleGenerativeAIEmbedding(
    model_name="models/text-embedding-004",
    api_key=os.getenv("GEMINI_API_KEY")
)

llm = Gemini(
    model="models/gemini-1.5-pro",
    api_key=os.getenv("GEMINI_API_KEY")
)

# Vector store conectado ao PostgreSQL
vector_store = PGVectorStore.from_params(
    database="advocacia_db",
    host="localhost",
    password="advocacia123",
    port=5432,
    user="postgres",
    table_name="document_chunks",
    embed_dim=768,
    # Configurações específicas para pgvector
    hnsw_kwargs={
        "hnsw_m": 16,
        "hnsw_ef_construction": 64,
        "hnsw_ef_search": 40,
    },
)

# Storage context para RAG
storage_context = StorageContext.from_defaults(vector_store=vector_store)
```

### Sistema de Ingestão de Documentos

```python
from llama_index.core import Document
from llama_index.readers.file import PyMuPDFReader
from typing import List, Dict

class LegalDocumentProcessor:
    """Processador de documentos legais para RAG"""
    
    def __init__(self, vector_store, embed_model, llm):
        self.vector_store = vector_store
        self.embed_model = embed_model
        self.llm = llm
        self.pdf_reader = PyMuPDFReader()
    
    async def ingest_legal_document(self, pdf_path: str, client_id: str, document_metadata: Dict) -> bool:
        """
        Ingere documento legal no sistema RAG
        Args:
            pdf_path: Caminho para o PDF
            client_id: ID do cliente (para isolamento)
            document_metadata: Metadados do documento
        """
        try:
            # 1. Extrair texto do PDF
            documents = self.pdf_reader.load_data(pdf_path)
            
            # 2. Adicionar metadados legais
            for doc in documents:
                doc.metadata.update({
                    'client_id': client_id,
                    'document_type': document_metadata.get('type', 'unknown'),
                    'upload_date': document_metadata.get('upload_date'),
                    'classification': document_metadata.get('classification', 'simple'),
                    'legal_context': self._identify_legal_context(doc.text)
                })
            
            # 3. Criar índice com chunking semântico
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=StorageContext.from_defaults(vector_store=self.vector_store),
                embed_model=self.embed_model,
                # Configurações de chunking para documentos legais
                chunk_size=1000,
                chunk_overlap=200,
                separator=" "
            )
            
            return True
            
        except Exception as e:
            print(f"Erro na ingestão: {str(e)}")
            return False
    
    def _identify_legal_context(self, text: str) -> str:
        """Identifica contexto legal do documento"""
        text_lower = text.lower()
        
        contexts = {
            'contract': ['contrato', 'acordo', 'cláusula', 'partes contratantes'],
            'petition': ['petição', 'requerimento', 'solicitação', 'excelentíssimo'],
            'judgment': ['sentença', 'decisão', 'julgamento', 'tribunal'],
            'opinion': ['parecer', 'opinião legal', 'análise jurídica'],
            'regulation': ['lei', 'decreto', 'portaria', 'regulamento']
        }
        
        for context, keywords in contexts.items():
            if any(keyword in text_lower for keyword in keywords):
                return context
        
        return 'general'
```

### Query Engine para Consultas Legais

```python
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor

class LegalRAGQueryEngine:
    """Engine de consultas RAG especializado em documentos legais"""
    
    def __init__(self, vector_store, embed_model, llm):
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embed_model
        )
        self.llm = llm
    
    def create_query_engine(self, client_id: str, similarity_threshold: float = 0.7):
        """Cria query engine com filtros por cliente"""
        
        # Retriever com filtros
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=10,
            # Filtro por cliente para isolamento de dados
            filters={'client_id': client_id}
        )
        
        # Post-processor para refinar resultados
        postprocessor = SimilarityPostprocessor(
            similarity_cutoff=similarity_threshold
        )
        
        # Query engine customizado para contexto legal
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=self.llm,
            node_postprocessors=[postprocessor],
            # Template personalizado para consultas legais
            text_qa_template=self._get_legal_qa_template()
        )
        
        return query_engine
    
    def _get_legal_qa_template(self):
        """Template customizado para respostas legais"""
        from llama_index.core import PromptTemplate
        
        template = """
        Você é um assistente jurídico especializado. Use os documentos fornecidos para responder à pergunta.
        
        INSTRUÇÕES:
        1. Base sua resposta APENAS nos documentos fornecidos
        2. Use linguagem jurídica apropriada
        3. Cite trechos relevantes dos documentos
        4. Se não houver informações suficientes, informe claramente
        5. Mantenha foco no contexto legal brasileiro
        
        DOCUMENTOS:
        {context_str}
        
        PERGUNTA: {query_str}
        
        RESPOSTA JURÍDICA:
        """
        
        return PromptTemplate(template)
    
    async def query_legal_documents(self, query: str, client_id: str) -> Dict:
        """
        Executa consulta nos documentos legais
        Args:
            query: Pergunta/consulta legal
            client_id: ID do cliente para isolamento
        Returns:
            Dict com resposta e documentos fonte
        """
        query_engine = self.create_query_engine(client_id)
        
        response = query_engine.query(query)
        
        return {
            'answer': str(response),
            'source_documents': [
                {
                    'text': node.text[:500] + "...",
                    'metadata': node.metadata,
                    'score': node.score
                }
                for node in response.source_nodes
            ],
            'confidence': self._calculate_confidence(response.source_nodes)
        }
    
    def _calculate_confidence(self, source_nodes) -> float:
        """Calcula confiança da resposta baseada nos scores dos nós"""
        if not source_nodes:
            return 0.0
        
        scores = [node.score for node in source_nodes if hasattr(node, 'score')]
        return sum(scores) / len(scores) if scores else 0.0

# Exemplo de uso completo
async def setup_legal_rag_system():
    """Configura sistema RAG completo para advocacia"""
    
    # Componentes base
    embed_model = GoogleGenerativeAIEmbedding(
        model_name="models/text-embedding-004",
        api_key=os.getenv("GEMINI_API_KEY")
    )
    
    llm = Gemini(
        model="models/gemini-1.5-pro",
        api_key=os.getenv("GEMINI_API_KEY")
    )
    
    vector_store = PGVectorStore.from_params(
        database="advocacia_db",
        host="localhost",
        password="advocacia123",
        port=5432,
        user="postgres",
        table_name="document_chunks",
        embed_dim=768
    )
    
    # Processador e query engine
    processor = LegalDocumentProcessor(vector_store, embed_model, llm)
    query_engine = LegalRAGQueryEngine(vector_store, embed_model, llm)
    
    return processor, query_engine

# Exemplo de consulta
async def example_legal_query():
    processor, query_engine = await setup_legal_rag_system()
    
    # Consulta legal
    result = await query_engine.query_legal_documents(
        query="Quais são as cláusulas de rescisão em contratos similares?",
        client_id="cliente-uuid-123"
    )
    
    print("Resposta:", result['answer'])
    print("Confiança:", result['confidence'])
    print("Documentos fonte:", len(result['source_documents']))
```


## 2. Conceitos Principais

- **Document**: Unidade de texto bruto com metadados.
- **Node**: Fragmento de `Document` usado em índices.
- **Embedding**: Representação vetorial de texto.
- **Index**: Estrutura de dados para recuperação (vetorial, árvore, gráfico).
- **Retriever / QueryEngine**: Módulos que consultam índices e retornam contexto.
- **ChatEngine**: Interface de chat multi-turno.
- **Agent / Workflow**: Componentes para orquestração de tarefas e ferramentas.


## 3. Leitores (Readers)

### 3.1 SimpleDirectoryReader

```python
from llama_index import SimpleDirectoryReader
reader = SimpleDirectoryReader("data/")
documents = reader.load_data()  # → List[Document]
```


### 3.2 PDFReader

```python
from llama_index.readers import PDFReader
reader = PDFReader()
docs = reader.load_data(file_path="docs/file.pdf")
```


## 4. Embeddings

### 4.1 HuggingFaceEmbedding

```python
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
embed = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
vectors = embed.embed_documents(["texto 1", "texto 2"])
```


### 4.2 Gemini Embedding

```python
from llama_index.embeddings.gemini import GeminiEmbedding
embed = GeminiEmbedding(model="gemini-embedding-model")
```


## 5. Índices (Indexes)

### 5.1 VectorStoreIndex

```python
from llama_index import VectorStoreIndex
index = VectorStoreIndex.from_documents(documents)
```

- `.as_query_engine()`: retorna um `QueryEngine`.
- `.as_chat_engine(chat_mode: str)`: retorna um `ChatEngine`.


### 5.2 TreeIndex

```python
from llama_index import TreeIndex
tree = TreeIndex.from_documents(documents)
```


### 5.3 KnowledgeGraphIndex

```python
from llama_index import KnowledgeGraphIndex
kg = KnowledgeGraphIndex.from_documents(documents)
```


## 6. Motores de Consulta

### 6.1 QueryEngine

```python
qe = index.as_query_engine()
response = qe.query("Qual a capital da França?")
```

- Parâmetros opcionais: `similarity_top_k`, `response_mode`, `logging`.


### 6.2 ChatEngine

```python
ce = index.as_chat_engine(chat_mode="condense_plus_context")
message = ce.chat("Me conte sobre Marie Curie.")
```

- `chat_mode`: `"plain"`, `"tree_summarize"`, `"condense_plus_context"`, etc.


## 7. Armazenamento (Storage)

```python
index.storage_context.persist(persist_dir="./storage")
# Carregar:
from llama_index import StorageContext, load_index_from_storage
ctx = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(ctx)
```


## 8. Agentes e Ferramentas

### 8.1 FunctionCallingAgent

```python
from llama_index.core.agent import FunctionCallingAgent
agent = FunctionCallingAgent.from_tools(
    tool_specs,  # List[ToolSpec]
    llm=llm_instance
)
response = agent.chat("Pesquise notícias sobre IA.")
```


### 8.2 ToolSpecs

- `GoogleSearchToolSpec`, `SupabaseVectorStoreSpec`, custom Python functions anotadas com `@tool`.


## 9. Workflows

```python
from llama_index.workflows import Workflow
wf = Workflow(
    nodes=[agent_node, processing_node, report_node],
    edges=[("agent_node", "processing_node"), ("processing_node", "report_node")]
)
wf.run(input_data)
```


## 10. Configurações Globais

```python
from llama_index import Settings
Settings.llm = GoogleGenAI(model="gemini-2.5-pro")
Settings.embed_model = HuggingFaceEmbedding("model-name")
Settings.chunk_size = 1024
```


## 11. Integrações Populares

- **LLMs**: OpenAI, Google GenAI (`llama_index.llms.openai`, `...google_genai`).
- **Vetores**: Chroma, Pinecone, Weaviate (`llama_index.vector_stores`).
- **Leitores**: CSV, JSON, HTML, SQL.
- **Ferramentas**: Google Search, Web Browser, Database query.


## Exemplo Rápido (5 linhas)

```python
from llama_index import SimpleDirectoryReader, VectorStoreIndex
docs = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(docs)
qe = index.as_query_engine()
print(qe.query("O que é Llama-Index?"))
```

Este guia atende à referência de programação para uso de **agentes Gemini** com **llama-index**, facilitando importações, classes principais, exemplos de uso e configuração.

<div style="text-align: center">⁂</div>

[^1_1]: https://github.com/run-llama/llama_index

[^1_2]: https://docs.linkup.so/pages/integrations/llama-index

[^1_3]: https://huggingface.co/llamaindex

[^1_4]: https://docs.llamaindex.ai/en/logan-llama_deploy_docs/api_reference/readers/readme/

[^1_5]: https://ai.google.dev/gemini-api/docs/llama-index

[^1_6]: https://llama-index.readthedocs.io/zh/stable/

[^1_7]: https://www.youtube.com/watch?v=A7EpJzaqtNc

[^1_8]: https://sdkdocs.zenml.io/0.44.2/integration_code_docs/integrations-llama_index/

[^1_9]: https://github.com/run-llama/llama_index/blob/main/docs/docs/getting_started/reading.md

[^1_10]: https://www.datacamp.com/tutorial/llama-index-adding-personal-data-to-llms

[^1_11]: https://docs.llamaindex.ai

[^1_12]: https://www.llamaindex.ai

[^1_13]: https://nvidia.github.io/GenerativeAIExamples/0.5.0/notebooks/04_llamaindex_hier_node_parser.html

[^1_14]: https://docs.llamaindex.ai/en/stable/api_reference/prompts/

[^1_15]: https://app.readthedocs.org/projects/llama-index/

[^1_16]: https://docs.databricks.com/gcp/pt/generative-ai/agent-framework/llamaindex-uc-integration

[^1_17]: https://ts.llamaindex.ai/docs/api

[^1_18]: https://mlflow.org/docs/latest/genai/flavors/llama-index/index.html

[^1_19]: https://sdkdocs.zenml.io/0.65.0/integration_code_docs/integrations-llama_index/

[^1_20]: https://llamahub.ai/l/readers/llama-index-readers-docstring-walker?from=

[^1_21]: https://docs.llamaindex.ai/en/stable/api_reference/

