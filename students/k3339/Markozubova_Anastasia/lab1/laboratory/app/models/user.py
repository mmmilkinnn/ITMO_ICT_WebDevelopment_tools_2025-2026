from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_salt: Mapped[str] = mapped_column(String(255), nullable=False)
    is_organizer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    organized_hackathons = relationship("Hackathon", back_populates="organizer") #список хакатонов, которые создал пользователь;
    hackathon_registrations = relationship("HackathonRegistration", back_populates="user") #список регистраций пользователя на хакатоны.
    team_memberships = relationship("TeamMembership", back_populates="user")  #список команд в которых состоит пользователь
    created_teams = relationship("Team", back_populates="created_by") #список созданных пользовтаелем команды
    submissions = relationship("Submission", back_populates="submitted_by")
    reviews = relationship("Review", back_populates="reviewer")
