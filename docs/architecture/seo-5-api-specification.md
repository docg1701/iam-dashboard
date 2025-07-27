# Seção 5: Especificação da API

A aplicação exporá uma API RESTful via FastAPI para gerenciar recursos e interagir com os agentes.

* `POST /v1/documents`: Faz o upload de um PDF, que dispara uma tarefa assíncrona de ingestão via Celery e Llama-Index.
* `GET /v1/tasks/{task_id}`: Verifica o status de uma tarefa de processamento.
* `POST /v1/query`: Envia uma pergunta para o agente de consulta (Agno), que utilizará o pipeline RAG (Llama-Index) para responder.
