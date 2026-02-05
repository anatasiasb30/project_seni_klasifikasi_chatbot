import os

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

# --- TAMBAHAN WAJIB (AGAR CLIP_SERVICE TIDAK ERROR) ---
# Pastikan nama file .pth di sini SAMA PERSIS dengan file yang kamu copy
MODEL_PATH = os.path.join("app", "weights", "best_clip_art_model.pth")