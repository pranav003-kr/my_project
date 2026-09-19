from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Reader(Base):
    __tablename__ = "readers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False
    )

    profile_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default=None
    )

    books: Mapped[list[Book]] = relationship(
        back_populates="reader",
        cascade="all, delete-orphan"
    )

    @property
    def profile_path(self) -> str:
        if self.profile_pic:
            return f"/media/reader_pics/{self.profile_pic}"

        return "/static/images/default-reader.jpg"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    reader_id: Mapped[int] = mapped_column(
        ForeignKey("readers.id"),
        nullable=False,
        index=True
    )

    borrowed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    reader: Mapped[Reader] = relationship(
        back_populates="books"
    )