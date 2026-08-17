"""
health.py — GET /api/health, GET /api/api-check

Health check and API connectivity status.
Does NOT expose API keys — only connected/disconnected status.
"""

from fastapi import APIRouter, Depends

from backend.services.auth_service import get_current_user

router = APIRouter()


@router.get("/api/health")
async def health_check():
    """Basic health check — no auth required."""
    return {"status": "ok", "service": "MAiX-YT Studio API", "version": "3.0.0"}


@router.get("/api/api-check")
async def check_apis(user_id: str = Depends(get_current_user)):
    """
    Check connectivity of all configured APIs.
    Returns only status — NEVER exposes API keys.
    """
    try:
        from scripts.api_status import check_all_apis
        results = check_all_apis()
        return results
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/presets")
async def get_presets(user_id: str = Depends(get_current_user)):
    """Return available duration presets and style options."""
    from scripts.config import DURATION_PRESETS, STYLE_EFFECT_PROFILES

    return {
        "duration_presets": DURATION_PRESETS,
        "styles": list(STYLE_EFFECT_PROFILES.keys()),
        "tones": ["educational", "entertaining", "motivational", "dramatic", "humorous"],
        "voice_engines": ["Edge-TTS (Neural)", "ElevenLabs (Premium)", "gTTS (Standard)"],
        "languages": ["english", "hindi", "gujarati"],
    }
