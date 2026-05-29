from __future__ import annotations

import requests
from celery import Celery
from celery.schedules import crontab

from app.config import settings
from app.parser_logic import DEFAULT_URLS

celery_app = Celery(
    "lab3_parser_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=True,
)


@celery_app.task(name="parse_url_task")
def parse_url_task(url: str) -> dict:
    response = requests.post(
        f"{settings.PARSER_SERVICE_URL}/parse",
        json={"url": url},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


@celery_app.task(name="parse_default_sources_task")
def parse_default_sources_task() -> list[dict]:
    return [parse_url_task.run(url) for url in DEFAULT_URLS]


celery_app.conf.beat_schedule = {
    "parse-default-hackathon-sources-hourly": {
        "task": "parse_default_sources_task",
        "schedule": crontab(minute=0),
    },
}
