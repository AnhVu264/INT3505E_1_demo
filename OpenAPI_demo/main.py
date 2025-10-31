from fastapi import FastAPI, HTTPException, APIRouter, status, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()

fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin",
    },
    "user": {
        "username": "user",
        "hashed_password": pwd_context.hash("user123"),
        "role": "user",
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    role: str

class UserInDB(User):
    hashed_password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ✅ Hàm lấy user từ Bearer token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

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
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    filtered_books = books_db
    if q:
        q_lower = q.lower()
        filtered_books = [
            b for b in books_db if q_lower in b["title"].lower() or q_lower in b["author"].lower()
        ]
    return filtered_books[skip: skip + limit]

@router_v1.get("/books/{id}", response_model=Book)
def get_book(id: int, current_user: User = Depends(get_current_user)):
    for book in books_db:
        if book["id"] == id:
            return book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy sách")

@router_v1.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def add_book(book_in: BookCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin được thêm sách")
    new_book = book_in.dict()
    new_book["id"] = max([b["id"] for b in books_db]) + 1 if books_db else 1
    books_db.append(new_book)
    return new_book

@router_v1.put("/books/{id}", response_model=Book)
def update_book(id: int, book_in: BookCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin được cập nhật sách")
    for index, book in enumerate(books_db):
        if book["id"] == id:
            updated = book_in.dict()
            updated["id"] = id
            books_db[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Không tìm thấy sách")

@router_v1.delete("/books/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(id: int, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin được xóa sách")
    for book in books_db:
        if book["id"] == id:
            books_db.remove(book)
            return
    raise HTTPException(status_code=404, detail="Không tìm thấy sách")


app = FastAPI(title="Book Management API with JWT (HTTPBearer)")

app.include_router(router_v1)

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Sai tài khoản hoặc mật khẩu")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_access_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@app.post("/token/refresh", response_model=Token)
async def refresh_access_token(token_data: RefreshTokenRequest):
    refresh_token = token_data.refresh_token
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=username)
    if user is None:
        raise credentials_exception
    
    new_access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(data={"sub": user.username}, expires_delta=new_access_token_expires)
    
    new_refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_access_token(data={"sub": user.username}, expires_delta=new_refresh_token_expires)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token
    }

@app.get("/")
def read_root():
    return {"message": "Book API có JWT (HTTPBearer) — Truy cập /docs để lấy token và nhập thủ công vào Authorize"}



