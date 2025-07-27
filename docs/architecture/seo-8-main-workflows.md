# Seção 8: Fluxos de Trabalho Principais

*   **Ingestão de Documento (Assíncrono):**
    1.  Usuário faz upload de um PDF via UI (NiceGUI).
    2.  A API (FastAPI) recebe o arquivo e enfileira uma tarefa no Celery.
    3.  O Worker Celery pega a tarefa e invoca o pipeline de ingestão do **Llama-Index**.
    4.  O Llama-Index lê o PDF, extrai o texto (usando OCR se necessário), o divide em chunks, gera embeddings via Gemini e os armazena no PostgreSQL/pgvector.
*   **Consulta via Agente de IA (Síncrono):**
    1.  Usuário envia uma pergunta através da UI.
    2.  A API delega a pergunta para o agente de consulta (Agno).
    3.  O agente Agno utiliza sua ferramenta de busca, que invoca o **Query Engine do Llama-Index**.
    4.  O Llama-Index converte a pergunta em um vetor, busca os chunks mais relevantes no pgvector (com filtro por cliente), e envia o contexto e a pergunta para o Gemini sintetizar a resposta.
    5.  A resposta final é retornada ao usuário.
