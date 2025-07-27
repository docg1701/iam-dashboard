# IAM DASHBOARD - SISTEMA DE ADVOCACIA SAAS

Este arquivo fornece orientações completas para trabalhar com o projeto IAM Dashboard, um sistema SaaS de agentes autônomos para escritórios de advocacia.

## Visão Geral do Projeto

### Contexto e Propósito
O IAM Dashboard é uma plataforma SaaS modular projetada para escritórios de advocacia, com arquitetura de agentes autônomos acessados através de um painel de ícones. O sistema automatiza tarefas cognitivas complexas como análise de documentos e redação jurídica usando LLMs (Google Gemini API).

### Tecnologias Principais
- **Frontend:** NiceGUI (interface web responsiva)
- **Backend:** FastAPI (API RESTful)
- **Banco de Dados:** PostgreSQL com extensão pgvector
- **IA/LLM:** Google Gemini 2.5 Pro e Flash API
- **Processamento de Documentos:** PyMuPDF, PyTesseract
- **Indexação:** Llama-Index para RAG (Retrieval-Augmented Generation)
- **Framework de Agentes:** Agno
- **Autenticação:** Python-JOSE com 2FA (PyOTP)
- **Injeção de Dependência:** python-dependency-injector
- **Processamento Assíncrono:** Celery + Redis
- **OCR:** Tesseract local ou API Gemini

## 🧱 Arquitetura e Estrutura do Código

### Estrutura de Diretórios
```
iam-dashboard/
├── app/
│   ├── main.py                 # Entry point da aplicação
│   ├── core/                   # Módulos fundamentais
│   │   ├── auth.py            # Sistema de autenticação
│   │   └── database.py        # Configurações do banco
│   ├── models/                 # Modelos SQLAlchemy
│   │   ├── base.py
│   │   ├── user.py
│   │   └── client.py
│   ├── repositories/           # Camada de acesso a dados
│   ├── services/              # Lógica de negócio
│   ├── ui_components/         # Componentes NiceGUI
│   ├── agents/                # Agentes autônomos (Agno)
│   ├── api/                   # Endpoints FastAPI
│   └── workers/               # Tarefas Celery
├── alembic/                   # Migrações do banco
├── tests/                     # Testes organizados
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                      # Documentação do projeto
└── scripts/                   # Scripts utilitários
```

### Princípios de Arquitetura
- **Modularidade:** Cada responsabilidade em módulos separados
- **Processamento Assíncrono:** Celery para operações pesadas
- **API-First:** FastAPI como contrato central
- **Arquitetura de Camadas:** Separação clara entre UI, API, serviços e dados
- **Injeção de Dependência:** Desacoplamento de componentes

## 🛠️ Ambiente de Desenvolvimento

### Configuração Inicial
```bash
# Instalar UV (gerenciador de pacotes Python)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Criar ambiente virtual
uv venv

# Instalar dependências
uv sync

# Configurar banco PostgreSQL
docker-compose up -d postgres redis

# Executar migrações
uv run alembic upgrade head
```

### Comandos de Desenvolvimento
```bash
# Executar aplicação
uv run python app/main.py

# Executar testes
uv run pytest

# Executar testes com cobertura
uv run pytest --cov=app --cov-report=html

# Formatação de código
uv run black app/

# Linting
uv run ruff check app/

# Type checking
uv run mypy app/

# Gerar migração
uv run python scripts/generate_migration.py "description"
```

## 📋 Padrões de Código

### Estilo Python
- **Formatador:** Black (linha máxima: 88 caracteres)
- **Linter:** Ruff com regras configuradas
- **Type Hints:** Obrigatório em todas as funções públicas
- **Docstrings:** Estilo Google para funções públicas
- **Convenções de Nomenclatura:**
  - Variáveis/funções: `snake_case`
  - Classes: `PascalCase`
  - Constantes: `UPPER_SNAKE_CASE`
  - Atributos privados: `_leading_underscore`

### Estrutura de Componentes NiceGUI
```python
def component_name() -> None:
    """Breve descrição do componente."""
    with ui.column().classes("container-classes"):
        ui.label("Título").classes("title-classes")
        
        with ui.row().classes("row-classes"):
            ui.button("Ação", on_click=handle_action)
```

### Padrão de Serviços
```python
class ServiceName:
    """Serviço responsável por [funcionalidade]."""
    
    def __init__(self, repository: RepositoryType) -> None:
        self._repository = repository
    
    async def method_name(self, param: Type) -> ReturnType:
        """Descrição do método."""
        # Implementação
```

## 🧪 Estratégia de Testes

### Estrutura de Testes
- **Testes Unitários:** Testam componentes isoladamente
- **Testes de Integração:** Testam fluxos completos
- **Testes E2E:** Testam interface do usuário

### Playwright MCP para Testes de Browser, Interface, UI e UX
**OBRIGATÓRIO:** Para qualquer teste que necessite de browser automation, SEMPRE use o Playwright via MCP. 

#### Tools disponíveis para testes
**ACESSE:** https://github.com/microsoft/playwright-mcp/blob/main/README.md#tools

### Padrões de Teste
```python
import pytest
from unittest.mock import AsyncMock

class TestServiceName:
    """Testes para ServiceName."""
    
    @pytest.fixture
    def service(self, mock_repository):
        return ServiceName(mock_repository)
    
    async def test_method_success(self, service):
        # Arrange
        expected_result = "expected"
        
        # Act
        result = await service.method_name("param")
        
        # Assert
        assert result == expected_result
```

## 🔧 Configuração e Variáveis de Ambiente

### Arquivo .env (Exemplo)
```bash
# Aplicação
APP_NAME="IAM Dashboard"
DEBUG=false
SECRET_KEY="your-secret-key-here"

# Banco de Dados
DATABASE_URL="postgresql://user:password@localhost:5432/iam_dashboard"

# Redis
REDIS_URL="redis://localhost:6379/0"

# Google Gemini API
GEMINI_API_KEY="your-gemini-api-key"

# Autenticação
JWT_SECRET_KEY="your-jwt-secret"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES=30
```

## 🚨 Tratamento de Erros

### Hierarquia de Exceções
```python
class IAMDashboardError(Exception):
    """Exceção base do sistema."""

class AuthenticationError(IAMDashboardError):
    """Erro de autenticação."""

class DocumentProcessingError(IAMDashboardError):
    """Erro no processamento de documentos."""
```

### Logging Estruturado
```python
import structlog

logger = structlog.get_logger()

# Log com contexto
logger.info(
    "Document processed",
    user_id=user.id,
    document_id=doc.id,
    processing_time=elapsed_time
)
```

## 🤖 Agentes Autônomos (Agno Framework)

### Estrutura de um Agente
```python
from agno import Agent

class ProcessorAgent(Agent):
    """Agente processador de PDFs."""
    
    def __init__(self, name: str = "pdf_processor"):
        super().__init__(name)
        self.gemini_client = GeminiClient()
    
    async def process_document(self, document_path: str) -> dict:
        """Processa um documento PDF."""
        # Implementação do processamento
```

### MVP: Agentes Implementados
1. **Processador de PDFs:** Ingestão e análise de documentos
2. **Redator de Quesitos:** Geração de quesitos judiciais

## 📊 Banco de Dados e Migrações

### Convenções de Nomenclatura
- **Tabelas:** `snake_case` (ex: `user_clients`, `legal_documents`)
- **Primary Keys:** `{entity}_id` (ex: `user_id`, `client_id`)
- **Foreign Keys:** `{referenced_entity}_id`
- **Timestamps:** `{action}_at` (ex: `created_at`, `updated_at`)
- **Booleans:** `is_{state}` (ex: `is_active`, `is_processed`)

### Exemplo de Modelo
```python
from sqlalchemy import Column, String, DateTime, Boolean
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
```

## 🔒 Segurança

### Autenticação e Autorização
- **2FA obrigatório** para todos os usuários
- **JWT tokens** com expiração configurável
- **Rate limiting** em endpoints públicos
- **Validação de entrada** com Pydantic

### Melhores Práticas
- Nunca commitar secrets no código
- Usar variáveis de ambiente para configurações sensíveis
- Validar toda entrada do usuário
- Logs estruturados sem informações sensíveis

## 🚀 Deploy e Produção

### Ambiente de Produção
- **Servidor:** VPS Ubuntu Server 24.x
- **Recursos mínimos:** 4 vCPUs, 4GB RAM
- **Proxy reverso:** Caddy
- **Containerização:** Docker + Docker Compose

### Checklist de Deploy
1. ✅ Todas as variáveis de ambiente configuradas
2. ✅ Banco de dados migrado
3. ✅ Redis configurado e funcionando
4. ✅ Testes passando
5. ✅ Logs estruturados configurados
6. ✅ Backup do banco configurado

## 📚 Recursos e Documentação

### Links Importantes
- [NiceGUI Documentation](https://nicegui.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Agno Framework](https://github.com/phidatahq/agno)
- [Google Gemini API](https://ai.google.dev/)

### Comandos Úteis de Desenvolvimento
```bash
# Buscar padrões no código
rg "pattern" --type py

# Listar arquivos Python
rg --files -g "*.py"

# Ver logs em tempo real
docker-compose logs -f

# Resetar banco de desenvolvimento
uv run alembic downgrade base && uv run alembic upgrade head
```

## 🎯 Filosofia de Desenvolvimento

### Princípios Core
- **KISS:** Soluções simples são preferíveis
- **YAGNI:** Implementar apenas o que é necessário agora
- **DRY:** Evitar duplicação de código
- **Fail Fast:** Detectar erros o mais cedo possível

### Fluxo de Trabalho
1. **TDD:** Escrever teste primeiro
2. **Implementação mínima:** Fazer o teste passar
3. **Refatoração:** Melhorar mantendo testes verdes
4. **Code Review:** Verificar qualidade e padrões
5. **Deploy:** Após todos os testes passarem

---

**Lembre-se:** Este projeto visa transformar a produtividade de escritórios de advocacia através da automação inteligente. Mantenha sempre o foco na experiência do usuário e na qualidade do código.