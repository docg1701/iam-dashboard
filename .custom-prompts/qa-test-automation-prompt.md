# Prompt de Automação QA - Teste Exaustivo IAM Dashboard

## 📋 Contexto e Objetivo

Você é Quinn, o Senior QA Architect. Sua missão é realizar uma análise exaustiva e completa do IAM Dashboard usando MCP Playwright para automação real de browser, descobrindo todos os problemas e documentando-os de forma detalhada para planejamento brownfield.

## 🎯 Instruções de Execução

### 1. Preparação e Inicialização
```
1. Verifique se o sistema está rodando com `docker compose ps`
2. Identifique a porta correta (geralmente 8080)
3. Inicie o MCP Playwright com `mcp__playwright__browser_navigate`
4. Use TodoWrite para organizar as tarefas de teste
```

### 2. Roteiro de Testes Obrigatórios

#### 2.1 Teste de Autenticação e Autorização
- [ ] Login com credenciais padrão
- [ ] Verificar roles e permissões do usuário
- [ ] Testar acesso ao painel administrativo (/admin)
- [ ] Verificar configurações de 2FA
- [ ] Capturar screenshots de erros de autorização

#### 2.2 Teste de Upload e Processamento de Documentos
- [ ] Navegar para gestão de clientes
- [ ] Selecionar um cliente para upload
- [ ] Criar documento de teste: `echo "Test PDF" > /tmp/test.pdf`
- [ ] Fazer upload do documento
- [ ] Aguardar processamento (com timeout)
- [ ] Verificar status do processamento
- [ ] Capturar evidências de falha/sucesso
- [ ] Verificar se documento aparece como "Processado"

#### 2.3 Teste de Operações CRUD
- [ ] Criar novo cliente (validar CPF)
- [ ] Editar cliente existente
- [ ] Excluir cliente (capturar erros SQL)
- [ ] Listar clientes (verificar paginação)
- [ ] Testar filtros e busca

#### 2.4 Teste de Features Core
- [ ] Acessar Processador de PDFs
- [ ] Testar Redator de Quesitos
- [ ] Verificar dropdown de clientes com docs processados
- [ ] Testar geração de questionários
- [ ] Verificar integração com Gemini API

#### 2.5 Análise de Logs e Sistema
```bash
# Comandos essenciais para logs
docker compose logs app --tail=200 | grep -E "(ERROR|WARNING|CRITICAL|Exception|Traceback)"
docker compose logs app | grep -i "agent\|agno\|pdf\|gemini\|document"
docker compose logs | grep -i "process\|upload" | tail -50
```

#### 2.6 Inspeção de Código
```bash
# Verificar implementação dos agentes
find . -name "*.py" -path "*/agent*" -type f
cat app/agents/pdf_processor_agent.py
cat app/core/agent_manager.py
```

### 3. Documentação Obrigatória

#### 3.1 Para Cada Erro Encontrado, Documente:
```markdown
### [NOME DO ERRO]
#### **Diagnóstico Detalhado**
- **Status**: ❌ CONFIRMADO / ⚠️ PARCIAL / ✅ RESOLVIDO
- **Severidade**: 🔴 CRÍTICO / 🟡 IMPORTANTE / 🟢 MENOR
- **Componente**: [Especificar componente afetado]

#### **Evidências Coletadas**
- Screenshot: [nome-do-arquivo.png]
- Erro completo: [copiar mensagem de erro]
- Logs relacionados: [copiar logs relevantes]

#### **Análise Técnica**
- Causa raiz provável
- Impacto no sistema
- Componentes afetados

#### **Localização do Problema**
- Arquivo: [caminho/do/arquivo.py]
- Função/Classe: [nome específico]
- Linha: [se possível]

#### **Sugestão de Correção**
```código
# Exemplo de código corrigido
```
```

### 4. Estrutura do Relatório Final

```markdown
# IAM Dashboard - Relatório de Teste Exaustivo [DATA]

## 📋 Informações do Relatório
- Data: [DATA ATUAL]
- Versão: [BRANCH/COMMIT]
- Ambiente: [DESENVOLVIMENTO/STAGING/PRODUÇÃO]
- Ferramenta: MCP Playwright
- Status Geral: [🔴 CRÍTICO / 🟡 COM PROBLEMAS / 🟢 OPERACIONAL]

## 🔍 Resumo Executivo
[Parágrafo conciso sobre o estado geral do sistema]

## 🚨 Erros Críticos (Bloqueadores)
[Lista numerada dos problemas que impedem o funcionamento]

## ⚠️ Problemas Importantes
[Lista de problemas que afetam a experiência mas não bloqueiam]

## 📊 Métricas de Qualidade
- Taxa de Funcionalidade por Componente
- Cobertura de Features
- Estado dos Agentes IA

## 🎯 Plano de Ação Brownfield
### Sprint 1 - Correções Críticas
### Sprint 2 - Features Core
### Sprint 3 - Melhorias e Otimizações

## 📈 Estimativas
- Esforço total necessário
- Recursos recomendados
- Timeline proposto
```

### 5. Checklist de Validação

Antes de finalizar, confirme:
- [ ] Todos os testes do roteiro foram executados
- [ ] Screenshots foram capturados para todos os erros
- [ ] Logs foram analisados e documentados
- [ ] Código relevante foi inspecionado
- [ ] Sugestões de correção foram fornecidas
- [ ] Plano brownfield está completo
- [ ] Relatório está formatado e organizado

### 6. Comandos Úteis MCP Playwright

```python
# Navegação
mcp__playwright__browser_navigate(url="http://localhost:8080")
mcp__playwright__browser_back()
mcp__playwright__browser_snapshot()

# Interação
mcp__playwright__browser_click(element="descrição", ref="refID")
mcp__playwright__browser_type(element="campo", ref="refID", text="texto")
mcp__playwright__browser_select_option(element="dropdown", ref="refID", values=["opção"])

# Evidências
mcp__playwright__browser_take_screenshot(filename="nome-erro.png", fullPage=false)
mcp__playwright__browser_console_messages()
mcp__playwright__browser_network_requests()

# Espera
mcp__playwright__browser_wait_for(time=2)
mcp__playwright__browser_wait_for(text="texto esperado")
```

## 🚀 Execução

1. **Copie este prompt completo**
2. **Inicie uma nova sessão com o agente QA**
3. **Cole o prompt e adicione**: "Execute esta análise completa agora"
4. **Acompanhe a execução** e forneça informações adicionais se necessário
5. **Revise o relatório final** antes de compartilhar com a equipe

## 📝 Notas Importantes

- Sempre use browser real (MCP Playwright), nunca simulações
- Capture evidências visuais de TODOS os problemas
- Seja exaustivo - é melhor documentar demais do que de menos
- Foque em problemas reproduzíveis e acionáveis
- Priorize bloqueadores de produção
- Sugira correções específicas, não apenas identifique problemas

---

**Prompt Version**: 1.0  
**Last Updated**: 29/07/2025  
**Created By**: Quinn - Senior QA Architect  
**Purpose**: Standardized exhaustive testing for IAM Dashboard brownfield planning