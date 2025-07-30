# Restrições Técnicas (Apenas Capacidades Nativas)

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