# Guia de Referência Completo para Implementação: Sistema de Processamento de Documentos PDF e Agentes Autônomos

**Para:** Agente de Geração de Código Sênior (LLM)

**De:** Arquiteto de Soluções de IA

**Assunto:** Planejamento e Arquitetura Detalhada de um Sistema de Ingestão e Consulta de Documentos com LLMs e Agentes Autônomos.

**Versão:** 2.0 (Expandida)




## 1. Filosofia e Princípios Fundamentais

Este documento delineia a arquitetura de um sistema robusto e escalável para processar documentos PDF e habilitar consultas em linguagem natural através de agentes autônomos. A arquitetura é fortemente inspirada nos padrões modulares do projeto Sparrow, mas foi reimaginada para um stack tecnológico moderno e focado, utilizando Python, Google Gemini 2.5 Pro e o framework Agno.

Os seguintes princípios são a espinha dorsal de todas as decisões de design e devem ser rigorosamente seguidos durante a implementação.

### 1.1. Modularidade e Desacoplamento

**O quê:** Cada responsabilidade funcional do sistema (serviço de API, processamento de tarefas, manipulação de arquivos, interação com LLM, armazenamento vetorial, lógica de agentes) será encapsulada em seu próprio módulo ou classe com interfaces claras e bem definidas.

**Por quê:** Este princípio é crucial para a manutenibilidade e evolução do sistema a longo prazo. Ele permite:

*   **Testabilidade:** Cada componente pode ser testado de forma isolada (testes unitários) mockando suas dependências.
*   **Evolução Independente:** Podemos, por exemplo, substituir o ChromaDB por um serviço gerenciado como Pinecone ou Weaviate simplesmente escrevendo um novo adaptador para a interface do banco de dados vetorial, sem alterar nenhuma outra parte do código. O mesmo se aplica à troca do modelo de LLM ou da biblioteca de manipulação de PDF.

### 1.2. Processamento Assíncrono por Design

**O quê:** O sistema utilizará um modelo de processamento assíncrono baseado em filas de tarefas para todas as operações de longa duração, principalmente a ingestão e o processamento de PDFs. A API principal nunca deve bloquear a thread de execução para esperar por uma tarefa pesada.

**Por quê:** A ingestão de um PDF de múltiplas páginas, envolvendo chamadas de rede para um LLM, é inerentemente lenta. Uma arquitetura síncrona resultaria em timeouts na API e uma péssima experiência do usuário. O modelo assíncrono com Celery e Redis oferece:

*   **Responsividade da API:** A API responde imediatamente com um `job_id`, confirmando que a tarefa foi enfileirada.
*   **Escalabilidade:** Podemos escalar o número de "workers" (processadores de tarefas) de forma independente do número de servidores de API para lidar com picos de carga.
*   **Resiliência:** Filas de tarefas podem ser configuradas com políticas de retentativa (retry) para lidar com falhas transitórias (ex: falha de rede ao chamar a API do Gemini).

### 1.3. API-First como Contrato

**O quê:** O sistema será projetado em torno de uma API RESTful bem definida. Esta API é o "contrato" entre o frontend (ou qualquer outro cliente) e o backend. O FastAPI será usado para gerar automaticamente uma documentação interativa (Swagger/OpenAPI) a partir do código.

**Por quê:** Uma abordagem API-First garante que a lógica do sistema seja agnóstica em relação à sua apresentação. Clientes diversos (uma aplicação web, um aplicativo móvel, outros serviços de backend, scripts de automação) podem consumir o sistema de forma consistente e previsível.

### 1.4. Estado e Persistência Claramente Definidos

**O quê:** O sistema gerenciará dois tipos distintos de estado: o estado do trabalho (Job State) e o estado do conhecimento (Knowledge State).

*   **Job State:** Informações sobre o andamento de uma tarefa de ingestão (ex: queued, processing, completed, failed). Será armazenado em um sistema rápido como o Redis.
*   **Knowledge State:** Os dados extraídos e processados dos documentos, armazenados de forma permanente e otimizada para busca no banco de dados vetorial.

**Por quê:** Separar esses estados evita a sobrecarga de um único sistema com responsabilidades diferentes e permite a escolha da tecnologia certa para cada tarefa.

### 1.5. Foco na Especialização (A Melhor Ferramenta para o Trabalho)

**O quê:** Em vez de adotar um framework monolítico que tenta resolver tudo, selecionaremos bibliotecas de ponta que são as melhores em suas respectivas áreas.

**Por quê:** Essa abordagem "best-of-breed" nos dá mais poder e flexibilidade. O FastAPI é inigualável para APIs em Python. O PyMuPDF é o padrão-ouro em performance para manipulação de PDFs. O Agno é projetado especificamente para o ciclo de vida de agentes autônomos, um problema complexo que merece uma ferramenta dedicada. Isso evita as limitações de frameworks genéricos.




## 2. Arquitetura de Alto Nível Detalhada

O sistema é logicamente dividido em duas camadas principais que operam de forma independente, mas conectada.

### A. Pipeline de Ingestão de Documentos

Esta camada é responsável por todo o ciclo de vida de um documento, desde o upload até sua transformação em conhecimento pesquisável.

```
                                      +-------------------------+
                                      |   Cliente (e.g., Web UI)  |
                                      +-------------------------+
                                                  |
                                (1. POST /v1/documents com PDF)
                                                  |
                                                  v
+--------------------------------------------------------------------------------------------------+
| API Gateway (FastAPI)                                                                            |
|   - Recebe o arquivo PDF                                                                         |
|   - Valida o tipo e tamanho do arquivo                                                           |
|   - Gera um job_id único (UUID)                                                                  |
|   - Salva o PDF em armazenamento temporário                                                      |
|   - (2. Enfileira Tarefa) -> Retorna (3. job_id, HTTP 202)                                        |
+--------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+--------------------------------------------------------------------------------------------------+
| Fila de Tarefas (Celery + Redis)                                                                 |
|   - Armazena a tarefa {job_id, temp_path} de forma persistente                                     |
+--------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+--------------------------------------------------------------------------------------------------+
| Worker de Ingestão (Processo Celery)                                                             |
|   - (4. Pega a tarefa da fila)                                                                   |
|   - **(4a) PDF Processor (PyMuPDF):** Divide o PDF em páginas (texto/imagem)                       |
|   - Loop por cada página:                                                                        |
|     - **(4b) LLM Processor (Gemini 2.5 Pro):** Envia a página para o LLM                           |
|       e recebe de volta um embedding vetorial e/ou um resumo textual.                            |
|     - **(4c) Vector DB Storage (ChromaDB):** Armazena o vetor e os metadados da página.            |
|   - (5. Atualiza status final do job) -> Limpa arquivo temporário                                |
+--------------------------------------------------------------------------------------------------+
```

### B. Camada de Agentes de Consulta

Esta camada fornece a interface inteligente para que os usuários possam "conversar" com a base de conhecimento criada pela primeira camada.

```
                                      +-------------------------+
                                      |   Cliente (e.g., Web UI)  |
                                      +-------------------------+
                                                  |
                                    (1. POST /v1/query com pergunta)
                                                  |
                                                  v
+--------------------------------------------------------------------------------------------------+
| API Gateway (FastAPI)                                                                            |
|   - Recebe a pergunta em linguagem natural.                                                      |
|   - (2. Delega a pergunta para o motor de agentes) -> Retorna (7. Resposta final)                |
+--------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+--------------------------------------------------------------------------------------------------+
| Motor de Agentes (Agno)                                                                          |
|   - **(3. Raciocínio Inicial - LLM):** O agente principal (pilotado pelo Gemini) analisa a pergunta |
|     e decide qual "Skill" (habilidade) usar. Ele determina que precisa buscar na base de dados.    |
|   - **(4. Execução da Skill):** Invoca a `VectorDBSearchSkill` com a pergunta.                    |
|                                                 |                                                |
|   +---------------------------------------------+                                                |
|   | VectorDBSearchSkill                         |                                                |
|   |   - (4a. Converte a pergunta em vetor)        |                                                |
|   |   - (4b. Consulta o Vector DB) -> Retorna (4c. Contexto relevante)                             |
|   +---------------------------------------------+                                                |
|                                                 |                                                |
|   - **(5. Raciocínio de Síntese - LLM):** O agente recebe o contexto relevante da skill.          |
|   - **(6. Geração Final - LLM):** O agente envia um prompt final para o Gemini contendo a         |
|     pergunta original e o contexto recuperado, solicitando uma resposta abrangente.              |
|     -> Retorna a resposta sintetizada para a API.                                                |
+--------------------------------------------------------------------------------------------------+
```




## 3. Stack Tecnológico Detalhado

| Componente | Tecnologia Sugerida | Justificativa Detalhada | Considerações de Implementação | Licença |
|---|---|---|---|---|
| Servidor API | FastAPI | Além do desempenho e da documentação automática, o FastAPI integra-se nativamente com o Pydantic para validação robusta de dados de entrada e saída, e seu sistema de injeção de dependências (Depends) simplifica o gerenciamento de recursos como conexões de banco de dados. | Utilize os lifespan events para inicializar recursos (como o cliente Agno) na inicialização e encerrá-los graciosamente no desligamento. | MIT |
| Fila de Tarefas | Celery | Padrão da indústria, altamente configurável, com suporte para retentativas, roteamento complexo de tarefas e monitoramento (via Flower). Permite escalar a camada de processamento de forma independente. | Configure filas separadas para diferentes prioridades de tarefas no futuro (ex: high_priority_ingestion, low_priority_analytics). Implemente um tratamento robusto de exceções dentro das tarefas. | BSD-3-Clause |
| Message Broker | Redis | Além de ser um broker para o Celery, o Redis pode ser usado como um banco de dados chave-valor de baixa latência para armazenar o estado dos jobs de ingestão, servindo como uma solução de cache ou para implementar rate limiting. | Utilize instâncias Redis separadas para o broker Celery e para o armazenamento de dados de aplicação para evitar contenção de recursos. | BSD-3-Clause |
| Manipulação de PDF | PyMuPDF (fitz) | Performance é o fator decisivo. O PyMuPDF é escrito em C e é significativamente mais rápido que alternativas em Python puro para extrair texto, imagens e metadados, reduzindo o tempo de processamento por página. | Atenção à licença AGPL-3.0. Para mitigar o impacto, encapsule toda a lógica de manipulação de PDF em um módulo bem isolado (core.pdf_processor). A recomendação é não modificar o código-fonte do PyMuPDF. | AGPL-3.0 |
| Modelo de Linguagem | Google Gemini 2.5 Pro | É um modelo multimodal de fronteira, capaz de entender não apenas o texto, mas também o layout, tabelas e imagens dentro de uma página de PDF. Essencial para extrair o contexto correto de documentos complexos. | O módulo core.llm_processor deve implementar lógica de retentativa com backoff exponencial para lidar com erros transitórios da API. Monitore os custos de API de perto. | Comercial |
| SDK do LLM | LangChain e Llama-Index | LangChain será utilizado para orquestrar as interações com os LLMs, fornecendo uma interface unificada para diferentes modelos e funcionalidades como cadeias de prompts e agentes. O Llama-Index será empregado para a gestão e recuperação de dados externos, otimizando a forma como os LLMs interagem com a base de conhecimento vetorial no PostgreSQL. | A integração com o Gemini 2.5 Pro será feita através dos módulos de integração do LangChain e Llama-Index. Será necessário configurar os embeddings e os modelos de linguagem dentro desses frameworks. | Apache-2.0 / MIT |
| Banco de Dados Vetorial | PostgreSQL (com pgvector) | O PostgreSQL com a extensão pgvector oferece uma solução robusta e escalável para armazenamento e busca vetorial, permitindo a persistência dos embeddings junto com outros dados relacionais. É ideal para ambientes de produção que exigem alta disponibilidade, backup e recuperação, e integração com o ecossistema de banco de dados existente. | Configure o PostgreSQL com a extensão `pgvector`. A classe `core.vector_db` deve ser adaptada para interagir com o PostgreSQL, utilizando um ORM como SQLAlchemy ou um cliente direto como `psycopg2` para gerenciar as conexões e operações de inserção/consulta. | PostgreSQL License (BSD-like) / pgvector (MIT) |
| Framework de Agentes | Agno | Projetado especificamente para o paradigma de agentes autônomos. Sua estrutura baseada em "Skills" é muito mais intuitiva e escalável para adicionar novas capacidades ao agente (ex: buscar na web, acessar outra API) do que frameworks mais genéricos. | Modele as "Skills" para serem atômicas e reutilizáveis. Uma skill não deve conter lógica de negócios complexa; ela deve ser uma ferramenta que o agente (LLM) aprende a usar. | MIT |




## 4. Detalhamento Extensivo dos Componentes

### Componente 1: API Gateway (FastAPI)

O `api/main.py` será o ponto de entrada. A estrutura de injeção de dependências será usada para fornecer serviços (como o cliente do agente) aos endpoints.

`api/models.py` - Modelos de Dados Pydantic:

```python
from pydantic import BaseModel, Field
from typing import Literal

class DocumentUploadResponse(BaseModel):
    job_id: str = Field(..., description="O ID único para o trabalho de ingestão do documento.")
    status: Literal["queued"] = Field("queued", description="O status inicial do trabalho.")

class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    details: str | None = None

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=10, description="A pergunta em linguagem natural a ser enviada ao agente.")
    session_id: str | None = Field(None, description="ID de sessão opcional para manter o histórico da conversa.")

class QueryResponse(BaseModel):
    answer: str
    source_documents: list[dict] | None = None # Metadados dos documentos fonte
```

`api/main.py` - Snippet de Endpoints:

```python
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from .models import DocumentUploadResponse, QueryRequest, QueryResponse
from workers.ingestion_worker import process_pdf_task
from agents.query_agent import get_query_agent # Função que retorna a instância do agente
from agno.agent import Agent
import uuid

app = FastAPI(title="Sistema de Documentos com Agentes de IA", version="1.0.0")

@app.post("/v1/documents", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Tipo de arquivo inválido. Apenas PDFs são aceitos.")

    job_id = str(uuid.uuid4())
    # Lógica para salvar o arquivo em um diretório temporário
    temp_file_path = f"/tmp/{job_id}_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Adiciona a tarefa pesada para ser executada em segundo plano
    background_tasks.add_task(process_pdf_task, job_id, temp_file_path)

    return DocumentUploadResponse(job_id=job_id, status="queued")

@app.post("/v1/query", response_model=QueryResponse)
async def query_agent_endpoint(request: QueryRequest, agent: Agent = Depends(get_query_agent)):
    # A injeção de dependência garante que temos a instância correta do agente
    if not request.query:
        raise HTTPException(status_code=400, detail="A query não pode ser vazia.")
    
    # A lógica de chat do Agno lida com o fluxo de raciocínio e execução
    response_text = await agent.chat(request.query)
    
    # Extrair fontes, se a resposta do agente as incluir
    # ...

    return QueryResponse(answer=response_text)
```

### Componente 2: Pipeline de Ingestão (Workers Celery)

`workers/celery_app.py` - Configuração:

```python
from celery import Celery
import os

# Use variáveis de ambiente para configuração
redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ingestion_tasks",
    broker=redis_url,
    backend=redis_url,
    include=["workers.ingestion_worker"] # Onde encontrar as tarefas
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer=\'json\',
    result_serializer=\'json\',
    accept_content=[\'json\'],
)
```

`workers/ingestion_worker.py` - Lógica da Tarefa Expandida:

```python
from .celery_app import celery_app
from core.pdf_processor import PDFProcessor
from core.llm_processor import LLMProcessor
from core.vector_db import PGVectorDBClient

# Instanciar os clientes fora da tarefa para reutilização, se possível
pdf_processor = PDFProcessor()
llm_processor = LLMProcessor()
vector_db = PGVectorDBClient()
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_pdf_task(self, job_id: str, pdf_path: str):
    logger.info(f"Iniciando processamento do job {job_id} para o arquivo {pdf_path}")
    
    # Lógica para atualizar o status do job para "processing"
    # ...
    
    try:
        pages_content = pdf_processor.split_pdf_to_pages(pdf_path)
        logger.info(f"Job {job_id}: PDF dividido em {len(pages_content)} páginas.")

        all_vectors = []
        all_metadata = []

        for i, page_text in enumerate(pages_content):
            page_num = i + 1
            logger.info(f"Job {job_id}: Processando página {page_num}...")
            
            # Gerar o vetor e o conteúdo para armazenamento
            # O LLM pode ser usado para resumir ou apenas para gerar o embedding do texto completo
            processed_data = llm_processor.embed_text(page_text)
            
            # Preparar dados para inserção em lote (mais eficiente)
            vector_id = f"{job_id}_{page_num}"
            metadata = {
                "source_file": pdf_path,
                "page_number": page_num,
                "original_text_preview": page_text[:200] # Salvar um preview
            }
            all_vectors.append((vector_id, processed_data[\'vector\'], metadata))

        # Inserção em lote no banco de dados vetorial
        if all_vectors:
            vector_db.store_batch(all_vectors)
            logger.info(f"Job {job_id}: {len(all_vectors)} vetores armazenados com sucesso.")

        # Lógica para atualizar o status do job para "completed"
        # ...

    except Exception as e:
        logger.error(f"Erro ao processar o job {job_id}: {e}", exc_info=True)
        # Lógica para atualizar o status do job para "failed" com a mensagem de erro
        # ...
        # A lógica de retentativa do Celery será acionada aqui
        raise self.retry(exc=e)
    
    finally:
        # Lógica para limpar o arquivo temporário
        # ...
        pass
```

### Componente 3: Camada de Agentes Autônomos (Agno)

A beleza do Agno está em sua simplicidade para definir capacidades complexas.

`agents/skills/vector_db_skill.py` - Definição da Skill:

```python
from agno.skill import Skill
from core.vector_db import PGVectorDBClient # Nossa classe de cliente de DB
from core.llm_processor import LLMProcessor # Para gerar embedding da query

class VectorDBSearchSkill(Skill):
    def __init__(self, db_client: PGVectorDBClient, llm_processor: LLMProcessor):
        super().__init__(
            name="knowledge_base_search",
            description=(
                "Busca na base de conhecimento interna de documentos para encontrar trechos de texto "
                "relevantes para responder à pergunta de um usuário. Use esta skill quando a pergunta "
                "for sobre o conteúdo de documentos previamente carregados."
            )
        )
        self.db_client = db_client
        self.llm_processor = llm_processor

    def execute(self, query: str) -> str:
        """
        Executa a busca vetorial e retorna o contexto formatado.
        """
        print(f"Executando a skill de busca com a query: \'{query}\'")
        
        # 1. Converter a pergunta do usuário em um vetor
        query_vector = self.llm_processor.embed_text(query)[\'vector\']
        
        # 2. Realizar a busca no banco de dados vetorial
        search_results = self.db_client.query_by_vector(query_vector, n_results=5)
        
        # 3. Formatar os resultados em uma string de contexto claro para o LLM
        if not search_results:
            return "Nenhuma informação relevante foi encontrada na base de conhecimento."
        
        context_str = "Contexto recuperado da base de conhecimento:\n\n"
        for i, result in enumerate(search_results):
            context_str += f"--- Trecho {i+1} (da página {result[\'metadata\'][\'page_number\']} do arquivo {result[\'metadata\'][\'source_file\']}) ---\n"
            context_str += result[\'text_preview\'] # Usar o preview do texto
            context_str += "\n\n"
            
        return context_str
```

`agents/query_agent.py` - Construção do Agente:

```python
from agno.agent import Agent
from .skills.vector_db_skill import VectorDBSearchSkill
from core.vector_db import PGVectorDBClient
from core.llm_processor import LLMProcessor
import os

def create_document_agent() -> Agent:
    # Instanciar as dependências necessárias
    db_client = PGVectorDBClient()
    llm_processor = LLMProcessor(api_key=os.getenv("GOOGLE_API_KEY"))

    # Instanciar a skill com suas dependências
    search_skill = VectorDBSearchSkill(db_client=db_client, llm_processor=llm_processor)

    # Definir a persona e o prompt do sistema para o agente
    system_prompt = (
        "Você é o \'Documentis\', um assistente de IA especialista em análise de documentos. "
        "Sua função é responder às perguntas dos usuários com base estritamente nas informações "
        "contidas em uma base de conhecimento de documentos PDF. "
        "Seu processo de raciocínio é: "
        "1. Analise a pergunta do usuário. "
        "2. Se a resposta provavelmente está nos documentos, use a skill \'knowledge_base_search\' para encontrar o contexto relevante. "
        "3. Analise o contexto retornado pela skill. "
        "4. Formule uma resposta final abrangente e clara para o usuário, citando a fonte (página e arquivo) se possível. "
        "5. Se a skill não retornar informações relevantes, informe educadamente ao usuário que a resposta não foi encontrada nos documentos."
    )
    
    # Criar e retornar a instância do agente Agno
    agent = Agent(
        name="DocumentExpertAgent",
        persona=system_prompt,
        skills=[search_skill],
        llm_client=llm_processor.get_agno_compatible_client() # Wrapper para o cliente Gemini
    )
    return agent

# Singleton para a instância do agente
_agent_instance = None

def get_query_agent() -> Agent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = create_document_agent()
    return _agent_instance
```




## 5. Fluxos de Trabalho Revisitados com Detalhes Adicionais

### A. Fluxo de Ingestão de um PDF:

1.  **Requisição:** Cliente envia `POST /v1/documents` com `arquivo.pdf`.
2.  **Validação na API:** FastAPI valida se `Content-Type` é `application/pdf`. Se não, retorna `400`.
3.  **Criação do Job:** Um UUID v4 é gerado (`job_id`). O PDF é lido em memória (`await file.read()`) e salvo em um disco compartilhado ou armazenamento de objetos (ex: S3) com o nome `job_id.pdf`.
4.  **Enfileiramento:** Uma tarefa é enviada para a fila "ingestion" do Celery: `process_pdf_task.delay(job_id)`. A API retorna `{"job_id": "...", "status": "queued"}`.
5.  **Execução do Worker:**
    *   Um worker Celery pega a tarefa.
    *   Ele atualiza o status do job no Redis: `redis.set(f"job_status:{job_id}", "processing")`.
    *   O worker abre o arquivo `job_id.pdf` usando PyMuPDF.
    *   Ele itera sobre cada `page` do documento. `page.get_text("text")` extrai o conteúdo.
    *   Para cada texto da página, ele chama o `llm_processor.embed_text(...)` (que internamente usará LangChain/Llama-Index) para obter um vetor de embedding.
    *   Ele prepara uma lista de tuplas `(id, vector, metadata)`. O `id` é `f"{job_id}_{page.number}"`.
    *   Após o loop, ele faz uma chamada única `vector_db.store_batch(all_vectors)` para inserir os dados no PostgreSQL.
    *   Se tudo for bem-sucedido, atualiza o status no Redis para `completed`.
    *   Em caso de exceção, atualiza para `failed` com a mensagem de erro. A política de retentativa do Celery pode ser acionada.
    *   Finalmente, deleta o arquivo `job_id.pdf` do armazenamento temporário.

### B. Fluxo de Consulta do Agente:

1.  **Requisição:** Cliente envia `POST /v1/query` com `{"query": "Qual foi o lucro líquido no relatório do Q4?"}`.
2.  **Delegação ao Agente:** A API FastAPI chama `await agent.chat(...)`.
3.  **Ciclo de Raciocínio-Ação do Agno:**
    *   **Pensamento 1 (LLM):** "O usuário está perguntando sobre 'lucro líquido' e 'relatório Q4'. Essa informação deve estar nos documentos. Vou usar a skill `knowledge_base_search`."
    *   **Ação 1:** O Agno chama `knowledge_base_search.execute(query="lucro líquido no relatório do Q4")`.
    *   **Execução da Skill:** A skill converte a query em um vetor, busca no PostgreSQL (com pgvector), encontra 3 trechos relevantes de um arquivo chamado `relatorio_anual.pdf` e os formata em uma única string de contexto.
    *   **Observação 1:** O Agno recebe o contexto relevante da skill.



