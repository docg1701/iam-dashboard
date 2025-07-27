# Celery para Sistema de Processamento de Documentos Legais

Este guia foca na implementação do Celery 5.5.3 para processamento assíncrono de documentos PDF no sistema de advocacia, cobrindo workers especializados, tasks de OCR e integração com Redis broker.

## 📦 Instalação

```bash
# Celery 5.5.3 com suporte Python 3.8-3.13
pip install celery==5.5.3
# Instalações opcionais para backends e brokers específicos:
pip install celery[redis]==5.5.3      # Redis como broker e/ou result backend
pip install celery[rabbitmq]==5.5.3   # RabbitMQ (AMQP)
pip install celery[s3]==5.5.3         # S3 como result backend
pip install celery[gcp]==5.5.3        # Google Cloud Pub/Sub (novo em 2025)
```


## 📝 Início Rápido

- **Introdução ao Celery**
Documentação: https://docs.celeryq.dev/en/stable/getting-started/introduction.html
Definição, conceitos de _broker_, _worker_ e _task_.
- **Primeiros Passos com Celery**
Documentação: https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html
Tutorial: escolher broker, criar tarefa, executar worker e chamar tarefas.


## ⚙️ Configuração

### User Guide: Configurações Gerais

https://docs.celeryq.dev/en/stable/userguide/configuration.html

- `broker_url`
- `result_backend`
- `task_serializer` / `result_serializer`
- `task_time_limit`, `task_soft_time_limit`
- `worker_concurrency`, `worker_prefetch_multiplier`


### Exemplo de `celeryconfig.py`

```python
broker_url = 'pyamqp://guest@localhost//'
result_backend = 'rpc://'  
task_annotations = {'tasks.add': {'rate_limit': '10/s'}}
```


## 🌐 API Reference

### Módulo Principal `celery.Celery`

https://docs.celeryq.dev/en/stable/reference/celery.html
Classe para instanciar a aplicação:

```python
from celery import Celery
app = Celery('proj', broker='pyamqp://guest@localhost//', backend='rpc://')
```


### Tarefas (Tasks)

- **Decorator e Classe Base**
`@app.task` / `celery.app.task.Task`
https://docs.celeryq.dev/en/stable/reference/celery.app.task.html
- **Assinaturas e Canvas**
`celery.canvas`: `chain`, `group`, `chord`, `map`
https://docs.celeryq.dev/en/stable/reference/celery.canvas.html


### Resultados (`AsyncResult`)

https://docs.celeryq.dev/en/stable/reference/celery.result.html

```python
res = my_task.delay(2, 3)
res.get(timeout=10)
res.status  # PENDING, SUCCESS, FAILURE
```


### Agendador de Tarefas (`Beat`)

- **Programação** via `crontab`, `schedule`
https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html


### CLI (`celery.bin.celery`)

https://docs.celeryq.dev/en/stable/reference/celery.bin.celery.html
Principais comandos:

- `celery -A proj worker`
- `celery -A proj beat`
- `celery -A proj status`


## 🔄 Brokers e Backends

| Tipo | Biblioteca | URL de Configuração |
| :-- | :-- | :-- |
| RabbitMQ (AMQP) | kombu (amqp) | `broker_url='amqp://guest@...'` |
| Redis | redis-py | `broker_url='redis://localhost'` |
| RPC | built-in | `result_backend='rpc://'` |
| Banco de Dados | SQLAlchemy/Django ORM | `result_backend='db+sqlite:///results.db'` |
| Amazon S3 | boto3 | Configurações `s3_*` |

## 🔧 Integrações com Frameworks

- **Flask**
https://flask.palletsprojects.com/en/stable/patterns/celery/
Padrões de criação de app Celery dentro de app Flask.
- **Django**
Real Python: https://realpython.com/asynchronous-tasks-with-django-and-celery/
Configuração em `settings.py` e integração via `django-celery-beat`, `django-celery-results`.


## 📚 Recursos Adicionais

- **User Guide Completo**
https://docs.celeryq.dev/en/stable/userguide/index.html
- **API Reference Completa**
https://docs.celeryq.dev/en/stable/reference/index.html
- **Canvas \& Workflows Complexos**
https://docs.celeryq.dev/en/stable/userguide/canvas.html
- **Monitoramento com Flower**
https://flower.readthedocs.io/

**Uso em Agentes LLM**: referencie diretamente as urls acima para obtenção de assinaturas de métodos, exemplos de payloads JSON e padrões de configuração, permitindo geração de código automatizado e correta formatação de chamadas Celery no contexto de prompts LLM.

<div style="text-align: center">⁂</div>

[^1_1]: https://docs.celeryq.dev/en/stable/

[^1_2]: https://docs.celeryq.dev/en/stable/reference/celery.html

[^1_3]: https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html

[^1_4]: https://celery-rabbitmq.readthedocs.io/en/latest/configuration.html

[^1_5]: https://docs.celeryproject.org/en/latest/reference/celery.result.html

[^1_6]: https://www.youtube.com/watch?v=VRHVEporra0\&vl=pt-BR

[^1_7]: https://docs.celeryq.dev/en/2.4-archived/configuration.html

[^1_8]: https://docs.celeryq.dev/en/stable/userguide/configuration.html

[^1_9]: http://docs.celeryproject.org/en/1.0-archived/getting-started/first-steps-with-celery.html

[^1_10]: https://stackoverflow.com/questions/53318596/where-should-i-put-the-celery-configuration-file

[^1_11]: https://docs.celeryproject.org/en/stable/reference/celery.app.task.html

[^1_12]: https://flask.palletsprojects.com/en/stable/patterns/celery/

[^1_13]: https://docs.celeryq.dev/en/2.0-archived/configuration.html

[^1_14]: https://docs.celeryq.dev/en/v5.5.1/reference/celery.bin.celery.html

[^1_15]: https://realpython.com/asynchronous-tasks-with-django-and-celery/

[^1_16]: https://airflow.apache.org/docs/apache-airflow-providers-celery/stable/configurations-ref.html

[^1_17]: https://github.com/celery/celery

[^1_18]: https://docs.celeryq.dev/en/latest/userguide/index.html

[^1_19]: https://docs.divio.com/how-to/configure-celery/

[^1_20]: https://docs.celeryq.dev/en/latest/getting-started/introduction.html

[^1_21]: https://docs.celeryq.dev/en/2.0-archived/tutorials/

[^1_22]: https://docs.celeryq.dev/en/stable/reference/index.html

[^1_23]: https://docs.celeryq.dev/en/stable/userguide/index.html


---

## Celery + FastAPI

### 1. Instalação e Dependências

Adicione ao seu `requirements.txt` e instale:

```text
fastapi==0.115.0
uvicorn[standard]==0.32.0
celery[redis]==5.5.3
redis==5.2.0
python-dotenv==1.0.1
```

```bash
pip install -r requirements.txt
```


### 2. Estrutura de Projeto

```
project/
├── app/
│   ├── main.py           # FastAPI
│   ├── celery_app.py     # Instância Celery
│   ├── tasks.py          # Definição de tasks
│   └── config.py         # Configurações (broker, backend)
├── .env                  # Variáveis de ambiente
└── requirements.txt
```


### 3. Configuração (`config.py`)

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    class Config:
        env_file = ".env"

settings = Settings()
```

`.env`:

```ini
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```


### 4. Instância Celery (`celery_app.py`)

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    __name__,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Auto-discover tasks em app.tasks
celery_app.autodiscover_tasks(["app.tasks"])
```


### 5. Definição de Tasks (`tasks.py`)

```python
from app.celery_app import celery_app

@celery_app.task(bind=True, name="tasks.add")
def add(self, x: int, y: int) -> int:
    return x + y
```


### 6. FastAPI: Endpoints de Tarefa (`main.py`)

```python
from fastapi import FastAPI, HTTPException
from app.tasks import add
from celery.result import AsyncResult

app = FastAPI()

@app.post("/tasks/add/")
async def run_add(x: int, y: int):
    task = add.delay(x, y)
    return {"task_id": task.id}

@app.get("/tasks/{task_id}/")
async def get_status(task_id: str):
    result = AsyncResult(task_id)
    status = result.status
    if status == "PENDING":
        return {"status": status}
    if status == "SUCCESS":
        return {"status": status, "result": result.result}
    if status == "FAILURE":
        return {"status": status, "error": str(result.result)}
    return {"status": status}
```


### 7. Execução

1. **FastAPI**

```bash
uvicorn app.main:app --reload
```

2. **Worker Celery**

```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

3. **Flower (monitoramento)**

```bash
celery -A app.celery_app.celery_app flower --port=5555
```


## Implementação para Sistema de Advocacia

### Tasks Específicas para Processamento de Documentos

```python
from app.celery_app import celery_app
from app.services.pdf_processor import PDFProcessor
from app.repositories.document_repository import DocumentRepository
from app.core.database import get_db_session
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_simple_pdf")
def process_simple_pdf(self, document_id: str, client_id: str, file_path: str) -> Dict:
    """
    Processa PDF simples (documentos digitais) sem OCR
    Args:
        document_id: ID único do documento
        client_id: ID do cliente para isolamento
        file_path: Caminho do arquivo PDF
    """
    try:
        # Atualizar status para processando
        with get_db_session() as session:
            doc_repo = DocumentRepository(session)
            doc_repo.update_processing_status(document_id, "processing")
        
        # Processar PDF com Gemini API
        processor = PDFProcessor()
        result = processor.extract_text_from_simple_pdf(file_path, client_id)
        
        with get_db_session() as session:
            doc_repo = DocumentRepository(session)
            # Salvar chunks no pgvector
            doc_repo.save_document_chunks(
                document_id=document_id,
                chunks=result['chunks'],
                embeddings=result['embeddings']
            )
            
            # Atualizar status para concluído
            doc_repo.update_processing_status(document_id, "completed")
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks_count": len(result['chunks']),
            "processing_time": result.get('processing_time', 0)
        }
        
    except Exception as exc:
        logger.error(f"Erro no processamento do PDF {document_id}: {str(exc)}")
        # Atualizar status para erro
        with get_db_session() as session:
            doc_repo = DocumentRepository(session)
            doc_repo.update_processing_status(document_id, "error", str(exc))
        
        # Retry com backoff exponencial
        raise self.retry(exc=exc, countdown=60, max_retries=3)

@celery_app.task(bind=True, name="process_complex_pdf")
def process_complex_pdf(self, document_id: str, client_id: str, file_path: str) -> Dict:
    """
    Processa PDF complexo (documentos escaneados) com OCR
    Args:
        document_id: ID único do documento
        client_id: ID do cliente para isolamento
        file_path: Caminho do arquivo PDF
    """
    try:
        with get_db_session() as session:
            doc_repo = DocumentRepository(session)
            doc_repo.update_processing_status(document_id, "processing_ocr")
        
        # Processar PDF com OCR + Gemini
        processor = PDFProcessor()
        result = processor.extract_text_with_ocr(file_path, client_id)
        
        with get_db_session() as session:
            doc_repo = DocumentRepository(session)
            # Salvar chunks processados
            doc_repo.save_document_chunks(
                document_id=document_id,
                chunks=result['chunks'],
                embeddings=result['embeddings']
            )
            
            doc_repo.update_processing_status(document_id, "completed")
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks_count": len(result['chunks']),
            "ocr_confidence": result.get('ocr_confidence', 0),
            "processing_time": result.get('processing_time', 0)
        }
        
    except Exception as exc:
        logger.error(f"Erro no processamento OCR do PDF {document_id}: {str(exc)}")
        with get_db_session() as session:
            doc_repo = DocumentRepository(session)
            doc_repo.update_processing_status(document_id, "error", str(exc))
        
        raise self.retry(exc=exc, countdown=120, max_retries=2)

@celery_app.task(bind=True, name="generate_legal_document")
def generate_legal_document(self, template_type: str, context_data: Dict, client_id: str) -> Dict:
    """
    Gera documento legal usando RAG e templates
    Args:
        template_type: Tipo do documento (petição, contrato, etc.)
        context_data: Dados do caso/cliente
        client_id: ID do cliente para busca RAG
    """
    try:
        from app.agents.legal_document_agent import LegalDocumentDraftingAgent
        
        agent = LegalDocumentDraftingAgent()
        result = agent.generate_document(
            template_type=template_type,
            context_data=context_data,
            client_id=client_id
        )
        
        return {
            "status": "success",
            "document_content": result['content'],
            "references_count": len(result.get('references', [])),
            "generation_time": result.get('generation_time', 0)
        }
        
    except Exception as exc:
        logger.error(f"Erro na geração de documento legal: {str(exc)}")
        raise self.retry(exc=exc, countdown=30, max_retries=2)
```

### Configuração Avançada para Sistema de Advocacia

```python
# app/workers/celery_config.py
from celery import Celery
from kombu import Queue
import os

def create_celery_app() -> Celery:
    """Cria e configura aplicação Celery para sistema de advocacia"""
    
    celery_app = Celery(
        'advocacia_workers',
        broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        backend=os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        include=['app.workers.tasks']
    )
    
    # Configurações específicas do Celery 5.5.3
    celery_app.conf.update(
        # Filas especializadas por tipo de processamento
        task_routes={
            'process_simple_pdf': {'queue': 'pdf_simple'},
            'process_complex_pdf': {'queue': 'pdf_complex'},
            'generate_legal_document': {'queue': 'document_generation'}
        },
        
        # Configurações de worker otimizadas para documentos
        worker_concurrency=4,
        worker_prefetch_multiplier=1,  # Evita sobrecarga de memória
        task_soft_time_limit=300,  # 5 minutos por task
        task_time_limit=600,       # 10 minutos timeout
        
        # Serialização segura
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        
        # Configurações de retry
        task_reject_on_worker_lost=True,
        task_acks_late=True,
        
        # Logging estruturado
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
        
        # Métricas e monitoramento
        worker_send_task_events=True,
        task_send_sent_event=True,
        
        # Configurações específicas para containerização
        worker_disable_rate_limits=True,
        worker_enable_remote_control=False,  # Segurança
        
        # Novos recursos do Celery 5.5.3
        worker_enable_soft_shutdown=True,    # Shutdown suave
        worker_soft_shutdown_timeout=30,     # Timeout para shutdown suave
    )
    
    # Definir filas especializadas
    celery_app.conf.task_default_queue = 'default'
    celery_app.conf.task_queues = (
        Queue('default', routing_key='default'),
        Queue('pdf_simple', routing_key='pdf.simple'),
        Queue('pdf_complex', routing_key='pdf.complex'),
        Queue('document_generation', routing_key='doc.generation'),
    )
    
    return celery_app

# Instância global
celery_app = create_celery_app()
```

### Monitoramento e Health Checks

```python
@celery_app.task(bind=True, name="health_check")
def health_check(self):
    """Task de health check para monitoramento"""
    from app.core.database import get_db_session
    
    try:
        # Verificar conexão com banco
        with get_db_session() as session:
            session.execute("SELECT 1").fetchone()
        
        # Verificar APIs externas
        import requests
        gemini_status = requests.get("https://generativelanguage.googleapis.com/v1/models", 
                                   timeout=5).status_code == 200
        
        return {
            "status": "healthy",
            "database": "ok",
            "gemini_api": "ok" if gemini_status else "error",
            "worker_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        return {
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
```

### Comandos de Deploy

```bash
# Iniciar workers especializados
celery -A app.workers.celery_app worker --queues=pdf_simple --concurrency=2 --loglevel=info
celery -A app.workers.celery_app worker --queues=pdf_complex --concurrency=1 --loglevel=info
celery -A app.workers.celery_app worker --queues=document_generation --concurrency=2 --loglevel=info

# Monitoramento com Flower
celery -A app.workers.celery_app flower --port=5555

# Beat scheduler para tasks periódicas
celery -A app.workers.celery_app beat --loglevel=info
```

Com este guia atualizado para Celery 5.5.3, o sistema de advocacia terá processamento assíncrono otimizado para documentos legais, com filas especializadas, retry inteligente e monitoramento completo.

<div style="text-align: center">⁂</div>

[^2_1]: https://testdriven.io/courses/fastapi-celery/getting-started/

[^2_2]: https://www.youtube.com/watch?v=eAHAKowv6hk

[^2_3]: https://github.com/testdrivenio/fastapi-celery

[^2_4]: https://www.fastapitutorial.com/blog/fastapi-celery-getting-started/

[^2_5]: https://www.youtube.com/watch?v=zjlq7Sn8h_g

[^2_6]: https://testdriven.io/blog/fastapi-and-celery/

[^2_7]: https://dev.to/derlin/fastapi-celery--33mh

[^2_8]: https://derlin.github.io/introduction-to-fastapi-and-celery/03-celery/

[^2_9]: https://derlin.github.io/introduction-to-fastapi-and-celery/02-fastapi/

