"""
history.py — GET /api/history

Retrieve the authenticated user's past video generations.
Queries MongoDB video_jobs collection, NOT the filesystem.
"""

from fastapi import APIRouter, Depends

from backend.services.auth_service import get_current_user
from scripts.database import get_jobs_by_user

router = APIRouter()


@router.get("/api/history")
async def get_history(user_id: str = Depends(get_current_user)):
    """
    List all past video generations for the authenticated user.

    Queries MongoDB video_jobs WHERE user_id = authenticated user.
    NOT os.listdir("output/").
    """
    jobs = get_jobs_by_user(user_id, limit=50)

    generations = []
    for job in jobs:
        generations.append({
            "job_id": job.get("_id", ""),
            "title": job.get("video_title") or job.get("topic", "Untitled"),
            "topic": job.get("topic", "Unknown"),
            "status": job.get("status", "unknown"),
            "created_at": job.get("created_at", ""),
            "duration": job.get("params", {}).get("duration", 0),
            "scene_count": job.get("metadata", {}).get("scene_count", 0),
            "video_url": job.get("video_url"),
            "thumbnail_url": job.get("thumbnail_url"),
            "timing": job.get("timing", {}),
            "params": job.get("params", {}),
            "metadata": job.get("metadata", {}),
            "errors": [job["error"]] if job.get("error") else [],
            "failed_step": job.get("failed_step"),
        })

    return {"generations": generations}
