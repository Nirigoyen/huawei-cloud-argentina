from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel
from typing import Optional
from datetime import date

app = FastAPI(title="Library API", version="1.0.0")


class Book(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    published_date: Optional[date] = None
    available: bool = True


class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str
    published_date: Optional[date] = None


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    available: Optional[bool] = None


books_db = {}


@app.get("/books", response_model=list[Book])
def list_books(
    author: Optional[str] = Query(None, description="Filter by author"),
    available: Optional[bool] = Query(None, description="Filter by availability"),
):
    results = list(books_db.values())
    if author:
        results = [b for b in results if b.author == author]
    if available is not None:
        results = [b for b in results if b.available == available]
    return results


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int = Path(..., description="The ID of the book")):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    return books_db[book_id]


@app.post("/books", response_model=Book, status_code=201)
def create_book(book: BookCreate):
    book_id = len(books_db) + 1
    new_book = Book(id=book_id, **book.model_dump())
    books_db[book_id] = new_book
    return new_book


@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book: BookUpdate):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    existing = books_db[book_id]
    update_data = book.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=update_data)
    books_db[book_id] = updated
    return updated


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    del books_db[book_id]
