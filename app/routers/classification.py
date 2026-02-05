from fastapi import APIRouter, UploadFile, File, Request, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.services.clip_service import clip_service
from app import config, models, dependencies
import shutil
import os
import urllib.parse 

router = APIRouter(tags=["Classification"])
templates = Jinja2Templates(directory="app/templates")

# --- HELPER ---
def get_username_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token: return None
    try:
        scheme, _, param = token.partition(" ")
        payload = jwt.decode(param, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload.get("sub")
    except JWTError: return None

# --- ROUTE GET: Tampilkan Halaman ---
@router.get("/classify")
async def classify_page(request: Request, db: Session = Depends(dependencies.get_db)):
    username_token = get_username_from_cookie(request)
    user_data = None
    if username_token:
        user_data = db.query(models.User).filter(models.User.username == username_token).first()

    # Variabel Default (KOSONG / TERKUNCI)
    result = None
    image_path = None
    current_history_id = None
    initial_chat_message = None
    error_msg = request.query_params.get("error")

    # =================================================================
    # LOGIKA BARU: HANYA LOAD DATA JIKA ADA PARAMETER DI URL
    # =================================================================
    
    # A. JIKA USER LOGIN: Cek apakah ada '?history_id=...' di URL?
    req_history_id = request.query_params.get("history_id")
    
    if user_data and req_history_id:
        # Ambil spesifik history ID yang diminta (hasil upload barusan)
        history_item = db.query(models.ClassificationHistory)\
            .filter(models.ClassificationHistory.id == req_history_id, 
                    models.ClassificationHistory.user_id == user_data.id)\
            .first()
        
        if history_item:
            result = {"label": history_item.label, "confidence": history_item.confidence}
            image_path = f"/storage/uploads/{history_item.image_filename}"
            current_history_id = history_item.id
            
            # [REVISI DISINI - FIX DOUBLE GAMBAR]
            # Untuk User Login, JANGAN isi initial_chat_message.
            # Biarkan JS mengambilnya dari Database via loadChatHistory().
            initial_chat_message = None 

    # B. JIKA TAMU: Cek parameter URL '?img=...'
    elif not user_data and request.query_params.get("img"):
        img_param = request.query_params.get("img")
        lbl_param = request.query_params.get("lbl")
        cnf_param = request.query_params.get("cnf")
        
        if img_param and lbl_param and cnf_param:
            result = {"label": lbl_param, "confidence": cnf_param}
            image_path = f"/storage/uploads/{img_param}"
            # Tamu TIDAK punya DB, jadi WAJIB pakai ini agar muncul
            initial_chat_message = f"[BOT][IMG_CARD]{img_param}|{lbl_param}|{cnf_param}"

    # Render Template
    return templates.TemplateResponse("user/classify.html", {
        "request": request,
        "user": user_data,
        "is_classify_page": True,
        "result": result,
        "image_path": image_path,
        "current_history_id": current_history_id,
        "initial_chat_message": initial_chat_message,
        "error": error_msg
    })

# --- Handle Refresh ---
@router.get("/upload")
async def redirect_upload_get():
    return RedirectResponse(url="/classify", status_code=status.HTTP_302_FOUND)

# --- ROUTE POST: Upload Gambar ---
@router.post("/upload")
async def upload_image(request: Request, file: UploadFile = File(...), db: Session = Depends(dependencies.get_db)):
    username_token = get_username_from_cookie(request)
    user_data = None
    if username_token:
        user_data = db.query(models.User).filter(models.User.username == username_token).first()

    if not file.filename:
        return RedirectResponse(url="/classify", status_code=status.HTTP_303_SEE_OTHER)

    safe_filename = file.filename.replace(" ", "_")
    upload_dir = "storage/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        result = clip_service.predict_image(file_path)
        
        if "Unknown" in result['label']:
            if os.path.exists(file_path):
                os.remove(file_path)

            # Kode kamu saat ini (Sudah Oke):
            error_msg = "Gambar+tidak+terdeteksi+sebagai+lukisan+Impressionism,+Expressionism,+atau+Surrealism"
            return RedirectResponse(url=f"/classify?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)

        # --- JIKA USER LOGIN ---
        if user_data:
            new_history_id = None
            
            # Siapkan string konten kartu gambar
            card_content = f"[IMG_CARD]{safe_filename}|{result['label']}|{result['confidence']}"
            
            try:
                # Cek existing history (untuk ambil ID-nya)
                existing = db.query(models.ClassificationHistory).filter(
                    models.ClassificationHistory.user_id == user_data.id,
                    models.ClassificationHistory.image_filename == safe_filename
                ).first()

                if existing:
                    new_history_id = existing.id
                    # TETAP SIMPAN CHAT LOG BARU (Agar konteks chatbot update)
                    db.add(models.ChatLog(
                        user_id=user_data.id,
                        message=f"[BOT]{card_content}", 
                        history_id=new_history_id
                    ))
                    db.commit()
                else:
                    # Buat History Baru
                    new_history = models.ClassificationHistory(
                        user_id=user_data.id,
                        image_filename=safe_filename,
                        label=result['label'],
                        confidence=result['confidence']
                    )
                    db.add(new_history)
                    db.commit()
                    db.refresh(new_history)
                    new_history_id = new_history.id
                    
                    # Simpan Chat Log Baru
                    db.add(models.ChatLog(
                        user_id=user_data.id,
                        message=f"[BOT]{card_content}", 
                        history_id=new_history_id
                    ))
                    db.commit()
            except Exception as e:
                print(f"Error saving to DB: {e}")
            
            # Redirect
            return RedirectResponse(url=f"/classify?history_id={new_history_id}", status_code=status.HTTP_303_SEE_OTHER)

        # --- JIKA TAMU ---
        encoded_lbl = urllib.parse.quote(result['label'])
        encoded_cnf = urllib.parse.quote(result['confidence'])
        redirect_url = f"/classify?img={safe_filename}&lbl={encoded_lbl}&cnf={encoded_cnf}"
        
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        
    except Exception as e:
        print(f"Error: {e}")
        return RedirectResponse(url="/classify?error=Server+Error", status_code=status.HTTP_303_SEE_OTHER)