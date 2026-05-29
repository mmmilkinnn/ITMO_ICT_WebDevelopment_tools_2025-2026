from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_organizer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    hackathons = relationship("Hackathon", back_populates="organizer")


class Hackathon(Base):
    __tablename__ = "hackathons"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="parsed", nullable=False)
    parser_approach: Mapped[str] = mapped_column(String(100), nullable=False)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    organizer = relationship("User", back_populates="hackathons")


def get_or_create_parser_organizer(session: Session) -> User:
    organizer = session.scalar(
        select(User).where(User.email == "lab3-parser@example.com")
    )
    if organizer is not None:
        return organizer

    organizer = User(
        email="lab3-parser@example.com",
        first_name="Lab3",
        last_name="Parser",
        is_organizer=True,
    )
    session.add(organizer)
    session.flush()
    return organizer


def create_parsed_hackathon(session: Session, url: str, title: str, approach: str) -> Hackathon:
    organizer = get_or_create_parser_organizer(session)
    today = date.today()

    hackathon = Hackathon(
        title=title[:255],
        source_url=url,
        description=f"Parsed from source: {url}. Parser approach: {approach}.",
        start_date=today,
        end_date=today + timedelta(days=7),
        status="parsed",
        parser_approach=approach,
        organizer_id=organizer.id,
    )
    session.add(hackathon)
    session.commit()
    session.refresh(hackathon)
    return hackathon
