from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app import database, models, config

# Setup Database Session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FUNGSI BARU: Ambil token dari Cookie
def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    # Hapus prefix "Bearer " jika ada
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
    return token

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = get_token_from_cookie(request)
    
    # Jika tidak ada token (belum login), kembalikan None (jangan error dulu)
    if not token:
        return None 

    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None

    user = db.query(models.User).filter(models.User.username == username).first()
    return user