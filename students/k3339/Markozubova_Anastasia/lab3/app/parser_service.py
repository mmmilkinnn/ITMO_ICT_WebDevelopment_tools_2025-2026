from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl
from requests import RequestException

from app.database import prepare_database
from app.parser_logic import parse_and_save_url

app = FastAPI(title="Lab 3 Parser Service")


class ParseRequest(BaseModel):
    url: HttpUrl


@app.on_event("startup")
def startup() -> None:
    prepare_database()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Parser service is running"}


@app.post("/parse")
def parse(payload: ParseRequest) -> dict[str, Any]:
    try:
        return parse_and_save_url(str(payload.url), "http-parser-service")
    except RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
