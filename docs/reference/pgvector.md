# pgvector para Sistema RAG de Documentos Legais

## Visão Geral

O **pgvector 0.7.x** é nossa extensão PostgreSQL para implementar busca semântica em documentos legais através de embeddings vetoriais. No contexto do sistema de advocacia, permite que agentes IA encontrem rapidamente informações relevantes em documentos processados usando Retrieval-Augmented Generation (RAG).

## Aplicação no Sistema de Advocacia

- **Busca semântica de documentos**: Encontrar precedentes e informações similares por significado
- **RAG para agentes IA**: Recuperação contextual para geração de documentos legais
- **Embeddings de Gemini API**: Vetores de 768 dimensões para texto legal
- **Filtragem por cliente**: Busca isolada por escritório com segurança de dados
- **Performance otimizada**: Índices HNSW para consultas < 1ms em milhares de documentos

## Configuração para Documentos Legais

### Schema Específico do Projeto

```sql
-- Tabela de chunks vetoriais com metadados legais
CREATE TABLE document_chunks (
    id VARCHAR(255) PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    text_content_preview TEXT,
    vector VECTOR(768) NOT NULL,  -- Gemini API embeddings
    chunk_type VARCHAR(50) DEFAULT 'content',  -- content, header, footer, signature
    legal_context VARCHAR(100),  -- contract, petition, judgment, etc.
    UNIQUE (document_id, page_number)
);

-- Índice HNSW otimizado para similaridade de cosseno
CREATE INDEX idx_document_chunks_vector_hnsw ON document_chunks 
USING hnsw (vector vector_cosine_ops) WITH (m = 16, ef_construction = 64);
```


## Instalação

### Linux e macOS

```bash
cd /tmp
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
make install # pode precisar de sudo
```


### Windows

```cmd
set "PGROOT=C:\Program Files\PostgreSQL\17"
c.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
nmake /F Makefile.win
nmake /F Makefile.win install
```


### Métodos Alternativos

- **Docker**: `docker pull pgvector/pgvector:pg17`
- **Homebrew**: `brew install pgvector`
- **APT**: `sudo apt install postgresql-17-pgvector`
- **Yum**: `sudo yum install pgvector_17`
- **conda-forge**: `conda install -c conda-forge pgvector`[^1_1][^1_4]


## Consultas RAG para Documentos Legais

### Busca Semântica com Filtros

```python
# Exemplo usando SQLAlchemy para busca contextual
from sqlalchemy import text
from pgvector.sqlalchemy import Vector

# Buscar documentos similares para um cliente específico
query = text("""
    SELECT 
        dc.text_content_preview,
        d.original_filename,
        dc.page_number,
        dc.vector <-> :query_vector as similarity
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    JOIN clients c ON d.client_id = c.id
    WHERE c.id = :client_id
        AND dc.legal_context = :context_type
    ORDER BY dc.vector <-> :query_vector
    LIMIT :limit
""")

# Executar busca para contratos similares
similar_contracts = session.execute(query, {
    'query_vector': gemini_embedding,
    'client_id': client_uuid,
    'context_type': 'contract',
    'limit': 5
}).fetchall()
```

### Pipeline RAG Completo

```python
# Integração com Llama-Index para RAG
from llama_index import VectorStoreIndex
from llama_index.vector_stores.postgres import PGVectorStore

# Configurar vector store
vector_store = PGVectorStore.from_params(
    database="advocacia_db",
    host="localhost",
    password="postgres_password",
    port=5432,
    user="postgres",
    table_name="document_chunks",
    embed_dim=768,
    hnsw_kwargs={
        "hnsw_m": 16,
        "hnsw_ef_construction": 64,
        "hnsw_ef_search": 40,
    },
)

# Criar índice RAG
index = VectorStoreIndex.from_vector_store(vector_store)

# Query engine para consultas legais
query_engine = index.as_query_engine(
    similarity_top_k=10,
    filters={"client_id": client_uuid}
)

# Consulta contextual
response = query_engine.query(
    "Quais são as cláusulas de rescisão em contratos similares?"
)
```

## Configuração Inicial

### Habilitando a Extensão

```sql
CREATE EXTENSION vector;
```


### Verificando a Instalação

```sql
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```


## Tipos de Dados Vetoriais

### 1. Vector (Precisão Simples)

```sql
-- Criando tabela com coluna vetorial
CREATE TABLE items (
    id bigserial PRIMARY KEY,
    embedding vector(3)
);

-- Inserindo vetores
INSERT INTO items (embedding) VALUES 
    ('[1,2,3]'), 
    ('[4,5,6]');
```

**Características**:

- Armazenamento: `4 * dimensões + 8` bytes
- Máximo: 16.000 dimensões
- Precisão: float32[^1_1]


### 2. Halfvec (Meia Precisão)

```sql
-- Tabela com half-precision vectors
CREATE TABLE items_half (
    id bigserial PRIMARY KEY,
    embedding halfvec(3)
);
```

**Características**:

- Armazenamento: `2 * dimensões + 8` bytes
- Máximo: 16.000 dimensões
- Precisão: float16[^1_1]


### 3. Bit (Vetores Binários)

```sql
-- Tabela com vetores binários
CREATE TABLE items_binary (
    id bigserial PRIMARY KEY,
    embedding bit(3)
);

INSERT INTO items_binary (embedding) VALUES ('000'), ('111');
```

**Características**:

- Armazenamento: `dimensões / 8 + 8` bytes
- Máximo: 64.000 dimensões[^1_1]


### 4. Sparsevec (Vetores Esparsos)

```sql
-- Tabela com vetores esparsos
CREATE TABLE items_sparse (
    id bigserial PRIMARY KEY,
    embedding sparsevec(5)
);

INSERT INTO items_sparse (embedding) VALUES 
    ('{1:1,3:2,5:3}/5'), 
    ('{1:4,3:5,5:6}/5');
```

**Características**:

- Formato: `{index1:value1,index2:value2}/dimensions`
- Armazenamento: `8 * elementos não-zero + 16` bytes
- Máximo: 16.000 elementos não-zero[^1_1]


## Operadores de Distância

### Para Vectors e Halfvecs

| Operador | Descrição | Uso |
| :-- | :-- | :-- |
| `<->` | Distância L2 (Euclidiana) | `embedding <-> '[^1_5][^1_1][^1_6]'` |
| `<#>` | Produto interno negativo | `embedding <#> '[^1_5][^1_1][^1_6]'` |
| `<=>` | Distância cosseno | `embedding <=> '[^1_5][^1_1][^1_6]'` |
| `<+>` | Distância L1 (Manhattan) | `embedding <+> '[^1_5][^1_1][^1_6]'` |

### Para Vetores Binários

| Operador | Descrição | Uso |
| :-- | :-- | :-- |
| `<~>` | Distância Hamming | `embedding <~> '101'` |
| `<%>` | Distância Jaccard | `embedding <%> '101'` |

### Para Vetores Esparsos

Todos os operadores (`<->`, `<#>`, `<=>`, `<+>`) são suportados[^1_1][^1_7].

## Funções Vetoriais

### Funções de Distância

```sql
-- Distância L2
SELECT l2_distance(embedding, '[3,1,2]') FROM items;

-- Distância cosseno
SELECT cosine_distance(embedding, '[3,1,2]') FROM items;

-- Produto interno
SELECT inner_product(embedding, '[3,1,2]') FROM items;

-- Similaridade cosseno (1 - distância cosseno)
SELECT 1 - cosine_distance(embedding, '[3,1,2]') AS cosine_similarity FROM items;
```


### Funções de Manipulação

```sql
-- Normalização L2
SELECT l2_normalize(embedding) FROM items;

-- Número de dimensões
SELECT vector_dims(embedding) FROM items;

-- Norma euclidiana
SELECT vector_norm(embedding) FROM items;

-- Subvetor
SELECT subvector(embedding, 1, 3) FROM items;

-- Quantização binária
SELECT binary_quantize(embedding) FROM items;
```


### Funções de Agregação

```sql
-- Média de vetores
SELECT AVG(embedding) FROM items;

-- Soma de vetores
SELECT SUM(embedding) FROM items;

-- Média por grupo
SELECT category_id, AVG(embedding) FROM items GROUP BY category_id;
```


## Consultas de Similaridade

### Busca de Vizinhos Mais Próximos

```sql
-- Buscar os 5 vizinhos mais próximos
SELECT * FROM items 
ORDER BY embedding <-> '[3,1,2]' 
LIMIT 5;

-- Busca por similaridade cosseno
SELECT * FROM items 
ORDER BY embedding <=> '[3,1,2]' 
LIMIT 5;
```


### Busca com Filtros

```sql
-- Busca dentro de uma categoria específica
SELECT * FROM items 
WHERE category_id = 123 
ORDER BY embedding <-> '[3,1,2]' 
LIMIT 5;

-- Busca por distância máxima
SELECT * FROM items 
WHERE embedding <-> '[3,1,2]' < 5
ORDER BY embedding <-> '[3,1,2]';
```


### Busca Baseada em Outro Registro

```sql
-- Encontrar itens similares a um item específico
SELECT * FROM items 
WHERE id != 1 
ORDER BY embedding <-> (SELECT embedding FROM items WHERE id = 1) 
LIMIT 5;
```


## Indexação

### Tipos de Índices

#### 1. HNSW (Hierarchical Navigable Small World)

**Características**:

- Melhor performance de consulta
- Tempo de construção mais lento
- Maior uso de memória
- Não requer dados para criação[^1_1][^1_8][^1_9]

```sql
-- Índice HNSW para distância L2
CREATE INDEX ON items USING hnsw (embedding vector_l2_ops);

-- Índice HNSW para produto interno
CREATE INDEX ON items USING hnsw (embedding vector_ip_ops);

-- Índice HNSW para distância cosseno
CREATE INDEX ON items USING hnsw (embedding vector_cosine_ops);

-- Índice HNSW para distância L1
CREATE INDEX ON items USING hnsw (embedding vector_l1_ops);
```

**Parâmetros de Configuração**:

```sql
-- Configurar parâmetros do índice
CREATE INDEX ON items USING hnsw (embedding vector_l2_ops) 
WITH (m = 16, ef_construction = 64);

-- Configurar parâmetros de consulta
SET hnsw.ef_search = 100;
```

**Parâmetros Importantes**:

- `m`: número máximo de conexões por camada (16 por padrão)
- `ef_construction`: tamanho da lista de candidatos dinâmica (64 por padrão)
- `ef_search`: tamanho da lista para busca (40 por padrão)[^1_1][^1_8]


#### 2. IVFFlat (Inverted File Flat)

**Características**:

- Construção mais rápida
- Menor uso de memória
- Performance de consulta inferior ao HNSW
- Requer dados existentes para melhor recall[^1_1][^1_8][^1_9]

```sql
-- Índice IVFFlat para distância L2
CREATE INDEX ON items USING ivfflat (embedding vector_l2_ops) 
WITH (lists = 100);

-- Índice IVFFlat para produto interno
CREATE INDEX ON items USING ivfflat (embedding vector_ip_ops) 
WITH (lists = 100);

-- Índice IVFFlat para distância cosseno
CREATE INDEX ON items USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

**Configuração de Consulta**:

```sql
-- Configurar número de probes
SET ivfflat.probes = 10;
```

**Diretrizes de Configuração**:

- **Listas**: `rows / 1000` para até 1M registros, `sqrt(rows)` para mais
- **Probes**: `sqrt(lists)` como ponto de partida[^1_1][^1_9]


### Scans Iterativos (pgvector 0.8.0+)

```sql
-- Habilitar scan iterativo estrito
SET hnsw.iterative_scan = 'strict_order';

-- Habilitar scan iterativo relaxado (melhor performance)
SET hnsw.iterative_scan = 'relaxed_order';

-- Configurar limite de tuplas escaneadas
SET hnsw.max_scan_tuples = 20000;

-- Configurar multiplicador de memória
SET hnsw.scan_mem_multiplier = 2;
```


### Indexação de Half-precision

```sql
-- Índice com half-precision para menor tamanho
CREATE INDEX ON items USING hnsw ((embedding::halfvec(3)) halfvec_l2_ops);

-- Consulta usando half-precision
SELECT * FROM items 
ORDER BY embedding::halfvec(3) <-> '[1,2,3]' 
LIMIT 5;
```


### Indexação de Subvetores

```sql
-- Índice em subvetor
CREATE INDEX ON items USING hnsw ((subvector(embedding, 1, 3)::vector(3)) vector_cosine_ops);

-- Consulta com re-ranking
SELECT * FROM (
    SELECT * FROM items 
    ORDER BY subvector(embedding, 1, 3)::vector(3) <=> subvector('[1,2,3,4,5]'::vector, 1, 3) 
    LIMIT 20
) ORDER BY embedding <=> '[1,2,3,4,5]' LIMIT 5;
```


## Operações de Dados

### Inserção

```sql
-- Inserção simples
INSERT INTO items (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');

-- Upsert
INSERT INTO items (id, embedding) VALUES (1, '[1,2,3]'), (2, '[4,5,6]')
ON CONFLICT (id) DO UPDATE SET embedding = EXCLUDED.embedding;

-- Carregamento em massa
COPY items (embedding) FROM STDIN WITH (FORMAT BINARY);
```


### Atualização

```sql
-- Atualizar vetor
UPDATE items SET embedding = '[1,2,3]' WHERE id = 1;

-- Adicionar coluna vetorial a tabela existente
ALTER TABLE items ADD COLUMN embedding vector(3);
```


### Exclusão

```sql
DELETE FROM items WHERE id = 1;
```


## Integração com Linguagens

### Python

#### Instalação

```bash
pip install pgvector psycopg2-binary
```


#### Exemplo Básico

```python
import psycopg2
from pgvector.psycopg2 import register_vector

# Conexão
conn = psycopg2.connect("dbname=test")
register_vector(conn)

cur = conn.cursor()

# Criar tabela
cur.execute('CREATE TABLE items (id bigserial PRIMARY KEY, embedding vector(3))')

# Inserir vetor
cur.execute('INSERT INTO items (embedding) VALUES (%s)', ([1, 2, 3],))

# Busca de similaridade
cur.execute('SELECT * FROM items ORDER BY embedding <-> %s LIMIT 5', ([3, 1, 2],))
results = cur.fetchall()

conn.commit()
cur.close()
conn.close()
```


#### SQLAlchemy

```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Item(Base):
    __tablename__ = 'item'
    
    id = Column(Integer, primary_key=True)
    embedding = Column(Vector(3))

# Consulta
session.query(Item).order_by(Item.embedding.l2_distance([3, 1, 2])).limit(5)
```


#### Django

```python
from django.db import models
from pgvector.django import VectorField

class Item(models.Model):
    embedding = VectorField(dimensions=3)

# Consulta
from pgvector.django import L2Distance
Item.objects.order_by(L2Distance('embedding', [3, 1, 2]))[:5]
```


### JavaScript/Node.js

#### Instalação

```bash
npm install pgvector pg
```


#### Exemplo com node-postgres

```javascript
import pgvector from 'pgvector/pg';
import pg from 'pg';

const client = new pg.Client('postgresql://localhost/test');
await client.connect();

// Registrar tipos
await pgvector.registerTypes(client);

// Criar tabela
await client.query('CREATE TABLE items (id bigserial PRIMARY KEY, embedding vector(3))');

// Inserir vetor
await client.query('INSERT INTO items (embedding) VALUES ($1)', 
    [pgvector.toSql([1, 2, 3])]);

// Busca de similaridade
const result = await client.query(
    'SELECT * FROM items ORDER BY embedding <-> $1 LIMIT 5',
    [pgvector.toSql([3, 1, 2])]
);

await client.end();
```


#### Exemplo com Prisma

```javascript
// schema.prisma
model Item {
  id        BigInt @id @default(autoincrement())
  embedding Unsupported("vector(3)")
}

// Cliente
const items = await prisma.$queryRaw`
  SELECT * FROM "Item" 
  ORDER BY embedding <-> ${pgvector.toSql([3, 1, 2])} 
  LIMIT 5
`;
```


### Outras Linguagens

O pgvector suporta **mais de 20 linguagens** através de bibliotecas específicas:


| Linguagem | Biblioteca |
| :-- | :-- |
| Python | pgvector-python |
| JavaScript/TypeScript | pgvector-node |
| Java/Kotlin/Scala | pgvector-java |
| Go | pgvector-go |
| Rust | pgvector-rust |
| Ruby | pgvector-ruby |
| C\# | pgvector-dotnet |
| PHP | pgvector-php |
| R | pgvector-r |

## Otimização de Performance

### Configurações de Memória

```sql
-- Aumentar memória para construção de índices
SET maintenance_work_mem = '8GB';

-- Configurar workers paralelos
SET max_parallel_maintenance_workers = 7;
SET max_parallel_workers = 8;

-- Para consultas sem índice
SET max_parallel_workers_per_gather = 4;
```


### Tuning de Parâmetros

```sql
-- Configurações HNSW
SET hnsw.ef_search = 100;  -- Maior = melhor recall, menor performance
SET hnsw.max_scan_tuples = 20000;  -- Limite para scans iterativos

-- Configurações IVFFlat
SET ivfflat.probes = 10;  -- Maior = melhor recall, menor performance
SET ivfflat.max_probes = 100;  -- Limite para scans iterativos
```


### Estratégias de Indexação

```sql
-- Índice parcial para filtros específicos
CREATE INDEX ON items USING hnsw (embedding vector_l2_ops) 
WHERE (category_id = 123);

-- Índice em coluna de filtro
CREATE INDEX ON items (category_id);

-- Índice multicoluna
CREATE INDEX ON items (location_id, category_id);
```


### Monitoramento

```sql
-- Verificar uso de índice
EXPLAIN ANALYZE SELECT * FROM items ORDER BY embedding <-> '[3,1,2]' LIMIT 5;

-- Monitorar progresso de criação de índice
SELECT phase, round(100.0 * blocks_done / nullif(blocks_total, 0), 1) AS "%" 
FROM pg_stat_progress_create_index;

-- Verificar tamanho do índice
SELECT pg_size_pretty(pg_relation_size('index_name'));
```


## Busca Híbrida

### Combinação com Full-Text Search

```sql
-- Busca híbrida texto + vetorial
SELECT id, content, 
       ts_rank_cd(textsearch, query) AS text_rank,
       embedding <-> '[vector]' AS vector_distance
FROM items, plainto_tsquery('search terms') query
WHERE textsearch @@ query
ORDER BY ts_rank_cd(textsearch, query) DESC, vector_distance
LIMIT 5;
```


### Reciprocal Rank Fusion (RRF)

```sql
WITH text_search AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(textsearch, query) DESC) as rank
  FROM items, plainto_tsquery('search terms') query
  WHERE textsearch @@ query
),
vector_search AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <-> '[vector]') as rank
  FROM items
)
SELECT 
  COALESCE(t.id, v.id) as id,
  1.0 / (60 + COALESCE(t.rank, 1000)) + 1.0 / (60 + COALESCE(v.rank, 1000)) AS combined_score
FROM text_search t
FULL OUTER JOIN vector_search v ON t.id = v.id
ORDER BY combined_score DESC
LIMIT 5;
```


## Casos de Uso Avançados

### Quantização Binária

```sql
-- Índice com quantização binária
CREATE INDEX ON items USING hnsw ((binary_quantize(embedding)::bit(3)) bit_hamming_ops);

-- Consulta com re-ranking
SELECT * FROM (
    SELECT * FROM items 
    ORDER BY binary_quantize(embedding)::bit(3) <~> binary_quantize('[1,-2,3]') 
    LIMIT 20
) ORDER BY embedding <=> '[1,-2,3]' LIMIT 5;
```


### Particionamento

```sql
-- Tabela particionada por categoria
CREATE TABLE items (embedding vector(3), category_id int) 
PARTITION BY LIST(category_id);

-- Partições específicas
CREATE TABLE items_electronics PARTITION OF items FOR VALUES IN (1);
CREATE TABLE items_clothing PARTITION OF items FOR VALUES IN (2);
```


### CTEs Materializadas para Performance

```sql
-- CTE materializada para consultas filtradas
WITH nearest_results AS MATERIALIZED (
    SELECT id, embedding <-> '[1,2,3]' AS distance 
    FROM items 
    ORDER BY distance 
    LIMIT 100
)
SELECT * FROM nearest_results 
WHERE distance < 5 
ORDER BY distance;
```


## Solução de Problemas

### Problemas Comuns

1. **Consulta não usa índice**:

```sql
-- Forçar uso do índice
BEGIN;
SET LOCAL enable_seqscan = off;
SELECT ...;
COMMIT;
```

2. **Menos resultados após criar índice HNSW**:

```sql
-- Aumentar ef_search ou habilitar scan iterativo
SET hnsw.ef_search = 200;
SET hnsw.iterative_scan = 'relaxed_order';
```

3. **Menos resultados após criar índice IVFFlat**:

```sql
-- Aumentar probes ou recriar índice com mais dados
SET ivfflat.probes = 50;
```


### Debugging

```sql
-- Verificar plano de execução
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM items 
ORDER BY embedding <-> '[3,1,2]' LIMIT 5;

-- Verificar estatísticas
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats WHERE tablename = 'items';
```


## Upgrading

```sql
-- Atualizar extensão
ALTER EXTENSION vector UPDATE;

-- Verificar versão atual
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```


## Limitações e Considerações

### Limitações por Tipo

| Tipo | Dimensões Máximas | Limite de Índice |
| :-- | :-- | :-- |
| vector | 16.000 | 2.000 (HNSW/IVFFlat) |
| halfvec | 16.000 | 4.000 (HNSW/IVFFlat) |
| bit | 64.000 | 64.000 (HNSW/IVFFlat) |
| sparsevec | 16.000 elem. | 1.000 elem. (HNSW) |

### Considerações de Performance

- **Índices devem ser criados após carregamento inicial dos dados**
- **Vacuuming pode ser lento para índices HNSW - considere REINDEX**
- **Vetores NULL não são indexados**
- **Vetores zero não são indexados para distância cosseno**[^1_1]


### Melhores Práticas

1. **Use COPY para carregamento em massa**
2. **Crie índices CONCURRENTLY em produção**
3. **Configure maintenance_work_mem adequadamente**
4. **Monitore performance com pg_stat_statements**
5. **Use half-precision ou quantização binária para datasets grandes**
6. **Considere particionamento para datasets muito grandes**[^1_1][^1_10][^1_11]

Este guia fornece uma referência abrangente para uso do pgvector em diferentes cenários, desde implementações básicas até otimizações avançadas de performance, adequado para ser usado como referência por agentes de codificação LLM.

<div style="text-align: center">⁂</div>

[^1_1]: https://github.com/pgvector/pgvector

[^1_2]: https://neon.com/docs/extensions/pgvector

[^1_3]: https://airbyte.com/data-engineering-resources/postgresql-as-a-vector-database

[^1_4]: https://www.aclweb.org/anthology/2020.coling-main.33.pdf

[^1_5]: https://arxiv.org/pdf/2205.04834.pdf

[^1_6]: http://arxiv.org/pdf/2408.13480.pdf

[^1_7]: https://pgdocptbr.sourceforge.io/pg80/catalog-pg-aggregate.html

[^1_8]: https://learn.microsoft.com/pt-br/azure/cosmos-db/postgresql/howto-use-pgvector

[^1_9]: https://support.servbay.com/pt/database-management/postgresql-extensions/pgvector

[^1_10]: https://www.youtube.com/watch?v=lyTvhGSMEGc

[^1_11]: https://www.tigerdata.com/learn/using-pgvector-with-python

[^1_12]: https://arxiv.org/pdf/2312.01476.pdf

[^1_13]: https://ojs.cvut.cz/ojs/index.php/gi/article/download/gi.11.5/2403

[^1_14]: https://arxiv.org/html/2504.09288v1

[^1_15]: https://journal.r-project.org/archive/2018/RJ-2018-025/RJ-2018-025.pdf

[^1_16]: https://zenodo.org/record/3632551/files/vectorizationcompilation.pdf

[^1_17]: http://arxiv.org/pdf/2504.01553.pdf

[^1_18]: http://arxiv.org/pdf/2306.02194.pdf

[^1_19]: https://arxiv.org/pdf/2501.11216.pdf

[^1_20]: https://www.datacamp.com/tutorial/pgvector-tutorial

[^1_21]: https://www.tigerdata.com/learn/postgresql-extensions-pgvector

[^1_22]: https://northflank.com/blog/postgresql-vector-search-guide-with-pgvector

[^1_23]: https://zilliz.com/blog/getting-started-pgvector-guide-developers-exploring-vector-databases

[^1_24]: https://support.servbay.com/database-management/postgresql-extensions/pgvector

[^1_25]: https://www.youtube.com/watch?v=j1QcPSLj7u0

[^1_26]: https://www.youtube.com/watch?v=80w4GVlp_qY

[^1_27]: https://arxiv.org/pdf/2502.02818.pdf

[^1_28]: http://ispras.ru/proceedings/docs/2016/28/4/isp_28_2016_4_217.pdf

[^1_29]: https://arxiv.org/pdf/2502.05237.pdf

[^1_30]: https://arxiv.org/pdf/2302.13140.pdf

[^1_31]: https://arxiv.org/html/2407.04823v1

[^1_32]: http://www.jurnal.unsyiah.ac.id/JRE/article/download/1011/10_3_1

[^1_33]: https://arxiv.org/pdf/2502.01528.pdf

[^1_34]: http://arxiv.org/pdf/2404.03880.pdf

[^1_35]: https://arxiv.org/pdf/1511.03086.pdf

[^1_36]: https://www.datacamp.com/pt/tutorial/pgvector-tutorial

[^1_37]: https://aws.amazon.com/blogs/database/optimize-generative-ai-applications-with-pgvector-indexing-a-deep-dive-into-ivfflat-and-hnsw-techniques/

[^1_38]: https://halleyoliv.gitlab.io/pgdocptbr/tutorial-agg.html

[^1_39]: https://tembo.io/blog/vector-indexes-in-pgvector

[^1_40]: https://www.reddit.com/r/LangChain/comments/1hzl7l6/creating_a_rag_system_with_pgvector_for_semantic/?tl=pt-br

[^1_41]: https://www.tigerdata.com/blog/nearest-neighbor-indexes-what-are-ivfflat-indexes-in-pgvector-and-how-do-they-work

[^1_42]: https://cloud.google.com/sql/docs/postgres/generate-manage-vector-embeddings

[^1_43]: https://www.semanticscholar.org/paper/4bf73ad6f0c453f73b09b6edd045d1d15490eb15

[^1_44]: https://www.semanticscholar.org/paper/366fa00d08d0f03b5802ce62df10e853c3243dca

[^1_45]: https://sol.sbc.org.br/index.php/ercemapi/article/view/11474

[^1_46]: https://sol.sbc.org.br/index.php/wgrs/article/view/12463

[^1_47]: http://www.teses.usp.br/teses/disponiveis/45/45134/tde-02042012-120707/

[^1_48]: https://arxiv.org/pdf/1906.04239.pdf

[^1_49]: https://academic.oup.com/bioinformatics/advance-article-pdf/doi/10.1093/bioinformatics/btad346/50453056/btad346.pdf

[^1_50]: https://arxiv.org/pdf/2204.12095v2.pdf

[^1_51]: http://arxiv.org/pdf/2002.05426.pdf

[^1_52]: https://arxiv.org/pdf/2310.14687.pdf

[^1_53]: https://github.com/pgvector/pgvector-node

[^1_54]: https://aws.amazon.com/blogs/database/supercharging-vector-search-performance-and-relevance-with-pgvector-0-8-0-on-amazon-aurora-postgresql/

[^1_55]: https://js.langchain.com/docs/integrations/vectorstores/pgvector/

[^1_56]: https://dev.to/shiviyer/performance-tips-for-developers-using-postgres-and-pgvector-l7g

[^1_57]: https://jkatz.github.io/post/postgres/pgvector-performance-150x-speedup/

[^1_58]: https://github.com/pgvector/pgvector-python

[^1_59]: https://www.tigerdata.com/blog/implementing-filtered-semantic-search-using-pgvector-and-javascript-2

[^1_60]: https://www.crunchydata.com/blog/pgvector-performance-for-developers

[^1_61]: https://arxiv.org/pdf/2402.02044.pdf

[^1_62]: https://arxiv.org/html/2411.04525

[^1_63]: https://arxiv.org/pdf/2210.15748.pdf

[^1_64]: https://arxiv.org/pdf/2206.13843.pdf

[^1_65]: https://arxiv.org/pdf/2311.15578.pdf

[^1_66]: https://aclanthology.org/2021.acl-long.392.pdf

[^1_67]: https://www.medrxiv.org/content/medrxiv/early/2020/05/23/2020.05.20.20108217.full.pdf

[^1_68]: https://arxiv.org/html/2411.14788v1

[^1_69]: https://dl.acm.org/doi/pdf/10.1145/3652024.3665515

[^1_70]: https://aclanthology.org/2023.emnlp-main.868.pdf

[^1_71]: https://www.yugabyte.com/blog/postgresql-pgvector-getting-started/

[^1_72]: https://supabase.com/docs/guides/database/extensions/pgvector

[^1_73]: https://www.youtube.com/watch?v=Ua6LDIOVN1s

[^1_74]: https://python.langchain.com/docs/integrations/vectorstores/pgvector/

[^1_75]: https://www.tigerdata.com/blog/postgresql-as-a-vector-database-using-pgvector

[^1_76]: https://github.com/igrishaev/pg2/blob/master/docs/pgvector.md

[^1_77]: https://www.dbvis.com/thetable/a-beginners-guide-to-vector-search-using-pgvector/

[^1_78]: https://www.postgresql.org/about/news/pgvector-070-released-2852/

[^1_79]: https://www.enterprisedb.com/docs/pg_extensions/pgvector/

[^1_80]: https://www.thenile.dev/docs/ai-embeddings/pg_vector

[^1_81]: https://pixion.co/blog/choosing-your-index-with-pg-vector-flat-vs-hnsw-vs-ivfflat

[^1_82]: https://learn.microsoft.com/pt-br/azure/postgresql/flexible-server/how-to-use-pgvector

[^1_83]: https://www.youtube.com/watch?v=y3qtQ9xXfN0

[^1_84]: https://learn.microsoft.com/pt-br/azure/postgresql/flexible-server/how-to-optimize-performance-pgvector

[^1_85]: https://www.youtube.com/watch?v=4IyZdI3LFJQ

[^1_86]: https://www.nocodo.ai/blog/vector-search-demystified-guide-to-pgvector-ivfflat-and-hnsw

[^1_87]: https://cloud.google.com/sql/docs/postgres/work-with-vectors

[^1_88]: https://hackernoon.com/lang/pt/usando-pgvector-para-localizar-semelhanças-em-dados-corporativos

[^1_89]: https://www.frontiersin.org/articles/10.3389/fninf.2021.659005/pdf

[^1_90]: https://joss.theoj.org/papers/10.21105/joss.06326.pdf

[^1_91]: https://www.mdpi.com/2220-9964/2/1/201/pdf?version=1363011806

[^1_92]: https://aclanthology.org/2023.emnlp-main.897.pdf

[^1_93]: https://joss.theoj.org/papers/10.21105/joss.05304.pdf

[^1_94]: https://arxiv.org/abs/2304.08639

[^1_95]: https://arxiv.org/pdf/2102.10073.pdf

[^1_96]: https://joss.theoj.org/papers/10.21105/joss.05205.pdf

[^1_97]: https://arxiv.org/abs/2107.13109

[^1_98]: https://arxiv.org/pdf/2009.02963.pdf

[^1_99]: https://www.youtube.com/watch?v=FCoGU072Bmc

[^1_100]: https://learn.microsoft.com/en-us/azure/cosmos-db/postgresql/howto-optimize-performance-pgvector

[^1_101]: https://dev.to/jherr/100-free-vector-search-with-openllama-postgres-nodejs-and-nextjs-3jm5

[^1_102]: https://cloud.google.com/blog/products/databases/faster-similarity-search-performance-with-pgvector-indexes

[^1_103]: https://pamelafox.github.io/my-py-talks/pgvector-python/

[^1_104]: https://www.koyeb.com/tutorials/use-pgvector-and-hugging-face-to-build-an-optimized-faq-search-with-sentence-similarity

