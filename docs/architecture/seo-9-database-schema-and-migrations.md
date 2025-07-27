# Seção 9: Esquema e Migrações do Banco de Dados

## Esquema do Banco de Dados (Single-Tenant)

O esquema para o PostgreSQL é projetado para ser compatível com o `PGVectorStore` do Llama-Index.

```sql
-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Tabela de usuários
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de clientes
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    date_of_birth DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de documentos
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    content_hash VARCHAR(64) NOT NULL,
    original_filename TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    classification VARCHAR(50) NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (client_id, content_hash)
);

-- Tabela de chunks para Llama-Index PGVectorStore
CREATE TABLE document_chunks (
    node_id VARCHAR PRIMARY KEY,
    embedding VECTOR(768),
    text TEXT NOT NULL,
    metadata JSONB NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE
);

-- Índices para performance
CREATE INDEX ix_document_chunks_document_id ON document_chunks (document_id);
CREATE INDEX ix_documents_client_id ON documents (client_id);
CREATE INDEX ix_documents_status ON documents (status);
-- Índice HNSW para busca vetorial
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);
```
## Gerenciamento de Migrações

Utilizaremos **Alembic** com **SQLAlchemy** para gerenciar as alterações no esquema do banco de dados de forma versionada e segura.
