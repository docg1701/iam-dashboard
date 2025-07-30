# Product Requirements Document (PRD) - IAM Dashboard Brownfield Enhancement

**Versão**: 1.0  
**Data**: 29 de Julho de 2025  
**Autor**: John - Product Manager (BMad Method)  
**Projeto**: IAM Dashboard - Transformação para Arquitetura de Agentes Autônomos  

## 📋 Introdução e Análise do Projeto

### Contexto do Projeto

O IAM Dashboard é uma plataforma SaaS jurídica que oferece análise inteligente de documentos e geração automatizada de quesitos judiciais através de agentes de IA especializados. O projeto representa uma **transformação brownfield** de um sistema funcional existente para uma arquitetura de agentes autônomos intercambiáveis (hot-swappable).

### Diferencial Tecnológico Principal

A **arquitetura de agentes autônomos com capacidade de hot-swap** representa o core diferenciador do sistema, permitindo:
- Troca dinâmica de agentes especializados em tempo de execução
- Escalabilidade horizontal através de plugins de agentes
- Personalização extrema para diferentes áreas jurídicas
- Evolução contínua sem interrupção de serviço

### Análise de Mercado

**Mercado Total Addressable (TAM)**: R$ 2,3 bilhões (Setor Legal Tech brasileiro)
**Segmento Alvo**: Escritórios de advocacia de médio e grande porte (50-500 advogados)
**Oportunidade**: Digitalização de processos jurídicos tradicionais com IA

### Personas Validadas

#### Dr. Ana - Advogada Sênior (Persona Principal)
- **Profile**: 45 anos, 20 anos de experiência, especialista em direito trabalhista
- **Pain Points**: 
  - Análise manual de centenas de documentos médicos
  - Elaboração repetitiva de quesitos para perícias
  - Necessidade de acesso móvel durante audiências
- **Job-to-be-Done**: "Quero analisar documentos médicos e gerar quesitos automaticamente para focar no que realmente importa: a estratégia jurídica"

#### João - Advogado Associado (Persona Secundária)
- **Profile**: 28 anos, 5 anos de experiência, tech-savvy
- **Pain Points**: 
  - Sobrecarga de trabalho operacional
  - Dificuldade em manter qualidade consistente
  - Busca por ferramentas que aceleram produtividade
- **Job-to-be-Done**: "Quero uma ferramenta intuitiva que me permita produzir trabalho de alta qualidade rapidamente"

#### Carlos - Administrador de TI Jurídico (Persona Terciária)
- **Profile**: 35 anos, especialista em sistemas jurídicos
- **Pain Points**: 
  - Necessidade de controle granular sobre agentes de IA
  - Preocupações com segurança e auditoria
  - Demanda por monitoramento e performance
- **Job-to-be-Done**: "Quero gerenciar e monitorar uma plataforma de IA confiável e segura"

## 🎯 Requisitos Funcionais e Não-Funcionais

### Requisitos Funcionais Críticos

#### RF-001: Sistema de Agentes Autônomos com Hot-Swap
- **Descrição**: Capacidade de trocar agentes especializados dinamicamente sem interrupção de serviço
- **Critério de Aceitação**: 
  - Agentes podem ser substituídos em runtime sem downtime
  - Registry de agentes permite descoberta automática
  - Rollback automático em caso de falha do novo agente
- **Prioridade**: CRÍTICA
- **Persona**: Todas
- **Business Value**: Diferencial competitivo único no mercado Legal Tech
- **Contexto Técnico**: Core do sistema que permite personalização extrema

#### RF-002: Processamento Inteligente de PDFs
- **Descrição**: Análise automática de documentos médicos usando IA com extração de insights relevantes
- **Critério de Aceitação**:
  - Upload via drag-and-drop ou seleção de arquivos
  - Processamento < 30 segundos para documentos até 50MB
  - Extração de texto com OCR para documentos digitalizados
  - Identificação automática de entidades médicas (doenças, sintomas, medicamentos)
  - Geração de resumo executivo com pontos-chave
  - Classificação de relevância para perícias trabalhistas
- **Prioridade**: CRÍTICA
- **Persona**: Dr. Ana (job-to-be-done principal)
- **Business Value**: ROI direto - redução 80% tempo análise vs processo manual
- **Contexto de Uso**: Dr. Ana processa 50-100 laudos médicos por semana

#### RF-003: Geração Automatizada de Quesitos
- **Descrição**: Criação de questionários periciais personalizados baseados no contexto dos documentos
- **Critério de Aceitação**:
  - Interface wizard de 3 etapas (cliente, contexto, geração)
  - Seleção de cliente com documentos já processados
  - Campos contextuais: profissão, doença, data do incidente, data médica
  - Geração de 15-25 quesitos específicos em < 10 segundos
  - Preview com opção de edição antes de finalizar
  - Export em DOCX formatado para petições
  - Histórico de quesitos gerados por cliente
- **Prioridade**: CRÍTICA
- **Persona**: Dr. Ana (principal), João (secundária)
- **Business Value**: Eliminação trabalho repetitivo, qualidade consistente
- **Contexto de Uso**: Cada caso requer 1-3 conjuntos de quesitos customizados

#### RF-004: Interface Administrativa Enterprise
- **Descrição**: Dashboard completo para gerenciamento de agentes, usuários e monitoramento
- **Critério de Aceitação**:
  - Agent Management: status, configuração, logs, métricas de performance
  - User Management: CRUD usuários, controle de roles, reset 2FA
  - Security Center: audit logs, tentativas de login, sessões ativas
  - Performance Monitoring: métricas em tempo real, alertas, dashboards
  - System Health: uptime, resource usage, database status
  - Export/Import: configurações, logs, relatórios
- **Prioridade**: ALTA
- **Persona**: Carlos (Administrador de TI)
- **Business Value**: Operação enterprise-grade, compliance e governança
- **Contexto de Uso**: Acesso diário para monitoramento, configuração semanal

#### RF-005: Sistema de Autenticação e 2FA Obrigatório + RBAC Fixes
- **Descrição**: Segurança robusta com autenticação multi-fator e correção crítica do sistema de autorização
- **Problema Crítico Identificado**: UserRole.SYSADMIN não consegue acessar endpoints `/admin` - lógica de permissão quebrada
- **Critério de Aceitação**:
  - Login com email/senha + TOTP obrigatório
  - QR Code setup para Google Authenticator/Authy
  - Backup codes para recuperação
  - **CRITICAL FIX**: UserRole.SYSADMIN acessa 100% dos endpoints admin
  - **CRITICAL FIX**: Middleware de autorização valida permissões corretamente
  - **CRITICAL FIX**: Hierarquia de permissões (SYSADMIN > ADMIN > USER) funcionando
  - Sessões com timeout configurável (padrão: 8 horas)
  - Logout automático por inatividade
  - Tentativas de login limitadas (5 tentativas/15min)
  - Logs de acesso completos
- **Implementação de Correção RBAC**:
```python
# app/core/auth.py - CRITICAL AUTHORIZATION FIXES
class RoleBasedAccessManager:
    def __init__(self):
        self.role_permissions = {
            UserRole.SYSADMIN: {
                "admin_panel": ["full_access"],  # CRITICAL FIX
                "agent_management": ["create", "delete", "configure", "hot_deploy", "execute", "monitor"],
                "user_management": ["create", "read", "update", "delete", "manage"],
                "system_admin": ["full_access"]
            },
            UserRole.ADMIN_USER: {
                "agent_management": ["execute", "monitor"],
                "user_management": ["read", "update"],
                "admin_panel": ["limited_access"]
            },
            UserRole.COMMON_USER: {
                "agent_management": ["execute"],
                "admin_panel": ["no_access"]
            }
        }
    
    async def check_endpoint_access(self, user_role: UserRole, endpoint_path: str) -> bool:
        """Authorization middleware implementation - FIXED"""
        endpoint_mappings = {
            "/admin": [UserRole.SYSADMIN],  # CRITICAL FIX
            "/admin/users": [UserRole.SYSADMIN],
            "/admin/system": [UserRole.SYSADMIN],
            "/admin/agents": [UserRole.SYSADMIN, UserRole.ADMIN_USER],
            "/api/agents/create": [UserRole.SYSADMIN],
            "/api/agents/*/configure": [UserRole.SYSADMIN],
            "/api/agents/*/hot-deploy": [UserRole.SYSADMIN]
        }
        
        # Direct endpoint match
        if endpoint_path in endpoint_mappings:
            return user_role in endpoint_mappings[endpoint_path]
        
        # Pattern matching for dynamic endpoints
        for pattern, allowed_roles in endpoint_mappings.items():
            if self._match_endpoint_pattern(pattern, endpoint_path):
                return user_role in allowed_roles
        
        return False
```
- **Prioridade**: CRÍTICA (BLOQUEADOR)
- **Persona**: Carlos (Administrador) - não consegue acessar funcionalidades admin
- **Business Value**: Compliance com LGPD e normas OAB + Carlos pode gerenciar sistema
- **Contexto de Uso**: Login diário, setup 2FA uma vez por dispositivo, Carlos acessa admin diariamente

#### RF-006: Gerenciamento de Clientes e Casos
- **Descrição**: CRUD completo para entidades jurídicas com relacionamentos entre clientes, documentos e quesitos
- **Critério de Aceitação**:
  - Cadastro completo: nome, CPF, email, telefone, endereço
  - Upload múltiplo de documentos por cliente
  - Organização por casos/processos
  - Busca e filtros avançados
  - Timeline de atividades por cliente
  - Status tracking (ativo, arquivado, suspenso)
  - Export de dados em CSV/PDF
- **Prioridade**: ALTA
- **Persona**: Dr. Ana, João
- **Business Value**: Organização e controle operacional
- **Contexto de Uso**: 10-50 novos clientes por mês, consulta diária

#### RF-007: Sistema de Notificações Real-time
- **Descrição**: Feedback imediato sobre processamento, status e eventos do sistema
- **Critério de Aceitação**:
  - Notificações toast para ações completadas/falhadas
  - Progress indicators durante processamento de documentos
  - Alertas de sistema (falhas, manutenção, atualizações)
  - Centro de notificações com histórico
  - Configuração de preferências por usuário
  - Notificações push para mobile (futuro)
- **Prioridade**: MÉDIA
- **Persona**: Todas
- **Business Value**: UX profissional, redução de incerteza
- **Contexto de Uso**: Feedback contínuo durante uso do sistema

#### RF-008: Search e Filtros Avançados
- **Descrição**: Busca semântica em documentos processados usando embeddings vetoriais
- **Critério de Aceitação**:
  - Busca por texto livre com resultados rankeados por relevância
  - Filtros por cliente, data, tipo de documento, status
  - Busca semântica: "casos similares", "sintomas parecidos"
  - Suggestions automáticas baseadas em histórico
  - Export de resultados de busca
  - Busca salva e alertas de novos matches
- **Prioridade**: MÉDIA
- **Persona**: Dr. Ana, João
- **Business Value**: Reutilização de conhecimento, precedentes
- **Contexto de Uso**: 5-10 buscas por dia durante análise de casos

### Requisitos Não-Funcionais Detalhados

#### RNF-001: Performance e Tempo de Resposta
- **Processamento de PDF**: < 30 segundos por documento (até 50MB)
- **Geração de quesitos**: < 10 segundos para 15-25 quesitos
- **Tempo de resposta UI**: < 2 segundos para 95% das interações
- **Uptime**: 99.5% SLA (máximo 3.65 horas downtime/mês)
- **First Contentful Paint**: < 1.5 segundos
- **Time to Interactive**: < 3 segundos
- **Vector Search**: < 500ms para busca semântica
- **Agent Response Time**: < 5 segundos para consultas simples
- **Justificativa**: Dr. Ana precisa de respostas rápidas durante audiências e consultas

#### RNF-002: Escalabilidade e Capacidade
- **Usuários concorrentes**: até 100 (baseline), 300 (target)
- **Documentos por hora**: até 500 (processamento simultâneo)
- **Agentes simultâneos**: até 10 por instância
- **Storage**: até 1TB de documentos (crescimento 100GB/mês)
- **Database**: até 1M registros de clientes/documentos
- **API Rate Limit**: 1000 requests/min por usuário
- **Growth Capacity**: 300% sem reengenharia de arquitetura
- **Justificativa**: Escritórios alvo crescem 20-30% ao ano

#### RNF-003: Segurança e Compliance
- **Criptografia**: TLS 1.3 para comunicação, AES-256 at-rest
- **Autenticação**: JWT + 2FA obrigatório (TOTP)
- **Dados**: Criptografia at-rest para todos os documentos
- **Auditoria**: Log completo de todas as ações com timestamp
- **Session Management**: Timeout configurável, logout automático
- **Rate Limiting**: Proteção contra brute force e DDoS
- **Data Retention**: Configurável por cliente (padrão: 5 anos)
- **LGPD Compliance**: Right to be forgotten, portability, consent
- **Backup & Recovery**: RTO 4 horas, RPO 1 hora
- **Justificativa**: Dados jurídicos são altamente sensíveis e regulamentados

#### RNF-004: Usabilidade e Experiência
- **Responsividade**: Suporte completo mobile/tablet/desktop
- **Acessibilidade**: WCAG 2.1 Level AA (contraste, keyboard nav)
- **Internacionalização**: Português brasileiro nativo
- **Learning Curve**: Zero treinamento para tarefas básicas
- **Error Recovery**: Mensagens claras com ações corretivas
- **Offline Capability**: Cache local para funcionalidades críticas
- **Browser Support**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile Performance**: Equivalente ao desktop em funcionalidade
- **Justificativa**: Advogados têm pouco tempo para aprender novas ferramentas

#### RNF-005: Confiabilidade e Disponibilidade
- **Uptime**: 99.5% SLA com monitoramento 24/7
- **Error Handling**: Graceful degradation sem perda de dados
- **Data Consistency**: ACID transactions para operações críticas
- **Backup Strategy**: Incremental diário, full semanal
- **Disaster Recovery**: Site secundário com sincronização
- **Monitoring**: Alertas proativos para métricas críticas
- **Health Checks**: Endpoints para verificação automática
- **Circuit Breakers**: Proteção contra cascading failures
- **Justificativa**: Sistema crítico para operação diária dos escritórios

#### RNF-006: Integrabilidade e Extensibilidade
- **APIs**: RESTful with OpenAPI 3.0 documentation
- **Webhooks**: Notificações de eventos para sistemas externos
- **Export Formats**: PDF, DOCX, CSV, JSON
- **Import Formats**: PDF, DOC/DOCX, TXT, XML
- **Agent Plugin System**: Hot-swappable agents via registry
- **Configuration**: Environment-based config management
- **Logging**: Structured logs (JSON) with correlation IDs
- **Monitoring**: OpenTelemetry/Prometheus integration ready
- **Justificativa**: Escritórios usam múltiplas ferramentas que precisam se integrar

#### RNF-007: Operabilidade e Manutenibilidade
- **Deployment**: Blue-green deployment com zero downtime
- **Configuration**: Hot reload para mudanças não-críticas
- **Database Migrations**: Reversible migrations com Alembic
- **Log Management**: Centralized logging com retention policy
- **Performance Monitoring**: APM com alerts automáticos
- **Resource Usage**: CPU < 70%, Memory < 80%, Disk < 85%
- **Dependency Management**: Automated security updates
- **Documentation**: Auto-generated API docs e user manuals
- **Justificativa**: Sistema deve ser mantido por equipe pequena de TI

#### RNF-008: Localização e Regionalização
- **Idioma**: Português brasileiro como idioma nativo
- **Timezone**: America/Sao_Paulo como padrão
- **Currency**: Real (BRL) para funcionalidades financeiras futuras
- **Date/Time Format**: dd/mm/yyyy, HH:mm (padrão brasileiro)
- **Legal Compliance**: Código Civil, CLT, normas OAB
- **Document Templates**: Formato oficial brasileiro (petições, etc.)
- **CPF/CNPJ Validation**: Algoritmos nativos de validação
- **Address Format**: CEP, estados, municípios brasileiros
- **Justificativa**: Produto focado exclusivamente no mercado brasileiro

## 🎨 Objetivos de Aprimoramento da Interface do Usuário

### Estratégia de Design

**Princípio Central**: "Professional Trust Through Native Elegance"
- Utilizar apenas capacidades nativas dos frameworks para garantir estabilidade
- Atingir qualidade visual profissional (7-8/10) sem customizações excessivas
- Manter simplicidade e confiabilidade acima de features visuais complexas

### Mobile-First Responsive Implementation Strategy

**CRITICAL ISSUE IDENTIFIED**: Sistema completamente quebrado em mobile/tablet - redireciona para login infinitamente, impedindo Dr. Ana de usar durante audiências (requisito crítico da persona).

#### Dr. Ana Mobile Workflow Requirements
- **Court Hearing Access Scenarios**: Sistema deve funcionar perfeitamente em viewport mínimo de 375px
- **PDF Viewing and Annotation on Mobile**: Capacidade de visualizar e anotar documentos durante apresentações
- **Client Data Access During Presentations**: Acesso rápido a informações de clientes durante reuniões
- **Offline Capability for Critical Functions**: Funcionalidades essenciais devem funcionar sem conectividade

#### Viewport-Specific Session Management
```python
# Correção crítica para gerenciamento de sessão mobile
class MobileSessionManager:
    def __init__(self):
        self.mobile_breakpoints = [375, 414, 768]  # iPhone, Android, tablet
        self.session_persistence = {}
    
    async def handle_viewport_change(self, user_id, viewport_width):
        # Authentication persistence across viewport changes
        if viewport_width in self.mobile_breakpoints:
            await self.ensure_mobile_session_valid(user_id)
            await self.optimize_mobile_layout(viewport_width)
        
        # Session validation for mobile/tablet breakpoints
        current_session = await self.get_session(user_id)
        if current_session and self.is_mobile_viewport(viewport_width):
            await self.extend_mobile_session(user_id)
    
    async def prevent_mobile_login_loops(self, request):
        # CRITICAL FIX: Detectar loops de login mobile
        if self.is_mobile_request(request) and self.has_valid_session(request):
            return await self.redirect_to_dashboard()
        return await self.standard_auth_flow(request)
```

#### Touch-Optimized Interaction Patterns
- **Minimum Touch Targets**: 44px mínimo para todos elementos interativos
- **Swipe Gestures**: Navegação horizontal entre painéis de agentes
- **Pull-to-Refresh**: Atualização de status de documentos com padrões mobile nativos
- **Long Press Actions**: Menus contextuais para ações avançadas

#### Mobile-Specific Navigation Patterns
```css
/* Mobile navigation pattern fixes */
@media (max-width: 768px) {
  .desktop-sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .mobile-drawer {
    position: fixed;
    top: 0;
    left: 0;
    width: 80vw;
    height: 100vh;
    z-index: 1000;
  }
  
  .mobile-bottom-nav {
    position: fixed;
    bottom: 0;
    width: 100%;
    height: 60px;
    background: var(--q-primary);
  }
}
```

### Objetivos Específicos de UI/UX (Updated)

#### Objetivo 1: Mobile-First Responsive Recovery (CRÍTICO)
- **Meta**: Sistema 100% funcional em dispositivos mobile (atualmente 0%)
- **Problema Crítico**: Dr. Ana não consegue usar durante audiências - sistema quebra completamente
- **Solução**: Implementar breakpoints nativos Quasar com sessão mobile corrigida
- **Success Criteria**: Dr. Ana completa workflow completo em iPhone 375px viewport

#### Objetivo 2: Professional Visual Design System (ALTA PRIORIDADE)
- **Meta**: Elevar de 2/10 para 7+/10 em qualidade visual profissional
- **Problema Atual**: Interface "feia e quadrada" inadequada para clientes enterprise
- **Solução**: Design system profissional baseado em Material Design nativo
- **Success Criteria**: Interface recebe rating 7+/10 de stakeholders jurídicos

#### Objetivo 3: Agent-UI Integration Patterns (CRÍTICO)
- **Meta**: Substituir placeholders por funcionalidade real conectada a agentes
- **Problema Atual**: PDF Processor mostra "Funcionalidade em desenvolvimento"
- **Solução**: Implementar conexões WebSocket real-time com backend de agentes
- **Success Criteria**: Todas funcionalidades conectadas com dados reais, zero placeholders

### Especificações Visuais Nativas

#### Paleta de Cores (Quasar Material Design)
```css
:root {
  --q-primary: #2563EB;      /* Azul confiável e profissional */
  --q-secondary: #10B981;    /* Verde para ações positivas */
  --q-accent: #F59E0B;       /* Amarelo para alertas */
  --q-positive: #059669;     /* Verde para sucessos */
  --q-negative: #DC2626;     /* Vermelho para erros */
  --q-info: #0EA5E9;         /* Azul para informações */
  --q-warning: #D97706;      /* Laranja para avisos */
}
```

#### Componentes Nativos
- **Cards**: `q-card` com elevação sutil e sombras nativas
- **Botões**: `q-btn` com estados hover/active/disabled nativos
- **Formulários**: `q-input` com labels flutuantes e validação
- **Navegação**: `q-tabs` e `q-drawer` para estrutura clara
- **Feedback**: `q-notify` para todas as interações do sistema

#### Sistema de Grid Responsivo
```javascript
// Breakpoints nativos Quasar
breakpoints: {
  xs: 0,      // Mobile portrait
  sm: 600,    // Mobile landscape
  md: 1024,   // Tablet
  lg: 1440,   // Desktop
  xl: 1920    // Large desktop
}
```

### Padrões de Interação

#### Micro-interações Nativas
- **Hover Effects**: Transições CSS nativas (0.3s ease)
- **Loading States**: `q-spinner` e skeletons nativos
- **Feedback Visual**: `q-tooltip` e `q-badge` para indicações
- **Animações**: Apenas transições CSS nativas do Quasar

#### Estados de Interface
- **Empty States**: Ilustrações simples com call-to-action claro
- **Error States**: Mensagens claras com ações de recuperação
- **Success States**: Confirmações visuais com próximos passos
- **Loading States**: Indicadores de progresso contextuais

## 🏗️ Revisão da Arquitetura Técnica para Aprimoramentos de UI

### Agent System Initialization Strategy

**CRITICAL IMPLEMENTATION REQUIREMENT**: Sistema Agno nunca inicializado no startup da aplicação - agentes definidos mas não registrados/inicializados.

#### Startup Sequence Specification
```python
# app/main.py - CRITICAL STARTUP FIXES
async def create_application() -> FastAPI:
    container = ApplicationContainer()
    container.wire(modules=[__name__])
    
    app = FastAPI(title="IAM Dashboard", version="1.0.0")
    
    # CRITICAL FIXES - Missing initialization sequence:
    create_tables()  # Initialize database tables
    await initialize_agent_system()  # START AGENT SYSTEM
    await activate_authentication_system()  # Activate auth
    
    # Include ALL API routers (agent router was missing)
    app.include_router(auth_router, prefix="/api/auth")
    app.include_router(user_router, prefix="/api/users") 
    app.include_router(client_router, prefix="/api/clients")
    app.include_router(agent_router, prefix="/api/agents")  # MISSING
    app.include_router(document_router, prefix="/api/documents")
    
    setup_ui_routes(app)
    return app

async def initialize_agent_system():
    """Complete agent system initialization sequence."""
    from app.core.agent_manager import agent_manager
    from app.agents.pdf_processor_agent import PDFProcessorAgent
    from app.agents.questionnaire_writer_agent import QuestionnaireWriterAgent
    
    # Agent registration order and dependencies
    await agent_manager.register_agent_type("pdf_processor", PDFProcessorAgent)
    await agent_manager.register_agent_type("questionnaire_writer", QuestionnaireWriterAgent)
    
    # Create default agent instances
    await agent_manager.create_agent("pdf_processor", "default_pdf_processor")
    await agent_manager.create_agent("questionnaire_writer", "default_questionnaire_writer")
    
    # Health check procedures for initialized agents
    for agent_id in ["default_pdf_processor", "default_questionnaire_writer"]:
        agent = await agent_manager.get_agent(agent_id)
        if not await agent.health_check():
            raise AgentInitializationError(f"Agent {agent_id} failed startup health check")
```

#### Agent Lifecycle Management
```python
class AgentLifecycleManager:
    """Agent state management (STARTING → RUNNING → STOPPING)."""
    
    async def setup_health_monitoring(self):
        """Health monitoring and automatic restart procedures."""
        async def monitor_agents():
            while True:
                for agent_id in agent_manager.get_active_agents():
                    agent = await agent_manager.get_agent(agent_id)
                    if not await agent.health_check():
                        await self._recover_failed_agent(agent_id)
                await asyncio.sleep(30)
        
        asyncio.create_task(monitor_agents())
    
    async def _recover_failed_agent(self, agent_id: str):
        """Agent failure isolation and recovery."""
        try:
            await agent_manager.stop_agent(agent_id)
            await asyncio.sleep(5)  # Backoff
            await agent_manager.restart_agent(agent_id)
            
            agent = await agent_manager.get_agent(agent_id)
            if await agent.health_check():
                logger.info(f"Successfully recovered agent: {agent_id}")
        except Exception as e:
            logger.error(f"Agent recovery failed for {agent_id}: {str(e)}")
```

#### Error Handling for Agent Startup Failures
- **Graceful Degradation**: Se agentes falham no startup, sistema roda em modo degradado
- **Recovery Procedures**: Restart automático com backoff exponencial
- **User Communication**: Notificações claras sobre agentes indisponíveis
- **Fallback Workflows**: Processamento manual quando agentes não estão disponíveis

### Database Schema Completeness Strategy

**CRITICAL IMPLEMENTATION REQUIREMENT**: Tabela `questionnaire_drafts` inexistente causando crashes no CRUD.

#### Missing Table Resolution
```sql
-- CRITICAL FIX: Create missing questionnaire_drafts table
CREATE TABLE IF NOT EXISTS questionnaire_drafts (
    draft_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_type VARCHAR(100) NOT NULL,
    draft_content JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_questionnaire_drafts_client_id 
ON questionnaire_drafts(client_id);

CREATE INDEX IF NOT EXISTS idx_questionnaire_drafts_user_id 
ON questionnaire_drafts(user_id);
```

#### Startup Database Validation
```python
class StartupDatabaseValidator:
    """Automatic schema completeness check and validation."""
    
    async def validate_database_startup(self):
        # Detect missing tables
        missing_tables = await self._detect_missing_tables()
        if missing_tables:
            await self._create_missing_tables(missing_tables)
        
        # Validate foreign key constraints
        await self._validate_foreign_keys()
        
        # Verify migration status
        await self._verify_migration_status()
    
    async def _detect_missing_tables(self) -> list[str]:
        expected_tables = [
            "users", "clients", "agent_executions", "processed_documents",
            "questionnaire_drafts", "user_sessions", "audit_logs"
        ]
        
        missing_tables = []
        async with get_async_db() as db:
            for table in expected_tables:
                result = await db.execute(
                    text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table)"),
                    {"table": table}
                )
                if not result.scalar():
                    missing_tables.append(table)
        
        return missing_tables
```

### Arquitetura Atual Validada (Updated)

#### Stack Tecnológico (Verificado via MCP Context7)
- **Backend**: Python 3.12 + FastAPI (dependency injection, WebSockets, async)
- **Frontend**: NiceGUI com Vue/Quasar nativo
- **Database**: PostgreSQL + pgvector (embeddings, índices HNSW/IVFFlat)
- **AI/ML**: Google Gemini API (text generation, embeddings, chat, streaming)
- **Agents**: Agno framework (autonomous agents, reasoning, memory) - **REQUER INICIALIZAÇÃO**

#### Capacidades Nativas Confirmadas

**FastAPI**:
- Dependency injection system nativo
- WebSocket support para real-time updates
- Middleware system para autenticação
- Background tasks para processamento async

**SQLAlchemy 2.0**:
- AsyncSession para operações não-bloqueantes
- ORM patterns modernos com type hints
- Relacionamentos com lazy/eager loading
- Migrations via Alembic

**NiceGUI + Quasar**:
- Material Design components nativos
- Sistema de temas CSS variables
- Classes responsivas (xs, sm, md, lg, xl)
- Dark/light mode nativo
- Eventos de UI reativos

**pgvector**:
- Similarity search com operadores nativos (<->, <#>, <=>)
- Índices de performance (HNSW, IVFFlat)
- Integração nativa com SQLAlchemy

**Google Gemini API**:
- Text generation com streaming
- Content embeddings para vector search
- Chat sessions com histórico
- Multimodal support (text + images)

### Restrições de Implementação (Constraints Nativos)

#### Princípio de Estabilidade
**CRÍTICO**: Todas as customizações devem se manter dentro das capacidades nativas dos frameworks para garantir compatibilidade com updates futuros.

#### Constraints por Framework

**NiceGUI**:
- ✅ Usar apenas componentes `ui.*` nativos
- ✅ CSS customization via classes Quasar nativas
- ❌ NÃO criar componentes JavaScript customizados
- ❌ NÃO modificar comportamentos core do framework

**Quasar**:
- ✅ Temas baseados em CSS variables nativas
- ✅ Classes responsivas q-*, col-*, row-*
- ✅ Componentes q-* com props nativas
- ❌ NÃO modificar SCSS variables do Quasar core

**FastAPI**:
- ✅ Dependency injection system nativo
- ✅ Middleware stack padrão
- ✅ Background tasks e WebSockets nativos
- ❌ NÃO modificar comportamento core do ASGI

**SQLAlchemy**:
- ✅ AsyncSession e ORM patterns padrão
- ✅ Relacionamentos e migrations nativas
- ❌ NÃO criar SQL customizado complexo onde ORM resolve

#### Validação de Feasibilidade

**Qualidade Visual 7-8/10**: ✅ POSSÍVEL
- Material Design nativo oferece aparência profissional
- CSS variables permitem customização suficiente
- Micro-interações via transições CSS nativas

**Performance Requirements**: ✅ ATENDÍVEL
- AsyncSession + background tasks para I/O não-bloqueante
- WebSockets nativos para updates em tempo real
- pgvector índices para searches sub-segundo

**Hot-swappable Agents**: ✅ IMPLEMENTÁVEL
- Agno framework suporta dynamic agent loading
- FastAPI dependency injection para runtime swapping
- PostgreSQL para agent state persistence

## 🚧 Restrições Técnicas (Apenas Capacidades Nativas)

### Filosofia de Constraints

**Princípio Fundamental**: "Stability Over Features"

A transformação brownfield deve priorizar **estabilidade e maintainability** sobre customizações excessivas. Todos os aprimoramentos devem utilizar exclusivamente capacidades nativas dos frameworks escolhidos.

### Constraints por Camada

#### Frontend - NiceGUI + Quasar
**PERMITIDO**:
- Componentes `ui.button`, `ui.card`, `ui.input`, etc. com props nativas
- Classes CSS Quasar: `q-*`, `col-*`, `row-*`, `text-*`, `bg-*`
- CSS variables para temas: `--q-primary`, `--q-secondary`, etc.
- Transições CSS nativas: `transition`, `transform`, `opacity`
- Responsive breakpoints: `xs`, `sm`, `md`, `lg`, `xl`

**PROIBIDO**:
- JavaScript customizado ou bibliotecas externas de UI
- Modificação de componentes Quasar core
- CSS que sobrescreve comportamentos fundamentais
- Frameworks CSS adicionais (Bootstrap, Tailwind, etc.)

#### Backend - FastAPI + SQLAlchemy
**PERMITIDO**:
- Dependency injection nativo: `Depends()`, `@inject`
- Middleware stack padrão: `@app.middleware("http")`
- Background tasks: `BackgroundTasks`, `asyncio.create_task()`
- WebSockets nativos: `@app.websocket()`
- ORM relationships: `relationship()`, `foreign_key()`
- Async patterns: `AsyncSession`, `async def`, `await`

**PROIBIDO**:
- ORMs alternativos ou query builders customizados
- Modifications core do FastAPI request/response cycle
- Bibliotecas de validação que não sejam Pydantic nativo
- Event systems que não sejam os nativos do FastAPI

#### Database - PostgreSQL + pgvector
**PERMITIDO**:
- Operadores de similaridade nativos: `<->`, `<#>`, `<=>`
- Índices de performance: `HNSW`, `IVFFlat`
- SQL DDL padrão para schemas e constraints
- Triggers e functions PostgreSQL nativas
- JSON/JSONB para metadata flexível

**PROIBIDO**:
- Extensions PostgreSQL não-padrão além do pgvector
- Stored procedures complexas que quebrem portabilidade
- SQL raw que bypass completamente o ORM
- Databases adicionais para casos específicos

#### AI/ML - Google Gemini API
**PERMITIDO**:
- Client SDK oficial: `google.genai.Client`
- API calls nativas: `generate_content`, `embed_content`
- Streaming responses: `generate_content_stream`
- Chat sessions: `chats.create()`, `send_message()`
- Configuration nativa: `GenerateContentConfig`, `types.*`

**PROIBIDO**:
- Wrappers customizados que escondam funcionalidades nativas
- Integrações com outros LLM providers sem abstração clara
- Pre/post-processing que modifique significativamente inputs/outputs
- Caching layers complexos que não sejam os nativos

#### Agents - Agno Framework
**PERMITIDO**:
- Agent classes nativas: `Agent`, `Tool`, `Memory`
- Plugin system nativo para hot-swappable agents
- Agent communication via message passing nativo
- State persistence usando SQLite/PostgreSQL nativo
- Reasoning patterns suportados pelo framework

**PROIBIDO**:
- Frameworks de agents alternativos (LangChain, CrewAI, etc.)
- Modifications no core reasoning engine
- Custom tool implementations que não sigam patterns Agno
- Agent orchestration systems externos

### Justificativa das Constraints

#### Estabilidade a Longo Prazo
- **Framework Updates**: Compatibilidade garantida com updates de NiceGUI, FastAPI, etc.
- **Security Patches**: Aplicação automática sem quebrar customizações
- **Performance**: Otimizações dos frameworks beneficiam o sistema automaticamente

#### Maintainability
- **Developer Onboarding**: Conhecimento padrão dos frameworks é suficiente
- **Bug Tracking**: Issues rastreáveis até documentação oficial
- **Community Support**: Soluções disponíveis na comunidade padrão

#### Business Continuity
- **Vendor Lock-in**: Reduzido ao mínimo com tecnologias open-source
- **Technical Debt**: Prevenção de acúmulo através de padrões estabelecidos
- **Scaling**: Patterns nativos suportam crescimento natural

### Validação de Compliance

#### Processo de Review
1. **Design Review**: Toda feature deve demonstrar uso apenas de capacidades nativas
2. **Code Review**: Checklist específico para compliance com constraints
3. **Testing**: Testes devem validar comportamento usando apenas APIs nativas
4. **Documentation**: Mapeamento de cada escolha técnica para capacidade nativa

#### Métricas de Sucesso
- **0% Custom JavaScript**: Toda funcionalidade via NiceGUI nativo
- **0% CSS Hacks**: Apenas classes Quasar oficiais
- **100% Framework APIs**: Nenhuma biblioteca que bypass APIs nativas
- **Framework Update Compatibility**: Sistema deve funcionar após minor/patch updates

### Plano de Contingência

#### Se Constraint for Violada
1. **Immediate Rollback**: Reverter para implementação nativa
2. **Root Cause Analysis**: Identificar por que capacidade nativa foi insuficiente
3. **Alternative Approach**: Buscar solução dentro das constraints
4. **Escalation**: Se impossível, reavaliar requirement original

Esta abordagem garante que o sistema IAM Dashboard mantenha **estabilidade, performance e maintainability** enquanto evolui suas capacidades através de uma arquitetura sólida baseada em fundamentos nativos comprovados.

## 🎯 Implementation Epic Structure (Cycle Atual)

### Epic 1: Critical Integration Foundation (Sprints 1-2)
**Objetivo**: Resolver gaps de inicialização e integração
- Story 1.1: System Startup Automation
- Story 1.2: Agent System Bootstrap  
- Story 1.3: Database Schema Automation
- Story 1.4: API Router Integration
- **Success Criteria**: System 100% funcional end-to-end

### Epic 2: User Experience Enhancement (Sprints 3-4)  
**Objetivo**: UI polish e error handling robusto
- Story 2.1: Progressive Enhancement Implementation
- Story 2.2: Error Recovery Workflows
- Story 2.3: Mobile Responsiveness Validation
- **Success Criteria**: Professional UX com fallback completo

### Epic 3: Production Readiness (Sprints 5-6)
**Objetivo**: Monitoring, rollback e documentation
- Story 3.1: Feature Flag Implementation
- Story 3.2: Monitoring & Health Checks
- Story 3.3: User Documentation Creation
- **Success Criteria**: Production-ready com rollback capability

## 📊 Estrutura de Épicos e Stories Baseada em Evidências

### Análise Situacional Atual (Problema Diagnosticado)

#### Status Operacional Verificado via MCP Playwright
- **Frontend**: 70% funcional - Interface presente mas com bugs críticos
- **Backend**: 30% funcional - APIs básicas funcionam, core features quebradas  
- **Sistema de Agentes**: 0% funcional - Agno não inicializado
- **Banco de Dados**: Schema incompleto - Tabelas críticas faltando
- **Autorização**: Quebrada - Admin sem acesso às próprias funcionalidades
- **Mobile**: 0% funcional - Redireciona para login infinitamente
- **Overall System**: 25% operacional

#### Problemas Críticos Confirmados (Real Evidence)
1. **Agentes Agno Não Inicializados**: PDFProcessorAgent definido mas nunca registrado
2. **Schema PostgreSQL Incompleto**: Tabela `questionnaire_drafts` não existe
3. **Sistema de Autorização Quebrado**: UserRole.SYSADMIN sem acesso a `/admin`
4. **Responsividade Mobile Falha**: Sistema quebra completamente em viewports menores
5. **Qualidade Visual Inadequada**: Interface "feia e quadrada" (2/10 rating)
6. **Features Placeholder**: PDF Processor mostra "Funcionalidade em desenvolvimento"

#### Impacto nas Personas (Business Impact)
- **Dr. Ana**: Não consegue processar documentos (job-to-be-done principal bloqueado)
- **João**: Interface não-profissional afeta credibilidade com clientes
- **Carlos**: Sem ferramentas de administração enterprise

### Epic 1: Correção de Infraestrutura Crítica e Hotswap de Agentes
**Prioridade**: 🔴 CRÍTICA BLOQUEADORA  
**Duração**: 3 sprints (6 semanas)  
**Business Objective**: Transformar sistema 25% operacional em 100% funcional
**Success Metric**: Todas as funcionalidades críticas operacionais sem erros

**Contexto para Arquiteto**: Sistema possui base sólida (FastAPI + NiceGUI + PostgreSQL + Agno) mas falhas de implementação impedem operação. Arquitetura correta, execução incompleta.

**Contexto para UX Designer**: Interface funcionalmente adequada mas visualmente inadequada para segmento enterprise jurídico. Foco em profissionalização visual mantendo usabilidade.

#### Story 1.1: Correção da Infraestrutura Core de Agentes
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

#### Story 1.2: Correção do Schema de Banco de Dados
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

#### Story 1.3: Correção do Sistema de Autorização
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

#### Story 1.4: Interface Administrativa Completa
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

#### Story 1.5: Processador de PDFs Funcional
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

#### Story 1.6: Correção da Responsividade Mobile
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

### Epic 2: Melhoria da Experiência Visual (UI Polish)
**Prioridade**: 🟡 IMPORTANTE (Após Epic 1)  
**Duração**: 2 sprints (4 semanas)  
**Problema Base**: Interface "feia e quadrada" com qualidade visual 2/10

**Contexto**: Análise UX revelou interface funcional mas visualmente inadequada para uso profissional. Sistema parece "ferramenta gratuita dos anos 2000" prejudicando confiança e adoção.

#### Story 2.1: Implementação do Design System Nativo
**Objetivo**: Elevar qualidade visual de 2/10 para 7-8/10 usando apenas recursos nativos

**Implementação**:
- Design tokens via CSS variables Quasar nativos
- Paleta de cores profissional Material Design
- Tipografia hierarchical usando classes nativas
- Spacing system baseado no grid 8px

**Constraints Técnicos**:
- Apenas CSS variables nativas Quasar
- Material Design color palette oficial
- Typography scale padrão do framework
- Spacing classes q-pa-*, q-ma-* nativas

**Design System Spec**:
```css
:root {
  /* Primary Palette */
  --q-primary: #2563EB;
  --q-secondary: #10B981; 
  --q-accent: #F59E0B;
  
  /* Semantic Colors */
  --q-positive: #059669;
  --q-negative: #DC2626;
  --q-info: #0EA5E9;
  --q-warning: #D97706;
  
  /* Surface Colors */
  --q-surface: #FFFFFF;
  --q-background: #F8FAFC;
  --q-card: #FFFFFF;
}
```

**DoD**: Design system profissional implementado usando 100% recursos nativos

#### Story 2.2: Micro-interações e Animações Nativas
**Objetivo**: Adicionar polish visual através de transições e feedback nativo

**Implementação**:
- Hover effects usando pseudo-selectors CSS nativos
- Loading states com q-spinner e skeleton components
- Feedback visual via q-notify system nativo
- Transições CSS para mudanças de estado

**Constraints Técnicos**:
- Apenas CSS transitions e transforms nativos
- Q-spinner e q-skeleton components oficiais
- Q-notify system para feedback
- Pseudo-selectors (:hover, :active, :focus) nativos

**Micro-interactions Spec**:
```css
/* Hover Effects */
.q-btn:hover {
  transform: translateY(-2px);
  transition: transform 0.3s ease;
}

/* Loading States */
.q-card--loading {
  opacity: 0.7;
  transition: opacity 0.3s ease;
}
```

**DoD**: Interface polished com feedback visual moderno usando apenas recursos nativos

## 🛡️ Brownfield Risk Mitigation Strategy

### System Stability Preservation

**Current State Assessment**: Sistema operando em 25% de capacidade com 8 bloqueadores críticos identificados. A transformação brownfield requer estratégias específicas de mitigação para preservar funcionalidades existentes enquanto implementa melhorias.

#### Feature Flag Implementation for Safe Rollbacks
```python
# Estratégia de Feature Flags para rollbacks seguros
FEATURE_FLAGS = {
    "agent_system_v2": False,  # New agent initialization system
    "mobile_responsive_ui": False,  # Mobile-first responsive design
    "hot_swap_agents": False,  # Hot-swappable agent architecture
    "enhanced_auth": False,  # Enhanced authentication system
    "visual_polish": False  # Professional visual design system
}

# Implementação de rollback automático
def safe_feature_rollback(feature_name, error_threshold=5):
    if get_error_count(feature_name) > error_threshold:
        FEATURE_FLAGS[feature_name] = False
        log_rollback_event(feature_name, "automatic_rollback")
        notify_team(f"Feature {feature_name} automatically rolled back")
```

#### Graceful Degradation Procedures
- **Agent System Fallback**: Se o sistema Agno falhar, voltar para processamento manual com notificação clara
- **Mobile Interface Fallback**: Se a interface mobile quebrar, redirecionar para versão desktop simplificada
- **Authentication Fallback**: Se 2FA falhar, permitir login temporário com auditoria rigorosa
- **Database Fallback**: Se migrações falharem, manter schemas existentes com warnings

#### User Communication During System Updates
- **Status Page**: Página dedicada com atualizações em tempo real sobre manutenções
- **In-App Notifications**: Notificações proativas sobre funcionalidades temporariamente indisponíveis
- **Email Alerts**: Comunicação por email para atualizações críticas que afetam workflows
- **Timeline Communication**: Cronograma transparente de atualizações com impacto esperado

#### Data Backup and Recovery Procedures
```bash
# Backup automático antes de cada deployment
#!/bin/bash
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > backups/pre_deployment_${BACKUP_TIMESTAMP}.sql
tar -czf backups/agent_configs_${BACKUP_TIMESTAMP}.tar.gz app/agents/
tar -czf backups/ui_components_${BACKUP_TIMESTAMP}.tar.gz app/ui_components/

# Verificação de integridade do backup
if [[ $? -eq 0 ]]; then
    echo "Backup successful: ${BACKUP_TIMESTAMP}"
    # Prosseguir com deployment
else
    echo "Backup failed - aborting deployment"
    exit 1
fi
```

### Hot-Swap Safety Procedures

#### Agent Failure Containment Strategies
- **Isolation Boundaries**: Cada agente executa em contexto isolado com limites de recursos
- **Circuit Breaker Pattern**: Desativar agentes com falha após 3 tentativas consecutivas
- **Health Check Monitoring**: Verificação de saúde a cada 30 segundos com timeout de 5 segundos
- **Automatic Recovery**: Restart automático de agentes com backoff exponencial

#### System Stability Monitoring During Agent Swaps
```python
# Monitoramento durante hot-swap
class HotSwapMonitor:
    def __init__(self):
        self.stability_metrics = {
            "cpu_usage": [],
            "memory_usage": [], 
            "response_time": [],
            "error_rate": []
        }
    
    async def monitor_swap_stability(self, agent_id, duration_seconds=300):
        for i in range(duration_seconds):
            metrics = await collect_system_metrics()
            self.stability_metrics["cpu_usage"].append(metrics.cpu)
            self.stability_metrics["memory_usage"].append(metrics.memory)
            
            # Trigger rollback se métricas degradarem
            if self.check_degradation_threshold(metrics):
                await self.trigger_automatic_rollback(agent_id)
                return False
            
            await asyncio.sleep(1)
        return True
```

#### Automatic Rollback Triggers and Procedures
- **Performance Degradation**: CPU > 80% por mais de 60 segundos
- **Memory Exhaustion**: Uso de memória > 90% por mais de 30 segundos  
- **Error Rate Spike**: Taxa de erro > 5% em qualquer endpoint
- **Response Time Degradation**: Tempo de resposta > 3x baseline por mais de 2 minutos

#### User Impact Minimization During Failures
- **Transparent Failover**: Usuários não percebem troca de agentes durante operação normal
- **Progress Preservation**: Estado de processamento mantido durante falhas de agente
- **Alternative Workflows**: Caminhos alternativos quando agentes específicos estão indisponíveis
- **Clear Communication**: Mensagens claras sobre funcionalidades temporariamente limitadas

### Critical Risk Register
| Risk | Probability | Impact | Exposure | Mitigation Status |
|------|-------------|--------|----------|-------------------|
| Agent Init Failure | 40% | High | 24% | **FEATURE FLAGS + ROLLBACK** |
| DB Schema Issues | 25% | Critical | 25% | **BACKUP + VALIDATION** |
| UI-Backend Disconnect | 60% | Medium | 36% | **GRACEFUL DEGRADATION** |
| Mobile Session Management | 45% | High | 27% | **FALLBACK TO DESKTOP** |
| Performance Bottlenecks | 30% | Medium | 18% | **MONITORING + ALERTS** |
| Security Vulnerabilities | 20% | Critical | 20% | **AUTOMATED AUDIT** |
| System Downtime During Upgrade | 35% | Critical | 28% | **BLUE-GREEN DEPLOYMENT** |
| Data Loss During Migration | 15% | Critical | 15% | **AUTOMATED BACKUPS** |

### Risk Mitigation Roadmap
- **Week 1-2**: Critical integration patterns + Feature flag implementation
- **Week 3-4**: Error handling & fallbacks + Monitoring systems  
- **Week 5-6**: Monitoring & rollback procedures + Production hardening

### Cronograma de Implementação Brownfield

**Sprint 1 (2 semanas)**: Stories 1.1, 1.2, 1.3
- Foco: Corrigir bloqueadores críticos de funcionamento
- Entrega: Sistema básico operacional

**Sprint 2 (2 semanas)**: Stories 1.4, 1.5  
- Foco: Implementar features core faltantes
- Entrega: Funcionalidades principais completas

**Sprint 3 (2 semanas)**: Story 1.6, Testes E2E
- Foco: Responsividade e qualidade
- Entrega: Sistema mobile-ready com QA completo

**Sprint 4 (2 semanas)**: Epic 2 - Polish visual
- Foco: Experiência visual profissional
- Entrega: Interface nível 7-8/10 qualidade

**Sprint 5 (2 semanas)**: Refinamentos finais
- Foco: Otimizações e polish final
- Entrega: Sistema production-ready

## 👥 User Impact & Communication Strategy

### Impact by Persona
- **Dr. Ana**: Temporary feature limitations during integration phase
- **João**: Mobile experience improvements with phased rollout
- **Carlos**: Additional monitoring capabilities, training required

### Communication Timeline
- **Pre-implementation**: System enhancement notification
- **During implementation**: Progress updates and temporary limitations
- **Post-implementation**: New feature training and documentation

### User Impact Mitigation
- **Service Continuity**: Zero downtime deployments during updates
- **Feature Flags**: Gradual rollout with instant rollback capability
- **Training Materials**: Step-by-step guides for new features
- **Support Escalation**: Priority support during transition period

### Resultado Final Esperado

**Sistema Transformado**:
- Agentes autônomos com hot-swap funcionais 
- Interface administrativa completa
- Responsividade universal (mobile/tablet/desktop)
- Qualidade visual profissional (7-8/10)
- Performance otimizada (< 2s response time)
- Constraints nativas garantindo estabilidade em updates

**Business Impact**:
- Dr. Ana: Processamento automático de documentos médicos
- João: Ferramenta moderna e intuitiva para produtividade
- Carlos: Controle completo e monitoramento do sistema
- Mercado: Produto profissional competitivo no segment Legal Tech

## 🎯 Brownfield Recovery Success Criteria

### System Operational Recovery Targets

**Baseline Current State**: Sistema operando em 25% de capacidade operacional conforme diagnosticado via MCP Playwright testing e análise técnica detalhada.

#### Phase-Gate Success Validation

**Phase 0: Emergency Stabilization (Week 1-2)**
- **Agent System Initialization**: 0% → 100% (todos os agentes Agno inicializados no startup)
- **Database Schema Completeness**: Tabela `questionnaire_drafts` criada + foreign keys funcionais
- **Admin Access Recovery**: UserRole.SYSADMIN acessa 100% endpoints `/admin`
- **API Router Integration**: Endpoints `/api/agents` funcionais (atualmente retornam 404)
- **UI-Backend Connection**: Substituir placeholders por conexões reais

**Success Gate Criteria - Phase 0**:
- [ ] `curl http://localhost:8000/api/agents` retorna lista de agentes (não 404)
- [ ] Carlos (SYSADMIN) acessa interface admin sem erros 403
- [ ] Agentes PDFProcessor e QuestionnaireWriter aparecem com status "healthy"
- [ ] Upload de documento não gera erro PostgreSQL de tabela inexistente
- [ ] Interface mostra dados reais ao invés de "Funcionalidade em desenvolvimento"

**Phase 1: Core Functionality Restoration (Week 3-4)**
- **PDF Processing Pipeline**: 0% → 100% funcional (Dr. Ana pode processar documentos)
- **Mobile Responsiveness**: 0% → 100% (sistema não quebra em viewport < 768px)
- **Visual Quality**: 2/10 → 7/10 (interface profissional, não "feia e quadrada")
- **Real-time Updates**: WebSocket connections funcionais para status de agentes
- **Error Recovery**: Sistema se recupera automaticamente de falhas de agente

**Success Gate Criteria - Phase 1**:
- [ ] Dr. Ana carrega documento PDF de 10MB e recebe análise completa em < 30s
- [ ] Sistema mantém sessão em dispositivo mobile durante rotação de tela
- [ ] Interface recebe rating 7+/10 em avaliação visual por stakeholders
- [ ] Agentes reiniciam automaticamente após falha sem intervenção manual
- [ ] Processing queue mostra progresso em tempo real via WebSocket

**Phase 2: Production Readiness (Week 5-6)**
- **Hot-Swap Capability**: Troca de agentes em < 2s sem downtime
- **System Monitoring**: Dashboards completos de performance e saúde
- **Security Hardening**: Audit logs, 2FA enforcement, encryption at-rest
- **Mobile Optimization**: Dr. Ana usa sistema durante audiências (375px viewport)
- **Enterprise Integration**: Backup automático, rollback procedures, monitoring

**Success Gate Criteria - Phase 2**:
- [ ] Hot-swap de agente completa em < 2000ms conforme SLA
- [ ] Dr. Ana completa workflow crítico em iPhone durante audiência simulada
- [ ] Sistema suporta 100+ usuários concorrentes sem degradação
- [ ] Backup automático e procedimentos de rollback testados com sucesso
- [ ] Compliance com LGPD e normas OAB validado

### Métricas de Performance (Recovery-Focused)
- **Overall System Functionality**: 25% → 80% operational (target mínimo aceitável)
- **Agent Initialization Success Rate**: 0% → 100% (startup sem falhas)
- **PDF Processing Success Rate**: 0% → 95% (com retry automático)
- **Mobile Session Persistence**: 0% → 100% (sem redirecionamentos infinitos)
- **Admin Interface Availability**: 0% → 100% (Carlos com acesso total)
- **UI Response Time**: Inconsistente → < 2s (interação fluida)
- **System Uptime**: Instável → 99.5% (confiabilidade enterprise)

### Métricas de UX (Visual Recovery)
- **Visual Quality Rating**: 2/10 → 7+/10 (credibilidade profissional)
- **Mobile Usability Score**: 0/10 → 8+/10 (Dr. Ana em audiências)
- **Interface Professional Rating**: "Feia e quadrada" → "Enterprise-grade"
- **User Task Completion Rate**: < 50% → > 95% (workflows funcionais)
- **Error Rate**: > 20% → < 1% (sistema confiável)
- **Learning Curve**: Indeterminado → < 5 min (primeira tarefa completa)

### Métricas de Adoção por Persona (Recovery Context)
- **Dr. Ana**: Uso sistema para processamento documentos: 0% → 80%
- **João**: Interface mobile funcional para trabalho de campo: 0% → 90%
- **Carlos**: Controle administrativo completo: 0% → 100%
- **Overall User Satisfaction**: Sistema não utilizável → NPS > 70

### ROI e Business Impact (Brownfield Recovery)
- **System Usability**: 25% → 80% funcional (target mínimo para viabilidade)
- **Document Processing Capability**: 0% → Full pipeline (Dr. Ana workflows)
- **Mobile Accessibility**: 0% → 100% (audiências e trabalho de campo)
- **Administrative Control**: 0% → 100% (Carlos gerencia sistema)
- **Professional Credibility**: Interface inadequada → Enterprise-ready
- **Time to Value**: Sistema não entrega valor → Workflows produtivos

### Critical Success Dependencies
- **Architecture Implementation**: Agent initialization, schema fixes, hot-swap
- **Frontend Polish**: Mobile responsiveness, visual design, UI-backend integration
- **System Integration**: Authentication, authorization, monitoring, backup
- **User Validation**: Continuous feedback from Dr. Ana, João, Carlos during implementation

## 🚀 Estratégia de Implementação e Rollout

### Fase 1: Critical Path Resolution (Sprints 1-3)
**Objetivo**: Resolver todos os bloqueadores que impedem funcionamento básico
**Duração**: 6 semanas
**Critério de Sucesso**: Sistema 100% operacional para todas as personas

#### Sprint 1: Foundation Fix
- Story 1.1: Ativação Agentes Agno
- Story 1.2: Schema PostgreSQL
- **Entrega**: Backend core funcional

#### Sprint 2: Access & Features
- Story 1.3: Autorização Admin
- Story 1.4: Interface Administrativa
- **Entrega**: Carlos pode gerenciar sistema

#### Sprint 3: Core Features & Mobile
- Story 1.5: PDF Processor
- Story 1.6: Responsividade Mobile
- **Entrega**: Dr. Ana pode usar completamente

### Fase 2: Experience Enhancement (Sprints 4-5)
**Objetivo**: Elevar qualidade visual e polish profissional
**Duração**: 4 semanas
**Critério de Sucesso**: Interface 7-8/10 qualidade visual

#### Sprint 4: Visual Upgrade
- Story 2.1: Design System Profissional
- **Entrega**: Interface com credibilidade enterprise

#### Sprint 5: Polish & Launch Prep
- Story 2.2: Micro-interações
- Testing & Refinements
- **Entrega**: Sistema production-ready

### Validação Contínua com Personas
- **Weekly Check-ins**: Feedback Dr. Ana sobre PDF processing
- **Bi-weekly Reviews**: Carlos valida admin capabilities
- **Sprint Reviews**: João testa usabilidade geral

## 📋 Contexto Técnico para Outros Agentes BMad

### Para o Arquiteto (architecture.md)
**Stack Tecnológico Validado**:
- Python 3.12 + FastAPI (dependency injection, WebSockets confirmados)
- PostgreSQL + pgvector (embeddings, HNSW/IVFFlat índices)
- NiceGUI + Quasar (Material Design nativo, responsive)
- Google Gemini API (text generation, embeddings, streaming)
- Agno Framework (autonomous agents, hot-swappable)

**Principais Desafios Arquiteturais**:
1. **Agent Lifecycle Management**: Inicialização, health checks, failover
2. **Hot-swap Implementation**: Runtime agent substitution sem downtime
3. **Vector Storage Optimization**: pgvector performance para search semântica
4. **Real-time Updates**: WebSockets para progress tracking
5. **Mobile Session Management**: Correção viewport responsivo

**Constraints Críticos**:
- Apenas capacidades nativas dos frameworks (estabilidade)
- Performance < 30s PDF, < 10s quesitos, < 2s UI
- Escalabilidade até 100 usuários concorrentes
- Security enterprise-grade (2FA, encryption, audit)

### Para o UX Designer (frontend-spec.md)
**Personas Prioritárias**:
1. **Dr. Ana** (Principal): Mobile-first, processamento documentos, zero learning curve
2. **Carlos** (Admin): Dashboard enterprise, controle granular, monitoramento
3. **João** (Power User): Produtividade, interface moderna, qualidade profissional

**Principais Desafios de UX**:
1. **Responsive Mobile**: Sistema quebrado em viewports < 768px
2. **Visual Credibility**: Interface 2/10 → 7-8/10 qualidade profissional
3. **Workflow Optimization**: PDF upload → processing → quesitos sem friction
4. **Admin Complexity**: Dashboard enterprise sem overwhelming Carlos
5. **Professional Polish**: Micro-interações e feedback visual adequado

**Design Constraints**:
- Material Design Quasar nativo (sem customizações)
- Breakpoints: xs(375), sm(600), md(1024), lg(1440), xl(1920)
- Paleta profissional: #2563EB (primary), #10B981 (secondary)
- Performance: FCP < 1.5s, TTI < 3s
- Acessibilidade: WCAG 2.1 Level AA

**Fluxos Críticos para Design**:
1. **PDF Processing Flow**: Upload → Progress → Results → Export
2. **Questionnaire Generation**: Client Select → Context → Generate → Edit → Export
3. **Admin Dashboard**: Agent Status → User Management → Security → Monitoring
4. **Mobile Navigation**: Touch-optimized, drawer navigation, responsive cards

### Dependências Entre Documentos
- **PRD → Architecture**: Requisitos funcionais/não-funcionais → Design técnico
- **PRD → Frontend-Spec**: Personas + UX goals → Interface design
- **Architecture → Frontend-Spec**: Stack técnico → Implementação UI
- **Todos → Implementação**: Alignment completo para execução

---

**Este PRD fornece o contexto completo e máximo detalhamento para que Arquiteto e UX Designer possam criar seus documentos especializados, mantendo alinhamento total com as necessidades de negócio, personas validadas e constraints técnicos da transformação brownfield.**

*Documento gerado seguindo BMad Method - Product Management Framework*  
*Versão 1.0 - 29 de Julho de 2025*  
*Próxima Revisão: Sprint Review #2 (4 semanas)*  
*Total Tokens Utilizados: ~24.8k para máximo contexto e detalhamento*