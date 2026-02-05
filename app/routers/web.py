from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse 
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import dependencies, models # <--- PENTING: Import ini agar bisa akses DB

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# --- Route Beranda ---
@router.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request):
    return templates.TemplateResponse("user/home.html", {"request": request})

# --- Route Tentang (About) ---
@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("user/about.html", {"request": request})

# --- [DIPERBAIKI] Route Artikel ---
@router.get("/articles", response_class=HTMLResponse)
async def articles(request: Request, db: Session = Depends(dependencies.get_db)):
    # 1. Ambil data dari Database
    all_articles = db.query(models.Article).order_by(models.Article.created_at.desc()).all()
    
    # 2. Siapkan wadah pengelompokan (sesuai ID modal di HTML)
    grouped_articles = {
        "general": [],
        "styles": [],
        "technique": []
    }
    
    # 3. Masukkan artikel ke kategori yang tepat
    for art in all_articles:
        # Pastikan kategori di database cocok dengan key dictionary (lowercase aman)
        cat_key = art.category.lower() if art.category else "general"
        
        if cat_key in grouped_articles:
            grouped_articles[cat_key].append(art)
        elif art.category == "general": # Jaga-jaga penamaan manual
             grouped_articles["general"].append(art)
    
    # 4. Kirim data 'articles' ke template HTML
    return templates.TemplateResponse("user/article.html", {
        "request": request, 
        "articles": grouped_articles 
    })