# Source Tree Integration

## Current Project Structure
```
iam-dashboard/
├── app/
│   ├── main.py                 # Entry point
│   ├── core/                   # Core modules
│   │   ├── auth.py
│   │   └── database.py
│   ├── models/                 # SQLAlchemy models
│   ├── repositories/           # Data access layer
│   ├── services/              # Business logic (TO BE REPLACED)
│   ├── ui_components/         # NiceGUI components
│   ├── api/                   # FastAPI endpoints
│   └── workers/               # Celery workers (TO BE REMOVED)
├── alembic/                   # Database migrations
├── tests/
└── docs/
```

## Target Project Structure with Agents
```
iam-dashboard/
├── app/
│   ├── main.py                 # Entry point (MODIFIED)
│   ├── core/                   # Core modules
│   │   ├── auth.py
│   │   ├── database.py
│   │   └── agent_manager.py    # NEW: Central agent management
│   ├── models/                 # SQLAlchemy models (UNCHANGED)
│   ├── repositories/           # Data access layer (UNCHANGED)
│   ├── agents/                 # NEW: Agno agents
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── pdf_processor_agent.py
│   │   └── questionnaire_agent.py
│   ├── tools/                  # NEW: Agno tools
│   │   ├── __init__.py
│   │   ├── pdf_tools.py
│   │   ├── vector_storage_tools.py
│   │   └── ocr_tools.py
│   ├── plugins/                # NEW: Agent plugins
│   │   ├── __init__.py
│   │   ├── pdf_processor_plugin.py
│   │   └── questionnaire_plugin.py
│   ├── ui_components/         # NiceGUI components (MODIFIED)
│   │   ├── dashboard.py        # Add agent status
│   │   ├── admin_control_panel.py # NEW: Agent management
│   │   └── ...
│   ├── api/                   # FastAPI endpoints (MODIFIED)
│   │   ├── documents.py        # Replace Celery with agents
│   │   ├── questionnaires.py   # Replace services with agents
│   │   └── admin.py           # NEW: Agent management API
│   ├── config/                # NEW: Agent configurations
│   │   └── agents.yaml
│   └── containers.py          # MODIFIED: Add agent providers
├── tests/                     # MODIFIED: Add agent tests
│   ├── unit/
│   │   ├── test_agents/        # NEW: Agent tests
│   │   └── test_tools/         # NEW: Tool tests
│   └── integration/
│       └── test_agent_workflows.py # NEW: Full workflow tests
└── docs/                      # UPDATED: Add agent documentation
    ├── architecture.md         # THIS FILE
    └── agent-development-guide.md # NEW
```

## File Integration Details

**Modified Files:**

1. **app/main.py** - Initialize agent manager
```python