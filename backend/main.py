"""
main.py — FastAPI Backend for MAiX-YT Studio (v2)

Modular route-based architecture. All state in MongoDB, not in-memory.
Designed to run on Railway alongside the Vercel-hosted Next.js frontend.

Run with: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path so scripts/ is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="MAiX-YT Studio API",
    description="Backend API for AI YouTube Video Automation Platform",
    version="3.0.0",
)

# ---------------------------------------------------------------------------
# CORS — explicit allowed origins, NOT ["*"]
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add production frontend URL from env
frontend_url = os.getenv("FRONTEND_URL", "")
if frontend_url:
    ALLOWED_ORIGINS.append(frontend_url)

# Also allow Vercel preview URLs
vercel_url = os.getenv("VERCEL_URL")
if vercel_url:
    ALLOWED_ORIGINS.append(f"https://{vercel_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register Routes
# ---------------------------------------------------------------------------
from backend.routes.generate import router as generate_router
from backend.routes.jobs import router as jobs_router
from backend.routes.history import router as history_router
from backend.routes.settings import router as settings_router
from backend.routes.trends import router as trends_router
from backend.routes.health import router as health_router
from fastapi.staticfiles import StaticFiles
from scripts.config import OUTPUT_DIR

app.mount("/api/videos", StaticFiles(directory=str(OUTPUT_DIR)), name="videos")

app.include_router(generate_router)
app.include_router(jobs_router)
app.include_router(history_router)
app.include_router(settings_router)
app.include_router(trends_router)
app.include_router(health_router)


# ---------------------------------------------------------------------------
# Root endpoint (alias for health check)
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    """Health check at root."""
    return {"status": "ok", "service": "MAiX-YT Studio API", "version": "3.0.0"}
