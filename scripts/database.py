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
from scripts.config import PROJECT_ROOT
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

_client = None
_db = None
_use_mongo = False

def init_db():
    global _client, _db, _use_mongo
    uri = os.getenv("MONGODB_URI")
    if not uri or uri == "your_mongodb_uri_here":
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
