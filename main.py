
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Please check your .env file.")
app = FastAPI(
    title="Library API",
    description="A simple API for managing a library of books.",
    version="1.0.0",
)


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=0, le=2100)


class Book(BookCreate):
    id: int


class BookUpdate(BaseModel):
    title: str = Field(default=None, min_length=1, max_length=200)
    author: str = Field(default=None, min_length=1, max_length=100)
    year: int = Field(default=None, ge=0, le=2100)





@app.get("/")
def home():
    return {"message": "Welcome to the Library API"}


@app.get("/books", response_model=list[Book])
def get_books():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, author, year FROM books ORDER BY id"
        ).fetchall()

    return [Book(id=row[0], title=row[1], author=row[2], year=row[3]) for row in rows]

@app.post("/books", response_model=Book, status_code=201)
def create_book(book_data: BookCreate):
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO books (title, author, year)
            VALUES (%s, %s, %s)
            RETURNING id, title, author, year
            """,
            (book_data.title, book_data.author, book_data.year),
        ).fetchone()

    return Book(id=row[0], title=row[1], author=row[2], year=row[3])

@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, title, author, year FROM books WHERE id = %s",
            (book_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return Book(id=row[0], title=row[1], author=row[2], year=row[3])

@app.patch("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book_data: BookUpdate):
    updates = book_data.model_dump(exclude_unset=True)

    if not updates:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, title, author, year FROM books WHERE id = %s",
                (book_id,),
            ).fetchone()
    else:
        allowed_fields = {"title", "author", "year"}
        fields = [field for field in updates if field in allowed_fields]
        set_clause = ", ".join(f"{field} = %s" for field in fields)
        values = [updates[field] for field in fields]

        with get_connection() as conn:
            row = conn.execute(
                f"""
                UPDATE books
                SET {set_clause}
                WHERE id = %s
                RETURNING id, title, author, year
                """,
                (*values, book_id),
            ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return Book(id=row[0], title=row[1], author=row[2], year=row[3])

@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "DELETE FROM books WHERE id = %s RETURNING id",
            (book_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

def get_connection():
    return psycopg.connect(DATABASE_URL)







