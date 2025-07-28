# IAM Dashboard UI/UX Specification

Este documento define a experiência do usuário, arquitetura da informação, fluxos de usuário e especificações de design visual para a interface do IAM Dashboard. Serve como base para o design visual e desenvolvimento frontend, garantindo uma experiência coesa e centrada no usuário.

## 🎯 Personas & Princípios UX

### **👩‍💼 Persona 1: "Dr. Ana Santos" - Advogada Sênior/Sócia**
**Perfil:** 45 anos, 20+ anos de experiência, especializada em direito médico  
**Competência Tech:** 3/10 - Usa apenas Word, navegador web, email básico  
**Principais Tarefas:** Análise documental (50%+ do tempo), redação de peças processuais, estratégia de casos, reuniões com clientes  
**Maior Dor:** "Perco horas lendo laudos médicos extensos e me canso mentalmente escrevendo peças técnicas repetitivas"  
**Necessidade UX:** Interface extremamente simples, resultados imediatos, sem curva de aprendizado

### **👨‍💻 Persona 2: "João Silva" - Advogado Associado**  
**Perfil:** 28 anos, 5 anos de experiência  
**Competência Tech:** 3/10 - Similar aos seniores, trabalho básico de escritório  
**Workflow Atual:** Analisa documentos 1 por 1 na tela, imprime para rabiscar, compila PDFs manualmente, anexa em plataformas jurídicas  
**Maior Ganho Esperado:** "IA analisando documentos e redigindo textos jurídicos com minha orientação revolucionaria minha produtividade"  
**Necessidade UX:** Fluxo intuitivo para orientar IA, visualização clara de análises

### **👩‍💼 Persona 3: "Maria Costa" - Secretária/Suporte**
**Perfil:** 35 anos, experiência administrativa  
**Competência Tech:** 3/10 - Mesma base dos advogados  
**Principais Tarefas:** Atendimento clientes, validação documentos, gestão agenda, chat/WhatsApp, arquivamento  
**Automação Ideal:** Conferência/análise documentos, gestão agenda, processos de arquivamento  
**Necessidade UX:** Dashboards claros para status, automações que não exigem configuração técnica

### **🔧 Persona 4: "Carlos Tech" - Administrador de Sistema**
**Perfil:** Responsável por infraestrutura e treinamento da equipe  
**Maior Preocupação:** "O software deve ser TÃO intuitivo que não precise de treinamentos longos e repetidos"  
**Necessidade UX:** Interface self-explanatory, onboarding automático, sistema que "se explica sozinho"

### **🎯 Princípios UX Derivados das Personas:**

1. **Simplicidade Extrema** - Interface deve ser mais simples que Word
2. **Resultados Imediatos** - Sem loading demorado, feedback instantâneo  
3. **Sem Curva de Aprendizado** - Sistema auto-explicativo
4. **Foco na Produtividade** - Cada clique deve economizar tempo significativo
5. **Redução de Fadiga Mental** - IA assume tarefas cognitivas pesadas

## 📋 Information Architecture & Navigation

### **Estrutura Baseada em Workflows dos Usuários**

#### **🏠 Dashboard Principal - "Painel de Agentes"**
**Layout:** Grid de ícones grandes e intuitivos  
**Rationale:** Dr. Ana (3/10 tech) precisa identificar instantaneamente cada função  

**Agentes MVP Identificados:**
1. **📄 Processador de PDFs** - "Analise meus documentos"
2. **✍️ Redator de Quesitos** - "Escreva peças jurídicas"

#### **🔗 Navegação Primária**
```
IAM Dashboard
├── 🏠 Início (Dashboard de Agentes)
├── 📁 Meus Documentos  
├── ✍️ Meus Textos Gerados
├── 👥 Clientes
├── ⚙️ Configurações (apenas Admin)
└── 🚪 Sair
```

#### **🎯 Hierarquia Visual Baseada em Frequência de Uso**
**Zona Primária:** Agentes mais usados (centro da tela)  
**Zona Secundária:** Gestão de arquivos (lateral direita)  
**Zona Terciária:** Configurações e Admin (menu hambúrguer)
**Zona Administrativa:** Painel de controle para admins (acesso restrito)

#### **🔐 Administrative Navigation Extension**
```
IAM Dashboard (Admin View)
├── 🏠 Início (Dashboard de Agentes)
├── 📁 Meus Documentos  
├── ✍️ Meus Textos Gerados
├── 👥 Clientes
├── 🤖 Agent Management (Admin only)
│   ├── 📊 Agent Status Overview
│   ├── ⚙️ Agent Configuration
│   ├── 📋 Performance Monitoring
│   └── 🔧 System Health
├── 🔒 Security Center (Admin only)
│   ├── 👤 User Management
│   ├── 🛡️ Authentication Settings
│   ├── 📊 Security Audit Log
│   └── ⚠️ Security Alerts
├── ⚙️ Configurações
└── 🚪 Sair
```

## 🔄 User Flows & Task Flows

### **Flow 1: Dr. Ana - Análise de Laudo Médico**
```
1. Login → Dashboard
2. Clique no ícone "📄 Processador PDFs" 
3. Arrasta arquivo PDF ou clica "Selecionar"
4. IA processa automaticamente (progress bar)
5. Resultados mostrados em linguagem simples
6. Botão "Salvar Análise" ou "Gerar Peça"
```
**UX Goal:** Máximo 3 cliques do login ao resultado

### **Flow 2: João - Compilação de Documentos do Cliente**
```
1. Dashboard → "👥 Clientes"
2. Seleciona cliente na lista
3. Arrasta múltiplos PDFs para área de upload
4. IA consolida automaticamente
5. Preview do documento unificado
6. Download ou envio direto para plataforma jurídica
```

### **Flow 3: Maria - Validação de Documentação**
```
1. Dashboard → "📋 Checklist de Documentos"
2. Seleciona tipo de processo
3. Arrasta documentos recebidos do cliente
4. IA verifica completude automaticamente
5. Lista clara: ✅ OK, ❌ Faltando, ⚠️ Atenção
6. Gera lista para cliente de documentos pendentes
```

### **Flow 4: Carlos - Agent Management & System Monitoring**
```
1. Login Admin → Security Dashboard
2. Verificar status geral: agentes, segurança, performance
3. Agent Management → Status Overview
4. Identificar agente com problema (⚠️ status)
5. Clique em "CONFIGURE" → Agent Configuration Panel
6. Ajustar parâmetros → "TEST" → "SAVE CHANGES"
7. Monitorar logs em tempo real
8. Verificar Security Center → Audit Log
```
**UX Goal:** Diagnóstico e resolução de problemas em menos de 5 minutos

### **Flow 5: Admin - Security Incident Response**
```
1. Alert notification → Security Center
2. Security Overview → identificar tipo de incident
3. Audit Log → investigar eventos relacionados
4. User Management → tomar ação (disable user, reset 2FA)
5. Authentication Settings → ajustar políticas se necessário
6. Generate incident report
```
**UX Goal:** Resposta a incidentes de segurança em menos de 10 minutos

## 🎨 Visual Design Direction

### **Paleta de Cores - Confiança Profissional**
**Primária:** Azul Corporativo (#2563EB) - Confiança, tecnologia  
**Secundária:** Cinza Neutro (#64748B) - Profissionalismo  
**Accent:** Verde Sucesso (#10B981) - Conclusão, aprovação  
**Warning:** Âmbar (#F59E0B) - Atenção necessária  
**Error:** Vermelho (#EF4444) - Problemas críticos  

### **Typography - Legibilidade Máxima**
**Headers:** Inter, peso 600, mínimo 18px  
**Body:** Inter, peso 400, mínimo 16px  
**Rationale:** Dr. Ana pode ter fadiga visual; texto pequeno = abandono

### **Iconografia - Universalmente Reconhecível**
**Estilo:** Material Design ou Heroicons  
**Tamanho mínimo:** 24px (mobile), 32px (desktop)  
**Acompanhado SEMPRE de labels textuais**

## 📱 Responsive Strategy

### **Desktop First (Uso Principal)**
**Breakpoints:**
- Desktop: 1200px+ (uso principal no escritório)
- Tablet: 768px-1199px (reuniões, apresentações)  
- Mobile: <768px (consulta rápida, emergências)

### **Mobile Considerations - Dr. Ana em Audiência**
**Cenário:** Precisa consultar análise durante audiência  
**Solução:** Cards de resumo grandes, navegação por swipe, informações essenciais visíveis sem scroll

## 🧱 Component Library & Interaction Patterns

### **Core Components - Otimizados para Baixa Competência Tech**

#### **🤖 Agent Management Components - Administrative Interface**

##### **Agent Status Card - Real-time Monitoring**
```
┌─────────────────────────────────┐
│  🤖 PDFProcessorAgent          │
│  ● Active    ⚡ Processing: 2   │
│                                 │
│  Health: ✅ Healthy             │
│  Uptime: 2h 15m                 │
│  Last Process: 30s ago          │
│                                 │
│  [CONFIGURE] [DISABLE] [LOGS]   │
└─────────────────────────────────┘
```

**Especificações:**
- **Status Indicators:** Real-time dot (● green/red/yellow) com texto status
- **Processing Count:** Contador em tempo real de tarefas ativas
- **Health Badge:** ✅/⚠️/❌ com tooltip explicativo
- **Action Buttons:** Configure (⚙️), Disable/Enable toggle, View Logs (📋)
- **Update Frequency:** 5 second polling para status real-time

##### **Agent Configuration Panel - Administrative Control**
```
┌─────────────────────────────────┐
│  ⚙️ Agent Configuration        │
│                                 │
│  Agent: PDFProcessorAgent       │
│  Status: ● Active               │
│                                 │
│  📋 Configuration Parameters    │
│  ┌─────────────────────────────┐ │
│  │ Timeout: [30] seconds       │ │
│  │ Max Retries: [3]            │ │
│  │ OCR Enabled: ☑️             │ │
│  │ Queue Priority: [normal ▼]   │ │
│  └─────────────────────────────┘ │
│                                 │
│  [SAVE CHANGES] [RESET] [TEST]  │
└─────────────────────────────────┘
```

**UX Requirements:**
- **Form Validation:** Real-time validation com feedback visual
- **Change Preview:** Mostrar impacto das mudanças antes de salvar
- **Test Button:** Testar configuração sem aplicar permanentemente
- **Auto-save Draft:** Salvar rascunhos de configuração automaticamente

##### **Security Status Dashboard - Authentication & Authorization**
```
┌─────────────────────────────────┐
│  🔒 Security Overview          │
│                                 │
│  Authentication: ✅ Active      │
│  2FA Status: ✅ Enforced        │
│  Session Timeout: 30 min        │
│                                 │
│  🛡️ Security Events (Last 24h)  │
│  • Login attempts: 15 ✅        │
│  • Failed logins: 2 ⚠️          │
│  • Blocked IPs: 0 ✅            │
│                                 │
│  [VIEW AUDIT LOG] [SETTINGS]    │
└─────────────────────────────────┘
```

**Integração com Requisitos de Segurança:**
- **REQ-API-AUTH-001 Compliance:** Display de status de autenticação JWT
- **REQ-API-AUTH-002 Integration:** Indicadores de health para OAuth2
- **REQ-SECURITY-HEADERS-001:** Status de headers de segurança (CSP, HSTS)
- **Rate Limiting Status:** Visualização de limites e uso atual

##### **User Management Interface - Administrative Control**
```
┌─────────────────────────────────┐
│  👥 User Management            │
│                                 │
│  Active Users: 12              │
│  Pending Invites: 3            │
│                                 │
│  📋 User List                   │
│  ┌─────────────────────────────┐ │
│  │ Dr. Ana Santos   ✅ Active  │ │
│  │ Role: Senior Lawyer         │ │
│  │ 2FA: ✅ Enabled  Last: 2h   │ │
│  │ [EDIT] [DISABLE] [RESET 2FA]│ │
│  ├─────────────────────────────┤ │
│  │ João Silva      ⚠️ Pending  │ │
│  │ Role: Associate             │ │
│  │ 2FA: ❌ Setup Required      │ │
│  │ [ACTIVATE] [DELETE]         │ │
│  └─────────────────────────────┘ │
│                                 │
│  [ADD NEW USER] [BULK ACTIONS]  │
└─────────────────────────────────┘
```

**UX Requirements:**
- **Role Management:** Dropdown com roles predefinidos (Admin, Senior Lawyer, Associate, Support)
- **2FA Management:** One-click reset com QR code regeneration
- **Bulk Actions:** Disable/enable múltiplos usuários simultaneamente
- **User Activity:** Last login, active sessions, recent actions

##### **Rate Limiting Dashboard - Real-time Monitoring**
```
┌─────────────────────────────────┐
│  ⚡ Rate Limiting Overview      │
│                                 │
│  🔥 Current Status              │
│  • API Calls: 847/1000 (85%)   │
│  • Auth Attempts: 12/50 (24%)  │
│  • File Uploads: 23/100 (23%)  │
│                                 │
│  📊 Top Consumers (Last Hour)   │
│  1. Dr. Ana Santos    245 calls │
│  2. João Silva        189 calls │
│  3. Maria Costa       156 calls │
│                                 │
│  🚨 Throttled Users             │
│  • user_123: 5 min cooldown    │
│                                 │
│  [CONFIGURE LIMITS] [WHITELIST] │
└─────────────────────────────────┘
```

**Funcionalidades:**
- **Real-time Updates:** Status de rate limiting atualizado a cada 10 segundos
- **Threshold Alerts:** Visual warnings quando approaching limits
- **User Drilling:** Click em usuário para ver detailed usage
- **Emergency Override:** Admin bypass para situações críticas

##### **Agent Plugin Management Interface**
```
┌─────────────────────────────────┐
│  🔌 Plugin Management          │
│                                 │
│  📦 Installed Plugins           │
│  ┌─────────────────────────────┐ │
│  │ 📄 PDFProcessor v2.1.0      │ │
│  │ Status: ✅ Active           │ │
│  │ Dependencies: ✅ Satisfied  │ │
│  │ [CONFIGURE] [UPDATE] [OFF]  │ │
│  ├─────────────────────────────┤ │
│  │ ✍️ QuestionnaireWriter v1.5 │ │
│  │ Status: ⚠️ Update Available │ │
│  │ Dependencies: ✅ Satisfied  │ │
│  │ [UPDATE TO v1.6] [CONFIG]   │ │
│  └─────────────────────────────┘ │
│                                 │
│  🛍️ Available Plugins           │
│  • DocumentAnalyzer v3.0        │
│  • LegalReviewer v1.2           │
│  • ClientNotifier v2.0          │
│                                 │
│  [BROWSE MARKETPLACE] [INSTALL] │
└─────────────────────────────────┘
```

**Hot-loading Features (REQ-INFRA-AGENT-004):**
- **Zero-downtime Installation:** Plugins instalados sem restart do sistema
- **Dependency Checking:** Validation automática de dependências
- **Rollback Support:** Revert para versão anterior em caso de falha
- **A/B Testing:** Enable plugin para subset de usuários

#### **🎯 Agent Card - Componente Principal**
```
┌─────────────────────────────────┐
│  📄      PROCESSADOR DE PDFs    │
│                                 │
│  Analise documentos             │
│  automaticamente                │
│                                 │
│  [   USAR AGENTE   ]           │
└─────────────────────────────────┘
```

**Especificações:**
- **Tamanho:** 280px x 200px (mínimo)
- **Ícone:** 48px, sempre presente
- **Título:** Inter 20px, peso 600
- **Descrição:** Inter 16px, máximo 2 linhas
- **CTA:** Button 48px altura, 100% largura
- **Hover:** Elevação sutil (shadow)
- **Estado Ativo:** Border azul 2px

#### **📤 File Upload Zone - Zero Friction**
```
┌─────────────────────────────────┐
│  📎  Arraste arquivos aqui      │
│      ou clique para selecionar  │
│                                 │
│  Formatos: PDF, DOCX, JPG      │
└─────────────────────────────────┘
```

**UX Requirements:**
- **Drag & Drop:** Sempre habilitado
- **Visual Feedback:** Borda tracejada ao hover/drag
- **Progress:** Barra de progresso para uploads >2MB
- **Error Handling:** Mensagens claras em português
- **Success State:** ✅ Arquivo carregado com sucesso

#### **🔄 Processing Indicator - Tranquilizar o Usuário**
```
┌─────────────────────────────────┐
│  🤖 IA analisando documento...  │
│  ████████████░░░░░░░░ 65%      │
│                                 │
│  Tempo estimado: 30 segundos    │
└─────────────────────────────────┘
```

**Rationale:** Dr. Ana fica ansiosa com delay; precisa saber que está funcionando

#### **📋 Results Display - Escaneabilidade Máxima**
```
┌─────────────────────────────────┐
│  📄 laudo-medico.pdf            │
│  ✅ Análise concluída           │
│                                 │
│  📊 RESUMO EXECUTIVO            │
│  • Diagnóstico: [texto]         │
│  • Recomendações: [texto]       │
│  • Próximos passos: [texto]     │
│                                 │
│  [BAIXAR] [COMPARTILHAR] [NOVA] │
└─────────────────────────────────┘
```

## ⚡ Interaction Patterns

### **Pattern 1: One-Click Magic**
**Princípio:** Cada ação deve produzir resultado imediato  
**Aplicação:** Botão "Analisar" → Resultado completo sem steps intermediários  
**Feedback:** Loading state → Success state → Action buttons

### **Pattern 2: Smart Defaults**
**Cenário:** Dr. Ana não quer configurar nada  
**Solução:** IA usa melhores práticas automaticamente  
**Exemplo:** Tipo de análise detectado pelo conteúdo do documento

### **Pattern 3: Progressive Disclosure**
**Nível 1:** Resultado resumido (o que Dr. Ana precisa saber)  
**Nível 2:** Detalhes técnicos (para João investigar)  
**Nível 3:** Raw output (para debugging do Carlos)

### **Pattern 4: Contextual Help**
**Trigger:** Hover em ícone "?" pequeno  
**Content:** Tooltip com exemplo prático  
**Never:** Modal ou popup que interrompe o fluxo

## 🎛️ States & Feedback

### **Loading States - Reduzir Ansiedade**
```javascript
// Micro-interactions
Button: "Analisar" → "Analisando..." → ✅ "Concluído"
Upload: Drag hover → Border animation → Success checkmark
AI Process: "Iniciando..." → "Lendo..." → "Analisando..." → "Finalizando..."
```

### **Error States - Linguagem Humana**
```
❌ "Arquivo muito grande. Tente um arquivo menor que 10MB."
❌ "Formato não suportado. Use PDF, DOCX ou JPG."
❌ "Conexão instável. Tentando novamente..."
```

**Nunca:** "Error 404", "Invalid input", "Exception thrown"

### **Empty States - Orientação Clara**
```
┌─────────────────────────────────┐
│  📂 Nenhum documento ainda      │
│                                 │
│  Comece fazendo upload de um    │
│  arquivo PDF ou DOCX            │
│                                 │
│  [  ENVIAR PRIMEIRO ARQUIVO  ]  │
└─────────────────────────────────┘
```

## 🔧 Technical Integration with NiceGUI

### **NiceGUI Component Mapping**
```python
# Agent Card
ui.card().classes('agent-card w-64 h-48 cursor-pointer hover:shadow-lg')

# File Upload
ui.upload(on_upload=handle_file).classes('upload-zone w-full h-32 border-dashed')

# Results Display
with ui.column().classes('results-container'):
    ui.markdown(analysis_result).classes('prose max-w-none')

# Agent Status Card - Administrative Components
def agent_status_card(agent_name: str, status: str, processing_count: int):
    with ui.card().classes('agent-status-card w-80 h-32 border-l-4 border-blue-500'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label(f'🤖 {agent_name}').classes('text-lg font-semibold')
            ui.badge(status, color='positive' if status == 'Active' else 'negative')
        
        with ui.row().classes('w-full justify-between items-center mt-2'):
            ui.label(f'⚡ Processing: {processing_count}').classes('text-sm')
            ui.label('Health: ✅ Healthy').classes('text-sm text-green-600')
        
        with ui.row().classes('w-full mt-3 gap-2'):
            ui.button('CONFIGURE', icon='settings').classes('text-xs')
            ui.button('DISABLE', icon='power_off').classes('text-xs')
            ui.button('LOGS', icon='article').classes('text-xs')

# Security Status Dashboard
def security_status_dashboard():
    with ui.card().classes('security-dashboard w-full max-w-md'):
        ui.label('🔒 Security Overview').classes('text-xl font-bold mb-4')
        
        with ui.column().classes('gap-3'):
            # Authentication Status
            with ui.row().classes('items-center justify-between'):
                ui.label('Authentication:').classes('font-medium')
                ui.badge('✅ Active', color='positive')
            
            # 2FA Status
            with ui.row().classes('items-center justify-between'):
                ui.label('2FA Status:').classes('font-medium')
                ui.badge('✅ Enforced', color='positive')
            
            # Security Events
            ui.separator()
            ui.label('🛡️ Security Events (Last 24h)').classes('font-medium')
            
            with ui.column().classes('gap-1 ml-4'):
                ui.label('• Login attempts: 15 ✅').classes('text-sm')
                ui.label('• Failed logins: 2 ⚠️').classes('text-sm text-yellow-600')
                ui.label('• Blocked IPs: 0 ✅').classes('text-sm')
        
        with ui.row().classes('mt-4 gap-2'):
            ui.button('VIEW AUDIT LOG', icon='history')
            ui.button('SETTINGS', icon='settings')

# Agent Configuration Panel
def agent_configuration_panel(agent_name: str):
    with ui.card().classes('config-panel w-full max-w-lg'):
        ui.label(f'⚙️ Agent Configuration').classes('text-xl font-bold mb-4')
        
        with ui.column().classes('gap-4'):
            ui.label(f'Agent: {agent_name}').classes('font-medium')
            ui.badge('● Active', color='positive')
            
            ui.separator()
            ui.label('📋 Configuration Parameters').classes('font-medium')
            
            with ui.card().classes('p-4 bg-gray-50'):
                with ui.row().classes('items-center gap-4'):
                    ui.label('Timeout:').classes('w-24')
                    ui.number('timeout', value=30, suffix='seconds').classes('w-32')
                
                with ui.row().classes('items-center gap-4'):
                    ui.label('Max Retries:').classes('w-24')
                    ui.number('max_retries', value=3).classes('w-32')
                
                with ui.row().classes('items-center gap-4'):
                    ui.label('OCR Enabled:').classes('w-24')
                    ui.switch('ocr_enabled', value=True)
                
                with ui.row().classes('items-center gap-4'):
                    ui.label('Queue Priority:').classes('w-24')
                    ui.select(['low', 'normal', 'high'], value='normal').classes('w-32')
        
        with ui.row().classes('mt-6 gap-2'):
            ui.button('SAVE CHANGES', color='primary')
            ui.button('RESET')
            ui.button('TEST', color='secondary')

# User Management Interface
def user_management_interface():
    with ui.card().classes('user-management w-full max-w-4xl'):
        ui.label('👥 User Management').classes('text-xl font-bold mb-4')
        
        # Statistics Row
        with ui.row().classes('w-full gap-4 mb-6'):
            with ui.card().classes('flex-1 p-4 bg-blue-50'):
                ui.label('Active Users').classes('text-sm text-gray-600')
                ui.label('12').classes('text-2xl font-bold text-blue-600')
            
            with ui.card().classes('flex-1 p-4 bg-yellow-50'):
                ui.label('Pending Invites').classes('text-sm text-gray-600')
                ui.label('3').classes('text-2xl font-bold text-yellow-600')
            
            with ui.card().classes('flex-1 p-4 bg-green-50'):
                ui.label('2FA Enabled').classes('text-sm text-gray-600')
                ui.label('9/12').classes('text-2xl font-bold text-green-600')
        
        # User List
        ui.separator()
        ui.label('📋 User List').classes('font-medium mt-4 mb-2')
        
        # User List Table
        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left'},
            {'name': 'role', 'label': 'Role', 'field': 'role', 'align': 'left'},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
            {'name': '2fa', 'label': '2FA', 'field': '2fa', 'align': 'center'},
            {'name': 'last_login', 'label': 'Last Login', 'field': 'last_login', 'align': 'left'},
            {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
        ]
        
        with ui.table(columns=columns, rows=[]).classes('w-full') as table:
            # Add sample users programmatically
            pass
        
        with ui.row().classes('mt-4 gap-2'):
            ui.button('ADD NEW USER', icon='person_add', color='primary')
            ui.button('BULK ACTIONS', icon='checklist')
            ui.button('EXPORT LIST', icon='download')

# Rate Limiting Dashboard
def rate_limiting_dashboard():
    with ui.card().classes('rate-limiting-dashboard w-full max-w-lg'):
        ui.label('⚡ Rate Limiting Overview').classes('text-xl font-bold mb-4')
        
        # Current Status
        ui.label('🔥 Current Status').classes('font-medium mb-2')
        
        with ui.column().classes('gap-2 mb-4'):
            # API Calls Progress
            with ui.row().classes('items-center gap-2'):
                ui.label('API Calls:').classes('w-24')
                ui.linear_progress(value=0.85, color='primary').classes('flex-1')
                ui.label('847/1000').classes('text-sm')
            
            # Auth Attempts Progress
            with ui.row().classes('items-center gap-2'):
                ui.label('Auth:').classes('w-24')
                ui.linear_progress(value=0.24, color='positive').classes('flex-1')
                ui.label('12/50').classes('text-sm')
            
            # File Uploads Progress
            with ui.row().classes('items-center gap-2'):
                ui.label('Uploads:').classes('w-24')
                ui.linear_progress(value=0.23, color='positive').classes('flex-1')
                ui.label('23/100').classes('text-sm')
        
        ui.separator()
        
        # Top Consumers
        ui.label('📊 Top Consumers (Last Hour)').classes('font-medium mb-2')
        
        with ui.column().classes('gap-1 mb-4'):
            ui.label('1. Dr. Ana Santos    245 calls').classes('text-sm')
            ui.label('2. João Silva        189 calls').classes('text-sm')
            ui.label('3. Maria Costa       156 calls').classes('text-sm')
        
        # Throttled Users
        ui.label('🚨 Throttled Users').classes('font-medium mb-2')
        ui.label('• user_123: 5 min cooldown').classes('text-sm text-red-600 mb-4')
        
        with ui.row().classes('gap-2'):
            ui.button('CONFIGURE LIMITS', icon='settings')
            ui.button('WHITELIST', icon='verified_user')

# Plugin Management Interface
def plugin_management_interface():
    with ui.card().classes('plugin-management w-full max-w-4xl'):
        ui.label('🔌 Plugin Management').classes('text-xl font-bold mb-4')
        
        # Installed Plugins Section
        ui.label('📦 Installed Plugins').classes('font-medium mb-3')
        
        with ui.column().classes('gap-3 mb-6'):
            # PDFProcessor Plugin
            with ui.card().classes('p-4 border-l-4 border-green-500'):
                with ui.row().classes('w-full justify-between items-start'):
                    with ui.column():
                        ui.label('📄 PDFProcessor v2.1.0').classes('font-semibold')
                        ui.label('Status: ✅ Active').classes('text-sm text-green-600')
                        ui.label('Dependencies: ✅ Satisfied').classes('text-sm')
                    
                    with ui.row().classes('gap-2'):
                        ui.button('CONFIGURE', icon='settings').classes('text-xs')
                        ui.button('UPDATE', icon='system_update').classes('text-xs')
                        ui.button('DISABLE', icon='power_off').classes('text-xs')
            
            # QuestionnaireWriter Plugin
            with ui.card().classes('p-4 border-l-4 border-yellow-500'):
                with ui.row().classes('w-full justify-between items-start'):
                    with ui.column():
                        ui.label('✍️ QuestionnaireWriter v1.5').classes('font-semibold')
                        ui.label('Status: ⚠️ Update Available').classes('text-sm text-yellow-600')
                        ui.label('Dependencies: ✅ Satisfied').classes('text-sm')
                    
                    with ui.row().classes('gap-2'):
                        ui.button('UPDATE TO v1.6', icon='upgrade').classes('text-xs')
                        ui.button('CONFIG', icon='settings').classes('text-xs')
        
        ui.separator()
        
        # Available Plugins Section
        ui.label('🛍️ Available Plugins').classes('font-medium mb-3')
        
        with ui.column().classes('gap-2 mb-4'):
            ui.label('• DocumentAnalyzer v3.0 - Advanced document analysis').classes('text-sm')
            ui.label('• LegalReviewer v1.2 - Legal document review automation').classes('text-sm')
            ui.label('• ClientNotifier v2.0 - Automated client communications').classes('text-sm')
        
        with ui.row().classes('gap-2'):
            ui.button('BROWSE MARKETPLACE', icon='store')
            ui.button('INSTALL PLUGIN', icon='add_circle')
            ui.button('IMPORT PLUGIN', icon='upload_file')

# Agent Performance Dashboard
def agent_performance_dashboard():
    with ui.card().classes('performance-dashboard w-full max-w-6xl'):
        ui.label('📈 Agent Performance Monitor').classes('text-xl font-bold mb-4')
        
        # Performance Chart
        ui.label('📊 Response Times (Last 24h)').classes('font-medium mb-2')
        
        # Chart placeholder - in real implementation would use ui.chart or ui.echart
        with ui.card().classes('p-4 bg-gray-50 h-64 mb-4'):
            ui.label('Performance Chart Visualization').classes('text-center text-gray-500 mt-24')
            ui.label('(Real-time response time graph)').classes('text-center text-gray-400')
        
        # Current Metrics Grid
        with ui.row().classes('w-full gap-4 mb-6'):
            with ui.card().classes('flex-1 p-4 bg-blue-50'):
                ui.label('Avg Response').classes('text-sm text-gray-600')
                ui.label('1.2s').classes('text-2xl font-bold text-blue-600')
            
            with ui.card().classes('flex-1 p-4 bg-red-50'):
                ui.label('Peak Response').classes('text-sm text-gray-600')
                ui.label('4.8s').classes('text-2xl font-bold text-red-600')
            
            with ui.card().classes('flex-1 p-4 bg-green-50'):
                ui.label('Success Rate').classes('text-sm text-gray-600')
                ui.label('99.2%').classes('text-2xl font-bold text-green-600')
            
            with ui.card().classes('flex-1 p-4 bg-purple-50'):
                ui.label('Active Requests').classes('text-sm text-gray-600')
                ui.label('7').classes('text-2xl font-bold text-purple-600')
        
        # Agent Breakdown
        ui.label('📋 Agent Breakdown').classes('font-medium mb-2')
        
        columns = [
            {'name': 'agent', 'label': 'Agent', 'field': 'agent', 'align': 'left'},
            {'name': 'response_time', 'label': 'Avg Response', 'field': 'response_time', 'align': 'center'},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
            {'name': 'requests_today', 'label': 'Requests Today', 'field': 'requests_today', 'align': 'center'},
        ]
        
        rows = [
            {'agent': 'PDFProcessor', 'response_time': '856ms', 'status': '✅', 'requests_today': '1,247'},
            {'agent': 'Questionnaire', 'response_time': '1.4s', 'status': '⚠️', 'requests_today': '89'},
            {'agent': 'DocumentAnalyzer', 'response_time': '2.1s', 'status': '⚠️', 'requests_today': '156'},
        ]
        
        ui.table(columns=columns, rows=rows).classes('w-full mb-4')
        
        with ui.row().classes('gap-2'):
            ui.button('DETAILED VIEW', icon='analytics')
            ui.button('EXPORT DATA', icon='download')
            ui.button('CONFIGURE ALERTS', icon='notifications')

# Resource Usage Monitor
def resource_usage_monitor():
    with ui.card().classes('resource-monitor w-full max-w-lg'):
        ui.label('💾 Resource Usage Monitor').classes('text-xl font-bold mb-4')
        
        # System Resources
        ui.label('🖥️ System Resources').classes('font-medium mb-3')
        
        with ui.column().classes('gap-3 mb-4'):
            # CPU Usage
            with ui.row().classes('items-center gap-2'):
                ui.label('CPU Usage:').classes('w-24')
                ui.linear_progress(value=0.75, color='warning').classes('flex-1')
                ui.label('75%').classes('text-sm font-semibold')
            
            # Memory
            with ui.row().classes('items-center gap-2'):
                ui.label('Memory:').classes('w-24')
                ui.linear_progress(value=0.60, color='primary').classes('flex-1')
                ui.label('60%').classes('text-sm font-semibold')
            
            # Disk I/O
            with ui.row().classes('items-center gap-2'):
                ui.label('Disk I/O:').classes('w-24')
                ui.linear_progress(value=0.25, color='positive').classes('flex-1')
                ui.label('25%').classes('text-sm font-semibold')
            
            # Network
            with ui.row().classes('items-center gap-2'):
                ui.label('Network:').classes('w-24')
                ui.linear_progress(value=0.45, color='primary').classes('flex-1')
                ui.label('45%').classes('text-sm font-semibold')
        
        ui.separator()
        
        # Agent Resource Usage
        ui.label('🤖 Agent Resource Usage').classes('font-medium mb-3')
        
        with ui.column().classes('gap-3 mb-4'):
            # PDFProcessor Agent
            with ui.card().classes('p-3 bg-blue-50'):
                ui.label('PDFProcessor').classes('font-semibold')
                with ui.row().classes('items-center gap-4 mt-1'):
                    ui.label('CPU:').classes('text-sm')
                    ui.linear_progress(value=0.30, color='primary').classes('w-16')
                    ui.label('30%').classes('text-xs')
                    ui.label('RAM: 256MB').classes('text-sm')
                ui.label('Processed: 1,247 docs today').classes('text-xs text-gray-600 mt-1')
            
            # QuestionnaireAgent
            with ui.card().classes('p-3 bg-green-50'):
                ui.label('QuestionnaireAgent').classes('font-semibold')
                with ui.row().classes('items-center gap-4 mt-1'):
                    ui.label('CPU:').classes('text-sm')
                    ui.linear_progress(value=0.20, color='positive').classes('w-16')
                    ui.label('20%').classes('text-xs')
                    ui.label('RAM: 128MB').classes('text-sm')
                ui.label('Generated: 89 forms today').classes('text-xs text-gray-600 mt-1')
        
        # Alerts
        ui.label('⚠️ Alerts').classes('font-medium mb-2')
        ui.label('• High CPU on PDFProcessor').classes('text-sm text-yellow-600 mb-4')
        
        with ui.row().classes('gap-2'):
            ui.button('SCALE AGENTS', icon='trending_up')
            ui.button('VIEW DETAILS', icon='info')

# Historical Performance Analytics
def historical_performance_analytics():
    with ui.card().classes('historical-analytics w-full max-w-4xl'):
        ui.label('📅 Historical Analytics').classes('text-xl font-bold mb-4')
        
        # Time Range Selector
        with ui.row().classes('items-center gap-4 mb-4'):
            ui.label('📊 Performance Trends').classes('font-medium')
            ui.select(['Last 7 Days', 'Last 30 Days', 'Last 3 Months'], value='Last 30 Days').classes('w-48')
        
        # Key Metrics Comparison
        ui.label('📈 Key Metrics Comparison').classes('font-medium mb-3')
        
        columns = [
            {'name': 'metric', 'label': 'Metric', 'field': 'metric', 'align': 'left'},
            {'name': 'this_month', 'label': 'This Month', 'field': 'this_month', 'align': 'center'},
            {'name': 'last_month', 'label': 'Last Month', 'field': 'last_month', 'align': 'center'},
            {'name': 'change', 'label': 'Change', 'field': 'change', 'align': 'center'},
        ]
        
        rows = [
            {'metric': 'Avg Response', 'this_month': '1.2s', 'last_month': '1.8s', 'change': '↗️ +33%'},
            {'metric': 'Success Rate', 'this_month': '99.2%', 'last_month': '97.1%', 'change': '↗️ +2.1%'},
            {'metric': 'Total Requests', 'this_month': '15.2K', 'last_month': '12.8K', 'change': '↗️ +18.7%'},
            {'metric': 'Peak Load', 'this_month': '47 rps', 'last_month': '39 rps', 'change': '↗️ +20.5%'},
        ]
        
        ui.table(columns=columns, rows=rows).classes('w-full mb-4')
        
        # Performance Breakdown
        ui.label('📊 Performance Breakdown').classes('font-medium mb-2')
        
        with ui.column().classes('gap-1 mb-4'):
            ui.label('• Document Processing: +23%').classes('text-sm text-green-600')
            ui.label('• Questionnaire Generation: +15%').classes('text-sm text-green-600')
            ui.label('• Authentication: +8%').classes('text-sm text-green-600')
        
        # Optimization Suggestions
        ui.label('🎯 Optimization Suggestions').classes('font-medium mb-2')
        
        with ui.column().classes('gap-1 mb-4'):
            ui.label('• Consider caching for PDFs').classes('text-sm text-blue-600')
            ui.label('• Scale QuestionnaireAgent').classes('text-sm text-blue-600')
            ui.label('• Optimize database queries').classes('text-sm text-blue-600')
        
        with ui.row().classes('gap-2'):
            ui.button('GENERATE REPORT', icon='summarize')
            ui.button('SCHEDULE REPORT', icon='schedule')
            ui.button('EXPORT CSV', icon='file_download')
```

### **Responsive Classes Strategy**
```python
# Desktop-first approach
ui.row().classes('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6')

# Mobile optimization
ui.button('Analisar').classes('w-full h-12 text-lg md:w-auto md:h-10 md:text-base')
```

## 🎨 Visual Design System - NiceGUI Implementation

### **Color Tokens**
```python
COLORS = {
    'primary': '#2563EB',      # Blue 600
    'secondary': '#64748B',    # Slate 500  
    'success': '#10B981',      # Emerald 500
    'warning': '#F59E0B',      # Amber 500
    'error': '#EF4444',        # Red 500
    'surface': '#F8FAFC',      # Slate 50
    'text': '#1E293B'          # Slate 800
}
```

### **Typography Scale**
```python
TEXT_STYLES = {
    'heading-1': 'text-2xl font-semibold text-slate-800',
    'heading-2': 'text-xl font-medium text-slate-700', 
    'body': 'text-base text-slate-600',
    'caption': 'text-sm text-slate-500'
}
```

## ♿ Accessibility & Usability Guidelines

### **🎯 Accessibility Priorities - Contexto Legal Brasileiro**

#### **WCAG 2.1 AA Compliance + Contexto Profissional**
**Rationale:** Escritórios de advocacia devem ser exemplares em compliance legal, incluindo acessibilidade digital

### **👀 Visual Accessibility - Fadiga Profissional**

#### **Contraste & Legibilidade**
```css
/* Mínimos obrigatórios */
Normal text: 4.5:1 contrast ratio
Large text (18px+): 3:1 contrast ratio  
UI components: 3:1 contrast ratio

/* Otimizado para Dr. Ana (fadiga visual) */
Body text: 16px mínimo (nunca menor)
Line height: 1.6 (espaçamento confortável)
Paragraph spacing: 1.5em entre blocos
```

#### **Zoom & Responsividade**
- **200% zoom:** Interface permanece funcional
- **Texto pode crescer até 200%** sem quebrar layout
- **Touch targets:** Mínimo 44px x 44px (dedos em tablets)

### **⌨️ Keyboard Navigation - Power Users**

#### **Tab Order Lógico**
```
1. Logo/Home → 2. Navigation → 3. Main Content → 4. Actions → 5. Footer
```

#### **Keyboard Shortcuts - João (Efficiency)**
```
Ctrl + U: Upload arquivo
Ctrl + Enter: Processar/Analisar  
Ctrl + S: Salvar resultado
Ctrl + N: Novo documento
Esc: Cancelar ação atual
```

#### **Focus Indicators**
```css
/* Visível e contrastante */
:focus {
    outline: 2px solid #2563EB;
    outline-offset: 2px;
    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}
```

## 🧠 Cognitive Accessibility - Simplificação Mental

### **Redução de Carga Cognitiva - Dr. Ana**

#### **Information Chunking**
```
Máximo 7±2 itens por grupo visual
Máximo 3 ações primárias por tela
Máximo 2 níveis de navegação para tarefas críticas
```

#### **Language Clarity**
```python
# ❌ Evitar
"Processamento de entidades nomeadas via NLP"
"Timeout da requisição HTTP"
"Falha na autenticação do token JWT"

# ✅ Usar  
"Analisando nomes e organizações no documento"
"Conexão demorou muito, tentando novamente"
"Sessão expirou, faça login novamente"
```

#### **Progressive Disclosure - Informação Graduada**
```
Nível 1: O que aconteceu (resultado principal)
Nível 2: Por que é importante (contexto)  
Nível 3: O que fazer agora (próximos passos)
```

## 📱 Mobile Usability - Consulta Rápida

### **Touch-First Design**
```css
/* Touch targets para Dr. Ana em audiência */
Buttons: min 48px altura, 44px largura
Inputs: min 48px altura  
Icons: min 24px (com padding 12px)
Spacing: min 8px entre elementos tocáveis
```

### **Thumb-Friendly Layout**
```
┌─────────────────┐
│ Header (safe)   │ ← Área segura
│                 │
│ Content         │ ← Conteúdo principal
│                 │
│ Primary Action  │ ← Polegar direito
└─────────────────┘
```

### **Offline Graceful Degradation**
```python
# Cenário: Dr. Ana em local com internet instável
@offline_handler
def show_cached_results():
    ui.notify("Exibindo última análise (offline)", type='warning')
    display_cached_analysis()
```

## ⚡ Performance Guidelines - Reduzir Ansiedade

### **Loading Performance - Expectativas Claras**

#### **Progressive Loading**
```
1. Skeleton UI (0-100ms): Estrutura visual imediata
2. Cached Content (100-300ms): Dados em cache 
3. Fresh Content (300ms+): Dados do servidor
4. AI Processing (2s+): Com indicador de progresso
```

#### **Perceived Performance**
```python
# Feedback imediato mesmo para operações lentas
async def upload_file():
    ui.notify("✅ Arquivo recebido, analisando...")  # Imediato
    show_progress_indicator()                        # Visual feedback
    result = await process_document_async()          # Background
    ui.notify("✅ Análise concluída!")              # Resultado
```

## 🔊 Audio & Screen Reader Support

### **ARIA Labels - Contexto Jurídico**
```html
<!-- Específico para workflow legal -->
<button aria-label="Analisar laudo médico com IA">Analisar</button>
<div aria-label="Resultado da análise: diagnóstico identificado">...</div>
<input aria-label="Carregar documento PDF do cliente">
```

### **Live Regions - Feedback Dinâmico**
```html
<div aria-live="polite" aria-atomic="true">
    Status da análise: processando página 3 de 15
</div>

<div aria-live="assertive" aria-atomic="true">
    Erro: arquivo muito grande. Máximo 10MB.
</div>
```

## 🧪 Usability Testing Strategy

### **Teste com Personas Reais**

#### **Dr. Ana - Task Scenario**
```
"Você recebeu um laudo médico de 50 páginas. 
Precisa entender rapidamente se há elementos 
que fortalecem o caso do seu cliente. 
Use o sistema para analisar o documento."

Métricas de sucesso:
- Tempo para primeira análise: <5 minutos
- Taxa de erro: <10%  
- Satisfação: >8/10
```

#### **Testes de Stress - João**
```
"Você tem 10 documentos de clientes diferentes 
para processar antes do fim do dia. 
Use o sistema da forma mais eficiente possível."

Métricas:
- Documentos processados/hora: >8
- Erros de workflow: 0
- Fadiga percebida: <5/10
```

## 🔧 Technical Implementation Considerations

### **NiceGUI Architecture Integration**

#### **Component Structure - Modular & Maintainable**
```python
# /app/ui_components/agents/
agent_card.py          # Reutilizável para todos os agentes
file_upload.py         # Upload zone universal  
results_display.py     # Layout de resultados padronizado
progress_indicator.py  # Loading states consistentes
```

#### **State Management Pattern**
```python
from nicegui import app, ui
from dataclasses import dataclass

@dataclass
class AppState:
    current_user: User
    active_documents: List[Document] 
    processing_status: Dict[str, str]
    
# Global state accessible em todos os componentes
app.storage.user['state'] = AppState()
```

### **Performance Optimization - Zero Friction**

#### **Lazy Loading Strategy**
```python
# Dashboard principal carrega instantaneamente
async def main_dashboard():
    render_agent_cards_sync()      # Crítico: imediato
    await load_recent_docs_async() # Background: não bloqueia UI
    await preload_user_prefs()     # Background: otimização
```

#### **Caching Strategy - Dr. Ana Efficiency**
```python
# Cache agressivo para reduzir re-processamento
@cache_result(expire_minutes=60)
async def analyze_document(file_hash: str):
    # IA analysis só roda 1x por documento único
    pass

@cache_result(expire_minutes=5) 
def get_user_recent_documents():
    # Lista de documentos cached para dashboard rápido
    pass
```

## 🚀 Deployment & Environment Considerations

### **Progressive Enhancement - Fallback Gracioso**
```python
# JavaScript disabled? Ainda funciona
def upload_fallback():
    with ui.form() as form:
        ui.upload(auto_upload=True)  # Funciona sem JS
        ui.button('Analisar', on_click=process_sync)
```

### **VPS Optimization - Recursos Limitados**
```python
# Lazy imports para startup rápido
def load_ai_models():
    if not hasattr(app.storage.general, 'models_loaded'):
        from app.services.gemini_client import GeminiClient
        app.storage.general['models_loaded'] = True
```

## 📊 Analytics & Monitoring - UX Insights

### **User Behavior Tracking**
```python
# Métricas UX críticas
track_event('agent_card_click', {'agent_type': 'pdf_processor'})
track_timing('document_analysis_complete', duration_ms)
track_error('upload_failed', {'file_type': 'pdf', 'error': 'too_large'})
```

### **Performance Monitoring**
```python
# Alertas para UX degradada
@monitor_performance
def upload_handler():
    if response_time > 5000:  # 5s = abandono provável
        alert_admin('Upload slow - user likely frustrated')
```

#### **📊 Performance Dashboards Detalhados - REQ-MONITOR-METRICS-001**

##### **Agent Performance Dashboard**
```
┌─────────────────────────────────┐
│  📈 Agent Performance Monitor   │
│                                 │
│  📊 Response Times (Last 24h)   │
│  ┌─────────────────────────────┐ │
│  │     ╭─╮                     │ │
│  │  ╭──╯ ╰─╮    ╭─╮            │ │
│  │ ╭╯      ╰────╯ ╰╮           │ │
│  │╭╯              ╰─╮          │ │
│  │╯                 ╰──────────│ │
│  │ 0h  6h  12h 18h  24h        │ │
│  └─────────────────────────────┘ │
│                                 │
│  🔥 Current Metrics             │
│  • Avg Response: 1.2s          │
│  • Peak Response: 4.8s         │
│  • Success Rate: 99.2%         │
│  • Active Requests: 7           │
│                                 │
│  📋 Agent Breakdown             │
│  PDFProcessor:    856ms ✅      │
│  Questionnaire:   1.4s  ⚠️      │
│  DocumentAnalyzer: 2.1s ⚠️      │
│                                 │
│  [DETAILED VIEW] [EXPORT DATA]  │
└─────────────────────────────────┘
```

##### **Resource Usage Tracking**
```
┌─────────────────────────────────┐
│  💾 Resource Usage Monitor      │
│                                 │
│  🖥️ System Resources            │
│  CPU Usage:    ████████░░ 75%   │
│  Memory:       ██████░░░░ 60%   │
│  Disk I/O:     ███░░░░░░░ 25%   │
│  Network:      █████░░░░░ 45%   │
│                                 │
│  🤖 Agent Resource Usage        │
│  ┌─────────────────────────────┐ │
│  │ PDFProcessor                │ │
│  │ CPU: ███░░ 30%  RAM: 256MB  │ │
│  │ Processed: 1,247 docs today │ │
│  ├─────────────────────────────┤ │
│  │ QuestionnaireAgent          │ │
│  │ CPU: ██░░░ 20%  RAM: 128MB  │ │
│  │ Generated: 89 forms today   │ │
│  └─────────────────────────────┘ │
│                                 │
│  ⚠️ Alerts                      │
│  • High CPU on PDFProcessor    │
│                                 │
│  [SCALE AGENTS] [VIEW DETAILS]  │
└─────────────────────────────────┘
```

##### **Historical Performance Analytics**
```
┌─────────────────────────────────┐
│  📅 Historical Analytics        │
│                                 │
│  📊 Performance Trends          │
│  Time Range: [Last 30 Days ▼]  │
│                                 │
│  📈 Key Metrics Comparison      │
│  ┌─────────────────────────────┐ │
│  │        This Month   Last    │ │
│  │ Avg Response  1.2s    1.8s  │ │
│  │ Success Rate  99.2%   97.1% │ │
│  │ Total Requests 15.2K  12.8K │ │
│  │ Peak Load     47 rps  39rps │ │
│  └─────────────────────────────┘ │
│                                 │
│  📊 Performance Breakdown       │
│  • Document Processing: +23%    │
│  • Questionnaire Gen: +15%     │
│  • Authentication: +8%         │
│                                 │
│  🎯 Optimization Suggestions    │
│  • Consider caching for PDFs   │
│  • Scale QuestionnaireAgent    │
│                                 │
│  [GENERATE REPORT] [SCHEDULE]   │
└─────────────────────────────────┘
```

## 🔒 Security & Privacy - Compliance Legal

### **Data Protection - LGPD Compliance**
```python
# Dados sensíveis nunca em logs
@secure_handler
def process_legal_document():
    logger.info("Document processed", 
                document_id=hash_id,  # ✅ Hash, não ID real
                user_role="lawyer")   # ✅ Categoria, não nome
```

### **Session Security**
```python
# Auto-logout para Dr. Ana esquecida
@session_timeout(minutes=30)
def secure_session():
    ui.notify("Sessão expirará em 5 minutos", type='warning')
```

## 📋 Implementation Checklist

### **Phase 1: MVP Foundation** 
- [ ] Dashboard com 2 agent cards principais
- [ ] Upload de arquivos drag-and-drop
- [ ] Integração básica com Gemini API
- [ ] Sistema de autenticação 2FA
- [ ] Layout responsivo mobile-first
- [ ] **NEW:** Agent status cards básicos no dashboard
- [ ] **NEW:** Authentication status indicators
- [ ] **NEW:** Basic admin navigation (role-based access)

### **Phase 2: User Experience**
- [ ] Loading states com progress indicators  
- [ ] Error handling em português claro
- [ ] Cache de resultados para performance
- [ ] Keyboard shortcuts para power users
- [ ] Feedback visual para todas as ações
- [ ] **NEW:** Real-time agent status updates (5s polling)
- [ ] **NEW:** Security event notifications
- [ ] **NEW:** Agent configuration validation with preview
- [ ] **NEW:** Administrative workflow optimization

### **Phase 3: Professional Features**
- [ ] Gestão de clientes e documentos
- [ ] Export de análises em PDF/DOCX
- [ ] Histórico de atividades
- [ ] Configurações de usuário
- [ ] Integração com plataformas jurídicas
- [ ] **NEW:** Comprehensive agent management interface
- [ ] **NEW:** Security audit log with filtering and search
- [ ] **NEW:** Performance monitoring dashboards
- [ ] **NEW:** Advanced agent configuration with templates
- [ ] **NEW:** Security incident response workflows
- [ ] **NEW:** Agent health monitoring and alerting
- [ ] **NEW:** Administrative reporting and analytics
- [ ] **NEW:** User management interface with role-based access
- [ ] **NEW:** Rate limiting dashboard with real-time monitoring
- [ ] **NEW:** Plugin management with hot-loading support
- [ ] **NEW:** Performance analytics with historical trends
- [ ] **NEW:** Resource usage tracking and optimization recommendations

## 🎯 Success Metrics - Business Impact

### **User Adoption (Dr. Ana)**
- **Time to First Value:** <5 minutos do login à primeira análise
- **Daily Active Usage:** >80% dos usuários retornam no dia seguinte  
- **Feature Discovery:** >90% encontram funcionalidade sem ajuda

### **Productivity Impact (João)**
- **Document Processing Speed:** 5x mais rápido vs método manual
- **Error Reduction:** <5% de retrabalho em análises
- **Task Completion Rate:** >95% das análises chegam ao fim

### **Administrative Efficiency (Carlos)**
- **Agent Issue Resolution:** <5 minutos para diagnóstico e correção
- **System Health Visibility:** Status de todos os componentes em <10 segundos
- **Security Incident Response:** <10 minutos do alerta à resolução
- **Configuration Changes:** <2 segundos para aplicar e verificar mudanças

### **Technical Performance**
- **Page Load Time:** <2 segundos para dashboard
- **AI Response Time:** <30 segundos para documentos <10MB
- **Uptime:** >99.5% durante horário comercial
- **Agent Performance Monitoring:** Real-time status com <5s latência
- **Security Monitoring:** 24/7 monitoring com alertas automáticos
- **Authentication Performance:** <1 segundo para login/logout/token verification

---

## 🔗 Requirements Integration Matrix

### **Alignment with Architectural Requirements**

Esta especificação UI/UX está diretamente alinhada com os requisitos documentados em `docs/architecture.md` durante o processo de validação PO:

#### **Agent Management Interface Requirements**
- **REQ-INFRA-AGENT-001:** UI para monitoramento em tempo real do AgentManager
- **REQ-INFRA-AGENT-002:** Interface para configuração de agentes via dependency injection
- **REQ-INFRA-AGENT-003:** Dashboard administrativo para lifecycle management
- **REQ-INFRA-AGENT-004:** UI para hot-loading de plugins sem restart

#### **Authentication & Security UI Requirements**
- **REQ-API-AUTH-001:** Status indicators para JWT authentication
- **REQ-API-AUTH-002:** OAuth2 health monitoring display
- **REQ-SECURITY-HEADERS-001:** Security headers status (CSP, HSTS)
- **REQ-SECURITY-RATE-LIMIT-001:** Rate limiting visualization
- **REQ-SECURITY-AUDIT-001:** Security audit log interface
- **REQ-SECURITY-2FA-001:** 2FA management and enforcement UI
- **REQ-USER-MGMT-001:** User management interface with role assignment
- **REQ-USER-MGMT-002:** 2FA reset and activation workflows
- **REQ-USER-MGMT-003:** Bulk user operations and audit trail

#### **Testing Integration Requirements**
- **REQ-TEST-PLAYWRIGHT-001:** Playwright MCP browser automation para todos os componentes UI
- **REQ-TEST-ADMIN-UI-001:** Testes administrativos completos via browser automation
- **REQ-TEST-SECURITY-UI-001:** Validação de interfaces de segurança
- **REQ-TEST-AGENT-UI-001:** Testes de interação com agent management

#### **Monitoring & Performance UI Requirements**
- **REQ-MONITOR-AGENT-001:** Real-time agent performance dashboards
- **REQ-MONITOR-SECURITY-001:** Security monitoring interfaces
- **REQ-MONITOR-HEALTH-001:** System health status displays
- **REQ-MONITOR-METRICS-001:** Performance metrics visualization
- **REQ-MONITOR-RESOURCE-001:** Resource usage tracking with alerts
- **REQ-MONITOR-TRENDS-001:** Historical performance analytics
- **REQ-PLUGIN-MGMT-001:** Plugin marketplace integration
- **REQ-PLUGIN-MGMT-002:** Hot-loading plugin management
- **REQ-PLUGIN-MGMT-003:** Plugin dependency validation and rollback

### **Implementation Priorities Aligned with Architecture**

**High Priority (REQ-*-001 series):**
- Agent status monitoring cards
- Authentication status indicators  
- Security overview dashboard
- Basic admin navigation

**Medium Priority (REQ-*-002 series):**
- Advanced agent configuration panels
- Security audit log interface
- Performance monitoring displays
- Plugin management UI
- User management with 2FA workflows
- Hot-loading plugin operations
- Historical performance trends

**Integration Priority (REQ-*-003 series):**
- Cross-component coordination interfaces
- Advanced security coordination
- Comprehensive admin control panels
- Full monitoring integration
- Plugin dependency management and rollback
- Bulk user operations with audit trail
- Resource optimization recommendations

### **Testing Strategy Integration**

All UI components especificados acima serão testados using **Playwright MCP** conforme requisitos:
- Browser automation para administrative interfaces
- UI interaction testing para agent management
- Security interface validation
- Performance monitoring UI testing
- End-to-end workflow validation
- User management workflow testing
- Rate limiting dashboard interaction testing
- Plugin management hot-loading testing
- Performance dashboard data validation
- Resource monitoring alert testing

---

## 🔧 Technical Implementation Notes (Updated July 2025)

### **Framework Versions (Current)**
```yaml
# Updated dependency versions for optimal performance:
nicegui>=2.21.0          # Latest UI framework (July 2025)
fastapi>=0.116.0         # Latest backend framework (July 2025)
agno>=1.7.5              # Latest agent framework (July 2025)
google-genai>=0.1.0      # NEW official Gemini SDK (GA ready)
llama-index>=0.12.52     # Latest RAG framework (July 2025)
dependency-injector>=4.48.1  # Latest DI container (June 2025)
```

### **Critical Dependencies Update**
```python
# IMPORTANT: Replace deprecated Google Generative AI
# OLD (DEPRECATED - EOL September 30, 2025):
# from google.generativeai import configure, GenerativeModel

# NEW (Official SDK - Required):
from google.genai import configure, GenerativeModel

# UI Components affected:
# - Agent status displays (using Gemini API)
# - Document processing indicators
# - Performance monitoring dashboards
```

### **NiceGUI v2.21.0 New Features**
- **Enhanced Performance**: Improved rendering speed for admin dashboards
- **Better Responsive Design**: Optimized mobile support for agent management
- **Advanced Components**: New monitoring widgets for real-time agent status
- **Security Enhancements**: Improved authentication flow integration

### **Agent Management UI Compatibility**
- **Agno v1.7.5 Integration**: Native support for 23+ model providers
- **Performance Monitoring**: Real-time metrics with <5s latency
- **Plugin Management**: Hot-loading support without system restart
- **Multi-modal Support**: Text, image, audio, video processing indicators

---

**Documento gerado pela UX Expert Sally com base em workshop de personas, análise do projeto IAM Dashboard e integração com requisitos arquiteturais do processo de validação PO.**

**Atualizado em Julho 2025 com versões de dependências verificadas e migração crítica do Google Generative AI SDK.**