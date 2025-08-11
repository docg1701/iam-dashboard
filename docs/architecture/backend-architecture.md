# Backend Architecture

The backend architecture implements a hybrid monolith + independent agents pattern with FastAPI, supporting flexible agent-based permissions and reliable multi-client VPS deployments.

## Service Architecture

### Controller/Route Organization
```
apps/backend/src/
├── main.py              # FastAPI application entry point
├── core/                # Core application configuration
│   ├── config.py       # Settings and environment configuration
│   ├── database.py     # Database connection and session management
│   ├── security.py     # Authentication and authorization utilities
│   └── exceptions.py   # Custom exception handlers
├── api/                 # API route controllers
│   ├── v1/             # API version 1 routes
│   │   ├── auth.py     # Authentication endpoints
│   │   ├── users.py    # User management endpoints
│   │   ├── clients.py  # Client management endpoints
│   │   ├── permissions.py # Permission management endpoints
│   │   └── audit.py    # Audit log endpoints
│   └── dependencies.py # Shared route dependencies
├── services/            # Business logic services
│   ├── auth_service.py # Authentication business logic
│   ├── permission_service.py # Permission validation and management
│   ├── client_service.py # Client data operations
│   └── audit_service.py # Audit logging service
├── models/              # SQLModel data models
│   ├── user.py         # User model and related schemas
│   ├── client.py       # Client model and related schemas
│   ├── permission.py   # Permission models
│   └── audit.py        # Audit log models
├── agents/              # Independent agent implementations
│   ├── client_management/ # Agent 1: Client CRUD operations
│   ├── pdf_processing/   # Agent 2: Document processing
│   ├── reports_analysis/ # Agent 3: Analytics and reporting
│   └── audio_recording/ # Agent 4: Audio capture and transcription
└── utils/               # Backend utilities
    ├── validators.py   # Data validation utilities
    ├── formatters.py   # Data formatting helpers
    └── cache.py        # Redis caching utilities
```

---
