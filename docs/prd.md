# Product Requirements Document (PRD): Sistema de Agentes Autônomos para Advocacia

| Data | Versão | Descrição | Autor |
| :--- | :--- | :--- | :--- |
| 24/07/2025 | 1.0 | Versão inicial gerada a partir do Project Brief. | John, Product Manager |
| 25/07/2025 | 1.1 | Adicionadas premissas de arquitetura (single-tenant, Alembic) e NFRs operacionais. Papéis de usuário refinados. | John, Product Manager |
| 25/07/2025 | 1.2 | Atualizada Estória 2.2 para refletir a interação via formulário estruturado, alinhando com front-end-spec e architecture. | John, Product Manager |

## 1. Metas e Contexto de Fundo

### Metas
* Aumentar a capacidade operacional do escritório, permitindo o gerenciamento de mais casos simultaneamente.
* Maximizar a lucratividade através da redução do tempo e custo gastos em tarefas cognitivas manuais.
* Estabelecer uma vantagem competitiva sustentável no mercado jurídico.
* Melhorar a retenção de talentos e o bem-estar da equipe, reduzindo a sobrecarga e a fadiga mental.
* Reduzir o tempo gasto pelos advogados desde o recebimento de um caso até a produção de insights e rascunhos.
* Diminuir o tempo gasto pela equipe de suporte com entrada manual de dados e respostas repetitivas.

### Contexto de Fundo
Este projeto visa resolver a sobrecarga de trabalho manual e a fadiga mental em escritórios de advocacia, problemas gerados pela análise demorada de grandes volumes de documentos e pela redação de textos jurídicos complexos. Atualmente, esses processos manuais limitam o crescimento dos escritórios, restringindo sua capacidade de aceitar novos clientes e reduzindo as margens de lucro devido ao alto custo de mão de obra por caso.

As ferramentas existentes são eficazes para a gestão administrativa, mas falham em automatizar o trabalho cognitivo, que é o principal gargalo. A solução proposta é uma plataforma SaaS com agentes de IA autônomos que não apenas organizam, mas executam tarefas de análise e redação, transformando a produtividade e permitindo que a equipe se concentre em atividades de maior valor estratégico.

---

## 2. Requisitos

### Funcional
* **FR1:** O sistema deve ter autenticação de usuário segura, incluindo autenticação de dois fatores (2FA). 
* **FR2:** Deve permitir o cadastro de clientes e o upload de documentos PDF. Para evitar duplicatas, o sistema deve gerar um **hash único baseado exclusivamente no conteúdo do arquivo**, ignorando nome e extensão. 
* **FR3:** Deve apresentar um painel de controle principal (dashboard) com ícones para acessar os agentes autônomos.
* **FR4:** Deve fornecer um pipeline completo para processamento de documentos, permitindo que o usuário classifique os arquivos como "simples" (digital) ou "complexos" (escaneado) para o processamento backend.
* **FR5:** As informações extraídas dos documentos devem ser armazenadas em um banco de dados vetorial para permitir acesso inteligente via RAG (Retrieval-Augmented Generation).
* **FR6:** O sistema deve incluir um agente "Processador de PDFs" para realizar a ingestão de documentos no banco de dados vetorial.
* **FR7:** O sistema deve incluir um agente de "Redação de Quesitos Judiciais" que utiliza as informações do banco de dados vetorial para gerar rascunhos de documentos.

### Não Funcional
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

## 3. Metas de Design da Interface do Usuário (UI)

### Visão Geral de UX (Experiência do Usuário)
A experiência do usuário deve ser focada em **eficiência e simplicidade profissional**. A interface deve ser limpa, direta e sem distrações, permitindo que os advogados ativem agentes poderosos com o mínimo de atrito. O valor está na tarefa executada pelo agente, não na complexidade da interface.

### Paradigmas Chave de Interação
* **Dashboard-cêntrico:** A interação principal será através de um painel de controle com ícones, funcionando como o hub central para todas as ações.
* **Agente como Ferramenta:** O usuário seleciona uma ferramenta (agente) para um trabalho específico (ex: "Processar PDFs", "Redigir Quesitos"), em vez de interagir através de um chat genérico.
* **Processamento Assíncrono Visível:** O usuário fará o upload de documentos para processamento em segundo plano. A interface deve fornecer feedback claro sobre o status dessas tarefas (ex: em fila, processando, concluído).
* **Fluxo de "Cadastrar Uma Vez, Usar Múltiplas Vezes":** A interface deve facilitar o uso de informações já processadas por novos agentes, reforçando o valor do banco de dados vetorial.

### Telas e Visões Principais (MVP)
* Tela de Login (para autenticação segura).
* Painel de Controle Principal (Dashboard com ícones dos agentes).
* **Tela de Cadastro/Gerenciamento de Clientes:**
    * Nesta tela, deve ser possível acessar os dados dos clientes cadastrados e visualizar o status dos documentos que cada um já possui processado no sistema.
* Tela de Upload e Classificação de Documentos.
* **Componente de Acompanhamento de Tarefas:** Um componente não obstrutivo (como um pop-up, slider ou uma seção dedicada no rodapé da interface) para notificar o usuário e mostrar o progresso de tarefas em processamento paralelo.
* Interface do Agente de Redação de Quesitos (onde o usuário interage com o agente para gerar o texto).

### Acessibilidade
* O produto deve atender, no mínimo, ao padrão **WCAG AA**.

### Branding
* O design inicial deve ser profissional, limpo e funcional, priorizando a usabilidade.
* **O sistema deve permitir a personalização da identidade visual (logotipo, esquema de cores) para cada cliente (escritório) contratante.**

### Dispositivos e Plataformas-Alvo
* **Web Responsivo:** A aplicação deve ser totalmente funcional em **desktops, tablets e celulares**.

---

## 4. Premissas Técnicas

### Estrutura do Repositório: Monorepo
* **Decisão:** Um monorepo será utilizado para gerenciar o código.
* **Justificativa:** Com múltiplos agentes autônomos que podem compartilhar lógica, um monorepo facilitará a consistência e o gerenciamento de dependências.

### Arquitetura de Serviço: Orientada a Serviços (Modular)
* **Decisão:** A arquitetura seguirá um padrão modular, orientado a serviços.
* **Justificativa:** O briefing enfatiza a modularidade. Uma arquitetura orientada a serviços alinha-se com essa visão, permitindo o desenvolvimento independente de novas capacidades.

### Requisitos de Teste: Pirâmide de Testes Completa
* **Decisão:** O projeto adotará uma estratégia de pirâmide de testes completa (unitários, integração e E2E).
* **Justificativa:** Essencial para garantir a qualidade de um produto SaaS robusto.

### Premissas Técnicas Adicionais
* **Linguagem e Framework:** Python, utilizando o framework niceGUI.
* **Banco de Dados:** PostgreSQL com a extensão pgvector.
* **IA e Orquestração:** O pipeline de RAG (Retrieval-Augmented Generation) será orquestrado pelo **Llama-Index**, que utilizará a **API do Google Gemini** para geração de embeddings e síntese de respostas. O framework **Agno** será usado para construir os agentes que interagem com este pipeline.
* **Processamento Assíncrono:** Filas de tarefas com Celery e Redis.
* **Arquitetura do Agente de PDFs:** O pipeline de ingestão de documentos será gerenciado pelo **Llama-Index**, que abstrai a leitura de PDFs (com PyMuPDF), o chunking de texto e o armazenamento vetorial no pgvector.
* **Modularidade (Plugins):** Gerenciada pela biblioteca `python-dependency-injector`.
* **Modelo de Implantação:** O sistema seguirá um modelo de implantação **single-tenant**, onde cada cliente (escritório de advocacia) terá sua própria instância isolada da aplicação e do banco de dados, hospedada em um VPS dedicado e gerenciado.
* **Gerenciamento do Banco de Dados:** A gestão e evolução do esquema do banco de dados serão controladas através de uma ferramenta de migração versionada (**Alembic** com **SQLAlchemy**), garantindo atualizações seguras e organizadas.

---

## 5. Lista de Épicos

1.  **Épico 1: Fundação e Ingestão de Documentos**
    * **Objetivo:** Estabelecer a infraestrutura fundamental da aplicação, incluindo autenticação, e entregar o pipeline completo de processamento e ingestão de documentos no banco de dados vetorial.

2.  **Épico 2: Utilização Inteligente e Geração de Conteúdo**
    * **Objetivo:** Habilitar a utilização inteligente dos documentos processados, introduzindo o primeiro agente de redação (Quesitos Judiciais) e a interface de gerenciamento de clientes.

---

## 6. Detalhes do Épico 1: Fundação e Ingestão de Documentos

**Objetivo Expandido:** O objetivo deste épico é construir a base da aplicação SaaS, desde a configuração inicial do projeto e a segurança de acesso do usuário até a implementação do pipeline principal de processamento de documentos. Ao final deste épico, a plataforma será capaz de receber arquivos PDF, processá-los de forma assíncrona e armazenar as informações extraídas em um banco de dados vetorial, entregando o valor fundamental de automação da ingestão de dados.

### Estória 1.1: Configuração Inicial da Aplicação e Autenticação de Usuários
**Como um** **usuário administrador da plataforma (sysadmin)**, **eu quero** configurar a estrutura inicial da aplicação e ter um sistema de login seguro com 2FA, **para** garantir que apenas usuários autorizados possam acessar a plataforma.

**Critérios de Aceite:**
1. A estrutura do projeto (niceGUI, pastas, etc.) está criada e o servidor web inicial está funcional.
2. Um usuário pode se registrar na plataforma.
3. Um usuário pode fazer login e logout.
4. A autenticação de dois fatores (2FA) é obrigatória e funcional.
5. Os dados do usuário são armazenados de forma segura no banco de dados PostgreSQL.

### Estória 1.2: Implementação do Dashboard Principal e Cadastro de Clientes
**Como um** **usuário administrador do escritório (admin_user)**, **eu quero** acessar um dashboard principal após o login e cadastrar meus clientes, **para** organizar meu trabalho e preparar o sistema para o upload de documentos.

**Critérios de Aceite:**
1. Após o login, o usuário é redirecionado para o dashboard principal.
2. O dashboard exibe ícones (placeholders) para as funcionalidades do MVP ("Processador de PDFs", "Redator de Quesitos").
3. O usuário pode acessar uma área de "Clientes".
4. Nesta área, o usuário pode cadastrar um novo cliente com os dados definidos (nome, CPF, data de nascimento).
5. Uma lista de clientes já cadastrados é exibida.

### Estória 1.3: Pipeline de Upload e Processamento Assíncrono de Documentos
**Como um** **usuário (admin_user ou common_user)**, **eu quero** fazer o upload de um documento PDF, classificá-lo e associá-lo a um cliente, **para** que o sistema possa iniciar o processamento de forma assíncrona.

**Critérios de Aceite:**
1. Na área de um cliente específico, existe a opção de fazer upload de um documento.
2. A interface de upload permite que o usuário selecione um arquivo PDF local.
3. O usuário deve classificar o documento como "simples" (digital) ou "complexo" (escaneado).
4. Ao enviar, o sistema calcula o hash do conteúdo do arquivo e verifica se já existe. Se for uma duplicata, o usuário é informado e o upload é interrompido.
5. Se não for uma duplicata, uma tarefa de processamento é criada na fila (Celery + Redis).
6. A interface exibe uma notificação de que o processamento foi iniciado.

### Estória 1.4: Agente Processador de PDFs e Ingestão no Banco Vetorial
**Como um** sistema, **eu quero** processar os documentos da fila, orquestrando a extração de conteúdo e o armazenamento no banco de dados vetorial, **para** que os dados fiquem disponíveis para consulta por outros agentes.

**Critérios de Aceite:**
1. Um worker (Celery) consome as tarefas da fila de processamento.
2. O pipeline de ingestão é gerenciado pelo **Llama-Index**.
3. Para documentos "simples", o Llama-Index utiliza o `PyMuPDFReader` para extrair o texto diretamente.
4. Para documentos "complexos", o Llama-Index extrai as imagens das páginas e utiliza uma função de pré-processamento (com OpenCV) e OCR (com Tesseract) para obter o texto.
5. O Llama-Index é responsável por dividir o texto em chunks, gerar os embeddings via API do Gemini e persistir os nós (chunks + vetores) no `PGVectorStore`.
6. O status do documento na interface é atualizado para "Concluído" ao final do processo.

---

## 7. Detalhes do Épico 2: Utilização Inteligente e Geração de Conteúdo

**Objetivo Expandido:** Este épico capitaliza sobre a fundação do Épico 1, ativando a capacidade de geração de conteúdo inteligente da plataforma. O foco é implementar o primeiro agente de redação que consome os dados do banco vetorial via RAG, provando o ciclo completo de valor. Adicionalmente, aprimoraremos a interface de gerenciamento de clientes para que o advogado possa visualizar os documentos processados e interagir com os novos agentes de forma contextualizada.

### Estória 2.1: Aprimoramento da Interface de Gerenciamento de Clientes
**Como um** **usuário (admin_user ou common_user)**, **eu quero** ver uma lista de todos os documentos que já foram processados para um cliente específico, juntamente com seu status, **para** que eu tenha o contexto necessário antes de usar um agente de redação.

**Critérios de Aceite:**
1. Na página de detalhes de um cliente, uma nova seção exibe uma lista de todos os documentos enviados para ele.
2. A lista exibe o nome do arquivo, a data do upload e o status atual ("Processando", "Concluído", "Falha").
3. A interface é atualizada para refletir quando o status de um documento muda.
4. O usuário pode visualizar um resumo dos dados extraídos de um documento "Concluído".

### Estória 2.2: Implementação do Agente de Redação de Quesitos Judiciais
**Como um** **usuário (admin_user ou common_user)**, **eu quero** selecionar um cliente com documentos já processados e ativar o agente de "Redação de Quesitos Judiciais", **para** gerar um rascunho de alta qualidade baseado nas informações contidas nesses documentos e nos dados específicos que eu fornecer.

**Critérios de Aceite:**
1. O ícone do "Redator de Quesitos Judiciais" no dashboard está funcional.
2. A interface do agente permite ao usuário selecionar um cliente da sua lista.
3. O agente exibe um formulário com campos específicos (ex: profissão, doença, datas) que o usuário deve preencher para guiar a geração do documento.
4. O agente utiliza RAG para buscar informações relevantes nos documentos do cliente no banco vetorial.
5. As informações recuperadas e os dados do formulário são enviados para a API do Google Gemini para gerar o rascunho.
6. O rascunho gerado é exibido em uma área de texto na interface.
7. Um botão "Copiar Texto" está presente e funcional.
