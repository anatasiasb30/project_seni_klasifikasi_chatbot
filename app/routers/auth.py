from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext

# Import file lokal
from app import models, schemas, config, dependencies

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- HELPER FUNCTIONS ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

# --- ROUTES (GET) ---
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

# --- ROUTES (POST) ---
@router.post("/register")
async def register(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(dependencies.get_db)
):
    # 1. [TAMBAHAN] Cek Email terlebih dahulu
    # Penting: Cek email dulu karena email sifatnya unik personal
    email_exists = db.query(models.User).filter(models.User.email == email).first()
    if email_exists:
        return templates.TemplateResponse("auth/register.html", {
            "request": request, 
            "error": "Email ini sudah terdaftar! Silakan login."
        })

    # 2. Cek Username
    username_exists = db.query(models.User).filter(models.User.username == username).first()
    if username_exists:
        return templates.TemplateResponse("auth/register.html", {
            "request": request, 
            "error": "Username sudah terdaftar! Cari username lain."
        })

    # 3. Proses Simpan User Baru
    hashed_password = get_password_hash(password)
    
    new_user = models.User(
        full_name=full_name,
        username=username, 
        email=email, 
        hashed_password=hashed_password, 
        role="USER" 
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(dependencies.get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    
    # Validasi User
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Username atau Password salah!"
        })

    # --- DEBUGGING: LIHAT INI DI TERMINAL ---
    print(f"DEBUG: User '{user.username}' memiliki role: '{user.role}'")
    # ----------------------------------------

    # Bersihkan Role (Hapus spasi & paksa huruf besar)
    user_role = user.role.strip().upper() if user.role else "USER"

    # Buat Token (Gunakan role yang sudah dibersihkan)
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user_role},
        expires_delta=access_token_expires
    )

    # --- LOGIKA REDIRECT (YANG SUDAH DIPERBAIKI) ---
    if user_role == "ADMIN":
        redirect_url = "/admin/dashboard"
    else:
        redirect_url = "/classify"

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True
    )
    return response