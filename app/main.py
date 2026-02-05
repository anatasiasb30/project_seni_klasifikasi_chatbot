from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import web, classification, chatbot, admin, auth
from app.database import engine, Base
from app.services.clip_service import clip_service

# Create Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NatsArt AI")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Mount storage for uploaded images
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Include routers
app.include_router(web.router)
app.include_router(auth.router)
app.include_router(classification.router)
app.include_router(chatbot.router)
app.include_router(admin.router)

# --- TAMBAHAN BARU DI BAWAH SINI ---
@app.on_event("startup")
async def startup_event():
    # Load model ke RAM saat aplikasi baru nyala
    print("System Startup: Loading AI Models...")
    clip_service.load_model()

@app.get("/health")
async def health_check():
    return {"status": "ok"}
