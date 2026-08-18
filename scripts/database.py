"""
database.py - MongoDB Cloud Integration

Handles all database operations for generations, ideas, and users.
Falls back gracefully if MONGODB_URI is not set.
"""
import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

# Load from config or env
from scripts.config import PROJECT_ROOT, get_env_or_secret
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

_client = None
_db = None
_use_mongo = False

def init_db():
    global _client, _db, _use_mongo
    uri = get_env_or_secret("MONGODB_URI")
    if not uri or uri == "your_mongodb_uri_here" or uri.startswith("your_"):
        print("[Database] MONGODB_URI not set. Falling back to local JSON storage.")
        _use_mongo = False
        return False

    try:
        _client = MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        # The ismaster command is cheap and does not require auth
        _client.admin.command('ismaster')
        _db = _client.get_database("maix_yt")
        _use_mongo = True
        print("[Database] Successfully connected to MongoDB Atlas.")
        return True
    except Exception as e:
        print(f"[Database] MongoDB connection failed: {e}. Falling back to local JSON storage.")
        _use_mongo = False
        return False

# Initialize on import
init_db()

def is_mongo_enabled() -> bool:
    return _use_mongo

def save_generation(metadata: dict) -> bool:
    """Save a video generation record to MongoDB."""
    if not _use_mongo or _db is None:
        return False
    try:
        _db.generations.update_one(
            {"project_dir": metadata.get("project_dir")},
            {"$set": metadata},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"[Database] Error saving generation: {e}")
        return False

def get_all_generations(user_id: str = None) -> list[dict]:
    """Retrieve all generation records, optionally filtered by user_id."""
    if not _use_mongo or _db is None:
        return []
    try:
        query = {"user_id": user_id} if user_id else {}
        cursor = _db.generations.find(query, {"_id": 0}).sort("timestamp", -1)
        return list(cursor)
    except Exception as e:
        print(f"[Database] Error fetching generations: {e}")
        return []

def delete_generation(project_dir: str) -> bool:
    """Delete a generation record."""
    if not _use_mongo or _db is None:
        return False
    try:
        _db.generations.delete_one({"project_dir": project_dir})
        return True
    except Exception as e:
        print(f"[Database] Error deleting generation: {e}")
        return False

def save_idea(idea: dict) -> bool:
    """Save an idea to MongoDB."""
    if not _use_mongo or _db is None:
        return False
    try:
        _db.ideas.insert_one(idea)
        return True
    except Exception as e:
        print(f"[Database] Error saving idea: {e}")
        return False

def get_all_ideas(user_id: str = None) -> list[dict]:
    """Retrieve all ideas."""
    if not _use_mongo or _db is None:
        return []
    try:
        query = {"user_id": user_id} if user_id else {}
        cursor = _db.ideas.find(query, {"_id": 0}).sort("created_at", -1)
        return list(cursor)
    except Exception as e:
        print(f"[Database] Error fetching ideas: {e}")
        return []


# ---------------------------------------------------------------------------
# Video Jobs Collection — Async Job Pattern
# ---------------------------------------------------------------------------

def create_job(job_data: dict) -> str:
    """Create a new video generation job. Returns the job_id."""
    if not _use_mongo or _db is None:
        raise RuntimeError("MongoDB not available")
    try:
        _db.video_jobs.insert_one(job_data)
        return job_data["_id"]
    except Exception as e:
        raise RuntimeError(f"Failed to create job: {e}")


def get_job(job_id: str) -> dict | None:
    """Retrieve a single job by ID."""
    if not _use_mongo or _db is None:
        return None
    try:
        return _db.video_jobs.find_one({"_id": job_id})
    except Exception as e:
        print(f"[Database] Error fetching job {job_id}: {e}")
        return None


def update_job(job_id: str, updates: dict) -> bool:
    """Update fields on a job document."""
    if not _use_mongo or _db is None:
        return False
    try:
        from datetime import datetime, timezone
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        _db.video_jobs.update_one({"_id": job_id}, {"$set": updates})
        return True
    except Exception as e:
        print(f"[Database] Error updating job {job_id}: {e}")
        return False


def get_jobs_by_user(user_id: str, limit: int = 50) -> list[dict]:
    """Retrieve all jobs for a specific user, newest first."""
    if not _use_mongo or _db is None:
        return []
    try:
        cursor = _db.video_jobs.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)
        return list(cursor)
    except Exception as e:
        print(f"[Database] Error fetching jobs for user {user_id}: {e}")
        return []


def get_next_queued_job() -> dict | None:
    """Atomically pick the oldest queued job and set its status to processing."""
    if not _use_mongo or _db is None:
        return None
    try:
        from datetime import datetime, timezone
        return _db.video_jobs.find_one_and_update(
            {"status": "queued"},
            {"$set": {
                "status": "generating_script",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
            sort=[("created_at", 1)],
            return_document=True,
        )
    except Exception as e:
        print(f"[Database] Error picking queued job: {e}")
        return None


# ---------------------------------------------------------------------------
# User Settings Collection — Per-User Settings (not settings.json)
# ---------------------------------------------------------------------------

DEFAULT_USER_SETTINGS = {
    "default_duration": 60,
    "default_tone": "educational",
    "default_voice": "Edge-TTS (Neural)",
    "default_voice_gender": "female",
    "default_style": "Documentary",
    "enable_transition_effects": True,
    "enable_motion_effects": True,
    "enable_text_highlights": True,
    "enable_subtitles": False,
    "enable_bg_music": True,
    "bg_music_volume": 0.10,
}


def get_user_settings(user_id: str) -> dict:
    """Retrieve settings for a specific user. Returns defaults if none saved."""
    if not _use_mongo or _db is None:
        return DEFAULT_USER_SETTINGS.copy()
    try:
        doc = _db.user_settings.find_one({"user_id": user_id}, {"_id": 0})
        if doc:
            merged = DEFAULT_USER_SETTINGS.copy()
            merged.update(doc)
            return merged
        return DEFAULT_USER_SETTINGS.copy()
    except Exception as e:
        print(f"[Database] Error fetching settings for {user_id}: {e}")
        return DEFAULT_USER_SETTINGS.copy()


def save_user_settings(user_id: str, settings: dict) -> bool:
    """Save or update user settings."""
    if not _use_mongo or _db is None:
        return False
    try:
        settings["user_id"] = user_id
        _db.user_settings.update_one(
            {"user_id": user_id},
            {"$set": settings},
            upsert=True,
        )
        return True
    except Exception as e:
        print(f"[Database] Error saving settings for {user_id}: {e}")
        return False


# ---------------------------------------------------------------------------
# OAuth Tokens Collection — Per-User OAuth Tokens (Google Drive, etc.)
# ---------------------------------------------------------------------------

def save_user_oauth_tokens(user_id: str, provider: str, token_data: dict) -> bool:
    """
    Save OAuth tokens for a user and provider.

    Args:
        user_id: Clerk user ID.
        provider: e.g. "google_drive".
        token_data: Dict with access_token, refresh_token, etc.
    """
    if not _use_mongo or _db is None:
        return False
    try:
        from datetime import datetime, timezone
        doc = {
            "user_id": user_id,
            "provider": provider,
            "tokens": token_data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        _db.oauth_tokens.update_one(
            {"user_id": user_id, "provider": provider},
            {"$set": doc},
            upsert=True,
        )
        return True
    except Exception as e:
        print(f"[Database] Error saving OAuth tokens for {user_id}/{provider}: {e}")
        return False


def get_user_oauth_tokens(user_id: str, provider: str) -> dict | None:
    """
    Retrieve stored OAuth tokens for a user and provider.

    Returns the token_data dict, or None if not found.
    """
    if not _use_mongo or _db is None:
        return None
    try:
        doc = _db.oauth_tokens.find_one(
            {"user_id": user_id, "provider": provider}
        )
        if doc:
            return doc.get("tokens")
        return None
    except Exception as e:
        print(f"[Database] Error fetching OAuth tokens for {user_id}/{provider}: {e}")
        return None


def delete_user_oauth_tokens(user_id: str, provider: str) -> bool:
    """Remove OAuth tokens for a user and provider."""
    if not _use_mongo or _db is None:
        return False
    try:
        _db.oauth_tokens.delete_one({"user_id": user_id, "provider": provider})
        return True
    except Exception as e:
        print(f"[Database] Error deleting OAuth tokens for {user_id}/{provider}: {e}")
        return False
