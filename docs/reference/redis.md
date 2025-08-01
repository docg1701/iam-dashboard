# Redis-py Complete Reference for Legal Document Processing Systems

This guide provides comprehensive coverage for Redis integration in legal advocacy systems:

- **Installation** and **connection** with Redis using `redis-py`
- **Integration** with FastAPI, NiceGUI and Celery for legal document processing
- **Production configuration** for legal document queues and processing workflows
- **Security and reliability** considerations for legal systems
- **Performance optimization** for document processing workloads


## 1. Installation for Legal Document Processing

```bash
# Core Redis components for legal systems
pip install redis[hiredis]>=5.0.0  # Redis-py with C parser for performance
pip install celery[redis]>=5.3.0   # Celery with Redis broker support
pip install fastapi>=0.104.1       # Modern async web framework
pip install nicegui>=2.21.0         # UI framework integration

# Additional dependencies for legal document processing
pip install redis-py-cluster        # For Redis cluster support
pip install redis-sentinel          # For high availability
```

**Important for Legal Systems:**
- `hiredis` provides significant performance improvements for document processing workloads
- Use virtual environments (venv, Poetry, Pipenv) to ensure dependency isolation
- Consider Redis Sentinel or ElastiCache for production legal systems requiring high availability


## 2. Redis Connection for Legal Document Systems

### Basic Connection with Security Considerations

```python
import redis
from redis.sentinel import Sentinel
import ssl

# Production connection with security features
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,  # Return strings instead of bytes
    ssl=True,               # Enable SSL/TLS for legal data
    ssl_cert_reqs=ssl.CERT_REQUIRED,
    ssl_ca_certs='/path/to/ca.pem',
    ssl_certfile='/path/to/client.crt',
    ssl_keyfile='/path/to/client.key',
    password='secure_password',  # Use environment variables
    socket_keepalive=True,
    socket_keepalive_options={},
    health_check_interval=30
)

# Verify connection health
try:
    r.ping()
    print("Redis connection established successfully")
except redis.ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")
```


### Exemplos Avançados

- **Cluster**

```python
from redis.cluster import RedisCluster
rc = RedisCluster(host='localhost', port=7000, decode_responses=True)
```

- **TLS/ACL**

```python
r = Redis(
    host="meu-redis.redislabs.com", port=6379,
    username="default", password="senha",
    ssl=True, ssl_certfile="user.crt",
    ssl_keyfile="user.key", ssl_ca_certs="ca.pem",
    decode_responses=True
)
```


## 3. Legal Document Processing Architecture

### 3.1 System Structure for Legal Applications

```
sistema-advocacia-saas/
│
├── app/
│   ├── main.py              # NiceGUI application entry point
│   ├── api/                 # FastAPI endpoints
│   ├── agents/              # Document processing agents
│   ├── workers/             # Celery tasks for document processing
│   │   ├── pdf_processor.py # PDF analysis and extraction
│   │   ├── ocr_worker.py    # OCR processing tasks
│   │   └── vector_worker.py # Vector embedding generation
│   ├── services/            # Business logic services
│   └── repositories/        # Data access layer
│
├── celery_worker.py         # Celery worker entry point
├── docker-compose.yml       # Redis + Celery + PostgreSQL + pgvector
└── pyproject.toml           # Dependencies and configuration
```


### 3.2 Legal Document Processing API Integration

```python
# app/main.py - NiceGUI with integrated FastAPI
from nicegui import app, ui
from fastapi import UploadFile, File, BackgroundTasks
from .workers.pdf_processor import process_legal_document
from .workers.ocr_worker import extract_text_with_ocr
from .services.document_service import DocumentService
from dependency_injector.wiring import Provide, inject

@app.post("/api/documents/upload")
@inject
async def upload_legal_document(
    file: UploadFile = File(...),
    classification: str = "simple",
    document_service: DocumentService = Provide["document_service"]
):
    """Upload and queue legal document for processing"""
    
    # Save uploaded file
    file_path = await document_service.save_upload(file)
    
    # Queue for background processing based on classification
    if classification == "complex":
        # Use OCR processing queue for scanned documents
        task = extract_text_with_ocr.delay(
            file_path=file_path,
            client_id=request.client_id,
            priority="high" if "urgent" in file.filename.lower() else "normal"
        )
    else:
        # Use standard PDF processing queue
        task = process_legal_document.delay(
            file_path=file_path,
            client_id=request.client_id,
            document_type="legal"
        )
    
    return {
        "task_id": task.id,
        "status": "queued",
        "estimated_completion": "2-5 minutes"
    }

@app.get("/api/documents/status/{task_id}")
async def get_processing_status(task_id: str):
    """Check document processing status"""
    task = process_legal_document.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
```


### 3.3 Legal Document Processing Workers

```python
# app/workers/pdf_processor.py
from celery import Celery
from typing import Dict, Any
import logging
from ..services.document_service import DocumentService
from ..agents.pdf_processor_agent import PDFProcessorAgent

# Configure Celery with Redis broker and result backend
celery_app = Celery(
    "legal_document_processor",
    broker="redis://localhost:6379/0",      # Task queue
    backend="redis://localhost:6379/1",     # Results storage
    include=[
        'app.workers.pdf_processor',
        'app.workers.ocr_worker',
        'app.workers.vector_worker'
    ]
)

# Production configuration for legal systems
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minute limit for document processing
    task_soft_time_limit=25 * 60,  # 25 minute soft limit
    worker_prefetch_multiplier=1,  # Important for large document processing
    task_acks_late=True,  # Ensure task completion before acknowledgment
    worker_max_tasks_per_child=50,  # Prevent memory leaks
    task_routes={
        'app.workers.pdf_processor.process_legal_document': {'queue': 'pdf_processing'},
        'app.workers.ocr_worker.extract_text_with_ocr': {'queue': 'high_priority'},
        'app.workers.vector_worker.generate_embeddings': {'queue': 'vector_processing'},
    }
)

@celery_app.task(bind=True, name='process_legal_document')
def process_legal_document(
    self, 
    file_path: str, 
    client_id: str, 
    document_type: str = "legal"
) -> Dict[str, Any]:
    """Process legal document and extract content for RAG system"""
    
    logger = logging.getLogger(__name__)
    logger.info(f"Processing legal document: {file_path} for client: {client_id}")
    
    try:
        # Update task status
        self.update_state(state='PROGRESS', meta={'step': 'initializing'})
        
        # Initialize document processor agent
        processor = PDFProcessorAgent()
        
        # Process document with deduplication check
        self.update_state(state='PROGRESS', meta={'step': 'processing'})
        result = processor.process_document(
            file_path=file_path,
            client_id=client_id,
            document_type=document_type
        )
        
        # Queue vector embedding generation
        if result.get('text_extracted'):
            from .vector_worker import generate_embeddings
            generate_embeddings.delay(
                document_id=result['document_id'],
                text_content=result['text_content']
            )
        
        logger.info(f"Successfully processed document {file_path}")
        return {
            'status': 'completed',
            'document_id': result['document_id'],
            'pages_processed': result.get('pages_processed', 0),
            'text_length': len(result.get('text_content', '')),
            'processing_time': result.get('processing_time')
        }
        
    except Exception as exc:
        logger.error(f"Error processing document {file_path}: {str(exc)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'file_path': file_path}
        )
        raise
```


### 3.4 `celery_worker.py`

```python
from app.tasks import celery_app

if __name__ == "__main__":
    celery_app.start()
```


### 3.5 Exemplos de `docker-compose.yml`

```yaml
version: '3'
services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  fastapi:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    depends_on:
      - redis
    ports:
      - "8000:8000"

  celery:
    build: .
    command: celery -A app.tasks worker --loglevel=info
    depends_on:
      - redis

  flower:
    image: mher/flower
    command: flower --broker=redis://redis:6379/0
    ports:
      - "5555:5555"
```


## 4. Redis Commands for Legal Document Processing

The `redis-py` library implements comprehensive Redis commands organized by category, essential for legal document processing workflows:


| Categoria | Descrição |
| :-- | :-- |
| Core Commands | GET, SET, DEL, EXPIRE, EXISTS etc. |
| Hash Commands | HGET, HSET, HDEL, HINCRBY, HGETALL etc. |
| List Commands | LPUSH, RPUSH, LPOP, RPOP, LINSERT, LRANGE etc. |
| Set Commands | SADD, SREM, SMEMBERS, SISMEMBER etc. |
| Sorted Set Commands | ZADD, ZRANGE, ZRANGEBYSCORE, ZREM etc. |
| Pub/Sub | PUBLISH, SUBSCRIBE, PSUBSCRIBE, UNSUBSCRIBE etc. |
| Transaction \& Pipelining | MULTI, EXEC, WATCH, UNWATCH, pipeline() |
| Lua Scripting | EVAL, EVALSHA, SCRIPT LOAD, SCRIPT FLUSH |
| Server Management | INFO, CONFIG GET/SET, FLUSHDB, FLUSHALL, SAVE, BGSAVE, BGREWRITEAOF |
| PubSub \& Streams | XADD, XREAD, XGROUP, XACK etc. |
| Geo Commands | GEOADD, GEORADIUS, GEOHASH, GEODIST etc. |
| HyperLogLog | PFADD, PFCOUNT, PFMERGE |
| ACL \& Security | ACL SETUSER, ACL LIST, ACL DELUSER etc. |

> Consulte em detalhe:
> https://redis-py.readthedocs.io/en/v4.1.2/commands.html[^1_2]

## 5. Legal Document Processing Command Examples

```python
# Document processing status tracking
r.set(f"doc_status:{document_id}", "processing")
r.expire(f"doc_status:{document_id}", 3600)  # 1 hour TTL

# Client document metadata
r.hset(f"client:{client_id}:doc:{doc_id}", mapping={
    "filename": "contract_2025.pdf",
    "status": "processed",
    "pages": "15",
    "processed_at": "2025-01-15T10:30:00Z",
    "ocr_required": "false"
})
client_doc = r.hgetall(f"client:{client_id}:doc:{doc_id}")

# Priority document processing queues
r.lpush("queue:urgent_documents", document_id)  # High priority
r.rpush("queue:standard_documents", document_id)  # Normal priority
next_urgent = r.rpop("queue:urgent_documents")

# Document processing leaderboard by client
r.zadd("client_processing_stats", {
    f"client:{client_id}": total_documents_processed
})
top_clients = r.zrange("client_processing_stats", 0, 9, desc=True, withscores=True)

# Real-time processing notifications
r.publish(f"client:{client_id}:notifications", json.dumps({
    "type": "document_processed",
    "document_id": document_id,
    "status": "completed",
    "timestamp": datetime.utcnow().isoformat()
}))

# Session management for legal users
r.setex(f"session:{session_id}", 3600, json.dumps({
    "user_id": user_id,
    "role": "admin_user",
    "client_id": client_id,
    "permissions": ["document_upload", "client_management"]
}))
```


## 6. Production Configuration for Legal Systems

### High Availability Setup

```python
# Redis Sentinel configuration for legal document processing
from redis.sentinel import Sentinel

sentinel = Sentinel([
    ('sentinel1.legal-system.com', 26379),
    ('sentinel2.legal-system.com', 26379),
    ('sentinel3.legal-system.com', 26379)
], socket_timeout=0.1)

# Get Redis master for writes
master = sentinel.master_for(
    'legal-redis-master',
    socket_timeout=0.1,
    password='secure_legal_password',
    ssl=True
)

# Get Redis slave for reads
slave = sentinel.slave_for(
    'legal-redis-master',
    socket_timeout=0.1,
    password='secure_legal_password',
    ssl=True
)
```

### Security Configuration

```python
# Redis configuration with encryption for legal data
import ssl

redis_config = {
    'host': 'redis.legal-system.com',
    'port': 6380,
    'password': os.getenv('REDIS_PASSWORD'),
    'ssl': True,
    'ssl_cert_reqs': ssl.CERT_REQUIRED,
    'ssl_ca_certs': '/etc/ssl/certs/ca-certificates.crt',
    'ssl_certfile': '/etc/ssl/legal-system/client.crt',
    'ssl_keyfile': '/etc/ssl/legal-system/client.key',
    'decode_responses': True,
    'health_check_interval': 30,
    'socket_keepalive': True
}

r = redis.Redis(**redis_config)
```

### Performance Optimization

```python
# Connection pooling for high-volume legal document processing
from redis.connection import ConnectionPool

pool = ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=20,  # Adjust based on Celery worker count
    retry_on_timeout=True,
    socket_keepalive=True,
    socket_keepalive_options={},
    health_check_interval=30
)

r = redis.Redis(connection_pool=pool)

# Pipeline for batch operations
with r.pipeline() as pipe:
    for doc_id in document_batch:
        pipe.hset(f"doc:{doc_id}", "status", "queued")
        pipe.lpush("processing_queue", doc_id)
    pipe.execute()
```

## Conclusion

This comprehensive guide provides:

1. **Production-ready installation** and **secure connection** patterns
2. **Legal document processing architecture** with NiceGUI + FastAPI + Celery + Redis
3. **Security configurations** appropriate for legal data handling
4. **Performance optimization** strategies for document processing workloads
5. **High availability setup** using Redis Sentinel

Use this as a foundation for building robust legal document processing systems that can handle sensitive data with appropriate security measures and high availability requirements.

<div style="text-align: center">⁂</div>

[^1_1]: https://redis.io/docs/latest/develop/clients/redis-py/

[^1_2]: https://redis-py.readthedocs.io/en/v4.1.2/commands.html

[^1_3]: https://github.com/redis/redis

[^1_4]: https://www.datacamp.com/tutorial/python-redis-beginner-guide

[^1_5]: https://github.com/luovkle/fastapi-celery-flower-redis

[^1_6]: https://redis-py-doc.readthedocs.io

[^1_7]: https://pypi.org/project/redispy/

[^1_8]: https://testdriven.io/courses/fastapi-celery/getting-started/

[^1_9]: https://github.com/redis/docs/blob/main/content/develop/clients/redis-py/_index.md?plain=1

[^1_10]: https://www.linkedin.com/pulse/fastapi-celery-redis-flower-anton-aksonov-ae8vf

[^1_11]: https://redis.io/docs/latest/develop/clients/redis-py/connect/

[^1_12]: https://github.com/redis/redis-py/blob/master/redis/commands/core.py

[^1_13]: https://github.com/Fidget-Spinner/fastapi-celery-redis

[^1_14]: https://redis.io/docs/latest/develop/clients/redis-py/queryjson/

[^1_15]: https://raw.githubusercontent.com/redis/redis-py/master/README.md

[^1_16]: https://www.youtube.com/watch?v=eAHAKowv6hk

[^1_17]: https://pypi.org/project/redis/4.3.4/

[^1_18]: https://redis.io/learn/howtos/quick-start/cheat-sheet

[^1_19]: https://testdriven.io/blog/fastapi-and-celery/

[^1_20]: https://redis.readthedocs.io

[^1_21]: https://derlin.github.io/introduction-to-fastapi-and-celery/03-celery/

