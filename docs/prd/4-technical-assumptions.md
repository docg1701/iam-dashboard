# 4. Premissas Técnicas

## Estrutura do Repositório: Monorepo
* **Decisão:** Um monorepo será utilizado para gerenciar o código.
* **Justificativa:** Com múltiplos agentes autônomos que podem compartilhar lógica, um monorepo facilitará a consistência e o gerenciamento de dependências.

## Arquitetura de Serviço: Orientada a Serviços (Modular)
* **Decisão:** A arquitetura seguirá um padrão modular, orientado a serviços.
* **Justificativa:** O briefing enfatiza a modularidade. Uma arquitetura orientada a serviços alinha-se com essa visão, permitindo o desenvolvimento independente de novas capacidades.

## Requisitos de Teste: Pirâmide de Testes Completa
* **Decisão:** O projeto adotará uma estratégia de pirâmide de testes completa (unitários, integração e E2E).
* **Justificativa:** Essencial para garantir a qualidade de um produto SaaS robusto.

## Premissas Técnicas Adicionais
* **Linguagem e Framework:** Python, utilizando o framework niceGUI.
* **Banco de Dados:** PostgreSQL com a extensão pgvector.
* **IA e Orquestração:** O pipeline de RAG (Retrieval-Augmented Generation) será orquestrado pelo **Llama-Index**, que utilizará a **API do Google Gemini** para geração de embeddings e síntese de respostas. O framework **Agno** será usado para construir os agentes que interagem com este pipeline.
* **Processamento Assíncrono:** Filas de tarefas com Celery e Redis.
* **Arquitetura do Agente de PDFs:** O pipeline de ingestão de documentos será gerenciado pelo **Llama-Index**, que abstrai a leitura de PDFs (com PyMuPDF), o chunking de texto e o armazenamento vetorial no pgvector.
* **Modularidade (Plugins):** Gerenciada pela biblioteca `python-dependency-injector`.
* **Modelo de Implantação:** O sistema seguirá um modelo de implantação **single-tenant**, onde cada cliente (escritório de advocacia) terá sua própria instância isolada da aplicação e do banco de dados, hospedada em um VPS dedicado e gerenciado.
* **Gerenciamento do Banco de Dados:** A gestão e evolução do esquema do banco de dados serão controladas através de uma ferramenta de migração versionada (**Alembic** com **SQLAlchemy**), garantindo atualizações seguras e organizadas.

---
