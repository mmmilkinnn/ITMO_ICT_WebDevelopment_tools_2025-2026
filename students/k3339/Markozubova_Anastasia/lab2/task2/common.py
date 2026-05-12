from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


LAB1_ROOT = Path(__file__).resolve().parents[2] / "lab1" / "laboratory"
if str(LAB1_ROOT) not in sys.path:
    sys.path.append(str(LAB1_ROOT))

from app.models.base import Base
import app.db.base
from app.models.hackathon import Hackathon
from app.models.user import User


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:1234@localhost:5432/hackathon_lab2",
)

URLS = [
    "https://devpost.com/hackathons",
    "https://hackathon.com/",
    "https://mlh.io/seasons/2026/events",
    "https://www.kaggle.com/competitions",
    "https://www.spaceappschallenge.org/",
]

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._inside_title = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._inside_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._inside_title = False

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self._parts.append(data.strip())

    @property
    def title(self) -> str:
        return " ".join(part for part in self._parts if part).strip()


def prepare_database() -> None:
    Base.metadata.create_all(bind=engine)
    get_or_create_parser_organizer()


def extract_title(html: str) -> str:
    parser = TitleParser()
    parser.feed(html)
    return parser.title or "Untitled hackathon source"


def split_urls(urls: list[str], parts: int) -> list[list[str]]:
    parts = max(1, min(parts, len(urls)))
    chunk_size, remainder = divmod(len(urls), parts)
    chunks = []
    start = 0

    for index in range(parts):
        current_size = chunk_size + (1 if index < remainder else 0)
        end = start + current_size
        chunks.append(urls[start:end])
        start = end

    return chunks


def get_or_create_parser_organizer() -> int:
    with SessionLocal() as session:
        organizer = session.scalar(
            select(User).where(User.email == "lab2-hackathon-parser@example.com")
        )
        if organizer is not None:
            return organizer.id

        organizer = User(
            email="lab2-hackathon-parser@example.com",
            first_name="Lab2",
            last_name="HackathonParser",
            phone_number="+70000002026",
            password_hash="not-used",
            password_salt="not-used",
            is_organizer=True,
        )
        session.add(organizer)

        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            organizer = session.scalar(
                select(User).where(User.email == "lab2-hackathon-parser@example.com")
            )
            if organizer is None:
                raise
        else:
            session.refresh(organizer)

        return organizer.id


def save_hackathon_title(url: str, title: str, approach: str) -> int:
    organizer_id = get_or_create_parser_organizer()
    today = date.today()

    with SessionLocal() as session:
        hackathon = Hackathon(
            title=title[:255],
            description=(
                f"Parsed from hackathon-related source: {url}. "
                f"Parser approach: {approach}."
            ),
            start_date=today,
            end_date=today + timedelta(days=7),
            status="parsed",
            organizer_id=organizer_id,
        )
        session.add(hackathon)
        session.commit()
        session.refresh(hackathon)
        return hackathon.id
