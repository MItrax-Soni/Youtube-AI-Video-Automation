"""
trends.py — POST /api/trends

Get trending video topic ideas for a niche using Gemini AI.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.services.auth_service import get_current_user
from scripts.trend import discover_trends

router = APIRouter()


class TrendRequest(BaseModel):
    niche: str


@router.post("/api/trends")
async def get_trends(req: TrendRequest, user_id: str = Depends(get_current_user)):
    """Get trending video topic ideas for a niche."""
    try:
        ideas = discover_trends(req.niche)
        return {"ideas": ideas[:10]}
    except Exception as e:
        return {"ideas": [], "error": str(e)}
