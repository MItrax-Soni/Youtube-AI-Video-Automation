"""
config.py — Centralized Configuration

Loads environment variables from .env and provides
path constants and API key accessors used by all scripts.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from the project root (one level up from scripts/)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Directory Paths
# ---------------------------------------------------------------------------
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure directories exist
ASSETS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------

def get_gemini_api_keys() -> list[str]:
    """
    Return all configured Gemini API keys.

    Reads GEMINI_API_KEY_1, GEMINI_API_KEY_2 (and optionally more) from
    the environment. Falls back to the legacy GEMINI_API_KEY if neither
    numbered key is set. At least one valid key must be present.
    """
    keys = []
    # Collect numbered keys (1, 2, … up to 10)
    for i in range(1, 11):
        k = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
        if k and k != "your_gemini_api_key_here":
            keys.append(k)

    # Legacy fallback
    if not keys:
        legacy = os.getenv("GEMINI_API_KEY", "").strip()
        if legacy and legacy != "your_gemini_api_key_here":
            keys.append(legacy)

    if not keys:
        raise ValueError(
            "No Gemini API key found. "
            "Set GEMINI_API_KEY_1 (and optionally GEMINI_API_KEY_2) in .env."
        )
    return keys


def get_gemini_api_key() -> str:
    """Return the first configured Gemini API key (backward-compatible)."""
    return get_gemini_api_keys()[0]


def get_pexels_api_key() -> str:
    """Return the Pexels API key from environment variables."""
    key = os.getenv("PEXELS_API_KEY", "")
    if not key or key == "your_pexels_api_key_here":
        raise ValueError(
            "PEXELS_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )
    return key


def get_n8n_webhook_url() -> str:
    """Return the n8n webhook URL."""
    return os.getenv(
        "N8N_WEBHOOK_URL",
        "http://localhost:5678/webhook/youtube-automation",
    )


def get_elevenlabs_api_key() -> str:
    """Return the ElevenLabs API key from environment variables."""
    key = os.getenv("ELEVENLABS_API_KEY", "")
    if not key or key == "your_elevenlabs_api_key_here":
        raise ValueError(
            "ELEVENLABS_API_KEY is not set. "
            "Add your key to .env."
        )
    return key


def get_pixabay_api_key() -> str:
    """Return the Pixabay API key from environment variables."""
    key = os.getenv("PIXABAY_API_KEY", "")
    if not key or key == "your_pixabay_api_key_here":
        raise ValueError(
            "PIXABAY_API_KEY is not set. "
            "Add your key to .env."
        )
    return key


# ---------------------------------------------------------------------------
# Duration-to-Scene-Count Mapping
# ---------------------------------------------------------------------------
DURATION_TO_SCENE_COUNT = [
    (15,   5),    # up to 15s  -> 5 scenes
    (30,  10),    # up to 30s  -> 10 scenes
    (60,  15),    # up to 60s  -> 15 scenes
    (120, 20),    # up to 120s -> 20 scenes
    (180, 30),    # up to 180s -> 30 scenes
]


def get_scene_count(duration_seconds: int) -> int:
    """Return the number of scenes/visuals to generate for a given video duration."""
    for max_dur, count in DURATION_TO_SCENE_COUNT:
        if duration_seconds <= max_dur:
            return count
    return DURATION_TO_SCENE_COUNT[-1][1]


# ---------------------------------------------------------------------------
# Local Settings Management
# ---------------------------------------------------------------------------
import json

SETTINGS_FILE = PROJECT_ROOT / "settings.json"

DEFAULT_SETTINGS = {
    "default_duration": 60,
    "default_tone": "educational",
    "default_voice": "gTTS (Standard)",
    "default_style": "Documentary",
    "output_folder": str(OUTPUT_DIR),
    "enable_n8n": False,
    "enable_transition_effects": True,
}

class SettingsManager:
    @staticmethod
    def load() -> dict:
        if not SETTINGS_FILE.exists():
            return DEFAULT_SETTINGS.copy()
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge with defaults
                merged = DEFAULT_SETTINGS.copy()
                merged.update(data)
                return merged
        except Exception:
            return DEFAULT_SETTINGS.copy()

    @staticmethod
    def save(settings: dict):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

