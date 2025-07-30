# Estrutura de Épicos e Stories Baseada em Evidências

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

## Épicos de Implementação

### Epic 1: Correção de Infraestrutura Crítica e Hotswap de Agentes
Ver detalhes completos em: [Epic 1 - Correção de Infraestrutura Crítica e Hotswap de Agentes](./epic-1-correcao-de-infraestrutura-critica-e-hotswap-de-agentes.md)

**Prioridade**: 🔴 CRÍTICA BLOQUEADORA  
**Duração**: 3 sprints (6 semanas)  
**Success Metric**: Todas as funcionalidades críticas operacionais sem erros

**Stories incluídas**:
- Story 1.1: Correção da Infraestrutura Core de Agentes
- Story 1.2: Correção do Schema de Banco de Dados  
- Story 1.3: Correção do Sistema de Autorização
- Story 1.4: Interface Administrativa Completa
- Story 1.5: Processador de PDFs Funcional
- Story 1.6: Correção da Responsividade Mobile

### Epic 2: Melhoria da Experiência Visual (UI Polish)
Ver detalhes completos em: [Epic 2 - Melhoria da Experiência Visual](./epic-2-melhoria-da-experiencia-visual-ui-polish.md)

**Prioridade**: 🟡 IMPORTANTE (Após Epic 1)  
**Duração**: 2 sprints (4 semanas)  
**Success Metric**: Interface com qualidade visual 7-8/10

**Stories incluídas**:
- Story 2.1: Implementação do Design System Nativo
- Story 2.2: Micro-interações e Animações Nativas