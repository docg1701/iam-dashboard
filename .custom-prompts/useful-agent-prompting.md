# Custom command-line prompts to use with BMAD agents

## DEV Agent
### Develop Story from start minding the BMAD Method:

```markdown
*develop-story docs/stories/[story-filename] e siga as instruções abaixo:
- FOLLOW the BMAD Method;
- Read docs/architecture/index.md and then read files in docs/architecture AS REQUIRED by the STORY FILE;
- IF CODING FRONTEND: read every UI/UX file in docs/architecture;
- SPAWN 2 agents in parallel to speed it up IDEPENDENT TASKS;
- ALWAYS use ABSOLUTE path to check files, directories and run scripts;
- USE SCRIPTS in scripts/ to run tests.
``` 

### Develop Story Again fixing errors and bugs:

```markdown
[ULTRATHINK] *develop-story according to the BMAD Method. Read core-config. Read docs/architecture/index.md and then all needed docs/architecture/*.md. Spawn 2 agents in parallel. And fix all the the remaning issues of docs/stories/STORY-FILENAME
``` 

### Make the Agent do a through review and honest report about his own work

```markdown
[ULTRATHINK] I need you to do a real and honest through assessment of your work in this last story you developed. Do all the checking, testing and step-by-step reading. Don't assume anything, test and prove it. Be very true about it and then fix the report section of the story file.
```

### Refatorar testes com mocking indevido e exagerado no Backend

```markdown
Refatore os testes de backend seguindo os padrões da story docs/stories/1.1.project-setup-and-development-environment.md - remova mocks de business logic e mantenha apenas mocks de external dependencies. Use AGENTS em paralelo para acelerar o processo.
```

### Refatorar testes com mocking indevido e exagerado no Frontend

```markdown
develop-story docs/stories/1.6.*.md - analise o arquivo de story e escreva APENAS os testes de FRONTEND que lá estão descritos. Não faça mock de código, faça mock apenas quando ESTRITAMENTE NECESSÁRIO e apenas de API EXTERNA. Leia core-config.yaml e os arquivos necessários em docs/architecture/*.md incluindo todos os arquivos de UI, UX e testing standards.
```

## Insistir na pesquisa de testes com mock exagerado na base de código
```markdown
Procure novamente por mocks escondidos nos arquivos de testes de FRONTEND que vao contra as diretrizes no CLAUDE.md
```

```markdown
Procure novamente por mocks escondidos nos arquivos de testes de BACKEND que vao contra as diretrizes no CLAUDE.md
```

## QA Agent

### Make a proper QA assesment

```markdown
[ULTRATHINK] *review docs/stories/FILENAME. I need you to do a real and honest through assessment of the DEV Agent's work in this story. Do all the checking, testing and step-by-step reading. Don't assume anything, test and prove it. Be very true about it.
```

```markdown
*review docs/stories/[story-file] para corrigir todos os testes que falham no [frontend, backend, quality, database, docker etc] -  ULTRATHINK - use scripts para testes - vença todos os testes - não modifique a documentação - pense e planeje e revise o plano antes de executar correções - lembre-se que o projeto usa DOCKER - para modificar ou escrever testes siga docs/architecture/testing-strategy.md
```

```markdown
[ultrathink] Rode o script de testes scripts/run-frontend-tests.sh e em seguida:
- leia os logs e descubra o coverage real;
- Estude a estratégia em "Test Configuration Troubleshooting" no CLAUDE.md;
- Use o MCP Context7 para atualizar seu conhecimento sobre as bibliotecas e frameworks utilizados no projeto;
- Evite erros de sintaxe e correção de bugs que geram outrosbugs: atualize seu conhecimento com MCP Context7;
- Use 2 agents em paralelo para acelerar TASKS que podem ser executadas de forma independente;
- Vença todos os TESTS e atinga a COVERAGE mínima esperada; 
- NÃO USE type Any, siga as recomendações em CLAUDE.md;
- NÃO TOME DECISÕES SEM PLANEJAR: Pense, planeje, revise o plano e só então execute;
- DADOS Fundamentais sobre o projeto: Roda em containers docker;
- CONTEXTO INDISPENSÁVEL: Leia docs/architecture/coding-standards.md, tech-stack.md, source-tree.md e testing-strategy.md;
- PROIBIDO: Não modifique a DOCUMENTAÇÃO nem a ARQUITETURA do projeto;
- Resolva todos os problemas.
```
