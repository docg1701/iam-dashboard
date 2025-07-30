# Contexto Técnico para Outros Agentes BMad

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