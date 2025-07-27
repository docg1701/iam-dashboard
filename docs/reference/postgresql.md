# PostgreSQL para Sistema de Agentes Autônomos de Advocacia

**Configuração Específica para Single-Tenant:**
Para nosso sistema SaaS de advocacia com arquitetura single-tenant, utilizamos PostgreSQL 16.x com:

1. **Modelo Single-Tenant** dedicado por escritório de advocacia para máxima segurança e compliance legal.
2. **pgvector 0.7.x** para embeddings de documentos legais e busca semântica RAG.
3. **Extensões de segurança:** pgcrypto para UUIDs seguros e hashing de dados sensíveis.
4. **Esquema otimizado:** Para usuários, clientes, documentos e chunks vetoriais de documentos.
5. **Integração com Gemini API:** Via Llama-Index para processamento de documentos e consultas RAG.

## 1. Arquitetura de Referência

| Camada | Responsabilidade | Serviço | Porta | Escala | Observações |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Edge API | TLS, Autenticação, Rate-Limit | Caddy/Nginx | 443 | N × pods | Reverse-proxy para /api |
| App API | FastAPI/Flask | Python HTTP | 8000 | auto | Conexão via PgBouncer |
| Banco de Dados | PostgreSQL primário + replicas (Hot) | Postgres 16 | 5432 | 3 nós | Streaming replication + Patroni para HA |
| Vector Search | pgvector | Extensão Vector | — | 3 nós | Índices HNSW/IVFFlat |
| Multi-Tenancy | Pool + RLS | Postgres 16 | 5432 | 3 nós | `current_setting('app.tenant')` + políticas RLS |
| Cache \& Jobs | Redis, pg_cron | Redis, Postgres | 6379 | 1 nó | Caching de lookups + jobs agendados |
| Observabilidade | Prometheus, Grafana, pg_stat_statements | — | 9187 | 1 pod | Métricas DB + queries top slow |

## 2. Esquema de Dados para Sistema de Advocacia

### Esquema Principal (Single-Tenant)

```sql
-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Tabela de usuários com RBAC
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('sysadmin', 'admin_user', 'common_user')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de clientes do escritório
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    date_of_birth DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de documentos com deduplicação por hash
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    content_hash VARCHAR(64) NOT NULL,
    original_filename TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    classification VARCHAR(50) NOT NULL CHECK (classification IN ('simple', 'complex')),
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (client_id, content_hash)
);

-- Tabela de chunks vetoriais para RAG
CREATE TABLE document_chunks (
    id VARCHAR(255) PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    text_content_preview TEXT,
    vector VECTOR(768) NOT NULL,
    UNIQUE (document_id, page_number)
);

-- Índices para performance
CREATE INDEX idx_document_chunks_vector_hnsw ON document_chunks 
USING hnsw (vector vector_cosine_ops);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_client_id ON documents(client_id);
```

### Configurações de Segurança

```sql
-- Configurações de segurança para dados legais sensíveis
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
```

**Recomendação:** *Pool* com RLS: adicionar `tenant_id` a tabelas críticas e criar política RLS:

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.tenant')::uuid);
```

Configure variável `app.tenant` por conexão via middleware no Python[^1][^2].

## 3. Fundamentos de Performance

1. **Conexões:**
    - Use PgBouncer no modo transaction pooling.
    - Limite max_connections do Postgres e do pool.
2. **Memória:**
    - `shared_buffers` ≈ 25% RAM, `work_mem` ajustado conforme queries.
3. **Autovacuum:**
    - Ajuste `autovacuum_vacuum_scale_factor`, `autovacuum_max_workers`.
4. **Particionamento:**
    - Particione por hash em grandes tabelas de logs ou métricas com `pg_partman`.
5. **Monitoramento:**
    - Habilite `pg_stat_statements` e crie dashboards para top-queries.

## 4. pgvector: Embeddings e Busca Vetorial

### Instalação

```bash
CREATE EXTENSION IF NOT EXISTS vector;
```


### CRUD de embeddings

```sql
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  tenant_id UUID,
  content TEXT,
  embedding VECTOR(1536)
);
```


### Pre-filtragem

Use cláusulas SQL normais antes da busca HNSW:

```sql
SELECT id, content
FROM documents
WHERE tenant_id = :tenant_id
ORDER BY embedding <=> :query_embedding
LIMIT 5;
```


### Índices HNSW vs IVFFlat

| Índice | Build Time | Query Latency | Rebuild on Updates |
| :-- | :-- | :-- | :-- |
| HNSW | Médio | <1 ms | Não |
| IVFFlat | Rápido | ~5 ms | Sim |

**Criação HNSW:**

```sql
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);
```

Testes mostram <1 ms por query em 10 M de vetores[^3].

## 5. Integração LLM \& RAG

- **LangChain + SQLDatabase**: transforma perguntas em SQL e executa no Postgres[^6].
- **PostgresML**: extensões PL/Python para inferência de LLM direto no banco usando GPUs[^4].
- **PgAI/PgML**: pipelines RAG nativos, chunk/embed/rank/transform com SQL functions.

Exemplo LangChain em Python:

```python
from langchain_community.sql_database_postgresql import SQLDatabase
from langchain import OpenAI
from langchain.chains import SQLDatabaseChain

db = SQLDatabase.from_uri("postgresql://user:pwd@db:5432/app_db")
llm = OpenAI(temperature=0)
chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)
chain.run("Quantos pedidos o tenant X fez em junho?")
```


## 6. Extensões Essenciais

| Extensão | Função |
| :-- | :-- |
| pg_stat_statements | Monitoramento de queries |
| pg_cron | Agendamento de jobs em SQL |
| pg_partman | Automação de particionamento |
| timescaledb | Séries temporais (metrics/logs) |
| pgaudit | Auditoria de segurança |

## 7. Checklist de Produção

- [ ] Pool multi-tenant configurado com RLS.
- [ ] Índices HNSW em colunas `vector`.
- [ ] PgBouncer no modo transaction pooling ativo.
- [ ] `shared_buffers`, `work_mem` e `autovacuum` ajustados.
- [ ] Extensões de observabilidade habilitadas (`pg_stat_statements`, Prometheus).
- [ ] Jobs agendados via `pg_cron`.
- [ ] Rotinas de backup/restore testadas e automáticas.
- [ ] Planos de manutenção (VACUUM, REINDEX) documentados.

Com esta referência, sua plataforma SaaS Python + LLM com PostgreSQL estará preparada para **alta performance**, **escala horizontal** e **busca semântica** embutida, mantendo **isolamento multi-tenant** e **baixo custo operacional**.

<div style="text-align: center">⁂</div>

[^1]: https://dev.to/shiviyer/how-to-build-multi-tenancy-in-postgresql-for-developing-saas-applications-p81

[^2]: https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-managed-postgresql/partitioning-models.html

[^3]: https://dl.acm.org/doi/10.1145/3701716.3715196

[^4]: https://github.com/postgresml/postgresml

[^5]: https://vanna.ai/docs/postgres-other-llm-chromadb.html

[^6]: https://blog.gopenai.com/query-your-postgresql-database-with-langchain-and-llama-3-1-exploring-llms-1-ba3a9560c0d1

[^7]: https://www.semanticscholar.org/paper/20ca87737d06e9099839ac001346b03a3bafbf1b

[^8]: https://www.semanticscholar.org/paper/48d90650b381c480d110890daf53a9b6821d998f

[^9]: https://ijsrcseit.com/index.php/home/article/view/CSEIT241051016

[^10]: https://www.semanticscholar.org/paper/b83644d2800742f0c13c1ec0bbcfa34f34b2b145

[^11]: https://www.semanticscholar.org/paper/325ab9a110cea9e886739f1d2c8a4eee61533576

[^12]: https://www.semanticscholar.org/paper/0fb6584071ed80d05e1cc71f425d8919c53bacc5

[^13]: https://www.semanticscholar.org/paper/0052f838cf9659f99c49b34ecbb6398da3ecb6ba

[^14]: https://www.semanticscholar.org/paper/963bcc3fad9b2be5041766730175f5180f17714b

[^15]: https://www.wto-ilibrary.org/content/books/9789287043689

[^16]: http://link.springer.com/10.1007/978-3-030-25943-3

[^17]: https://neon.com/postgresql/tutorial

[^18]: https://www.tigerdata.com/learn/guide-to-postgresql-database-operations

[^19]: https://blog.logto.io/implement-multi-tenancy

[^20]: https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/generative-ai-frameworks

[^21]: https://www.postgresql.org/docs/8.1/tutorial-advanced.html

[^22]: https://www.postgresql.org/docs/7.1/advanced.html

[^23]: https://ieeexplore.ieee.org/document/10737548/

[^24]: https://arxiv.org/abs/2410.19811

[^25]: https://www.ijfmr.com/research-paper.php?id=45879

[^26]: https://arxiv.org/abs/2406.00115

[^27]: https://arxiv.org/abs/2410.18792

[^28]: https://www.semanticscholar.org/paper/46a41357eadac1459c81588136c5c053abfeefe4

[^29]: https://arxiv.org/abs/2406.10018

[^30]: https://ieeexplore.ieee.org/document/10765766/

[^31]: https://arxiv.org/abs/2408.13781

[^32]: https://www.yugabyte.com/blog/postgresql-pgvector-getting-started/

[^33]: https://www.datacamp.com/tutorial/pgvector-tutorial

[^34]: https://supabase.com/docs/guides/database/extensions/pgvector

[^35]: https://www.tigerdata.com/blog/use-open-source-llms-in-postgresql-with-ollama-and-pgai

[^36]: https://northflank.com/blog/postgresql-vector-search-guide-with-pgvector

[^37]: https://www.crunchydata.com/blog/designing-your-postgres-database-for-multi-tenancy

[^38]: https://www.reddit.com/r/PostgreSQL/comments/1b6owig/postgres_and_llm_integration/

[^39]: https://github.com/pgvector/pgvector

[^40]: https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-managed-postgresql/welcome.html

[^41]: https://arxiv.org/pdf/2205.04834.pdf

[^42]: https://arxiv.org/html/2502.12918v2

[^43]: http://arxiv.org/pdf/1909.03291.pdf

[^44]: https://zenodo.org/record/5779772/files/loleops.pdf

[^45]: https://arxiv.org/html/2411.14788v1

[^46]: https://arxiv.org/pdf/2306.03714.pdf

[^47]: http://arxiv.org/pdf/2202.12535.pdf

[^48]: http://arxiv.org/pdf/2111.00163.pdf

[^49]: https://arxiv.org/abs/1003.3370

[^50]: https://arxiv.org/html/2503.14929

[^51]: https://dev.to/arctype/advanced-postgresql-features-a-guide-5dl0

[^52]: https://www.instaclustr.com/education/postgresql/complete-guide-to-postgresql-features-use-cases-and-tutorial/

[^53]: https://learn.microsoft.com/en-us/azure/cosmos-db/postgresql/quickstart-build-scalable-apps-model-multi-tenant

[^54]: https://anabot12.hashnode.dev/large-language-model-llm-with-django-postgresql-and-api

[^55]: https://thoughtbot.com/blog/advanced-postgres-performance-tips

[^56]: https://opensource-db.com/multi-tenancy-on-postgres/

[^57]: https://arxiv.org/pdf/2404.10209v1.pdf

[^58]: http://arxiv.org/pdf/2406.13161.pdf

[^59]: https://arxiv.org/pdf/2412.07786.pdf

[^60]: https://arxiv.org/pdf/2306.08891.pdf

[^61]: https://arxiv.org/pdf/2310.18752.pdf

[^62]: https://arxiv.org/html/2403.08291

[^63]: https://arxiv.org/pdf/2502.01298.pdf

[^64]: https://arxiv.org/pdf/2408.11847.pdf

[^65]: http://arxiv.org/pdf/2312.17449.pdf

[^66]: https://arxiv.org/pdf/2408.16151.pdf

[^67]: https://www.tigerdata.com/blog/how-to-build-llm-applications-with-pgvector-vector-store-in-langchain

[^68]: https://zilliz.com/blog/getting-started-pgvector-guide-developers-exploring-vector-databases

[^69]: https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/postgresql

[^70]: https://www.tigerdata.com/learn/postgresql-extensions-pgvector

