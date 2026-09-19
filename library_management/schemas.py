from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ReaderBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=50
    )

    email: EmailStr = Field(
        max_length=120
    )


class ReaderCreate(ReaderBase):
    pass


class ReaderResponse(ReaderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_file: str | None
    profile_path: str


class ReaderUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    email: EmailStr | None = Field(
        default=None,
        max_length=120
    )

    profile_file: str | None = Field(
        default=None,
        min_length=1,
        max_length=200
    )


class BookBase(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100
    )

    description: str = Field(
        min_length=1
    )


class BookCreate(BookBase):
    reader_id: int


class BookUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    description: str | None = Field(
        default=None,
        min_length=1
    )


class BookResponse(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reader_id: int
    borrowed_at: datetime
    reader: ReaderResponse