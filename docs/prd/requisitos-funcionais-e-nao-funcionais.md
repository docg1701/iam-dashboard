# Requisitos Funcionais e Não-Funcionais

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
        \"\"\"Authorization middleware implementation - FIXED\"\"\"
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