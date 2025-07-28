# Data Models and Schema Changes

## Database Schema Strategy: Zero Modification Approach

**Rationale:**
Since agents will integrate directly with existing PostgreSQL infrastructure, we maintain the current schema without modifications. This ensures data integrity and eliminates migration risks.

**Current Schema Preservation:**
```sql
-- Existing tables remain unchanged
users (user_id, email, password_hash, ...)
clients (client_id, user_id, name, ...)
documents (document_id, client_id, content, vectors, ...)
questionnaire_drafts (draft_id, client_id, content, ...)
```

**Agent Metadata Strategy:**
Instead of new tables, agents will use existing metadata patterns:
- Document processing status tracked in existing `documents` table
- Agent execution logs stored in existing logging infrastructure
- Configuration managed through YAML files and environment variables

## Data Flow Integration

**Document Processing Flow:**
```
PDF Upload → PDFProcessorAgent → Existing DB Schema
    ↓              ↓                    ↓
FastAPI      Agno Tools         documents table
Endpoint   (PDF, OCR, Vector)    + metadata
```

**Questionnaire Generation Flow:**
```
Request → QuestionnaireAgent → RAG Retrieval → DB Storage
   ↓           ↓                    ↓             ↓
FastAPI   Llama-Index         Existing Vector   questionnaire_drafts
Endpoint  Integration         Store (pgvector)  table
```

## Vector Store Integration

**Existing Integration Preserved:**
- **Llama-Index Integration:** Agents use existing Llama-Index setup
- **pgvector Extension:** Continue using PostgreSQL vector capabilities
- **Embedding Strategy:** Maintain current embedding generation and storage patterns

**Vector Storage Workflow:**
```python
class VectorStorageWorkflow:
    """Agent-based vector storage maintaining existing patterns."""
    
    async def store_document_vectors(self, document_content: str, document_id: str):
        # Use existing Llama-Index integration
        index = self.llama_index_service.get_index()
        
        # Generate embeddings (same as current process)
        embeddings = await self.embedding_service.generate_embeddings(document_content)
        
        # Store in existing pgvector table structure
        await self.vector_repository.store_vectors(
            document_id=document_id,
            vectors=embeddings,
            metadata={"processed_by": "agent", "timestamp": datetime.utcnow()}
        )
```

## Database Connection Patterns

**Agent Database Access:**
```python
class AgentDatabaseIntegration:
    """Database integration for agents using existing patterns."""
    
    def __init__(self, container: Container):
        # Use existing database session from container
        self.db_session = container.db_session()
        
        # Use existing repositories
        self.document_repository = container.document_repository()
        self.client_repository = container.client_repository()
        self.user_repository = container.user_repository()
    
    async def save_document_processing_result(self, result: ProcessingResult):
        """Save agent processing results using existing repositories."""
        async with self.db_session() as session:
            # Use existing document repository patterns
            document = await self.document_repository.create(
                session=session,
                client_id=result.client_id,
                content=result.content,
                vectors=result.vectors,
                processing_status="completed",
                processed_at=datetime.utcnow()
            )
            return document
```

## Configuration Data Management

**Agent Configuration Storage:**
```yaml
# config/agents.yaml - Version controlled configuration
agents:
  pdf_processor:
    enabled: true
    timeout_seconds: 300
    max_concurrent: 3
    tools:
      pdf_reader:
        library: "pymupdf"
        timeout: 120
      ocr_processor:
        engine: "tesseract"
        languages: ["por", "eng"]
      vector_storage:
        batch_size: 100
        
  questionnaire_writer:
    enabled: true
    timeout_seconds: 180
    max_concurrent: 2
    tools:
      rag_retriever:
        similarity_threshold: 0.7
        max_results: 10
      llm_processor:
        model: "gemini-pro"
        temperature: 0.3
```

**Runtime Configuration Management:**
```python
class AgentConfigManager:
    """Manage agent configuration without database changes."""
    
    def __init__(self, config_path: str = "config/agents.yaml"):
        self.config_path = config_path
        self._config_cache = {}
    
    async def get_agent_config(self, agent_id: str) -> dict:
        """Get agent configuration from YAML file."""
        if agent_id not in self._config_cache:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                self._config_cache[agent_id] = config['agents'][agent_id]
        
        return self._config_cache[agent_id]
    
    async def update_agent_config(self, agent_id: str, updates: dict):
        """Update agent configuration and persist to file."""
        config = await self.get_agent_config(agent_id)
        config.update(updates)
        
        # Update cache
        self._config_cache[agent_id] = config
        
        # Persist to file
        await self._save_config_file()
```

## Metadata and Logging Integration

**Agent Processing Metadata:**
```python
class DocumentProcessingMetadata:
    """Metadata for agent-processed documents."""
    
    @staticmethod
    def create_processing_metadata(agent_id: str, processing_time: float) -> dict:
        return {
            "processed_by": "agent",
            "agent_id": agent_id,
            "processing_time_seconds": processing_time,
            "agno_version": "1.7.5",
            "processing_timestamp": datetime.utcnow().isoformat(),
            "tools_used": ["pdf_reader", "ocr_processor", "vector_storage"]
        }
```

**Existing Logging Integration:**
```python
class AgentLoggingIntegration:
    """Integration with existing application logging."""
    
    def __init__(self):
        # Use existing application logger
        self.logger = logging.getLogger("iam_dashboard.agents")
    
    async def log_processing_event(self, event: str, agent_id: str, **kwargs):
        """Log agent events using existing logging infrastructure."""
        self.logger.info(
            f"Agent {agent_id}: {event}",
            extra={
                "agent_id": agent_id,
                "event_type": event,
                "timestamp": datetime.utcnow(),
                **kwargs
            }
        )
```

## Data Consistency and Transactions

**Transactional Agent Operations:**
```python
class TransactionalAgentOperations:
    """Ensure data consistency in agent operations."""
    
    async def process_document_with_transaction(self, document_request: DocumentProcessRequest):
        """Process document with full transaction support."""
        async with self.db_session.begin() as transaction:
            try:
                # Create document record
                document = await self.document_repository.create(
                    session=transaction,
                    client_id=document_request.client_id,
                    filename=document_request.filename,
                    processing_status="processing"
                )
                
                # Process with agent
                result = await self.pdf_agent.process_document(document_request.file_path)
                
                # Update document with results
                document.content = result.content
                document.vectors = result.vectors
                document.processing_status = "completed"
                document.processed_at = datetime.utcnow()
                
                # Commit transaction
                await transaction.commit()
                
                return document
                
            except Exception as e:
                # Rollback on any error
                await transaction.rollback()
                
                # Update document status to failed
                document.processing_status = "failed"
                document.error_message = str(e)
                
                raise AgentProcessingError(f"Document processing failed: {e}")
```

## Performance Optimization

**Database Query Optimization:**
```python
class OptimizedAgentQueries:
    """Optimized database queries for agent operations."""
    
    async def bulk_vector_storage(self, vectors_batch: List[VectorData]):
        """Optimized bulk vector storage for agent processing."""
        # Use existing bulk insert patterns
        await self.vector_repository.bulk_insert(vectors_batch)
    
    async def get_client_documents_for_rag(self, client_id: str) -> List[Document]:
        """Optimized query for RAG context retrieval."""
        # Use existing optimized queries with proper indexing
        return await self.document_repository.get_by_client_with_vectors(client_id)
```

**Connection Pool Management:**
```python
class AgentConnectionPooling:
    """Database connection pooling for agents."""
    
    def __init__(self, container: Container):
        # Use existing connection pool configuration
        self.engine = container.db_engine()
        self.session_factory = container.db_session_factory()
    
    async def get_session_for_agent(self, agent_id: str):
        """Get database session for agent with proper pooling."""
        # Use existing session management patterns
        return self.session_factory()
```

## Migration Validation

**Data Integrity Checks:**
```python
class DataIntegrityValidator:
    """Validate data integrity during agent migration."""
    
    async def validate_document_processing_parity(self):
        """Ensure agent processing produces same results as Celery."""
        # Compare document processing results
        celery_documents = await self.get_celery_processed_documents()
        agent_documents = await self.get_agent_processed_documents()
        
        # Validate content similarity
        for celery_doc, agent_doc in zip(celery_documents, agent_documents):
            similarity = self.calculate_content_similarity(
                celery_doc.content, 
                agent_doc.content
            )
            assert similarity > 0.95, f"Content similarity too low: {similarity}"
```

## Rollback Procedures

**Database Rollback Strategy:**
Since no schema changes are made, rollback involves:
1. **Configuration Rollback:** Revert agent YAML configurations
2. **Processing Rollback:** Re-enable Celery workers if needed
3. **Data Cleanup:** Remove agent-specific metadata if necessary
4. **Service Restart:** Restart application without agent components

**No Database Migration Rollback Required:**
- Schema remains unchanged
- Existing data fully compatible
- No data migration or transformation needed