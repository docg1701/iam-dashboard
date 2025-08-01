# MVP
    ## Principios
        - SaaS
        - Hospedagem VPS com deploy semi-automatizado
        - Servidor GNU/Linux (Ubuntu Server 24.x ou semelhante)
        - Containerização com docker e docker compose
        - Implementação single tenant (cada cliente terá sua própria cópia em seu próprio VPS)
        - Processamento 100% server-side
        - Segurança com autenticação em 2 fatores e criptografia.
        - Peças fundamentais: Frontend, Backend e Banco de Dados
        - Usar apenas bibliotecas e frameworks industry-standand
        - Usar python para tudo que for possível
        - Usar linguagens de frontend mais comuns e documentada da internet
        - Evitar ao máximo complexidades estruturais, logísticas e filosóficas
        - Manter tudo extremamente simples ao máximo para facilitar e acelerar o desenvolvimento, a escrita de testes e a refatoração do código
        - Core (frontend + backend) serve como agregador de links na forma de cards que apontam para aplicativos independentes
        - Aplicativos servidos pelo core são agentes autônomos que seguem os mesmos princípios visuais (mesmo tema), mas são contindos em seu próprio container docker e são desenvolvidos separadamente.
        - Aplicativos servidos pelo core tem acesso ao banco de dados do Core para buscar informações relevantes que servirão para a sua operação e usam o banco de dados para guardar as informações por eles geradas
        - Aplicativos servidos pelo dashboard: não alteram o funcionamento do Core e não modificam a estrutura do core.
        - Aplicativos precisam ler as tabelas do banco de dados servidos pelo Core e por outros aplicativos, porém não podem modificar essas tabelas.
        - Aplicativos precisam ter suas próprias tabelas, no banco de dados, com dados próprios de suas operações.
        - Cada aplicativo funciona completamente independente, o máximo que o aplicativo pode fazer é buscar informações no banco de dados disponível no Core e adicionar dados a sua própria tabela
        - No desenvolvimento de novos aplicativos, o desenvolvedor deve adaptar o funcionamento do Aplicativo à estrutura disponível do banco de dados do Core e não pode modificá-la, pois isso comprometeria o funcionamento dos outros Aplicativos
        - Os dados compartilhados entre Aplicativos devem ficar guardados em tabelas no banco de dados
        - Aplicação completamente responsiva e adaptada a telas de celular, tablet e desktop.
        - Exemplo de estrutura core + agentes (aplicativos)
            - Agente1: cadastra e gerencia clientes. Usuário preenche formulário que alimenta banco de dados. Os dados cadastrados ficam em uma tabela do Agente1.
            - Agente2: processa arquivos PDFs e guarda chuncks vetoriais em formato RAG. Para identificar os arquivos PDFs ele precisa acessar a tabela de clientes cadastrados e oferecer ao usuário uma lista selecionável desses clientes. O usuário seleciona 1 cliente e processa os PDFs. Na tabela do Agente2, há identificadores de qual cliente corresponde a quais arquivos PDF.
            - Agente3: faz análise e relatórios estruturados de documentação em PDF e envia para clientes. O usuário acessa a interface do agente, seleciona o cliente cadastrado pelo Agente1 e seleciona o tipo de relatório disponível para confecção. Os dados são buscados nas tabelas do Agente1 e do Agente2. O relatório é criado e armazenado na tabela do Agente3 com referências às tabelas dos outros agentes.
            - Agente4: faz gravação, transcrição e relatórios de audio de consultas de clientes. Ele grava o audio das consultas, processa e salva no banco de dados. O cliente a ser consultado está guardado na tabela do Agente1. Os documentos relevantes do cliente podem ou não existir na tabela do Agente2. Relatório estruturados dos documentos do cliente podem ou não existir em tabelas do Agente3. Tudo que o Agente4 processar e gerar ficará guardado na tabela do Agente4.
            - Se o sistema contratado pelo cliente não tiver o Agente4, isso não atrapalhará o funcionamento dos outros 3 agentes. Se o sistema não tiver o Agente3, o Agente4 funcionará perfeitamente. Se o Agente2 estiver ausente, os outros agentes ainda poderão funcionar, só não terão acesso a PDFs.
            - Nessa estrutura há um agente fundamental de gestão de clientes e todos os outros são independentes, ganhando funcionalidades com a adição de novos agentes, porém funcionando ainda de forma ordeira na ausência deles.
            - A limitação é que o Agente4 deverá analisar profundamente a estrutura de todos os outros agentes disponíveis para aproveitar ao máximo os recursos disponíveis e oferecidos pelos outros agentes.
            - É preciso estabelecer uma hierarquia explícita de dependência entre agentes e das funcionalidades que são adicionadas quando todos as dependências estão disponíveis
            - Mesmo com um regime de dependências, cada Agente deve funcionar apesar da ausência de qualquer outro. Exceção se faz a um grupo seletíssimo de Agentes fundamentais.        


    ## Fontend
        - Tela de login com logo, titulo, subtitulo, caixa de texto e botao
        - Acesso ao dashboard com links na forma de cards que levam para aplicações independentes
        - Interface de administração visivel após login e acessível apenas ao usuario sysadmin
        - Acesso a interface de administração feita através do clique de 1 botão ou link no frontend
        - Interface de administração cadastra novos usuários e verifica status do sistema
        - Interface de gestão de usuários acessível ao Administrador local (gestor da empresa): gerir o acesso dos usuários comuns aos Aplicativos disponíveis
        - Interface de gestão do próprio perfil: cada usuário pode modificar os dados de sua própria conta
        - Usuário tem nome, email, senha, autenticação 2FA, avatar, nível de acesso
        - Niveis de acesso: sysadmin (acesso total irrestrito e ao painel adminitrativo do SaaS); admin (acesso a todos os aplicativos e ao seu próprio cadastro); usuário-comum (acesso ao seu próprio perfil)
        - Acesso a interface de administração em 1 link, à gestão de usuários em outro link e à gestão do próprio perfil em outro link (ou clicando na foto do avatar)

    ## Backend
        - FastAPI, banco de dados etc.
        - Gestão dos cards no frontend é feita através de 1 arquivo de configuração e a interface de administração modifica esse arquivo de configuração
        - Todas as configurações do aplicativo devem ser guardadas em arquivos de configuração. As interfaces de gestão e administração são meios para modificar esses arquivos.
        - O frontend deve identificar falhas de sintaxe e erros de digitação nos arquivos de configuração emitindo logs e avisos em caso de edição manual que não deu certo. Isso evita que ações maliciosas sejam executadas a partir de arquivos de configuração.
        - Proxy reverso
       
    ## Aplicativos
        - 1 App de Gestão de Clientes: 
            - Cadastrar: nome, cpf e data de nascimento.
            - Funções: cadastrar, modificar, visualizar e deletar.
            - Implementar ações individuais e ações em massa (apagar múltiplas entradas, download em formato csv etc.)
            - Relatório sobre os dados armazenados: clica em um ou mais clientes, exporta um relatório que é um apanhado organizado de dados do cliente em csv.

    ## Estética
        - Implementar visual profissional a partir de temas para o frontend
        - Frontend deve aceitar temas configuráveis para que o SaaS tenha o formato white-label
        - Cada cliente poderá escolher seu tema: cores, tipografia, logomarca e ícones
        - Temas devem ser simples e baseados em tecnologia opensource
        - A temificação é fundamental, porém não deve consumir atenção demasiada
        - A identidade visual do cliente contratante do site deve ser transferida para o Frontend de uma forma extremamente simples
        - A estrutura visual do Frontend deve se manter e ser apenas levemente modificada para dar a sensação que é outro produto
        - A temificação não pode mudar drasticamente a estrutura do frontend, pois isso quebraria a visualização das aplicações, principalmente em ambiente responsivo (celular, tablet e desktop)

    ## Tech-Stack
        - FastAPI
        - PostgreSQL
        - pgvector
        - Agno: https://github.com/agno-agi/agno
        - NEXT.js: frontend (react + typescript)
        - shadcn/ui: temas
        - Caddy: proxy reverso
        - Celery
        - Redis
        - google-genai
        - Docker e docker compose
        - SQLModel no lugar do SQLAlchemy+Pydantic
        - Alembic
        - Pytest
        - asyncpg e asyncio
        - template full-stack
        - gunicorn (uvicorn)
        - OAuth2 e tokens JWT


