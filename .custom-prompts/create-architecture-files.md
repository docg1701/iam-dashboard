# Prompt Estruturado para Criação de Arquivos de Arquitetura

## **PROMPT PARA AGENT ARCHITECT**

```
[ULTRATHINK] Você precisa realizar uma operação específica de criação e correção de arquivos de arquitetura baseada em templates do BMad Method. Siga exatamente estas instruções:

### CONTEXTO:
Tenho um projeto com o arquivo `docs/architecture.md` já criado, mas preciso gerar 4 arquivos específicos de arquitetura que estão faltando e são referenciados em tarefas do BMad Method, causando referências quebradas.

### OPERAÇÃO REQUERIDA:
Analisar completamente a estrutura do projeto atual e criar/corrigir 4 arquivos específicos baseados no template `.bmad-core/templates/fullstack-architecture-tmpl.yaml`.

### ARQUIVOS ALVO (paths completos):

1. **`/docs/architecture/unified-project-structure.md`**
2. **`/docs/architecture/tech-stack.md`**  
3. **`/docs/architecture/coding-standards.md`**
4. **`/docs/architecture/source-tree.md`**

### INSTRUÇÕES DETALHADAS:

#### PASSO 1: ESTUDO COMPLETO DO PROJETO
**CRÍTICO**: Antes de escrever qualquer arquivo, você DEVE estudar e conhecer profundamente todo o projeto atual para ter contexto suficiente e evitar alucinações ou invenções.

**Análise Obrigatória:**
- Leia completamente o arquivo `docs/architecture.md` para entender o contexto e objetivos
- Explore toda a estrutura de diretórios do projeto (use LS e Glob extensivamente)
- Examine arquivos-chave em `app/` para entender a arquitetura real implementada
- Identifique todas as tecnologias realmente usadas (verifique pyproject.toml, requirements, imports)
- Entenda os padrões de código existentes (examine múltiplos arquivos .py)
- Verifique configurações existentes (docker-compose.yml, .env.example, etc.)
- Analise testes existentes para entender padrões de testing
- Examine documentação existente em `docs/` para manter consistência

**Validação de Conhecimento:**
- Liste as tecnologias REAIS encontradas no projeto
- Identifique a estrutura de diretórios ATUAL
- Confirme os padrões de código EXISTENTES
- NUNCA invente ou assuma tecnologias que não estão presentes
- SEMPRE baseie as informações no que realmente existe no projeto

#### PASSO 2: EXTRAIR TEMPLATES
- Abra o arquivo `.bmad-core/templates/fullstack-architecture-tmpl.yaml`
- Localize as seções específicas:
  - `unified-project-structure` (para o arquivo 1)
  - `tech-stack` com a tabela de tecnologias (para o arquivo 2)  
  - `coding-standards` com regras críticas (para o arquivo 3)
- Use essas seções como base estrutural para os novos arquivos

#### PASSO 3: CRIAR unified-project-structure.md
- Path: `/docs/architecture/unified-project-structure.md`
- Base: Seção `unified-project-structure` do template fullstack
- Adapte a estrutura para o stack tecnológico REAL identificado no projeto
- Inclua: estrutura de diretórios REAL, convenções de nomenclatura OBSERVADAS, padrões de navegação EXISTENTES
- Mantenha consistência com a arquitetura descrita em `docs/architecture.md`
- Use apenas tecnologias e estruturas que você CONFIRMOU que existem

#### PASSO 4: PROCESSAR tech-stack.md  
- Path: `/docs/architecture/tech-stack.md`
- Base: Seção `tech-stack-table` do template fullstack
- Formato: Tabelas com colunas [Category, Technology, Version, Purpose, Rationale]
- Inclua APENAS as tecnologias identificadas e confirmadas no projeto real
- Use versões REAIS encontradas em pyproject.toml, requirements.txt, imports
- Use versões com `>=` (minimum ranges) conforme padrão do projeto
- Categorias baseadas nas tecnologias REALMENTE presentes
- NUNCA inclua tecnologias que não estão sendo usadas no projeto

#### PASSO 5: PROCESSAR coding-standards.md
- Path: `/docs/architecture/coding-standards.md`
- Base: Seção `coding-standards` do template fullstack
- Foque em regras CRÍTICAS específicas do projeto REAL
- Inclua: padrões de arquitetura OBSERVADOS no código, convenções de nomenclatura EXISTENTES, regras de segurança IMPLEMENTADAS
- Adapte para o stack tecnológico ESPECÍFICO confirmado no projeto
- Baseie nos padrões de código que você OBSERVOU nos arquivos existentes
- Mantenha consistência com as práticas descritas em `docs/architecture.md`

#### PASSO 6: PROCESSAR source-tree.md
- Path: `/docs/architecture/source-tree.md`
- Expanda/crie o arquivo com estrutura REAL do projeto
- Base na estrutura CONFIRMADA dos diretórios `app/`, `tests/`, `docs/`, etc.
- Inclua: propósito de cada diretório REAL, padrões de organização OBSERVADOS, workflows EXISTENTES
- Adicione padrões de navegação baseados na estrutura REAL
- Use apenas diretórios e arquivos que você CONFIRMOU que existem

### CRITÉRIOS DE QUALIDADE:

#### FIDELIDADE À REALIDADE:
- ZERO alucinações - use apenas o que existe no projeto
- ZERO invenções - não adicione tecnologias não presentes
- ZERO suposições - confirme tudo através de análise dos arquivos
- Toda informação deve ser baseada em evidências encontradas no projeto

#### CONSISTÊNCIA:
- Todos os arquivos devem ser consistentes entre si
- Referenciar as mesmas tecnologias e versões REAIS
- Usar nomenclatura OBSERVADA no projeto

#### ESPECIFICIDADE:
- Adaptar para o stack tecnológico CONFIRMADO do projeto
- Não usar exemplos genéricos - usar o que EXISTE no projeto
- Incluir paths REAIS e estruturas REAIS

#### COMPLETUDE:
- Cada arquivo deve ser auto-suficiente
- Incluir toda informação necessária para desenvolvedores
- Resolver as referências quebradas das tarefas BMad

#### PRATICIDADE:
- Fornecer guidance real e utilizável baseado no projeto REAL
- Incluir exemplos práticos baseados no código EXISTENTE
- Facilitar navegação e desenvolvimento do projeto ATUAL

### VALIDAÇÃO FINAL:
Após criar/processar todos os arquivos, verifique:
- [ ] Todos os 4 arquivos estão nos paths corretos
- [ ] Conteúdo baseado nos templates do fullstack-architecture-tmpl.yaml
- [ ] Informações consistentes entre todos os arquivos
- [ ] Stack tecnológico reflete EXATAMENTE o projeto real
- [ ] NENHUMA informação inventada ou alucinada
- [ ] Tudo baseado em análise REAL do projeto atual
- [ ] Referências quebradas foram resolvidas

### IMPORTANTE:
- SEMPRE leia primeiro o `docs/architecture.md` para entender o contexto
- SEMPRE estude completamente o projeto antes de escrever qualquer arquivo
- SEMPRE use como base estrutural o template `.bmad-core/templates/fullstack-architecture-tmpl.yaml`
- SEMPRE adapte para o stack tecnológico ESPECÍFICO confirmado no projeto
- NUNCA use informações genéricas - use APENAS o que existe no projeto real
- NUNCA invente ou assuma - confirme tudo através de análise dos arquivos
```

## **INSTRUÇÕES DE USO:**

1. **Copie o prompt completo** acima (apenas o conteúdo entre as aspas)
2. **Cole para o Agent Architect** em uma nova conversa  
3. **Aguarde a execução** - o agente seguirá todas as etapas automaticamente
4. **Valide os resultados** - todos os 4 arquivos estarão prontos e consistentes

Este prompt é **auto-contido** e **reproduzível** - você pode usá-lo em qualquer projeto futuro que tenha a mesma necessidade!