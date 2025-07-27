# Project Brief: Sistema de Agentes Autônomos para Advocacia

| Data | Versão | Descrição | Autor |
| :--- | :--- | :--- | :--- |
| 24/07/2025 | 1.0 | Versão inicial criada através de sessão de análise. | Mary, Business Analyst |

## Resumo Executivo

Este projeto propõe o desenvolvimento de um sistema SaaS (Software as a Service) modular, projetado inicialmente para escritórios de advocacia, com uma arquitetura de agentes autônomos acessados através de um painel de ícones. O sistema aborda o problema fundamental da sobrecarga de trabalho manual e da fadiga mental em escritórios de advocacia, que são causados tanto pela análise demorada de grandes volumes de documentos quanto pela redação de textos jurídicos complexos e especializados. O público-alvo inicial são escritórios de advocacia que buscam modernização e escalabilidade. A proposta de valor principal é transformar a produtividade e a competitividade do escritório, aumentando a qualidade e o valor do trabalho produzido através da automação de tarefas complexas de análise e redação com o uso de LLMs. Isso permite que a equipe atenda a um volume maior de clientes com menos esforço, resultando em maior lucratividade e bem-estar, garantindo assim sua relevância e sucesso na era da IA.

## Declaração do Problema

### Estado Atual e Pontos de Dor
Atualmente, escritórios de advocacia operam sob intensa pressão, onde a maior parte do trabalho de alto valor depende de processos manuais, lentos e propensos à fadiga. As equipes jurídicas gastam uma quantidade desproporcional de tempo e energia cognitiva na análise de vastos volumes de documentos não estruturados (laudos, contratos, processos) e na redação de peças jurídicas complexas e repetitivas. Este processo manual não só é um gargalo para a produtividade, mas também gera um cansaço mental significativo, levando ao esgotamento da equipe (burnout).

### Impacto do Problema
O impacto direto desse gargalo é a limitação do crescimento do escritório. A capacidade de aceitar novos clientes é restrita não pela falta de oportunidade, mas pela capacidade de processamento da equipe. Isso resulta em perda de receita potencial e margens de lucro reduzidas devido ao alto custo de mão de obra por caso. Além disso, a qualidade do serviço pode se tornar inconsistente sob pressão, e a equipe se sente sobrecarregada e incapaz de cumprir suas tarefas com excelência.

### Por que as Soluções Atuais Falham
As ferramentas existentes no mercado, como CRMs jurídicos e sistemas de gestão de documentos, são eficazes para a organização administrativa, mas falham em endereçar o trabalho cognitivo. Elas ajudam a armazenar arquivos, mas não a extrair, analisar, correlacionar e utilizar a informação contida neles de forma inteligente. Falta-lhes a camada de inteligência (LLM) necessária para automatizar as tarefas de análise e redação que consomem a maior parte do tempo dos advogados.

### Urgência e Importância
A ascensão da Inteligência Artificial transformou este problema de uma ineficiência para uma ameaça existencial. Escritórios que não otimizarem seus processos cognitivos e escalarem sua produtividade ficarão rapidamente ultrapassados. A urgência reside na necessidade de garantir a competitividade e a sobrevivência no mercado, posicionando-se como pioneiro na advocacia impulsionada por IA para capturar espaço de mercado e definir o novo padrão de excelência e eficiência.

## Solução Proposta

### Conceito e Abordagem Principal
A solução é uma plataforma SaaS (Software as a Service) que atua como um "cérebro" de Inteligência Artificial para escritórios de advocacia. A experiência do usuário será centrada em um painel de controle (dashboard) com ícones clicáveis, onde cada ícone representa e ativa um Agente Autônomo especializado em uma tarefa cognitiva específica (ex: Processador de PDFs, Redator de Quesitos, Analisador de Laudos). A abordagem é modular, permitindo que novas capacidades (agentes) sejam adicionadas como plugins independentes ao core do sistema.

### Diferenciais-Chave
Diferentemente das soluções atuais que focam na gestão administrativa, nossa plataforma foca na automação do trabalho cognitivo. O principal diferencial é o uso intensivo de LLMs (Google Gemini API) para interpretar, analisar, correlacionar e criar conteúdo complexo. Enquanto concorrentes ajudam a organizar o trabalho, nossa solução executa partes significativas desse trabalho, funcionando como um membro produtivo da equipe.

### Por que Esta Solução Terá Sucesso
O sucesso desta solução está atrelado ao seu foco direto no maior gargalo dos escritórios: o tempo e o esforço mental necessários para as tarefas de análise e redação. Ao oferecer um ganho de produtividade "vertiginoso" (reduzindo horas a minutos), a plataforma permite um modelo de negócio mais escalável e lucrativo para os escritórios. Ela não apenas melhora o fluxo de trabalho existente, mas o transforma, liberando os advogados para se concentrarem em atividades estratégicas de maior valor.

### Visão de Alto Nível para o Produto
A visão é estabelecer um novo padrão de operação para a prática jurídica na era da IA. O sistema se tornará a plataforma central de inteligência do escritório, capacitando todos os membros da equipe — de estagiários a sócios — a produzirem mais, com maior qualidade e menos estresse. O objetivo final é ser a ferramenta indispensável que confere a um escritório de advocacia uma vantagem competitiva decisiva no mercado.

## Usuários-Alvo

### Segmento de Usuário Primário: O Advogado Executor
* **Perfil:** Advogados associados, plenos ou seniores dentro de um escritório de pequeno a médio porte. São responsáveis diretos pela execução das tarefas do dia a dia: analisar documentos, pesquisar, redigir peças e comunicar-se com clientes. São tecnicamente competentes para usar softwares do dia a dia (editores de texto, CRMs básicos), mas não são especialistas em tecnologia.
* **Comportamentos e Fluxos de Trabalho Atuais:** O dia de trabalho é reativo e fragmentado, alternando entre a leitura de dezenas de documentos PDF, redação de peças em um editor de texto, busca de informações em sistemas judiciais e comunicação com clientes via e-mail e WhatsApp. Grande parte do tempo é gasta em tarefas repetitivas e de baixo valor estratégico.
* **Necessidades e Pontos de Dor:**
    * **Dor:** Cansaço mental e esgotamento (burnout) devido ao volume de leitura e escrita.
    * **Dor:** Frustração com a ineficiência e a repetição de tarefas manuais.
    * **Necessidade:** Ferramentas que acelerem a análise de documentos para que possam focar na estratégia do caso.
    * **Necessidade:** Reduzir o tempo gasto em rascunhos iniciais de peças processuais.
* **Objetivos:**
    * Aumentar sua produtividade pessoal para cumprir prazos com menos estresse.
    * Melhorar a qualidade de seu trabalho (peças e análises) para se destacar profissionalmente.
    * Ter mais tempo disponível para se dedicar a atividades estratégicas e ao relacionamento com o cliente.

### Segmento de Usuário Secundário: Equipe de Suporte e Operações
* **Perfil:** Estagiários, assistentes jurídicos e a equipe administrativa (financeiro, recepção, sucesso do cliente). Possuem habilidades variadas com tecnologia e são responsáveis por tarefas que apoiam tanto os advogados quanto os clientes.
* **Comportamentos e Fluxos de Trabalho Atuais:** O trabalho envolve muita entrada manual de dados no CRM, atendimento de primeiro contato com clientes (telefone, chats), agendamento, cobranças e organização de documentos. Frequentemente respondem às mesmas perguntas e gastam tempo buscando informações para os advogados.
* **Necessidades e Pontos de Dor:**
    * **Dor:** Tarefas repetitivas e de baixo valor, como cadastrar informações que já estão em um documento.
    * **Dor:** Interrupções constantes para responder a perguntas rotineiras de clientes.
    * **Necessidade:** Automatizar a captura de dados e a comunicação inicial para poderem focar em um suporte mais qualificado.
    * **Necessidade:** Ter acesso rápido a resumos e status de casos para informar os clientes de forma eficiente, como no monitoramento de um chatbot.
* **Objetivos:**
    * Reduzir o tempo gasto com tarefas administrativas e de entrada de dados.
    * Fornecer respostas mais rápidas e precisas aos clientes.
    * Apoiar a equipe de advogados de forma mais eficaz, antecipando suas necessidades de informação.

## Metas e Métricas de Sucesso

### Objetivos de Negócio
* Aumentar a capacidade operacional do escritório, permitindo que a mesma equipe gerencie um número maior de casos simultaneamente.
* Maximizar a lucratividade através da redução drástica do tempo (e custo) gasto em tarefas cognitivas manuais, como análise de documentos e redação.
* Estabelecer uma vantagem competitiva sustentável no mercado jurídico, posicionando o escritório como um pioneiro na adoção de IA.
* Melhorar a retenção de talentos e o bem-estar da equipe, reduzindo a sobrecarga de trabalho e a fadiga mental.

### Métricas de Sucesso do Usuário
* **Para Advogados:** Redução significativa no tempo gasto desde o recebimento de um novo caso até a produção dos primeiros insights e rascunhos de documentos.
* **Para a Equipe de Suporte:** Diminuição no tempo gasto com entrada manual de dados e na resposta a perguntas repetitivas de clientes.
* **Para Sócios-Gerentes:** Aumento visível na taxa de "casos por advogado" sem comprometer a qualidade do serviço ou aumentar as horas de trabalho.
* **Para Clientes Finais:** Recebimento de atualizações e informações de forma mais rápida, precisa e estruturada.

### Indicadores-Chave de Desempenho (KPIs)
* **Eficiência:** Redução do tempo médio para processar um lote de documentos de um novo caso (de horas para minutos).
* **Produtividade:** Aumento no número de peças processuais redigidas por advogado/mês.
* **Qualidade:** Redução na quantidade de erros ou omissões na análise inicial de documentos.
* **Satisfação do Cliente:** Aumento na pontuação de satisfação do cliente (medido via pesquisas ou feedback no portal).
* **Adoção:** Percentual de funcionários utilizando ativamente os agentes de IA em suas rotinas diárias.

## Escopo do MVP (Produto Mínimo Viável)

### Funcionalidades Principais (Inclusas no MVP)
* **Autenticação de Usuário Segura:** Sistema de login com autenticação de dois fatores (2FA).
* **Cadastro de Clientes e Documentos:** Funcionalidade para registrar dados pessoais do cliente (nome, CPF, data de nascimento). Cada arquivo PDF analisado receberá um **hash único baseado em seu conteúdo** para evitar duplicatas.
* **Painel de Controle Principal (Dashboard):** Uma interface inicial simples com ícones, permitindo o acesso aos agentes disponíveis.
* **Pipeline de Processamento de Documentos:** A funcionalidade completa de upload de documentos, incluindo a interface para o usuário classificar os arquivos como "simples" (digital) ou "complexos" (escaneado), e o processamento backend correspondente (Tesseract local ou API do Gemini).
* **Banco de Dados Vetorial com Acesso RAG:** Os documentos processados e suas informações extraídas serão armazenados em um banco de dados vetorial. Isso permitirá que os agentes acessem essas informações de forma inteligente via RAG (Retrieval-Augmented Generation), seguindo a filosofia de **"cadastrar uma vez, utilizar infinitas vezes"**.
* **Agente "Processador de PDFs":** O agente fundamental responsável pelo processamento e ingestão dos documentos no banco de dados vetorial.
* **Agente de "Redação de Quesitos Judiciais":** Um segundo agente que utilizará as informações do banco de dados vetorial para gerar rascunhos de quesitos para processos judiciais.

### Fora de Escopo para o MVP
* **Outros Agentes Autônomos:** Todos os demais agentes (Analisador de Laudos, Impugnador de Sentença, etc.) estão fora do escopo inicial.
* **Chatbot de Atendimento ao Cliente:** A funcionalidade de chatbot para interação com os clientes do escritório será desenvolvida em uma fase futura.
* **Configurações Avançadas da Interface:** Opções de personalização do painel (temas, layout, etc.) não estarão inclusas no MVP.
* **Suporte para Outros Empreendimentos:** O MVP será focado e otimizado exclusivamente para o fluxo de trabalho de escritórios de advocacia.

### Critérios de Sucesso do MVP
O MVP será considerado um sucesso se:
1.  Os usuários conseguirem processar documentos e receber dados estruturados em uma fração do tempo manual.
2.  O **Agente de Redação de Quesitos Judiciais conseguir usar as informações do banco de dados vetorial (via RAG) para produzir rascunhos relevantes e de alta qualidade**, validando o fluxo "cadastrar uma vez, utilizar múltiplas vezes".
3.  O feedback qualitativo dos usuários confirmar que o fluxo de trabalho integrado (processar e depois usar os dados com outro agente) é valioso e resolve uma dor significativa.

## Visão Pós-MVP

### Fase 2: Próximas Funcionalidades
Após o sucesso do MVP, a próxima fase se concentrará em expandir a biblioteca de Agentes Autônomos e aprimorar a interação com o cliente, incluindo:
* **Novos Agentes de Redação e Análise:** Introdução de agentes mais especializados, como o "Analisador de Documentação Médica", "Impugnador de Sentença Judicial" e "Impugnador de Laudo Pericial".
* **Chatbot de Atendimento ao Cliente:** Implementação do chatbot para ser monitorado pelas equipes de recepção e sucesso do cliente, automatizando a comunicação rotineira.
* **Configurabilidade da Interface:** Adição de opções para que os escritórios personalizem a aparência do painel de controle.

### Visão de Longo Prazo
A longo prazo, a plataforma evoluirá para se tornar o sistema nervoso central de inteligência para escritórios de advocacia. O objetivo é que cada funcionário, de estagiários a sócios, interaja com os agentes como "super-colaboradores", elevando a capacidade produtiva e a qualidade do trabalho de todo o escritório. A plataforma será sinônimo de advocacia de alta performance na era da IA.

### Oportunidades de Expansão
O core modular e a arquitetura de agentes foram projetados desde o início com a expansão em mente. Uma vez consolidado o modelo no setor jurídico, a maior oportunidade de expansão é adaptar a plataforma para outros setores de serviços profissionais que dependem de análise de documentos e conhecimento especializado, como consultorias, escritórios de contabilidade e clínicas médicas.

## Considerações Técnicas

### Requisitos da Plataforma
* **Plataformas-Alvo:** Aplicação web (SaaS), acessível através de navegadores modernos.
* **Hospedagem:** Servidor Privado Virtual (VPS) rodando GNU/Linux Ubuntu Server 24.x.
* **Requisitos de Servidor (Mínimo):** 4 vCPUs e 4 GB de RAM, com capacidade de escalonamento conforme a demanda. A infraestrutura não disporá de GPU dedicada.

### Preferências de Tecnologia
* **Linguagem:** Python.
* **Frontend:** niceGUI.
* **Backend (API):** FastAPI.
* **Banco de Dados:** PostgreSQL com a extensão pgvector.
* **Indexação e Orquestração de Dados:** Llama-Index.
* **Framework de Injeção de Dependência (Plugins):** python-dependency-injector.
* **Framework de Agentes Autônomos:** Agno.
* **Inteligência Artificial:** API do Google Gemini 2.5 Pro e Flash.
* **Filosofia de Licenciamento:** Preferência máxima por projetos de código aberto com licenças permissivas (MIT, Apache 2.0, etc.).

### Considerações de Arquitetura
* **Documento de Referência:** A arquitetura para a construção do **agente de processamento de PDFs será baseada exclusivamente** nos princípios e na estrutura detalhados no documento `estrutura-sparrow-para-agnos.md` fornecido. A arquitetura dos demais agentes será definida posteriormente.
* **Princípios Fundamentais (para o Agente de PDFs):** A implementação será guiada pelos seguintes princípios:
    * **Modularidade e Desacoplamento:** Cada responsabilidade funcional será encapsulada em seu próprio módulo.
    * **Processamento Assíncrono:** Operações de ingestão de PDFs utilizarão filas de tarefas (Celery + Redis) para não bloquear a API.
    * **API-First:** A API RESTful definida com FastAPI é o "contrato" central do sistema.
* **Fluxo de Dados (para o Agente de PDFs):** O agente será dividido em duas camadas principais: um "Pipeline de Ingestão de Documentos" assíncrono e uma "Camada de Agentes de Consulta" para interação.

## Restrições e Premissas

### Restrições
* **Orçamento:** Os custos diretos do projeto serão limitados aos de hospedagem do VPS e ao uso da API do Google Gemini. Todo o software utilizado será de código aberto.
* **Cronograma:** O MVP deve ser desenvolvido e implantado em um prazo máximo de 4 semanas.
* **Recursos da Equipe:** 1 desenvolvedor humano trabalhando em conjunto com um LLM como assistente de codificação ("super-coder").
* **Recursos Técnicos (Hardware):** A aplicação deve rodar em um servidor VPS com no mínimo 4 vCPUs e 4GB de RAM e sem GPU dedicada.
* **Recursos Técnicos (Software):** O dev-stack definido deve ser preservado. Novas bibliotecas só podem ser adicionadas se for estritamente necessário para: **reduzir a quantidade de código escrito, facilitar a leitura e manutenção, adicionar funcionalidades essenciais ou evitar problemas futuros comprovados.**

### Premissas-Chave
* **Viabilidade da API:** Estamos assumindo que a API do Google Gemini será performática, disponível e com um custo operacional que se encaixa no modelo de negócio.
* **Adoção pelo Usuário:** Assumimos que as equipes dos escritórios de advocacia estarão dispostas a adotar um novo fluxo de trabalho centrado em IA.
* **Classificação de Documentos:** A eficácia do pipeline depende da premissa de que os usuários conseguirão classificar corretamente os documentos.
* **Privacidade e Conformidade:** Assumimos que o envio de dados para a API do Google Gemini é uma abordagem aceitável. **(Premissa crítica a ser validada)**.
* **Integração Tecnológica:** Assumimos que as tecnologias de código aberto escolhidas podem ser integradas de forma coesa.

## Riscos e Decisões

### Riscos-Chave
* **Risco de Conformidade e Privacidade:** A premissa de que o uso da API do Gemini é aceitável para documentos jurídicos confidenciais é o maior risco do projeto.
* **Risco Técnico de Integração:** A complexidade da integração das tecnologias de ponta pode impactar o cronograma.
* **Risco de Dependência da API:** O modelo de negócio é fundamentalmente dependente da performance, preço e disponibilidade da API do Google Gemini.
* **Risco de Adoção pelo Usuário:** Existe o risco de que os usuários achem o processo de classificação de documentos muito trabalhoso.
* **Risco Operacional (Pós-MVP):** A falta de agentes de backup e monitoramento no MVP introduz um risco operacional que precisará ser priorizado logo após o lançamento inicial.

### Decisões sobre Questões Abertas
* **Consentimento:** Será obtido no ato da assinatura do contrato com o escritório de advocacia ou durante a conversa inicial no chat de onboarding.
* **Backup e Monitoramento do VPS:** Serão desenvolvidos como agentes específicos em uma fase pós-MVP.
* **Documentos Ileíveis:** Documentos que a API do Gemini não conseguir processar serão considerados ilegíveis para humanos e o sistema deverá solicitar a substituição ao usuário.
* **Pesquisa de Conformidade/Segurança:** A pesquisa sobre as implicações legais e de segurança foi considerada concluída e satisfatória pelo stakeholder do projeto.

## Próximos Passos

### Ações Imediatas
1.  **Aprovação do Briefing:** Com a sua aprovação final desta seção, consideraremos o Briefing do Projeto completo e aprovado.
2.  **Handoff para o Gerente de Produto (PM):** O próximo passo no framework BMad é entregar este briefing ao agente Gerente de Produto (PM). A função dele será usar este documento como base para criar o PRD (Documento de Requisitos do Produto), onde cada funcionalidade do MVP será detalhada em Épicos e Histórias de Usuário.
3.  **Início da Arquitetura:** Após a criação do PRD, o agente Arquiteto usará ambos os documentos para desenhar a arquitetura técnica detalhada do sistema, respeitando as diretrizes que você já estabeleceu.

### Handoff para o Gerente de Produto (PM)
Este Briefing de Projeto fornece o contexto completo para o sistema de agentes autônomos. Por favor, inicie o modo de "Geração de PRD", revise o briefing detalhadamente para trabalhar com o usuário na criação do PRD seção por seção, conforme o modelo indica, pedindo qualquer esclarecimento necessário ou sugerindo melhorias.
