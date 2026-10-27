
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

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
    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=0, le=2100)


books: list[Book] = [
    Book(id=1, title="The Hobbit", author="J.R.R. Tolkien", year=1937),
    Book(id=2, title="1984", author="George Orwell", year=1949),
]

next_book_id = 3


@app.get("/")
def home():
    return {"message": "Welcome to the Library API"}


@app.get("/books", response_model=list[Book])
def get_books():
    return books


@app.post("/books", response_model=Book, status_code=201)
def create_book(book_data: BookCreate):
    global next_book_id

    new_book = Book(id=next_book_id, **book_data.model_dump())
    books.append(new_book)
    next_book_id += 1

    return new_book


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    for book in books:
        if book.id == book_id:
            return book

    raise HTTPException(status_code=404, detail="Book not found")


@app.patch("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book_data: BookUpdate):
    for index, book in enumerate(books):
        if book.id == book_id:
            updates = book_data.model_dump(exclude_unset=True)
            updated_book = book.model_copy(update=updates)
            books[index] = updated_book
            return updated_book

    raise HTTPException(status_code=404, detail="Book not found")


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    for index, book in enumerate(books):
        if book.id == book_id:
            books.pop(index)
            return

    raise HTTPException(status_code=404, detail="Book not found")
