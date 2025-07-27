# Seção 6: Componentes

O sistema é decomposto nos seguintes componentes lógicos, implementados como serviços Docker:

* **Reverse Proxy (Caddy):** Ponto de entrada da aplicação, gerencia tráfego e TLS.
* **Web Application (NiceGUI/FastAPI):** Serve a interface do usuário e os endpoints da API.
* **Task Queue (Celery + Redis):** Gerencia o enfileiramento de tarefas de processamento de documentos.
* **Processing Worker (Celery Worker):** Executa as tarefas da fila, invocando o pipeline de ingestão do Llama-Index.
* **RAG Pipeline (Llama-Index):** Componente lógico (não um serviço separado) que orquestra a extração, chunking, embedding e armazenamento de dados.
* **Query Agent (Agno):** Componente lógico que encapsula a lógica de consulta, utilizando o RAG pipeline como uma ferramenta.
* **Database (PostgreSQL + pgvector):** Camada de persistência para dados relacionais e vetoriais.
