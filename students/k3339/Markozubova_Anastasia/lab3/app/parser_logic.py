from __future__ import annotations

from html.parser import HTMLParser

import requests

from app.database import SessionLocal
from app.models import create_parsed_hackathon

DEFAULT_URLS = [
    "https://devpost.com/hackathons",
    "https://hackathon.com/",
    "https://mlh.io/seasons/2026/events",
    "https://www.kaggle.com/competitions",
    "https://www.spaceappschallenge.org/",
]


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


def extract_title(html: str) -> str:
    parser = TitleParser()
    parser.feed(html)
    return parser.title or "Untitled hackathon source"


def parse_and_save_url(url: str, approach: str) -> dict:
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 lab3-parser"},
        timeout=30,
    )
    response.raise_for_status()

    title = extract_title(response.text)
    with SessionLocal() as session:
        hackathon = create_parsed_hackathon(session, url, title, approach)

    return {
        "message": "Parsing completed",
        "url": url,
        "title": title,
        "hackathon_id": hackathon.id,
    }
