from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String) 
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="USER")

    # Relasi Bersih
    classification_logs = relationship("ClassificationHistory", back_populates="user")
    chat_logs = relationship("ChatLog", back_populates="user")

# Tabel Riwayat Klasifikasi
class ClassificationHistory(Base):
    __tablename__ = "classification_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    image_filename = Column(String)
    label = Column(String)
    confidence = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="classification_logs")
    
    # Relasi: Satu gambar punya banyak chat
    chats = relationship("ChatLog", back_populates="history")

# Tabel Log Chat
class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Hubungkan chat ke riwayat upload spesifik
    history_id = Column(Integer, ForeignKey("classification_history.id"), nullable=True)
    
    message = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="chat_logs")
    
    # Relasi balik ke history
    history = relationship("ClassificationHistory", back_populates="chats")

# --- TAMBAHAN BARU: Tabel Artikel ---
class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)  # 'general', 'styles', 'technique'
    type = Column(String)      # 'WEB' atau 'PDF'
    url = Column(String)       # Link eksternal atau path static
    created_at = Column(DateTime, default=datetime.now)