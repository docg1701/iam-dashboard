# IAM Dashboard - Wireframes Detalhados

## 🏠 Dashboard Principal - Painel de Agentes

### Desktop View (1200px+)
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🏢 IAM Dashboard           👤 Dr. Ana Santos                    🚪 Sair     │ │
│ │ Advocacia Digital                [foto]                                      │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                        🎯 SEUS ASSISTENTES INTELIGENTES                      │ │
│ │                     Clique em um agente para começar                         │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│ ┌───────────────────────────────────────────────────────────────────┐           │
│ │  ┌─────────────────────┐  ┌─────────────────────┐                 │ Acesso   │
│ │  │                     │  │                     │                 │ Rápido   │
│ │  │         📄          │  │         ✍️          │                 │          │
│ │  │                     │  │                     │                 │ ┌──────┐ │
│ │  │   PROCESSADOR DE    │  │     REDATOR DE      │                 │ │ 📁   │ │
│ │  │       PDFs          │  │      QUESITOS       │                 │ │ Docs │ │
│ │  │                     │  │                     │                 │ └──────┘ │
│ │  │  Analise documentos │  │   Crie peças com    │                 │          │
│ │  │   automaticamente   │  │    inteligência     │                 │ ┌──────┐ │
│ │  │                     │  │                     │                 │ │ ✍️   │ │
│ │  │  [  USAR AGENTE  ] │  │  [  USAR AGENTE  ]  │                 │ │Textos│ │
│ │  └─────────────────────┘  └─────────────────────┘                 │ └──────┘ │
│ │                                                                    │          │
│ │  ┌─────────────────────┐  ┌─────────────────────┐                 │ ┌──────┐ │
│ │  │        🔜           │  │        🔜           │                 │ │ 👥   │ │
│ │  │    EM BREVE:       │  │    EM BREVE:       │                 │ │Client│ │
│ │  │ VALIDADOR DOCS     │  │ GESTOR PRAZOS      │                 │ └──────┘ │
│ │  │                     │  │                     │                 │          │
│ │  │  (Disponível em    │  │  (Disponível em    │                 │ ┌──────┐ │
│ │  │     Fevereiro)     │  │      Março)        │                 │ │ ⚙️   │ │
│ │  └─────────────────────┘  └─────────────────────┘                 │ │Config│ │
│ │                                                                    │ └──────┘ │
│ └───────────────────────────────────────────────────────────────────┘           │
│                                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 Atividade Recente                                              Ver Tudo → │ │
│ │ ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ • Laudo médico analisado - Cliente João Silva          há 2 horas       │ │ │
│ │ │ • Quesitos trabalhistas gerados - Processo 123456      há 3 horas       │ │ │
│ │ │ • 5 documentos processados - Cliente Maria Costa       hoje, 09:30      │ │ │
│ │ └─────────────────────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

Dimensões e Espaçamentos:
- Header: 80px altura
- Agent Cards: 280px x 240px
- Card spacing: 24px
- Side menu: 120px largura
- Activity feed: 320px altura
```

### Mobile View (<768px)
```
┌────────────────────┐
│ ☰  IAM Dashboard   │
│    Dr. Ana Santos  │
├────────────────────┤
│                    │
│   ASSISTENTES      │
│                    │
├────────────────────┤
│ ┌────────────────┐ │
│ │      📄        │ │
│ │  PROCESSADOR   │ │
│ │   DE PDFs      │ │
│ │                │ │
│ │ Analise docs   │ │
│ │ automaticamente│ │
│ │                │ │
│ │ [ USAR AGENTE ]│ │
│ └────────────────┘ │
│                    │
│ ┌────────────────┐ │
│ │      ✍️        │ │
│ │   REDATOR DE   │ │
│ │   QUESITOS     │ │
│ │                │ │
│ │  Crie peças    │ │
│ │ inteligentes   │ │
│ │                │ │
│ │ [ USAR AGENTE ]│ │
│ └────────────────┘ │
│                    │
│ [↓] Ver atividades │
└────────────────────┘
```

## 📄 Processador de PDFs - Fluxo Completo

### Estado 1: Upload de Arquivo
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ← Voltar ao Dashboard                                    👤 Dr. Ana   🚪 Sair   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   📄 PROCESSADOR DE PDFs                                                         │
│   Análise inteligente de documentos jurídicos e médicos                         │
│                                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                               │ │
│ │                          ┌─────────────────────┐                             │ │
│ │                          │         📎          │                             │ │
│ │                          │                     │                             │ │
│ │                          │ Arraste arquivos   │                             │ │
│ │                          │      aqui ou       │                             │ │
│ │                          │                     │                             │ │
│ │                          │ [ ESCOLHER ARQUIVO ]│                             │ │
│ │                          │                     │                             │ │
│ │                          │ PDF, DOCX ou JPG   │                             │ │
│ │                          │   Máximo: 10MB     │                             │ │
│ │                          └─────────────────────┘                             │ │
│ │                                                                               │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ 📚 Documentos Recentes                                                       │ │
│ │ ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 📄 laudo-cardiologico.pdf - João Silva          [Reanalisar] [Ver]      │ │ │
│ │ │ 📄 pericia-ortopedica.pdf - Maria Costa         [Reanalisar] [Ver]      │ │ │
│ │ │ 📄 exames-laboratoriais.pdf - Pedro Santos      [Reanalisar] [Ver]      │ │ │
│ │ └─────────────────────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

Comportamentos:
- Drag hover: Borda azul pulsante + fundo azul claro
- File hover em "Recentes": Highlight linha + cursor pointer
- Botão hover: Elevação sombra + escurecer 10%
```

### Estado 2: Processando
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ← Voltar ao Dashboard                                    👤 Dr. Ana   🚪 Sair   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   📄 PROCESSADOR DE PDFs                                                         │
│   Análise inteligente de documentos jurídicos e médicos                         │
│                                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                               │ │
│ │   📄 laudo-medico-completo.pdf (2.3 MB)                                     │ │
│ │                                                                               │ │
│ │   ┌───────────────────────────────────────────────────────────────────┐     │ │
│ │   │                                                                   │     │ │
│ │   │                    🤖 Analisando documento...                    │     │ │
│ │   │                                                                   │     │ │
│ │   │   ████████████████████████████░░░░░░░░░░░░░░░░░░  72%          │     │ │
│ │   │                                                                   │     │ │
│ │   │   📖 Lendo página 18 de 25...                                   │     │ │
│ │   │   🔍 Identificando diagnósticos e recomendações                 │     │ │
│ │   │                                                                   │     │ │
│ │   │   ⏱️ Tempo estimado: 15 segundos                                │     │ │
│ │   │                                                                   │     │ │
│ │   └───────────────────────────────────────────────────────────────────┘     │ │
│ │                                                                               │ │
│ │   💡 Dica: Enquanto processamos, você pode começar outro documento          │ │
│ │                                                                               │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

Animações:
- Progress bar: Smooth animation, 100ms transitions
- Status text: Fade in/out entre mudanças
- Icon rotation: 🤖 gira suavemente
```

### Estado 3: Resultado da Análise
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ← Voltar ao Dashboard                                    👤 Dr. Ana   🚪 Sair   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   📄 PROCESSADOR DE PDFs > Resultado da Análise                                 │
│                                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ ✅ Análise Concluída - laudo-medico-completo.pdf                            │ │
│ │                                                                               │ │
│ │ ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 📊 RESUMO EXECUTIVO                                                      │ │ │
│ │ │                                                                           │ │ │
│ │ │ 👤 Paciente: João da Silva Santos                                       │ │ │
│ │ │ 📅 Data do Exame: 15/01/2025                                            │ │ │
│ │ │ 🏥 Instituição: Hospital São Lucas                                      │ │ │
│ │ │                                                                           │ │ │
│ │ │ 🔍 DIAGNÓSTICOS IDENTIFICADOS:                                          │ │ │
│ │ │ • Cardiopatia isquêmica moderada (CID I25.1)                           │ │ │
│ │ │ • Hipertensão arterial sistêmica (CID I10)                             │ │ │
│ │ │ • Dislipidemia mista (CID E78.2)                                       │ │ │
│ │ │                                                                           │ │ │
│ │ │ 💊 MEDICAÇÕES EM USO:                                                   │ │ │
│ │ │ • Atenolol 50mg 1x/dia                                                  │ │ │
│ │ │ • Sinvastatina 20mg 1x/dia                                              │ │ │
│ │ │ • AAS 100mg 1x/dia                                                      │ │ │
│ │ │                                                                           │ │ │
│ │ │ ⚡ PONTOS RELEVANTES PARA O PROCESSO:                        [Ver mais] │ │ │
│ │ └─────────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                               │ │
│ │ ┌─────────────┬─────────────┬─────────────┬─────────────┐                  │ │
│ │ │ 📥 BAIXAR   │ 📧 ENVIAR   │ ✍️ GERAR    │ 📄 NOVO    │                  │ │
│ │ │  ANÁLISE    │ POR EMAIL   │  QUESITOS   │ DOCUMENTO  │                  │ │
│ │ └─────────────┴─────────────┴─────────────┴─────────────┘                  │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ 📋 Detalhes Técnicos                                                    [-] │ │
│ │ Tempo de processamento: 23 segundos | Páginas: 25 | Confiança: 98%         │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

Interações:
- [Ver mais]: Expande seção com smooth animation
- Botões ação: Hover com elevação + tooltip
- Cards: Box-shadow sutil para hierarquia
```

## ✍️ Redator de Quesitos - Interface

### Estado 1: Configuração Inicial
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ← Voltar ao Dashboard                                    👤 Dr. Ana   🚪 Sair   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   ✍️ REDATOR DE QUESITOS                                                        │
│   Crie quesitos judiciais com inteligência artificial                           │
│                                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                               │ │
│ │  1️⃣ TIPO DE PROCESSO                                                         │ │
│ │  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                  │ │
│ │  │   👨‍⚕️ MÉDICO    │ │ 👷 TRABALHISTA │ │ 🚗 TRÂNSITO   │                  │ │
│ │  │   [SELECTED]   │ │                │ │               │                  │ │
│ │  └────────────────┘ └────────────────┘ └────────────────┘                  │ │
│ │                                                                               │ │
│ │  2️⃣ CONTEXTO DO CASO                                                        │ │
│ │  ┌─────────────────────────────────────────────────────────────────────┐   │ │
│ │  │ Descreva brevemente o caso (opcional):                              │   │ │
│ │  │                                                                     │   │ │
│ │  │ Ex: Paciente com sequelas de AVC solicita benefício por           │   │ │
│ │  │ incapacidade. Preciso questionar sobre limitações funcionais...   │   │ │
│ │  │                                                                     │   │ │
│ │  └─────────────────────────────────────────────────────────────────────┘   │ │
│ │                                                                               │ │
│ │  3️⃣ DOCUMENTOS DE REFERÊNCIA (Opcional)                                     │ │
│ │  ┌─────────────────────────────────────────────────────────────────────┐   │ │
│ │  │                         📎                                          │   │ │
│ │  │              Arraste laudos ou documentos                          │   │ │
│ │  │                    para análise                                    │   │ │
│ │  │                                                                     │   │ │
│ │  │              [ ADICIONAR DOCUMENTOS ]                               │   │ │
│ │  └─────────────────────────────────────────────────────────────────────┘   │ │
│ │                                                                               │ │
│ │              [ GERAR QUESITOS ]    [ USAR MODELO PADRÃO ]                   │ │
│ │                                                                               │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

Estados dos componentes:
- Radio buttons: Selected com borda azul 2px
- Textarea: Focus com borda azul, resize vertical only
- Buttons: Primary (azul) vs Secondary (cinza outline)
```

### Estado 2: Quesitos Gerados
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ← Voltar ao Dashboard                                    👤 Dr. Ana   🚪 Sair   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   ✍️ REDATOR DE QUESITOS > Resultado                                           │
│                                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │ ✅ Quesitos Gerados - Perícia Médica                                        │ │
│ │                                                                               │ │
│ │ ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 📝 QUESITOS PARA O PERITO                                   [ ✏️ Editar] │ │ │
│ │ │                                                                           │ │ │
│ │ │ 1. Queira o Sr. Perito informar qual o diagnóstico atual do(a)         │ │ │
│ │ │    periciando(a), especificando o CID correspondente.                   │ │ │
│ │ │                                                                           │ │ │
│ │ │ 2. O(a) periciando(a) apresenta limitações funcionais decorrentes       │ │ │
│ │ │    da patologia diagnosticada? Em caso positivo, especificar quais.     │ │ │
│ │ │                                                                           │ │ │
│ │ │ 3. As limitações identificadas impedem o exercício das atividades       │ │ │
│ │ │    laborais habituais do(a) periciando(a)?                             │ │ │
│ │ │                                                                           │ │ │
│ │ │ 4. Existe possibilidade de reabilitação profissional? Em quanto        │ │ │
│ │ │    tempo estima-se a recuperação?                                       │ │ │
│ │ │                                                                           │ │ │
│ │ │ 5. A incapacidade verificada é temporária ou definitiva?               │ │ │
│ │ │                                                                           │ │ │
│ │ │ [+ Adicionar quesito]                                                   │ │ │
│ │ └─────────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                               │ │
│ │ ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 💡 SUGESTÕES ADICIONAIS                                          [▼]    │ │ │
│ │ │ • Considere incluir quesito sobre nexo causal                          │ │ │
│ │ │ • Questione sobre medicações em uso                                    │ │ │
│ │ │ • Pergunte sobre exames complementares necessários                     │ │ │
│ │ └─────────────────────────────────────────────────────────────────────────┘ │ │
│ │                                                                               │ │
│ │ ┌───────────────┬───────────────┬───────────────┬───────────────┐          │ │
│ │ │ 📄 COPIAR     │ 📥 BAIXAR     │ 📧 ENVIAR     │ ✍️ NOVO      │          │ │
│ │ │   TEXTO       │   DOCX         │  EMAIL        │  QUESITO     │          │ │
│ │ └───────────────┴───────────────┴───────────────┴───────────────┘          │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

Funcionalidades:
- ✏️ Editar: Inline editing com save/cancel
- Drag & Drop: Reordenar quesitos
- Copy: Feedback visual "Copiado!"
- Sugestões: Expandir/colapsar smooth
```

## 🔧 Menu Lateral Rápido (Todos os Screens)
```
┌──────────┐
│ Acesso   │
│ Rápido   │
│          │
│ ┌──────┐ │
│ │ 📁   │ │  ← Hover: Tooltip "Meus Documentos"
│ │ Docs │ │     Click: Slide panel direita
│ └──────┘ │
│          │
│ ┌──────┐ │
│ │ ✍️   │ │  ← Badge com número se houver novos
│ │Textos│ │
│ └──────┘ │
│          │
│ ┌──────┐ │
│ │ 👥   │ │
│ │Client│ │
│ └──────┘ │
│          │
│ ┌──────┐ │
│ │ ⚙️   │ │  ← Visível apenas para admin
│ │Config│ │
│ └──────┘ │
└──────────┘

Comportamento:
- Fixed position right
- Z-index alto
- Mobile: Hidden, acessível via menu
```

## 📱 Componentes Mobile-Specific

### Bottom Navigation (Mobile)
```
┌────────────────────┐
│                    │
│   [Content Area]   │
│                    │
├────────────────────┤
│ 🏠   📁   ✍️   👥  │  ← Fixed bottom
│Home Docs Text Cli  │     48px altura
└────────────────────┘
```

### Drawer Menu (Mobile)
```
┌────────────────────┐
│ ← IAM Dashboard    │
├────────────────────┤
│ 👤 Dr. Ana Santos  │
│    ana@email.com   │
├────────────────────┤
│ 🏠 Início          │
│ 📁 Meus Documentos │
│ ✍️ Textos Gerados  │
│ 👥 Clientes        │
│ ⚙️ Configurações   │
├────────────────────┤
│ 🚪 Sair            │
└────────────────────┘
```

## 🎨 Micro-interações e Feedback

### Upload States
```
Default:            Drag Over:           Uploading:          Success:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│      📎     │    │      📎     │    │      ⏫     │    │      ✅     │
│             │    │   ░░░░░░░   │    │  ████░░░░░  │    │             │
│   Arraste   │    │   SOLTE     │    │    45%      │    │  Uploaded!  │
│   arquivo   │    │   AQUI!     │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                   (Blue glow)       (Progress bar)     (Green check)
```

### Button States
```
Default:            Hover:              Active:            Disabled:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   ANALISAR  │    │   ANALISAR  │    │ ANALISANDO..│    │   ANALISAR  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
(Blue bg)          (Darker blue)      (Loading spin)     (Gray, 50% opacity)
                   (Shadow)           (Pulsing)
```

### Notification Types
```
Success:                     Error:                      Info:
┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐
│ ✅ Análise concluída! │   │ ❌ Arquivo muito grande│   │ ℹ️ Processando...     │
└───────────────────────┘   └───────────────────────┘   └───────────────────────┘
(Green border)              (Red border)                (Blue border)
(Slide from top)            (Shake animation)           (Fade in)
```