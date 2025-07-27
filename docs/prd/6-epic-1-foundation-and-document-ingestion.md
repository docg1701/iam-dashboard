# 6. Detalhes do Épico 1: Fundação e Ingestão de Documentos

**Objetivo Expandido:** O objetivo deste épico é construir a base da aplicação SaaS, desde a configuração inicial do projeto e a segurança de acesso do usuário até a implementação do pipeline principal de processamento de documentos. Ao final deste épico, a plataforma será capaz de receber arquivos PDF, processá-los de forma assíncrona e armazenar as informações extraídas em um banco de dados vetorial, entregando o valor fundamental de automação da ingestão de dados.

## Estória 1.1: Configuração Inicial da Aplicação e Autenticação de Usuários
**Como um** **usuário administrador da plataforma (sysadmin)**, **eu quero** configurar a estrutura inicial da aplicação e ter um sistema de login seguro com 2FA, **para** garantir que apenas usuários autorizados possam acessar a plataforma.

**Critérios de Aceite:**
1. A estrutura do projeto (niceGUI, pastas, etc.) está criada e o servidor web inicial está funcional.
2. Um usuário pode se registrar na plataforma.
3. Um usuário pode fazer login e logout.
4. A autenticação de dois fatores (2FA) é obrigatória e funcional.
5. Os dados do usuário são armazenados de forma segura no banco de dados PostgreSQL.

## Estória 1.2: Implementação do Dashboard Principal e Cadastro de Clientes
**Como um** **usuário administrador do escritório (admin_user)**, **eu quero** acessar um dashboard principal após o login e cadastrar meus clientes, **para** organizar meu trabalho e preparar o sistema para o upload de documentos.

**Critérios de Aceite:**
1. Após o login, o usuário é redirecionado para o dashboard principal.
2. O dashboard exibe ícones (placeholders) para as funcionalidades do MVP ("Processador de PDFs", "Redator de Quesitos").
3. O usuário pode acessar uma área de "Clientes".
4. Nesta área, o usuário pode cadastrar um novo cliente com os dados definidos (nome, CPF, data de nascimento).
5. Uma lista de clientes já cadastrados é exibida.

## Estória 1.3: Pipeline de Upload e Processamento Assíncrono de Documentos
**Como um** **usuário (admin_user ou common_user)**, **eu quero** fazer o upload de um documento PDF, classificá-lo e associá-lo a um cliente, **para** que o sistema possa iniciar o processamento de forma assíncrona.

**Critérios de Aceite:**
1. Na área de um cliente específico, existe a opção de fazer upload de um documento.
2. A interface de upload permite que o usuário selecione um arquivo PDF local.
3. O usuário deve classificar o documento como "simples" (digital) ou "complexo" (escaneado).
4. Ao enviar, o sistema calcula o hash do conteúdo do arquivo e verifica se já existe. Se for uma duplicata, o usuário é informado e o upload é interrompido.
5. Se não for uma duplicata, uma tarefa de processamento é criada na fila (Celery + Redis).
6. A interface exibe uma notificação de que o processamento foi iniciado.

## Estória 1.4: Agente Processador de PDFs e Ingestão no Banco Vetorial
**Como um** sistema, **eu quero** processar os documentos da fila, orquestrando a extração de conteúdo e o armazenamento no banco de dados vetorial, **para** que os dados fiquem disponíveis para consulta por outros agentes.

**Critérios de Aceite:**
1. Um worker (Celery) consome as tarefas da fila de processamento.
2. O pipeline de ingestão é gerenciado pelo **Llama-Index**.
3. Para documentos "simples", o Llama-Index utiliza o `PyMuPDFReader` para extrair o texto diretamente.
4. Para documentos "complexos", o Llama-Index extrai as imagens das páginas e utiliza uma função de pré-processamento (com OpenCV) e OCR (com Tesseract) para obter o texto.
5. O Llama-Index é responsável por dividir o texto em chunks, gerar os embeddings via API do Gemini e persistir os nós (chunks + vetores) no `PGVectorStore`.
6. O status do documento na interface é atualizado para "Concluído" ao final do processo.

---
