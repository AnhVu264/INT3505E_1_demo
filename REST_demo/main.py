from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional

app = FastAPI(title="REST Principles Demo")

books = [
    {"id": 1, "title": "Vo chong A Phu", "author": "To Hoai"},
    {"id": 2, "title": "Chiec thuyen ngoai xa", "author": "Nguyen Minh Chau"},
    {"id": 3, "title": "Vo nhat", "author": "Kim Lan"},
    {"id": 4, "title": "Chi Pheo", "author": "Nam Cao"},
    {"id": 5, "title": "Viet Bac", "author": "To Huu"},
    {"id": 6, "title": "Nguoi lai do song Da", "author": "Nguyen Tuan"},
]


# CLIENT–SERVER 
@app.get("/books")
def get_books():
    return books



# STATELESS
@app.get("/secure/books")
def get_secure_books(authorization: Optional[str] = Header(None)):
    if authorization != "Bearer SECRET_TOKEN":
        raise HTTPException(status_code=401, detail="Unauthorized: Missing or invalid token")
    return {"message": "Access granted", "data": books}


# CACHEABLE 
@app.get("/cacheable/books")
def get_cacheable_books():
    response = JSONResponse(content=books)
    response.headers["Cache-Control"] = "public, max-age=60"
    return response



# UNIFORM INTERFACE 
@app.get("/books/{book_id}")
def get_book(book_id: int):
    for book in books:
        if book["id"] == book_id:
            return {
                "data": book,
                "links": {
                    "self": f"/books/{book_id}",
                    "all_books": "/books",
                    "update": f"/books/{book_id}",
                    "delete": f"/books/{book_id}"
                }
            }
    raise HTTPException(status_code=404, detail="Book not found")
