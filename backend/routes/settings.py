"""
settings.py — GET/PUT /api/settings

Per-user settings stored in MongoDB user_settings collection.
NOT settings.json.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.services.auth_service import get_current_user
from scripts.database import get_user_settings, save_user_settings

router = APIRouter()


class SettingsUpdate(BaseModel):
    settings: dict


@router.get("/api/settings")
async def get_settings(user_id: str = Depends(get_current_user)):
    """Get the authenticated user's settings from MongoDB."""
    settings = get_user_settings(user_id)
    return {"settings": settings}


@router.put("/api/settings")
async def update_settings(req: SettingsUpdate, user_id: str = Depends(get_current_user)):
    """Update the authenticated user's settings in MongoDB."""
    save_user_settings(user_id, req.settings)
    return {"status": "ok", "settings": req.settings}
