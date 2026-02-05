from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional # <--- Tambah ini
from app.services.openai_service import openai_service
from app import models, dependencies, config
from jose import jwt

router = APIRouter(tags=["Chatbot"])

class ChatRequest(BaseModel):
    message: str
    art_style: str
    image_filename: Optional[str] = None 
    history_id: Optional[int] = None # <--- Pakai Optional agar aman jika null

# Helper: Ambil user dari token (Sama seperti sebelumnya)
def get_current_user_from_token(request: Request, db: Session):
    token = request.cookies.get("access_token")
    if not token: return None
    try:
        scheme, _, param = token.partition(" ")
        payload = jwt.decode(param, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username = payload.get("sub")
        return db.query(models.User).filter(models.User.username == username).first()
    except:
        return None

# --- 1. AMBIL HISTORY ---
@router.get("/chat/history")
async def get_chat_history(request: Request, db: Session = Depends(dependencies.get_db)):
    user = get_current_user_from_token(request, db)
    if not user:
        return [] # Tamu selalu return kosong (tapi frontend akan handle gambar awal lewat initial_msg)
    
    chats = db.query(models.ChatLog).filter(models.ChatLog.user_id == user.id).order_by(models.ChatLog.created_at.asc()).all()
    
    cleaned_history = []
    for chat in chats:
        clean_msg = chat.message.split(" [SYSTEM_LOG:")[0]
        cleaned_history.append({
            "id": chat.id,
            "user_id": chat.user_id,
            "message": clean_msg,
            "history_id": chat.history_id,
            "created_at": chat.created_at
        })
    return cleaned_history

# --- 2. HAPUS HISTORY (REVISI: Izinkan Tamu) ---
@router.delete("/chat/history")
async def delete_chat_history(request: Request, db: Session = Depends(dependencies.get_db)):
    user = get_current_user_from_token(request, db)
    
    # [REVISI] Jika Tamu, langsung return success (Frontend akan bersihkan layar)
    # Jangan error 401
    if not user:
        return {"status": "success", "msg": "Guest chat cleared"}
    
    # Jika User Login, hapus dari DB
    db.query(models.ChatLog).filter(models.ChatLog.user_id == user.id).delete()
    db.query(models.ClassificationHistory).filter(models.ClassificationHistory.user_id == user.id).delete()
    db.commit()
    
    return {"status": "success"}

# --- 3. KIRIM PESAN ---
@router.post("/chat")
async def chat_with_ai(request: Request, chat_req: ChatRequest, db: Session = Depends(dependencies.get_db)):
    if not chat_req.message:
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong")
    
    user = get_current_user_from_token(request, db)
    recent_history = []

    # 1. Simpan Pesan User & Siapkan Context (Hanya User Login)
    if user:
        try:
            message_to_save = chat_req.message
            if chat_req.image_filename and chat_req.art_style and chat_req.art_style not in ["Unknown", "Unknown Image"]:
                message_to_save += f" [SYSTEM_LOG: User mengunggah gambar beraliran {chat_req.art_style}]"

            new_chat = models.ChatLog(
                user_id=user.id,
                message=message_to_save,
                history_id=chat_req.history_id 
            )
            db.add(new_chat)
            db.commit()

            # Ambil Context
            recent_history_objs = db.query(models.ChatLog)\
                .filter(models.ChatLog.user_id == user.id)\
                .order_by(models.ChatLog.created_at.desc())\
                .limit(20).all()
            
            recent_history = recent_history_objs[::-1] # Balik urutan
            
            # Hapus pesan terakhir (current) agar tidak duplikat di prompt
            if recent_history and recent_history[-1].message == message_to_save:
                recent_history.pop()

        except Exception as e:
            print(f"Error saving chat: {e}")
    
    # 2. Kirim ke AI (Tamu & User sama-sama diproses)
    if chat_req.art_style in ["Unknown Image", "Unknown"]:
        reply_text = "Maaf, gambar ini tidak terdeteksi sebagai lukisan yang valid."
    else:
        # Service OpenAI harus bisa handle chat_history kosong (list [])
        reply_text = openai_service.get_art_explanation(
            chat_req.message, 
            chat_req.art_style, 
            chat_req.image_filename,
            chat_history=recent_history
        )
    
    # 3. Simpan Balasan AI (Hanya User Login)
    if user:
        try:
            bot_chat = models.ChatLog(
                user_id=user.id,
                message=f"[BOT]{reply_text}", 
                history_id=chat_req.history_id
            )
            db.add(bot_chat)
            db.commit()
        except:
            pass
    
    return {"reply": reply_text}