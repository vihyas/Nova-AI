import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "nova_assistant.db"

# Ensure data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    app_name: str = "NOVA AI — Intelligent Personal Assistant"
    version: str = "3.0.0"
    debug: bool = True
    default_provider: str = "gemini"  # "gemini", "openai", "offline"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    system_language: str = "en"  # "en", "ta"
    voice_speed: float = 1.0
    voice_pitch: float = 1.0

settings = Settings()

