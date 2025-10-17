from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import yaml
from typing import Optional, List

# Tạo ứng dụng FastAPI
app = FastAPI(title="Book Management API", version="1.0.0")

# Đọc file OpenAPI YAML
with open("book_api.yaml", "r", encoding="utf-8") as f:
    spec = yaml.safe_load(f)

@app.get("/openapi.yaml")
def get_spec():
    """Trả về nội dung OpenAPI YAML dưới dạng JSON"""
    return JSONResponse(content=spec)

books = [
        {"id": 1, "title": "Vo chong A Phu", "author": "To Hoai"},
        {"id": 2, "title": "Chiec thuyen ngoai xa", "author": "Nguyen Minh Chau"},
        {"id": 3, "title": "Vo nhat", "author": "Kim Lan"},
        {"id": 4, "title": "Chi Pheo", "author": "Nam Cao"},
    ]

@app.get("/books")
def get_books():
    return books


@app.get("/books/search")
def search_books(q: Optional[str] = None, skip: int = 0, limit: int = 2):
    """
    Tìm kiếm sách theo từ khóa (q) trong tiêu đề hoặc tác giả.
    Có hỗ trợ phân trang bằng skip (bỏ qua N sách đầu) và limit (số sách trả về).
    """
    filtered_books = books
    if q:
        q_lower = q.lower()
        filtered_books = [
            b for b in books if q_lower in b["title"].lower() or q_lower in b["author"].lower()
        ]
    return filtered_books[skip: skip + limit]


@app.get("/books/{id}")
def get_book(id: int):
    for book in books:
        if book["id"] == id:
            return book
    raise HTTPException(status_code=404, detail="Khong tim thay sach")


@app.post("/books")
def add_book(book: dict):
    book["id"] = max([b["id"] for b in books]) + 1 if books else 1
    books.append(book)
    return {"message": "Sach duoc them thanh cong", "book": book}


@app.put("/books/{id}")
def update_book(id: int, new_data: dict):
    for book in books:
        if book["id"] == id:
            book.update(new_data)
            return {"message": "Sach da duoc cap nhat", "book": book}
    raise HTTPException(status_code=404, detail="Khong tim thay sach")


@app.delete("/books/{id}")
def delete_book(id: int):
    for book in books:
        if book["id"] == id:
            books.remove(book)
            return {"message": "Sach duoc xoa thanh cong"}
    raise HTTPException(status_code=404, detail="Khong tim thay sach")



