# Technology Stack

This document defines the DEFINITIVE technology selection for the IAM Dashboard project. This table is the single source of truth - all development must use these exact versions and technologies.

## Core Technology Stack

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Language** | Python | 3.12+ | Primary development language | Modern Python with latest features, excellent async support, rich ecosystem for AI/ML |
| **Web Framework** | FastAPI | >= 0.116.0 | Backend API and web server | High performance, automatic OpenAPI docs, excellent async support, type hints |
| **UI Framework** | NiceGUI | >= 1.4.0 | Web-based user interface | Python-native UI, rapid development, real-time updates, no separate frontend build |
| **Database** | PostgreSQL | >= 14 | Primary data storage | ACID compliance, JSON support, excellent performance, mature ecosystem |
| **Vector Database** | pgvector | >= 0.5.0 | Vector embeddings storage | Native PostgreSQL extension, efficient similarity search, integrated with main DB |
| **ORM** | SQLAlchemy | >= 2.0.41 | Database abstraction layer | Modern async support, excellent type hints, powerful query capabilities |
| **Agent Framework** | Agno | >= 1.0.0 | Autonomous agent orchestration | Plugin-based architecture, hot-swappable agents, reasoning capabilities |
| **Package Manager** | UV | >= 0.5.0 | Dependency management | Fast Python package manager, reliable resolution, improved caching |

## AI & Machine Learning Stack

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **LLM API** | Google Gemini | >= 1.5 Pro | Document analysis and generation | Excellent document understanding, competitive pricing, reliable API |
| **Embeddings** | Google Gemini Embeddings | >= 1.0 | Text vectorization | Consistent with Gemini ecosystem, high-quality embeddings for legal documents |
| **RAG Framework** | LlamaIndex | >= 0.11.0 | Retrieval Augmented Generation | Mature RAG framework, excellent document processing, vector store integration |
| **Document Processing** | PyMuPDF | >= 1.24.0 | PDF text extraction | Fast PDF parsing, excellent text extraction accuracy, memory efficient |
| **OCR Engine** | PyTesseract | >= 0.3.10 | Optical character recognition | Industry standard OCR, excellent accuracy for legal documents |
| **Image Processing** | OpenCV | >= 4.10.0 | Image preprocessing for OCR | Robust image enhancement, noise reduction, layout analysis |
| **Image Manipulation** | Pillow | >= 10.4.0 | Image format handling | Wide format support, efficient image operations, Python native |

## Authentication & Security

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Authentication** | JWT | >= 2.8.0 | Token-based authentication | Stateless, scalable, industry standard for APIs |
| **2FA** | PyOTP | >= 2.9.0 | Two-factor authentication | TOTP standard implementation, security compliance |
| **Password Hashing** | bcrypt | >= 4.0.0 | Secure password storage | Industry standard, resistant to rainbow table attacks |
| **Encryption** | cryptography | >= 41.0.0 | Data encryption at rest | FIPS-compliant encryption, secure key management |

## Development & Testing

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Code Formatting** | Ruff | >= 0.6.0 | Code formatting and linting | Fastest Python linter, replaces multiple tools, excellent defaults |
| **Type Checking** | MyPy | >= 1.11.0 | Static type checking | Industry standard, excellent FastAPI integration, catches errors early |
| **Unit Testing** | Pytest | >= 8.3.0 | Unit and integration testing | Most popular Python testing framework, excellent fixtures, async support |
| **E2E Testing** | MCP Playwright | >= 1.0.0 | End-to-end browser testing | Real browser automation, cross-browser testing, reliable UI testing |
| **Test Coverage** | pytest-cov | >= 5.0.0 | Code coverage analysis | Standard coverage tool, integrates with pytest, detailed reporting |
| **Performance Testing** | Locust | >= 2.17.0 | Load testing | Python-native, scalable load testing, agent performance validation |

## Infrastructure & Deployment

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Containerization** | Docker | >= 24.0.0 | Application containerization | Industry standard, consistent environments, easy deployment |
| **Orchestration** | Docker Compose | >= 2.21.0 | Local development orchestration | Simple multi-container setup, development environment consistency |
| **Database Migrations** | Alembic | >= 1.13.0 | Database schema versioning | SQLAlchemy integration, safe migrations, rollback capabilities |
| **Dependency Injection** | dependency-injector | >= 4.41.0 | IoC container | Clean architecture, testability, loose coupling |
| **Reverse Proxy** | Caddy | >= 2.7.0 | Web server and reverse proxy | Automatic HTTPS, simple configuration, excellent performance |
| **Monitoring** | Prometheus | >= 2.45.0 | Metrics collection | Industry standard metrics, excellent alerting, grafana integration |
| **Logging** | Structlog | >= 23.2.0 | Structured logging | JSON logs, excellent debugging, cloud-native friendly |

## Data Storage & Caching

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Cache** | Redis | >= 7.2.0 | In-memory caching | Fast key-value store, excellent for session storage, agent state caching |
| **File Storage** | MinIO | >= 2023.11.0 | Object storage | S3-compatible, self-hosted, excellent for document storage |
| **Search Engine** | PostgreSQL FTS | Native | Full-text search | Built into PostgreSQL, good performance, no additional infrastructure |

## Documentation & Development Tools

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Documentation** | MCP Context7 | >= 1.0.0 | Framework documentation queries | Real-time documentation access, context-aware help |
| **API Documentation** | FastAPI Swagger | Native | Automatic API documentation | Built into FastAPI, interactive testing, always up-to-date |
| **Code Analysis** | SonarQube | >= 10.3.0 | Code quality analysis | Security vulnerability detection, code smell identification |

## Development Environment

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Python Version Manager** | pyenv | >= 2.3.0 | Python version management | Multiple Python versions, consistent across environments |
| **IDE Integration** | VS Code Extensions | Latest | Development productivity | Excellent Python support, debugging, testing integration |
| **Git Hooks** | pre-commit | >= 3.6.0 | Code quality automation | Automated formatting, linting, testing before commits |

## Architecture Patterns

The technology stack supports these key architectural patterns:

- **Async-First Architecture**: All I/O operations are asynchronous using Python's asyncio
- **Agent-Driven Processing**: Autonomous agents handle complex document processing workflows
- **Plugin-Based Extensibility**: Agent capabilities extended through dynamic plugin loading  
- **Repository Pattern**: Clean separation between business logic and data access
- **Service Layer Architecture**: Business logic encapsulated in service classes
- **Event-Driven Communication**: Agents coordinate through event messaging
- **Hot-Swappable Components**: Runtime agent replacement without system downtime
- **Defensive Programming**: Comprehensive error handling and graceful degradation

## Version Management Strategy

All dependencies use **minimum version ranges** (`>=`) to allow:
- Security patch updates
- Bug fix updates
- Compatible feature updates

Critical exceptions using exact versions (`==`):
- None currently - all dependencies stable with semver compatibility

## Performance Characteristics

The selected technology stack provides:
- **Async Performance**: FastAPI + SQLAlchemy async for high concurrency
- **Memory Efficiency**: UV package management, efficient Python runtime
- **Scalability**: Stateless design, horizontal scaling capabilities
- **Developer Productivity**: Type safety, excellent tooling, rapid development

## Security Compliance

Technologies selected meet security requirements:
- **OWASP Top 10**: Protection against common vulnerabilities
- **Data Encryption**: At-rest and in-transit encryption capabilities
- **Authentication Standards**: OAuth 2.0, TOTP 2FA compliance
- **Audit Logging**: Comprehensive security event logging