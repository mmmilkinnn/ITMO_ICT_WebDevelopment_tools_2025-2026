from typing import Any

import requests
from celery.result import AsyncResult
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.celery_app import celery_app, parse_url_task
from app.config import settings
from app.database import get_db, prepare_database
from app.models import Hackathon

app = FastAPI(title=settings.PROJECT_NAME)


class ParseRequest(BaseModel):
    url: HttpUrl


class HackathonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_url: str
    status: str
    parser_approach: str


@app.on_event("startup")
def startup() -> None:
    prepare_database()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Lab 3 API is running"}


@app.get("/hackathons", response_model=list[HackathonResponse])
def get_hackathons(db: Session = Depends(get_db)) -> list[Hackathon]:
    return list(db.scalars(select(Hackathon).order_by(Hackathon.id.desc())).all())


@app.post("/parser/parse")
def parse_url(payload: ParseRequest) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{settings.PARSER_SERVICE_URL}/parse",
            json={"url": str(payload.url)},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Parser service is unavailable: {exc}",
        ) from exc

    return response.json()


@app.post("/parser/tasks", status_code=status.HTTP_202_ACCEPTED)
def create_parse_task(payload: ParseRequest) -> dict[str, str]:
    task = parse_url_task.delay(str(payload.url))
    return {"task_id": task.id, "status": "queued"}


@app.get("/parser/tasks/{task_id}")
def get_parse_task(task_id: str) -> dict[str, Any]:
    task = AsyncResult(task_id, app=celery_app)
    response: dict[str, Any] = {"task_id": task_id, "status": task.status}

    if task.ready():
        if task.successful():
            response["result"] = task.result
        else:
            response["error"] = str(task.result)

    return response
