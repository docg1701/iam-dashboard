# 2. Requisitos

## Funcional
* **FR1:** O sistema deve ter autenticação de usuário segura, incluindo autenticação de dois fatores (2FA). 
* **FR2:** Deve permitir o cadastro de clientes e o upload de documentos PDF. Para evitar duplicatas, o sistema deve gerar um **hash único baseado exclusivamente no conteúdo do arquivo**, ignorando nome e extensão. 
* **FR3:** Deve apresentar um painel de controle principal (dashboard) com ícones para acessar os agentes autônomos.
* **FR4:** Deve fornecer um pipeline completo para processamento de documentos, permitindo que o usuário classifique os arquivos como "simples" (digital) ou "complexos" (escaneado) para o processamento backend.
* **FR5:** As informações extraídas dos documentos devem ser armazenadas em um banco de dados vetorial para permitir acesso inteligente via RAG (Retrieval-Augmented Generation).
* **FR6:** O sistema deve incluir um agente "Processador de PDFs" para realizar a ingestão de documentos no banco de dados vetorial.
* **FR7:** O sistema deve incluir um agente de "Redação de Quesitos Judiciais" que utiliza as informações do banco de dados vetorial para gerar rascunhos de documentos.

## Não Funcional
* **NFR1:** A aplicação deve ser uma plataforma web (SaaS) acessível através de navegadores modernos.
* **NFR2:** A aplicação deve ser hospedada em um Servidor Privado Virtual (VPS) com GNU/Linux Ubuntu Server 24.x.
* **NFR3:** Os requisitos mínimos de hardware do servidor são 4 vCPUs e 4 GB de RAM, sem GPU dedicada, com capacidade de escalonamento.
* **NFR4:** A aplicação será desenvolvida inteiramente em Python, utilizando **NiceGUI**, que integra capacidades de frontend e backend (via FastAPI).
* **NFR5:** O banco de dados deve ser PostgreSQL com a extensão pgvector.
* **NFR6:** A solução deve utilizar a API do Google Gemini (2.5 Pro e Flash).
* **NFR7:** O uso de novas bibliotecas deve ser restrito ao estritamente necessário para reduzir código, facilitar manutenção ou adicionar funcionalidades essenciais.
* **NFR8:** Todos os softwares utilizados devem ser de código aberto com licenças permissivas (MIT, Apache 2.0, etc.). Uma exceção notável é o **PyMuPDF**, que utiliza a licença AGPL e cujo uso deve ser encapsulado para conformidade.
* **NFR9:** O sistema deve possuir um mecanismo de backup diário automatizado do banco de dados e arquivos da aplicação.
* **NFR10:** A saúde da infraestrutura do VPS (CPU, RAM, Disco) deve ser continuamente monitorada, com um sistema de alertas para a equipe de administração em caso de anomalias.

---
