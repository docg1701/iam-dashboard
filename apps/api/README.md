# IAM Dashboard API

FastAPI backend for the Multi-agent IAM Dashboard.

## Development

```bash
# Install dependencies
uv sync --dev

# Run development server
uv run uvicorn src.main:app --reload

# Run tests
uv run pytest

# Run migrations
uv run alembic upgrade head
```

## Docker

```bash
# Build development image
docker build --target development -t iam-dashboard-api:dev .

# Build production image
docker build --target production -t iam-dashboard-api:prod .
```