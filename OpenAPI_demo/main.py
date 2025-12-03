from fastapi import FastAPI, HTTPException, APIRouter, status, Query, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator
import sys
import os
from dotenv import load_dotenv

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key_neu_quen_cau_hinh")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()

# Cấu hình Logger (Ghi ra file và Console)
logger.remove() # Xóa logger mặc định
logger.add(sys.stderr, level="INFO") # Hiện ra màn hình
logger.add("app_logs.json", format="{time} {level} {message}", level="INFO", rotation="10 MB", serialize=True) # Lưu file JSON

# Cấu hình Rate Limiter (Chặn spam theo IP)
limiter = Limiter(key_func=get_remote_address)

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
    links: List[Link] = []
    class Config:
        orm_mode = True

# VERSION 2
class PaymentIntentRequest(BaseModel):
    book_id: int
    quantity: int

class PaymentIntentResponse(BaseModel):
    intent_id: str
    client_secret: str # Gửi cái này về client (app/web)
    amount: float
    currency: str = "VND"

class PaymentConfirmRequest(BaseModel):
    payment_method_id: str # Token an toàn, ví dụ "pm_abc123"

class PaymentConfirmResponse(BaseModel):
    success: bool
    charge_id: str
    message: str

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
            # Tạo base URL động (ví dụ: http://localhost:8000/v1/books/1)
            base_url = str(request.base_url).rstrip("/")
            
            links = [
                {"rel": "self", "href": f"{base_url}/v1/books/{id}", "method": "GET"},
            ]
            
            # Nếu là admin thì gợi ý thêm link sửa/xóa
            if current_user.role == "admin":
                links.append({"rel": "update", "href": f"{base_url}/v1/books/{id}", "method": "PUT"})
                links.append({"rel": "delete", "href": f"{base_url}/v1/books/{id}", "method": "DELETE"})
            
            # Copy data để không ảnh hưởng DB gốc
            response_book = book.copy()
            response_book["links"] = links
            return response_book
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

router_v2 = APIRouter(prefix="/v2/checkout")

payment_intents_db = {}

@router_v2.post("/intents", response_model=PaymentIntentResponse, summary="[V2 - Bước 1] Tạo ý định thanh toán")
def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: User = Depends(get_current_user)
):
    book = next((b for b in books_db if b["id"] == request.book_id), None)
    if not book:
        raise HTTPException(status_code=404, detail="Không tìm thấy sách")


    amount = 100000 * request.quantity

    intent_id = f"pi_{current_user.username}_{datetime.now().timestamp()}"
    client_secret = f"{intent_id}_secret_key" # Key bí mật để client xác nhận

    # Lưu lại ý định thanh toán
    payment_intents_db[intent_id] = {
        "amount": amount,
        "book_title": book["title"],
        "status": "requires_payment_method"
    }

    return PaymentIntentResponse(
        intent_id=intent_id,
        client_secret=client_secret,
        amount=amount
    )

@router_v2.post("/intents/{intent_id}/confirm", response_model=PaymentConfirmResponse, summary="[V2 - Bước 2] Xác nhận thanh toán")
def confirm_payment(
    intent_id: str,
    request: PaymentConfirmRequest,
    current_user: User = Depends(get_current_user)
):
    if intent_id not in payment_intents_db:
        
        logger.error(f"Payment failed: Intent ID {intent_id} not found for user {current_user.username}")
        raise HTTPException(status_code=404, detail="Không tìm thấy ý định thanh toán")

    intent = payment_intents_db[intent_id]

    
    logger.info(f"Processing payment for Intent: {intent_id} | Amount: {intent['amount']} | Method: {request.payment_method_id}")

    # Giả lập logic Circuit Breaker (đơn giản hóa bằng try-except log)
    try:
        # Giả sử đây là code gọi Stripe/MoMo
        intent["status"] = "succeeded"
        charge_id = f"ch_v2_{intent_id}"
        
        logger.success(f"Payment successful: Charge ID {charge_id}") 
        
        return PaymentConfirmResponse(
            success=True,
            charge_id=charge_id,
            message=f"Cảm ơn {current_user.username} đã mua sách '{intent['book_title']}' thành công."
        )
    except Exception as e:
        logger.critical(f"CRITICAL PAYMENT ERROR: {str(e)}") 
        raise HTTPException(status_code=500, detail="Lỗi cổng thanh toán")

app = FastAPI(title="Book Management API with JWT (HTTPBearer)")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Tự động đo đạc metrics cho toàn bộ API
Instrumentator().instrument(app).expose(app)

app.include_router(router_v1)
app.include_router(router_v2) 

@app.post("/token", response_model=Token)
@limiter.limit("5/minute") 
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()): 
    
    logger.info(f"Login attempt | IP: {request.client.host} | Username: {form_data.username}")
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        
        logger.warning(f"Login failed | IP: {request.client.host} | Username: {form_data.username}")
        raise HTTPException(status_code=400, detail="Sai tài khoản hoặc mật khẩu")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_access_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    
    logger.success(f"Login successful | User: {user.username}")

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


