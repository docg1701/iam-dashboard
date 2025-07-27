# 7. Detalhes do Épico 2: Utilização Inteligente e Geração de Conteúdo

**Objetivo Expandido:** Este épico capitaliza sobre a fundação do Épico 1, ativando a capacidade de geração de conteúdo inteligente da plataforma. O foco é implementar o primeiro agente de redação que consome os dados do banco vetorial via RAG, provando o ciclo completo de valor. Adicionalmente, aprimoraremos a interface de gerenciamento de clientes para que o advogado possa visualizar os documentos processados e interagir com os novos agentes de forma contextualizada.

## Estória 2.1: Aprimoramento da Interface de Gerenciamento de Clientes
**Como um** **usuário (admin_user ou common_user)**, **eu quero** ver uma lista de todos os documentos que já foram processados para um cliente específico, juntamente com seu status, **para** que eu tenha o contexto necessário antes de usar um agente de redação.

**Critérios de Aceite:**
1. Na página de detalhes de um cliente, uma nova seção exibe uma lista de todos os documentos enviados para ele.
2. A lista exibe o nome do arquivo, a data do upload e o status atual ("Processando", "Concluído", "Falha").
3. A interface é atualizada para refletir quando o status de um documento muda.
4. O usuário pode visualizar um resumo dos dados extraídos de um documento "Concluído".

## Estória 2.2: Implementação do Agente de Redação de Quesitos Judiciais
**Como um** **usuário (admin_user ou common_user)**, **eu quero** selecionar um cliente com documentos já processados e ativar o agente de "Redação de Quesitos Judiciais", **para** gerar um rascunho de alta qualidade baseado nas informações contidas nesses documentos e nos dados específicos que eu fornecer.

**Critérios de Aceite:**
1. O ícone do "Redator de Quesitos Judiciais" no dashboard está funcional.
2. A interface do agente permite ao usuário selecionar um cliente da sua lista.
3. O agente exibe um formulário com campos específicos (ex: profissão, doença, datas) que o usuário deve preencher para guiar a geração do documento.
4. O agente utiliza RAG para buscar informações relevantes nos documentos do cliente no banco vetorial.
5. As informações recuperadas e os dados do formulário são enviados para a API do Google Gemini para gerar o rascunho.
6. O rascunho gerado é exibido em uma área de texto na interface.
7. Um botão "Copiar Texto" está presente e funcional.
