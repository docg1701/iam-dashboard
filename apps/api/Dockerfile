# Multi-stage Dockerfile for FastAPI application
FROM python:3.13-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    UV_CACHE_DIR=/app/.cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Create non-root user FIRST
RUN useradd --create-home --shell /bin/bash app

# Set work directory and change ownership
WORKDIR /app
RUN chown -R app:app /app

# Switch to app user for all subsequent operations
USER app

# Copy dependency files with proper ownership
COPY --chown=app:app pyproject.toml ./
COPY --chown=app:app requirements.txt* ./
COPY --chown=app:app README.md ./

# Development stage
FROM base as development

# Install development dependencies as app user
RUN uv sync --dev

# Copy application code with proper ownership
COPY --chown=app:app src/ ./src/
COPY --chown=app:app alembic/ ./alembic/
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app tests/ ./tests/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application with hot reload
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Install only production dependencies as app user
RUN uv sync --frozen

# Copy application code with proper ownership
COPY --chown=app:app src/ ./src/
COPY --chown=app:app alembic/ ./alembic/
COPY --chown=app:app alembic.ini ./

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]