from fastapi import APIRouter, Request, Depends, status, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os 

# --- PERBAIKAN IMPORT (Agar dependencies.get_db jalan) ---
from app.models import User, Article, ClassificationHistory, ChatLog 
from app import dependencies, models, config

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="app/templates")

# Setup Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# --- FUNGSI BANTUAN TOKEN ---
def create_new_token_for_user(username: str, role: str):
    to_encode = {"sub": username, "role": role}
    expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

# --- HELPER: Cek Admin ---
def get_current_admin(request: Request, db: Session):
    token = request.cookies.get("access_token")
    if not token: return None
    try:
        scheme, _, param = token.partition(" ")
        payload = jwt.decode(param, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username = payload.get("sub")
        if not username: return None
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user or user.role != "ADMIN": 
            return None
        return user
    except:
        return None

# =========================================================
# 1. HALAMAN DASHBOARD (BERSIH & SIAP)
# =========================================================
@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(dependencies.get_db)):
    # 1. Cek Login Admin
    admin_user = get_current_admin(request, db)
    
    if not admin_user:
        token = request.cookies.get("access_token")
        if token:
            try:
                _, _, param = token.partition(" ")
                payload = jwt.decode(param, config.SECRET_KEY, algorithms=[config.ALGORITHM])
                if payload.get("role") == "USER":
                    return RedirectResponse(url="/classify", status_code=status.HTTP_302_FOUND)
            except:
                pass
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # 2. Ambil List User (Untuk Tabel Akun)
    users_list = db.query(models.User).all()

    # 3. [PENTING] Ambil List Artikel (Untuk Tabel Artikel Baru)
    articles_list = db.query(models.Article).order_by(models.Article.created_at.desc()).all()

    # 4. Hitung Statistik (Untuk Kartu di Atas)
    total_users = db.query(models.User).filter(models.User.role == "USER").count()
    # total_uploads = db.query(models.ClassificationHistory).count()
    total_articles = len(articles_list) # Hitung jumlah artikel

    stats = {
        "users": total_users,
        # "uploads": total_uploads,
        "chats": 0, # Chat tidak ditampilkan detailnya, tapi angkanya boleh 0
        "articles": total_articles # Kirim ke HTML
    }

    # 5. Render Template (Hanya kirim yang dibutuhkan HTML)
    return templates.TemplateResponse("admin/dashboard.html", {  # Tambahkan 'admin/'
        "request": request,
        "user": admin_user,
        "stats": stats,
        "users_list": users_list,
        "articles_list": articles_list, # <--- Wajib ada agar tabel artikel muncul!
        "is_admin_page": True 
    })

# =========================================================
# 2. CREATE USER
# =========================================================
@router.post("/create-user")
async def create_user(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(dependencies.get_db)
):
    if not get_current_admin(request, db):
        return JSONResponse(status_code=403, content={"status": "error", "message": "Not authorized"})

    if db.query(models.User).filter(models.User.email == email).first():
        return JSONResponse(content={"status": "exists", "message": "Email sudah terdaftar!"})

    if db.query(models.User).filter(models.User.username == username).first():
        return JSONResponse(content={"status": "exists", "message": "Username sudah dipakai!"})

    try:
        hashed_pwd = get_password_hash(password)
        new_user = models.User(
            full_name=full_name,
            username=username,
            email=email,
            hashed_password=hashed_pwd,
            role=role 
        )
        db.add(new_user)
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Akun berhasil dibuat!"})
    except Exception as e:
        db.rollback()
        return JSONResponse(content={"status": "error", "message": f"Error: {str(e)}"})

# =========================================================
# 3. EDIT USER
# =========================================================
@router.post("/edit-user")
async def edit_user(
    request: Request,
    user_id: int = Form(...),
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(dependencies.get_db)
):
    current_admin = get_current_admin(request, db)
    if not current_admin:
        return JSONResponse(status_code=403, content={"status": "error", "message": "Unauthorized"})

    user_to_edit = db.query(models.User).filter(models.User.id == user_id).first()
    
    if user_to_edit:
        try:
            user_to_edit.full_name = full_name
            user_to_edit.username = username
            user_to_edit.email = email
            user_to_edit.role = role
            db.commit()
            
            response = JSONResponse(content={"status": "success", "message": "Data berhasil diperbarui!"})

            # Jika admin edit diri sendiri, refresh token
            if current_admin.id == user_to_edit.id:
                new_token = create_new_token_for_user(user_to_edit.username, role)
                response.set_cookie(key="access_token", value=f"Bearer {new_token}", httponly=True)
            
            return response
        except Exception as e:
            db.rollback()
            return JSONResponse(content={"status": "error", "message": str(e)})

    return JSONResponse(status_code=404, content={"status": "error", "message": "User tidak ditemukan"})

# =========================================================
# 4. DELETE USER
# =========================================================
@router.post("/delete-user")
async def delete_user(
    request: Request,
    user_id: int = Form(...),
    db: Session = Depends(dependencies.get_db)
):
    if not get_current_admin(request, db):
        return {"status": "error", "message": "Unauthorized"}

    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if user_to_delete:
        try:
            # Hapus data terkait dulu (Cascade manual)
            db.query(models.ClassificationHistory).filter(models.ClassificationHistory.user_id == user_id).delete()
            db.query(models.ChatLog).filter(models.ChatLog.user_id == user_id).delete()
            
            db.delete(user_to_delete)
            db.commit()
            return {"status": "success", "message": "User berhasil dihapus"}
        except Exception as e:
            db.rollback()
            return {"status": "error", "message": str(e)}
            
    return {"status": "error", "message": "User tidak ditemukan"}

# =========================================================
# 5. RESET PASSWORD
# =========================================================
@router.post("/reset-password")
async def reset_password(
    request: Request,
    user_id: int = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(dependencies.get_db)
):
    if not get_current_admin(request, db):
        return JSONResponse(status_code=403, content={"status": "error", "message": "Unauthorized"})

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        try:
            if pwd_context.verify(new_password, user.hashed_password):
                return JSONResponse(content={"status": "error", "message": "Password baru tidak boleh sama!"})

            user.hashed_password = get_password_hash(new_password)
            db.commit()
            return JSONResponse(content={"status": "success", "message": "Password berhasil direset!"})
        except Exception as e:
            db.rollback()
            return JSONResponse(content={"status": "error", "message": str(e)})
            
    return JSONResponse(status_code=404, content={"status": "error", "message": "User tidak ditemukan"})

# =========================================================
# 6. ARTIKEL: SAVE (ADD/EDIT)
# =========================================================
@router.post("/save-article")
async def save_article(
    article_id: str = Form(None), 
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    type: str = Form(...),
    url: str = Form(...),
    db: Session = Depends(dependencies.get_db) # <-- Panggil via dependencies
):
    try:
        if article_id and article_id.strip():
            # Mode EDIT
            art = db.query(models.Article).filter(models.Article.id == int(article_id)).first()
            if not art:
                return JSONResponse({"status": "error", "message": "Artikel tidak ditemukan"})
            
            art.title = title
            art.description = description
            art.category = category
            art.type = type
            art.url = url
            db.commit()
            return JSONResponse({"status": "success", "message": "Artikel berhasil diperbarui!"})
        
        else:
            # Mode ADD NEW
            new_art = models.Article(
                title=title,
                description=description,
                category=category,
                type=type,
                url=url
            )
            db.add(new_art)
            db.commit()
            return JSONResponse({"status": "success", "message": "Artikel berhasil ditambahkan!"})
            
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Error: {str(e)}"})

# =========================================================
# 7. ARTIKEL: DELETE
# =========================================================
@router.post("/delete-article")
async def delete_article(
    article_id: int = Form(...), 
    db: Session = Depends(dependencies.get_db) # <-- Panggil via dependencies
):
    try:
        art = db.query(models.Article).filter(models.Article.id == article_id).first()
        if not art:
            return JSONResponse({"status": "error", "message": "Artikel tidak ditemukan"})
        
        db.delete(art)
        db.commit()
        return JSONResponse({"status": "success", "message": "Artikel berhasil dihapus."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})