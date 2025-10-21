from fastapi import FastAPI, HTTPException, APIRouter, status, Query
from pydantic import BaseModel
from typing import Optional, List


class BookBase(BaseModel):
    title: str
    author: str

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    class Config:
        orm_mode = True

router_v1 = APIRouter(prefix="/v1")

books_db = [
    {"id": 1, "title": "Vợ chồng A Phủ", "author": "Tô Hoài"},
    {"id": 2, "title": "Chiếc thuyền ngoài xa", "author": "Nguyễn Minh Châu"},
    {"id": 3, "title": "Vợ nhặt", "author": "Kim Lân"},
    {"id": 4, "title": "Chí Phèo", "author": "Nam Cao"},
    {"id": 5, "title": "Việt Bắc", "author": "Tố Hữu"},
    {"id": 6, "title": "Nguoi lái đò sông Đà", "author": "Nguyẽn Tuân"},
]


@router_v1.get("/books", response_model=List[Book])
def get_books(
    q: Optional[str] = Query(None, description="Tìm kiếm theo tiêu đề hoặc tác giả"),
    skip: int = 0,
    limit: int = 10
):
    filtered_books = books_db
    if q:
        q_lower = q.lower()
        filtered_books = [
            b for b in books_db if q_lower in b["title"].lower() or q_lower in b["author"].lower()
        ]
    return filtered_books[skip: skip + limit]


@router_v1.get("/books/{id}", response_model=Book)
def get_book(id: int):
    for book in books_db:
        if book["id"] == id:
            return book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy sách")


@router_v1.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def add_book(book_in: BookCreate):
    new_book_data = book_in.dict()
    new_book_data["id"] = max([b["id"] for b in books_db]) + 1 if books_db else 1
    
    books_db.append(new_book_data)
    return new_book_data


@router_v1.put("/books/{id}", response_model=Book)
def update_book(id: int, book_in: BookCreate):
    for index, book in enumerate(books_db):
        if book["id"] == id:
            updated_book_data = book_in.dict()
            updated_book_data["id"] = id
            books_db[index] = updated_book_data
            return updated_book_data
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy sách")


@router_v1.delete("/books/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(id: int):
    book_to_delete = None
    for book in books_db:
        if book["id"] == id:
            book_to_delete = book
            break
    
    if book_to_delete:
        books_db.remove(book_to_delete)
        return # Trả về response 204 (No Content)
        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy sách")


app = FastAPI(title="Book Management API")

app.include_router(router_v1)

@app.get("/")
def read_root():
    return {"message": "Chào mừng đến với Book API. Thử truy cập /v1/books hoặc /docs"}