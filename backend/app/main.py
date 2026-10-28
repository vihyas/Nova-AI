import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings, BASE_DIR
from backend.app.database import init_db
from backend.app.routers import (
    chat, tasks, reminders, documents, memory, analytics, settings as settings_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    init_db()
    yield
    # Shutdown actions

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Multimodal AI Assistant & Autonomous Productivity Platform",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(reminders.router)
app.include_router(documents.router)
app.include_router(memory.router)
app.include_router(analytics.router)
app.include_router(settings_router.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "mode": "premium_agent_platform"
    }

# Mount static frontend
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "NOVA AI backend is running. Frontend index.html not yet initialized."}

