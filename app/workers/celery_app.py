"""Celery application configuration."""

import os

from celery import Celery

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Create Celery app
celery_app = Celery(
    "iam_dashboard",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=[
        "app.workers.document_processor",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
)

if __name__ == "__main__":
    celery_app.start()
