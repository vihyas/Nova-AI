from datetime import datetime
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.schemas import SettingsUpdate, SettingsResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])

def get_setting_from_db(key: str, default: str = "") -> str:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

def save_setting_to_db(key: str, value: str):
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """, (key, value, now))

@router.get("", response_model=SettingsResponse)
def get_current_settings():
    gemini_key = get_setting_from_db("gemini_api_key", settings.gemini_api_key)
    openai_key = get_setting_from_db("openai_api_key", settings.openai_api_key)
    
    return SettingsResponse(
        app_name=settings.app_name,
        version=settings.version,
        default_provider=get_setting_from_db("default_provider", settings.default_provider),
        gemini_api_key_configured=bool(gemini_key),
        gemini_model=get_setting_from_db("gemini_model", settings.gemini_model),
        openai_api_key_configured=bool(openai_key),
        openai_model=get_setting_from_db("openai_model", settings.openai_model),
        temperature=float(get_setting_from_db("temperature", str(settings.temperature))),
        system_language=get_setting_from_db("system_language", settings.system_language),
        voice_speed=float(get_setting_from_db("voice_speed", str(settings.voice_speed))),
        voice_pitch=float(get_setting_from_db("voice_pitch", str(settings.voice_pitch)))
    )

@router.post("", response_model=SettingsResponse)
def update_settings(updates: SettingsUpdate):
    if updates.default_provider is not None:
        save_setting_to_db("default_provider", updates.default_provider)
    if updates.gemini_api_key is not None:
        save_setting_to_db("gemini_api_key", updates.gemini_api_key)
    if updates.gemini_model is not None:
        save_setting_to_db("gemini_model", updates.gemini_model)
    if updates.openai_api_key is not None:
        save_setting_to_db("openai_api_key", updates.openai_api_key)
    if updates.openai_model is not None:
        save_setting_to_db("openai_model", updates.openai_model)
    if updates.temperature is not None:
        save_setting_to_db("temperature", str(updates.temperature))
    if updates.system_language is not None:
        save_setting_to_db("system_language", updates.system_language)
    if updates.voice_speed is not None:
        save_setting_to_db("voice_speed", str(updates.voice_speed))
    if updates.voice_pitch is not None:
        save_setting_to_db("voice_pitch", str(updates.voice_pitch))

    return get_current_settings()

