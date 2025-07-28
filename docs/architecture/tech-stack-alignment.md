# Tech Stack Alignment

## Current vs. Target Architecture

**Current Implementation (To Be Replaced):**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NiceGUI UI   │────│   FastAPI       │────│  PostgreSQL     │
│                 │    │   + Services    │    │  + pgvector     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │ Celery Workers  │
                       │ + Redis Queue   │
                       └─────────────────┘
```

**Target Agent Architecture:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NiceGUI UI   │────│   FastAPI       │────│  PostgreSQL     │
│  + Agent Mgmt   │    │  + AgentManager │    │  + pgvector     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │ Agno Agents     │
                       │ + Plugin System │
                       └─────────────────┘
```

## Technology Integration Matrix

| Component | Current | Target (Updated July 2025) | Integration Strategy |
|-----------|---------|------------------------------|---------------------|
| **Framework** | FastAPI>=0.104.0 | FastAPI>=0.116.0 + Agno>=1.7.5 | Direct integration, maintain existing endpoints |
| **Database** | PostgreSQL+pgvector | PostgreSQL+pgvector + asyncpg>=0.30.0 | No changes, direct agent connection |
| **Processing** | Celery+Redis | Agno Agents (1.7.5) | Complete replacement, maintain functionality |
| **DI Container** | dependency-injector>=4.48.0 | dependency-injector>=4.48.1 + Agent plugins | Extend existing container |
| **Frontend** | NiceGUI>=1.4.0 | NiceGUI>=2.21.0 + Agent UI | Add management interfaces |
| **Authentication** | Python-JOSE + 2FA | Python-JOSE + 2FA | No changes |
| **External APIs** | google-generativeai>=0.3.0 | google-genai>=0.1.0 | ⚠️ CRITICAL: Replace deprecated package |
| **RAG Framework** | llama-index>=0.12.0 | llama-index>=0.12.52 | Update to latest stable |
| **PDF Processing** | pymupdf>=1.24.0 | pymupdf>=1.26.0 | Update to latest stable |

## New Technology Components

**Agno Framework Integration (Updated July 2025):**
- **Latest Version:** agno>=1.7.5 (July 17, 2025)
- **Version Requirements:** Python 3.12+ (recommended)
- **Core Installation:** `uv add agno>=1.7.5`
- **Agent Base Classes:** Foundation for autonomous agents
- **Tool Architecture:** Modular tools for PDF processing, OCR, vector storage
- **Plugin System:** Dynamic agent loading and lifecycle management
- **Performance Characteristics (v1.7.5):** 
  - Agent instantiation: ~3μs
  - Memory footprint: ~6.5 KiB per agent
  - Supports 23+ model providers
  - ~10,000x faster than LangGraph
  - ~50x less memory than LangGraph
- **Multi-modal Support:** Text, image, audio, video input/output

**Modern Dependency Management (Updated July 2025):**
```bash