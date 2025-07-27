# SQLAlchemy 2.x & Alembic para Sistema de Advocacia

**Configuração Single-Tenant para SaaS Jurídico**
Este guia foca na implementação específica de SQLAlchemy 2.x e Alembic para nosso sistema de agentes autônomos de advocacia. Cobre os modelos de dados, as migrações com pgvector e os padrões de desenvolvimento para a aplicação single-tenant.

## 1. Modelos de Dados (SQLAlchemy ORM)

Os modelos abaixo representam a estrutura de dados do sistema, alinhada com a arquitetura e os requisitos do Llama-Index para o armazenamento de vetores.

```python
# app/models.py
import uuid
from datetime import datetime
from sqlalchemy import (Column, String, Boolean, DateTime, ForeignKey, Text,
                        Integer, UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    """Base para todos os modelos do ORM."""
    pass

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'sysadmin', 'admin_user', 'common_user'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    clients = relationship("Client", back_populates="owner")

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False)
    date_of_birth = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    owner = relationship("User", back_populates="clients")
    documents = relationship("Document", back_populates="client", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    content_hash = Column(String(64), nullable=False)
    original_filename = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default='queued', index=True) # 'queued', 'processing', 'completed', 'failed'
    classification = Column(String(50), nullable=False)  # 'simple', 'complex'
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("Client", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (UniqueConstraint('client_id', 'content_hash', name='_client_content_hash_uc'),)

class DocumentChunk(Base):
    """
    Modelo para armazenar os chunks de documentos vetorizados.
    Este schema é compatível com o PGVectorStore do Llama-Index.
    """
    __tablename__ = "document_chunks"
    
    node_id = Column(String, primary_key=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Colunas requeridas pelo Llama-Index
    text = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=False) # O Llama-Index espera a coluna 'metadata'
    embedding = Column(Vector(768), nullable=False) # Dimensão para embeddings do Gemini
    
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (UniqueConstraint('document_id', 'node_id', name='_document_node_uc'),)
```

## 2. Configuração e Migração com Alembic

A ferramenta Alembic gerencia as evoluções do esquema do banco de dados de forma versionada e segura.

### `alembic.ini`
A configuração principal do Alembic, onde definimos o caminho para os scripts e a URL do banco de dados.

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql+psycopg://user:password@host:port/dbname
```

### `env.py`
Este arquivo é executado toda vez que o Alembic é invocado. É aqui que conectamos os modelos do SQLAlchemy ao Alembic para que ele possa detectar alterações automaticamente.

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.models import Base  # Importe a Base dos seus modelos

# Importar pgvector para que o Alembic reconheça o tipo VECTOR
from pgvector.sqlalchemy import Vector

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Aponte o target_metadata para a Base dos seus modelos
target_metadata = Base.metadata

def run_migrations_online() -> None:
    """Executa migrações em modo 'online'."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

### Script de Migração Inicial
Este é um exemplo do primeiro script de migração, gerado pelo Alembic, que cria todas as tabelas do zero.

```python
"""Migração inicial do sistema de advocacia

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-07-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector # Importar o tipo Vector

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Habilitar extensões necessárias
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector";')
    
    # Criar tabela users
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Criar tabela clients
    op.create_table('clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('cpf', sa.String(14), nullable=False),
        sa.Column('date_of_birth', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cpf')
    )
    
    # Criar tabela documents
    op.create_table('documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('original_filename', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='queued'),
        sa.Column('classification', sa.String(50), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id', 'content_hash', name='_client_content_hash_uc')
    )
    op.create_index(op.f('ix_documents_client_id'), 'documents', ['client_id'], unique=False)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)
    
    # Criar tabela document_chunks (compatível com Llama-Index)
    op.create_table('document_chunks',
        sa.Column('node_id', sa.String(), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=False),
        sa.Column('embedding', Vector(768), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('node_id'),
        sa.UniqueConstraint('document_id', 'node_id', name='_document_node_uc')
    )
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
    
    # Criar índice HNSW para busca vetorial
    op.execute('CREATE INDEX idx_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops)')

def downgrade() -> None:
    op.drop_index('idx_document_chunks_embedding', table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_document_id'), table_name='document_chunks')
    op.drop_table('document_chunks')
    
    op.drop_index(op.f('ix_documents_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_client_id'), table_name='documents')
    op.drop_table('documents')
    
    op.drop_table('clients')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
    
    op.execute('DROP EXTENSION IF EXISTS "vector";')
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto";')
```

