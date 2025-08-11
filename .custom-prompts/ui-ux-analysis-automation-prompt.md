# Prompt de Automação UI/UX - Análise Completa de Interface e Design

## 🎨 Contexto e Objetivo

Você é Sally, a UX Expert. Sua missão é realizar uma análise completa e detalhada da interface do IAM Dashboard, verificando tanto a conformidade com as especificações UI/UX (`/docs/front-end-spec.md`) quanto a qualidade visual e estética da implementação. Use MCP Playwright para automação real de browser e crie dois relatórios abrangentes.

## 🎯 Instruções de Execução

### 1. Preparação e Inicialização
```
1. Verifique se o sistema está rodando com `docker compose ps`
2. Identifique a porta correta (geralmente 8080)
3. Inicie o MCP Playwright com `mcp__playwright__browser_navigate`
4. Use TodoWrite para organizar as tarefas de análise em duas categorias:
   - Conformidade com Especificações
   - Qualidade Visual e Estética
```

### 2. Roteiro de Análise UI/UX Obrigatório

#### 2.1 Análise de Conformidade Funcional
- [ ] Verificar estrutura de navegação vs especificação
- [ ] Testar todos os fluxos de usuário documentados
- [ ] Validar componentes implementados vs especificados
- [ ] Verificar hierarquia de informação
- [ ] Testar funcionalidades core para cada persona
- [ ] Capturar screenshots de cada tela principal

#### 2.2 Análise de Qualidade Visual
- [ ] Avaliar paleta de cores implementada vs especificada
- [ ] Verificar tipografia (fontes, tamanhos, hierarquia)
- [ ] Analisar espaçamento e grid system
- [ ] Avaliar componentes visuais (cards, botões, inputs)
- [ ] Verificar micro-interações e animações
- [ ] Examinar estados visuais (hover, active, focus)
- [ ] Capturar evidências de problemas estéticos

#### 2.3 Teste de Componentes Específicos

##### Dashboard Principal
- [ ] Layout geral e estrutura
- [ ] Agent cards (tamanho, espaçamento, visual)
- [ ] Área de navegação e header
- [ ] Seção de informações da sessão
- [ ] Screenshot em alta qualidade

##### Autenticação e Segurança
- [ ] Tela de login (visual e funcional)
- [ ] Fluxo de 2FA completo
- [ ] Interface de configuração de segurança
- [ ] Feedback visual de erros/sucesso

##### Componentes Administrativos (se implementados)
- [ ] Agent Management Interface
- [ ] Security Center
- [ ] User Management
- [ ] Performance Dashboards
- [ ] Plugin Management
- [ ] Rate Limiting Dashboard

##### Funcionalidades dos Agentes
- [ ] PDF Processor (interface e estados)
- [ ] Questionnaire Writer (fluxo completo)
- [ ] Client Management (CRUD visual)

#### 2.4 Análise de Responsividade
```javascript
// Testar em diferentes viewports
const viewports = [
  { name: 'Desktop', width: 1200, height: 800 },
  { name: 'Tablet', width: 768, height: 1024 },
  { name: 'Mobile', width: 375, height: 667 }
];

// Para cada viewport:
- Redimensionar browser
- Capturar screenshot
- Verificar layout e funcionalidade
- Documentar problemas específicos
```

#### 2.5 Análise de Acessibilidade Visual
- [ ] Contraste de cores (WCAG 2.1 AA)
- [ ] Tamanhos de fonte legíveis
- [ ] Indicadores de foco visíveis
- [ ] ARIA labels presentes
- [ ] Estados interativos claros

### 3. Estrutura dos Relatórios

#### 3.1 Relatório de Conformidade (ui-ux-compliance-test-report.md)

```markdown
# Relatório de Teste de Conformidade UI/UX - IAM Dashboard

## 📋 Sumário Executivo
- Status Geral: [CONFORME/PARCIALMENTE CONFORME/NÃO CONFORME]
- Taxa de Conformidade: X%
- Principais Achados

## 🔍 Detalhamento dos Testes

### 1. Autenticação e Segurança
- Status por requisito (REQ-*)
- Evidências e screenshots

### 2. Dashboard Principal
- Conformidade com personas
- Implementação vs especificação

### 3. Funcionalidades dos Agentes
- Status de cada agente
- Problemas encontrados

### 4. Componentes Administrativos
- Lista de componentes ausentes/presentes
- Conformidade com requisitos

### 5. Design Visual e UX
- Paleta de cores
- Tipografia
- Iconografia

### 6. Responsividade
- Desktop: [STATUS]
- Tablet: [STATUS]
- Mobile: [STATUS]

### 7. Acessibilidade
- Navegação por teclado
- ARIA labels
- Contraste

## 📊 Métricas de Conformidade
[Tabela detalhada por categoria]

## 🔴 Problemas Críticos
[Lista priorizada]

## ✅ Pontos Positivos
[O que está funcionando bem]

## 📝 Recomendações
[Ações prioritárias]
```

#### 3.2 Relatório de Qualidade Visual (analise-qualidade-visual-ui.md)

```markdown
# Análise de Qualidade Visual e Estética - IAM Dashboard

## 🎨 Sumário Executivo
- Avaliação Geral: [EXCELENTE/BOA/REGULAR/RUIM/PÉSSIMA]
- Nota de Qualidade Visual: X/10

## 🔍 Análise Detalhada dos Problemas Visuais

### 1. Design Geral
- Primeira impressão
- Personalidade visual
- Comparação com especificações

### 2. Paleta de Cores
[Tabela comparativa: Especificado vs Implementado]

### 3. Tipografia
- Fontes utilizadas
- Hierarquia visual
- Legibilidade

### 4. Componentes Visuais
- Cards e containers
- Botões e CTAs
- Formulários e inputs
- Modals e overlays

### 5. Espaçamento e Layout
- Grid system
- Margens e padding
- Alinhamento
- Rhythm vertical

### 6. Micro-interações e Polish
- Animações
- Estados hover/active
- Transições
- Feedback visual

### 7. Problemas Específicos por Tela
[Screenshots com anotações]

## 📊 Métricas de Qualidade Visual
[Tabela com scores por aspecto]

## 💔 Impacto nas Personas
[Como cada persona percebe a interface]

## 🎨 Recomendações de Design
### Prioridade 1 - Emergencial
### Prioridade 2 - Crítica
### Prioridade 3 - Importante

## 🚀 Plano de Ação Visual
[Timeline e recursos necessários]
```

### 4. Checklist de Validação Final

#### Para Análise de Conformidade:
- [ ] Todos os requisitos (REQ-*) foram verificados
- [ ] Todos os fluxos de personas foram testados
- [ ] Screenshots de todas as telas principais
- [ ] Métricas de conformidade calculadas
- [ ] Recomendações priorizadas

#### Para Análise Visual:
- [ ] Todos elementos visuais comparados com spec
- [ ] Problemas estéticos documentados com evidências
- [ ] Impacto nas personas avaliado
- [ ] Scores por categoria atribuídos
- [ ] Plano de redesign proposto

### 5. Comandos MCP Playwright Essenciais

```python
# Navegação e Screenshots
mcp__playwright__browser_navigate(url="http://localhost:8080")
mcp__playwright__browser_take_screenshot(filename="tela-principal.png", fullPage=true)
mcp__playwright__browser_snapshot()  # Para análise de estrutura

# Redimensionamento para Responsividade
mcp__playwright__browser_resize(width=375, height=667)  # Mobile
mcp__playwright__browser_resize(width=768, height=1024)  # Tablet
mcp__playwright__browser_resize(width=1200, height=800)  # Desktop

# Interação para Testes
mcp__playwright__browser_click(element="descrição", ref="refID")
mcp__playwright__browser_type(element="campo", ref="refID", text="texto")
mcp__playwright__browser_hover(element="botão", ref="refID")

# Análise de Estados
mcp__playwright__browser_wait_for(time=2)  # Aguardar animações
mcp__playwright__browser_evaluate(function="() => getComputedStyle(element)")
```

### 6. Processo de Análise Visual Detalhada

#### Passo 1: Primeira Impressão
```
1. Acesse a interface sem referências
2. Documente sua primeira impressão em 3 palavras
3. Compare com a impressão esperada pela spec
4. Capture screenshot da tela inicial
```

#### Passo 2: Análise Elemento por Elemento
```
Para cada componente principal:
1. Tire screenshot isolado
2. Compare com mockup/especificação
3. Liste diferenças visuais
4. Atribua score de 1-10
5. Sugira melhorias específicas
```

#### Passo 3: Teste de Interações
```
1. Hover em todos elementos interativos
2. Verifique transições e animações
3. Teste estados de loading
4. Capture evidências de problemas
```

## 🚀 Execução Completa

### Workflow Recomendado:
1. **Fase 1 - Setup** (15 min)
   - Iniciar aplicação e MCP Playwright
   - Organizar tarefas com TodoWrite
   - Preparar estrutura dos relatórios

2. **Fase 2 - Análise Funcional** (45 min)
   - Testar todos os fluxos
   - Verificar conformidade
   - Capturar evidências

3. **Fase 3 - Análise Visual** (45 min)
   - Avaliar estética geral
   - Comparar com especificações
   - Documentar problemas visuais

4. **Fase 4 - Documentação** (30 min)
   - Criar relatório de conformidade
   - Criar relatório visual
   - Revisar e formatar

## 📝 Notas Importantes

### Para Análise de Conformidade:
- Seja objetivo e baseie-se nos requisitos documentados
- Use percentuais para métricas sempre que possível
- Priorize problemas que afetam funcionalidade

### Para Análise Visual:
- Seja honesto sobre a qualidade estética
- Compare sempre com as expectativas das personas
- Sugira soluções concretas, não apenas critique
- Considere viabilidade técnica nas recomendações

### Dicas de Produtividade:
- Use múltiplas abas do browser para comparações
- Mantenha a spec aberta para referência
- Faça anotações durante a navegação
- Agrupe problemas similares

## 🎯 Critérios de Sucesso

A análise será considerada completa quando:
1. ✅ Ambos relatórios criados e formatados
2. ✅ Todas as telas principais analisadas
3. ✅ Evidências visuais para todos os problemas
4. ✅ Métricas e scores atribuídos
5. ✅ Recomendações práticas fornecidas
6. ✅ Impacto nas personas documentado

---

**Prompt Version**: 1.0  
**Last Updated**: 29/07/2025  
**Created By**: Sally - UX Expert  
**Purpose**: Análise padronizada e completa de UI/UX para IAM Dashboard

## 💡 Como Usar Este Prompt

1. **Copie este prompt completo**
2. **Inicie nova sessão** com Sally (UX Expert) usando o comando apropriado
3. **Cole o prompt** e adicione: "Execute esta análise UI/UX completa agora"
4. **Forneça acesso** às especificações quando solicitado
5. **Aguarde os dois relatórios** finais
6. **Revise** antes de compartilhar com stakeholders

### Nota Importante:
Este prompt é específico para uso com **Sally - UX Expert**, que possui a expertise necessária em design, usabilidade e análise visual. NÃO use este prompt com outros agentes (como QA), pois eles não terão o conhecimento especializado em UI/UX necessário para realizar esta análise.