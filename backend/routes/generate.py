"""
generate.py — POST /api/generate

Creates a new video generation job in MongoDB and returns the job_id.
The actual pipeline work is done by the worker process.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.services.auth_service import get_current_user
from scripts.database import create_job

router = APIRouter()


class GenerateRequest(BaseModel):
    topic: str
    tone: str = "educational"
    duration: int = 60
    voice_gender: str = "female"
    voice_engine: str = "Edge-TTS (Neural)"
    style: str = "Documentary"
    language: str = "english"
    aspect_ratio: str = "16:9"


@router.post("/api/generate")
async def start_generation(req: GenerateRequest, user_id: str = Depends(get_current_user)):
    """
    Start a video generation pipeline.

    Creates a job document in MongoDB with status 'queued'.
    The worker process picks it up and runs the pipeline.
    Returns the job_id immediately — frontend polls GET /api/jobs/{job_id}.
    """
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    job_data = {
        "_id": job_id,
        "user_id": user_id,
        "topic": req.topic,
        "status": "queued",
        "progress": 0,
        "current_step": "Queued",
        "params": req.model_dump(),
        "created_at": now,
        "updated_at": now,
        "video_url": None,
        "thumbnail_url": None,
        "video_title": None,
        "metadata": {},
        "error": None,
        "failed_step": None,
        "timing": {},
    }

    create_job(job_data)

    return {"job_id": job_id, "status": "queued"}
