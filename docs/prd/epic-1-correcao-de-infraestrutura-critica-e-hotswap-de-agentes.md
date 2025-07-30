# Epic 1: Correção de Infraestrutura Crítica e Hotswap de Agentes

**Prioridade**: 🔴 CRÍTICA BLOQUEADORA  
**Duração**: 3 sprints (6 semanas)  
**Business Objective**: Transformar sistema 25% operacional em 100% funcional
**Success Metric**: Todas as funcionalidades críticas operacionais sem erros

**Contexto para Arquiteto**: Sistema possui base sólida (FastAPI + NiceGUI + PostgreSQL + Agno) mas falhas de implementação impedem operação. Arquitetura correta, execução incompleta.

**Contexto para UX Designer**: Interface funcionalmente adequada mas visualmente inadequada para segmento enterprise jurídico. Foco em profissionalização visual mantendo usabilidade.

## Story 1.1: Correção da Infraestrutura Core de Agentes
**Problema Identificado**: Sistema Agno não inicializado - Agentes definidos mas não registrados/inicializados
**Severidade**: 🔴 BLOQUEADOR ABSOLUTO  
**Impacto**: Processamento de documentos 0% funcional

**Implementação**:
- Corrigir inicialização do AgentManager no startup da aplicação
- Registrar PDFProcessorAgent com integração Gemini API
- Implementar health checks para monitoramento de agentes autônomos
- Configurar pipeline: Upload → Storage → Agent Processing → Vector Store

**Constraints Técnicos**:
- Apenas recursos nativos do Agno framework
- Integração via dependency injection nativo FastAPI
- Persistence usando SQLAlchemy AsyncSession

**Critérios de Aceitação**:
- [ ] AgentManager inicializa automaticamente no startup
- [ ] PDFProcessorAgent processa documentos em < 30 segundos
- [ ] Health check API retorna status de todos os agentes
- [ ] Logs mostram agent lifecycle events

**DoD**: Agentes processando documentos PDFs em tempo real com análise via Gemini API

## Story 1.2: Correção do Schema de Banco de Dados
**Problema Identificado**: Tabela `questionnaire_drafts` inexistente causando crashes no CRUD
**Severidade**: 🔴 BLOQUEADOR DE PRODUÇÃO  
**Impacto**: Exclusão de clientes falha com PostgreSQL error

**Implementação**:
- Executar migrações Alembic pendentes: `alembic upgrade head`
- Validar esquema completo contra models SQLAlchemy
- Implementar script de verificação de integridade do schema
- Corrigir relacionamentos cascade para deleção de entidades

**Constraints Técnicos**:
- Apenas recursos nativos SQLAlchemy 2.0 + Alembic
- Migrations seguindo padrões PostgreSQL
- ForeignKey constraints para integridade referencial

**Critérios de Aceitação**:
- [ ] Tabela `questionnaire_drafts` criada com schema correto
- [ ] CRUD de clientes funciona sem erros de banco
- [ ] Script de verificação valida 100% do schema
- [ ] Relacionamentos cascade funcionando corretamente

**DoD**: CRUD completo sem erros de banco, schema 100% consistente

## Story 1.3: Correção do Sistema de Autorização
**Problema Identificado**: Admin role configurado mas sem acesso - lógica de permissão quebrada
**Severidade**: 🔴 PROBLEMA DE SEGURANÇA  
**Impacto**: UserRole.SYSADMIN não consegue acessar `/admin`

**Implementação**:
- Corrigir verificação de roles em `app/core/auth.py`
- Implementar middleware de autorização nativo FastAPI
- Validar hierarquia de permissões (SYSADMIN > ADMIN > USER)
- Adicionar testes unitários para todas as permissões

**Constraints Técnicos**:
- Apenas decorators nativos FastAPI (`@requires_auth`)
- Dependency injection para user context
- Enum validation para UserRole

**Critérios de Aceitação**:
- [ ] UserRole.SYSADMIN acessa todas as rotas admin
- [ ] Middleware valida permissões em todas as requests
- [ ] Testes cobrem 100% dos cenários de autorização
- [ ] UI mostra/esconde elementos baseado em permissões

**DoD**: Admin acessando 100% das funcionalidades administrativas

## Story 1.4: Interface Administrativa Completa
**Problema Identificado**: 0% dos componentes admin especificados implementados
**Severidade**: 🔴 FEATURE CORE AUSENTE  
**Impacto**: Carlos (Admin) não consegue gerenciar sistema

**Implementação**:
- Agent Management Dashboard usando componentes NiceGUI nativos
- Security Center com audit logs e user management
- Performance Monitoring dashboard com métricas real-time
- User Management com 2FA reset e role assignment

**Constraints Técnicos**:
- Apenas componentes `ui.*` nativos do NiceGUI
- Classes Quasar para layout responsivo
- WebSockets nativos para updates real-time
- CSV export usando pandas + FastAPI Response

**Componentes Detalhados**:
```python
# Agent Management Panel
ui.card().classes('q-pa-md'):
    ui.label('Agent Status').classes('text-h6')
    ui.table(agents_data).classes('q-table--responsive')
    
# Performance Dashboard  
ui.grid().classes('row q-gutter-md'):
    ui.card().classes('col-xs-12 col-md-6'):
        ui.plotly(performance_chart)
```

**Critérios de Aceitação**:
- [ ] Dashboard admin acessível via `/admin` 
- [ ] Agent status cards mostram health em tempo real
- [ ] Security center permite gestão completa de usuários
- [ ] Performance monitoring com charts e métricas
- [ ] Audit logs com filtros e export

**DoD**: Interface admin 100% funcional conforme especificação original

## Story 1.5: Processador de PDFs Funcional
**Problema Identificado**: Feature core implementada como placeholder - "Funcionalidade em desenvolvimento"
**Severidade**: 🔴 FEATURE CRÍTICA AUSENTE  
**Impacto**: Dr. Ana não consegue processar documentos (job-to-be-done principal)

**Implementação**:
- Conectar PDFProcessorAgent existente à interface UI
- Implementar pipeline completo: Upload → PyMuPDF → pgvector → Gemini API
- Progress tracking usando WebSockets nativos FastAPI
- Interface de resultados com insights extraídos

**Constraints Técnicos**:
- PyMuPDF + PyTesseract nativos para extração de texto
- pgvector com índices HNSW para similarity search
- Google Gemini API oficial para análise de conteúdo
- NiceGUI file upload component nativo

**Pipeline Detalhado**:
```python
# Upload Flow
1. ui.upload() → temp storage
2. PDFProcessorAgent.process() → text extraction
3. Gemini embed_content() → vectors  
4. pgvector insert → similarity indexing
5. Gemini generate_content() → insights
6. UI update via WebSocket → results display
```

**Critérios de Aceitação**:
- [ ] PDF upload funciona via drag-and-drop
- [ ] Processamento completa em < 30 segundos
- [ ] Progress bar mostra etapas em tempo real
- [ ] Resultados exibem insights extraídos
- [ ] Vector search funciona para documentos similares

**DoD**: PDFs processados com embeddings vetoriais e análise IA completa

## Story 1.6: Correção da Responsividade Mobile
**Problema Identificado**: Sistema 100% quebrado em mobile/tablet - redireciona para login
**Severidade**: 🔴 BLOQUEADOR UX  
**Impacto**: Dr. Ana não consegue usar durante audiências (requisito crítico da persona)

**Implementação**:
- Corrigir gerenciamento de sessão em viewports menores
- Implementar breakpoints Quasar nativos (xs, sm, md, lg, xl)
- Validar UX completa em dispositivos móveis reais
- Otimizar layout para touch interaction

**Constraints Técnicos**:
- Classes responsivas nativas Quasar (col-*, row-*, q-*)
- Breakpoints system nativo NiceGUI
- Touch-friendly components (q-btn size="lg")
- CSS media queries apenas quando necessário

**Responsive Strategy**:
```python
# Adaptive Layout
ui.grid().classes('row q-gutter-md'):
    ui.card().classes('col-xs-12 col-sm-6 col-md-4')  # Responsive cards
    
# Mobile Navigation  
ui.drawer().classes('q-drawer--mobile'):
    ui.list()  # Touch-optimized menu
```

**Critérios de Aceitação**:
- [ ] Login mantém sessão em mobile/tablet
- [ ] Dashboard adapta layout para todos breakpoints  
- [ ] Touch interactions funcionam perfeitamente
- [ ] Performance mobile equivalent ao desktop
- [ ] Testes reais em iOS/Android dispositivos

**DoD**: Sistema 100% funcional mobile/tablet/desktop com UX otimizada