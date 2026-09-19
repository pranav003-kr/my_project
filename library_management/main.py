from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

import models

from database import Base, engine, get_db

from schemas import (
    BookCreate,
    BookResponse,
    BookUpdate,
    ReaderCreate,
    ReaderResponse,
    ReaderUpdate,
)


Base.metadata.create_all(bind=engine)


# app = FastAPI(
#     title="BookShelf API",
#     description="A simple library management backend",
#     version="1.0.0"
# )

app = FastAPI()


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

app.mount(
    "/media",
    StaticFiles(directory="media"),
    name="media"
)


templates = Jinja2Templates(
    directory="templates"
)


# HTML PAGES

@app.get(
    "/",
    include_in_schema=False,
    name="home"
)
@app.get(
    "/books",
    include_in_schema=False,
    name="books"
)
def home(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Book)
    )

    books = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "books": books,
            "title": "BookShelf"
        }
    )


@app.get(
    "/books/{book_id}",
    include_in_schema=False
)
def book_page(
    request: Request,
    book_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Book)
        .where(models.Book.id == book_id)
    )

    book = result.scalars().first()

    if book:
        title = book.title[:50]

        return templates.TemplateResponse(
            request,
            "book.html",
            {
                "book": book,
                "title": title
            }
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Book not found"
    )


@app.get(
    "/readers/{reader_id}/books",
    include_in_schema=False,
    name="reader_books"
)
def reader_books_page(
    request: Request,
    reader_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Reader)
        .where(models.Reader.id == reader_id)
    )

    reader = result.scalars().first()

    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found"
        )

    result = db.execute(
        select(models.Book)
        .where(models.Book.reader_id == reader_id)
    )

    books = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "reader_books.html",
        {
            "books": books,
            "reader": reader,
            "title": f"{reader.name}'s Books"
        }
    )


# READER API

@app.post(
    "/api/readers",
    response_model=ReaderResponse,
    status_code=status.HTTP_201_CREATED
)
def create_reader(
    reader: ReaderCreate,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Reader)
        .where(models.Reader.name == reader.name)
    )

    existing_reader = result.scalars().first()

    if existing_reader:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reader name already exists"
        )

    result = db.execute(
        select(models.Reader)
        .where(models.Reader.email == reader.email)
    )

    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_reader = models.Reader(
        name=reader.name,
        email=reader.email
    )

    db.add(new_reader)
    db.commit()
    db.refresh(new_reader)

    return new_reader


@app.get(
    "/api/readers/{reader_id}",
    response_model=ReaderResponse
)
def get_reader(
    reader_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Reader)
        .where(models.Reader.id == reader_id)
    )

    reader = result.scalars().first()

    if reader:
        return reader

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Reader not found"
    )


@app.get(
    "/api/readers/{reader_id}/books",
    response_model=list[BookResponse]
)
def get_reader_books(
    reader_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Reader)
        .where(models.Reader.id == reader_id)
    )

    reader = result.scalars().first()

    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found"
        )

    result = db.execute(
        select(models.Book)
        .where(models.Book.reader_id == reader_id)
    )

    books = result.scalars().all()

    return books


@app.patch(
    "/api/readers/{reader_id}",
    response_model=ReaderResponse
)
def update_reader(
    reader_id: int,
    reader_update: ReaderUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Reader)
        .where(models.Reader.id == reader_id)
    )

    reader = result.scalars().first()

    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found"
        )

    if (
        reader_update.name is not None
        and reader_update.name != reader.name
    ):
        result = db.execute(
            select(models.Reader)
            .where(
                models.Reader.name == reader_update.name
            )
        )

        existing_reader = result.scalars().first()

        if existing_reader:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reader name already exists"
            )

    if (
        reader_update.email is not None
        and reader_update.email != reader.email
    ):
        result = db.execute(
            select(models.Reader)
            .where(
                models.Reader.email == reader_update.email
            )
        )

        existing_email = result.scalars().first()

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    if reader_update.name is not None:
        reader.name = reader_update.name

    if reader_update.email is not None:
        reader.email = reader_update.email

    if reader_update.profile_file is not None:
        reader.profile_file = reader_update.profile_file

    db.commit()
    db.refresh(reader)

    return reader


@app.delete(
    "/api/readers/{reader_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_reader(
    reader_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Reader)
        .where(models.Reader.id == reader_id)
    )

    reader = result.scalars().first()

    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found"
        )

    db.delete(reader)
    db.commit()


# BOOK API

@app.get(
    "/api/books",
    response_model=list[BookResponse]
)
def get_books(
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Book)
    )

    books = result.scalars().all()

    return books


@app.post(
    "/api/books",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED
)
def create_book(
    book: BookCreate,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Reader)
        .where(models.Reader.id == book.reader_id)
    )

    reader = result.scalars().first()

    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader not found"
        )

    new_book = models.Book(
        title=book.title,
        description=book.description,
        reader_id=book.reader_id
    )

    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    return new_book


@app.get(
    "/api/books/{book_id}",
    response_model=BookResponse
)
def get_book(
    book_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Book)
        .where(models.Book.id == book_id)
    )

    book = result.scalars().first()

    if book:
        return book

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Book not found"
    )


@app.put(
    "/api/books/{book_id}",
    response_model=BookResponse
)
def update_book_full(
    book_id: int,
    book_data: BookCreate,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Book)
        .where(models.Book.id == book_id)
    )

    book = result.scalars().first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    if book_data.reader_id != book.reader_id:
        result = db.execute(
            select(models.Reader)
            .where(
                models.Reader.id == book_data.reader_id
            )
        )

        reader = result.scalars().first()

        if not reader:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reader not found"
            )

    book.title = book_data.title
    book.description = book_data.description
    book.reader_id = book_data.reader_id

    db.commit()
    db.refresh(book)

    return book


@app.patch(
    "/api/books/{book_id}",
    response_model=BookResponse
)
def update_book_partial(
    book_id: int,
    book_data: BookUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Book)
        .where(models.Book.id == book_id)
    )

    book = result.scalars().first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    update_data = book_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)

    return book


@app.delete(
    "/api/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_book(
    book_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.Book)
        .where(models.Book.id == book_id)
    )

    book = result.scalars().first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    db.delete(book)
    db.commit()


# ERROR HANDLERS

@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(
    request: Request,
    exception: StarletteHTTPException
):
    message = (
        exception.detail
        if exception.detail
        else "Something went wrong."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message}
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message
        },
        status_code=exception.status_code
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request,
    exception: RequestValidationError
):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": exception.errors()
            }
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input."
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )