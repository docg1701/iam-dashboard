# Seção 3: Stack de Tecnologia

Esta tabela é a fonte definitiva de verdade para todas as tecnologias e suas versões que serão utilizadas no projeto.

| Categoria | Tecnologia | Versão | Propósito | Justificativa |
| :--- | :--- | :--- | :--- | :--- |
| **Linguagem** | Python | 3.12.x | Linguagem principal do projeto. | Requisito do PRD (NFR4). |
| **Framework Web (UI)** | NiceGUI | 1.4+ | Construção da interface de usuário interativa. | Requisito do PRD (NFR4). |
| **Framework Web (API)** | FastAPI | 0.104+ | Servir a API RESTful para o frontend e clientes. | Padrão de mercado, integrado ao NiceGUI. |
| **Banco de Dados** | PostgreSQL | 16.x | Armazenamento de dados relacionais (usuários, clientes, documentos). | Requisito do PRD (NFR5). |
| **Extensão Vetorial** | pgvector | 0.7.x | Habilita o armazenamento e a busca de similaridade de vetores. | Requisito do PRD (NFR5). |
| **Processamento Assíncrono**| Celery | 5.3+ | Fila de tarefas para processar PDFs de forma assíncrona. | Padrão da indústria para tarefas em background. |
| **Message Broker** | Redis | 7.2.x | Broker para Celery e cache de estado de tarefas. | Rápido, confiável e padrão para Celery. |
| **IA Generativa** | Google Gemini API | v1.5 | Geração de embeddings e síntese de respostas. | Requisito do PRD (NFR6). |
| **Orquestração de RAG**| Llama-Index | 0.12.x | Orquestra todo o pipeline de ingestão e consulta RAG. | Abstrai a complexidade do RAG. |
| **Framework de Agentes** | Agno | 1.7.x | Estrutura para a criação dos agentes autônomos que consomem o RAG. | Especializado na criação de agentes com ferramentas. |
| **Manipulação de PDF** | PyMuPDF | 1.24+ | Extração de texto e imagens de arquivos PDF. | Performance e robustez. Licença AGPL. |
| **OCR** | Tesseract | 5.5.x | Extração de texto de imagens (documentos escaneados). | Solução open-source robusta, usada pelo Llama-Index. |
| **Injeção de Dependência**| dependency-injector | 4.48.x| Gerenciamento de modularidade e dependências. | Facilita testes e desacoplamento. |
| **ORM & Migrações** | SQLAlchemy & Alembic | 2.x | Mapeamento Objeto-Relacional e migrações de esquema. | Padrão para gestão de esquema de BD em Python. |
| **Conteinerização** | Docker & Docker Compose | 29.x | Empacotamento e orquestração dos serviços. | Consistência e portabilidade do ambiente. |
| **Proxy Reverso** | Caddy | 2.10.x | Roteamento de tráfego e gerenciamento automático de SSL/TLS. | Simplicidade e segurança. |
