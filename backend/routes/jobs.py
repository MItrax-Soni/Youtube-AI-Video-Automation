"""
jobs.py — GET /api/jobs/{job_id}

Poll the status of a video generation job.
Enforces user isolation — a user can only see their own jobs.
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.services.auth_service import get_current_user
from scripts.database import get_job

router = APIRouter()


@router.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str, user_id: str = Depends(get_current_user)):
    """
    Poll the status of a generation job.

    User isolation: verifies job.user_id == authenticated user.
    Returns the full job document with status, progress, current_step, video_url.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # User isolation — a user can only see their own jobs
    if job.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
