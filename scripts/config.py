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
# Cloud Environment Detection
# ---------------------------------------------------------------------------
IS_CLOUD = bool(os.getenv("STREAMLIT_SHARING_MODE") or os.getenv("STREAMLIT_CLOUD"))
IS_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT"))
IS_RENDER = bool(os.getenv("RENDER"))

# ---------------------------------------------------------------------------
# Directory Paths
# On Railway, use persistent volume at /data/ for output, /tmp/ for assets.
# On Render (Free), persistent disks aren't available, so use /tmp/
# ---------------------------------------------------------------------------
if IS_RAILWAY:
    ASSETS_DIR = Path("/tmp/maix_assets")
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/data/videos"))
elif IS_RENDER or IS_CLOUD:
    ASSETS_DIR = Path("/tmp/maix_assets")
    OUTPUT_DIR = Path("/tmp/maix_output")
else:
    ASSETS_DIR = PROJECT_ROOT / "assets"
    OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure directories exist
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# API Keys & Secrets Accessor Helper
# ---------------------------------------------------------------------------

def get_env_or_secret(key: str, default: str = "") -> str:
    """Retrieve config from environment variable, falling back to Streamlit secrets."""
    val = os.getenv(key, "").strip()
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default


def get_gemini_api_keys() -> list[str]:
    """
    Return all configured Gemini API keys.

    Reads GEMINI_API_KEY_1, GEMINI_API_KEY_2 (and optionally more) from
    the environment or Streamlit secrets. Falls back to the legacy GEMINI_API_KEY if neither
    numbered key is set. At least one valid key must be present.
    """
    keys = []
    # Collect numbered keys (1, 2, … up to 10)
    for i in range(1, 11):
        k = get_env_or_secret(f"GEMINI_API_KEY_{i}")
        if k and k != "your_gemini_api_key_here" and not k.startswith("your_"):
            keys.append(k)

    # Legacy fallback
    if not keys:
        legacy = get_env_or_secret("GEMINI_API_KEY")
        if legacy and legacy != "your_gemini_api_key_here" and not legacy.startswith("your_"):
            keys.append(legacy)

    if not keys:
        raise ValueError(
            "No Gemini API key found. "
            "Set GEMINI_API_KEY_1 (and optionally GEMINI_API_KEY_2) in .env or Streamlit Secrets."
        )
    return keys


def get_gemini_api_key() -> str:
    """Return the first configured Gemini API key (backward-compatible)."""
    return get_gemini_api_keys()[0]


def get_pexels_api_key() -> str:
    """Return the Pexels API key from environment variables or Streamlit secrets."""
    key = get_env_or_secret("PEXELS_API_KEY")
    if not key or key == "your_pexels_api_key_here" or key.startswith("your_"):
        raise ValueError(
            "PEXELS_API_KEY is not set. "
            "Configure it in .env or Streamlit Secrets."
        )
    return key


def get_n8n_webhook_url() -> str:
    """Return the n8n webhook URL."""
    return get_env_or_secret(
        "N8N_WEBHOOK_URL",
        "http://localhost:5678/webhook/youtube-automation",
    )


def get_elevenlabs_api_key() -> str:
    """Return the ElevenLabs API key from environment variables or Streamlit secrets."""
    key = get_env_or_secret("ELEVENLABS_API_KEY")
    if not key or key == "your_elevenlabs_api_key_here" or key.startswith("your_"):
        raise ValueError(
            "ELEVENLABS_API_KEY is not set. "
            "Configure it in .env or Streamlit Secrets."
        )
    return key


def get_pixabay_api_key() -> str:
    """Return the Pixabay API key from environment variables or Streamlit secrets."""
    key = get_env_or_secret("PIXABAY_API_KEY")
    if not key or key == "your_pixabay_api_key_here" or key.startswith("your_"):
        raise ValueError(
            "PIXABAY_API_KEY is not set. "
            "Configure it in .env or Streamlit Secrets."
        )
    return key


def get_clerk_publishable_key() -> str:
    """Return the Clerk publishable key from environment variables or Streamlit secrets."""
    return get_env_or_secret("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")


def get_clerk_secret_key() -> str:
    """Return the Clerk secret key from environment variables or Streamlit secrets."""
    return get_env_or_secret("CLERK_SECRET_KEY")



# ---------------------------------------------------------------------------
# Duration Presets & Word-Count Enforcement
# ---------------------------------------------------------------------------
DURATION_PRESETS = {
    "min": {
        "key": "min",
        "label": "Min (Shorts / 30s)",
        "seconds": 30,
        "scenes": 5,
        "min_words": 60,
        "max_words": 75,
    },
    "medium": {
        "key": "medium",
        "label": "Medium (Standard / 60s)",
        "seconds": 60,
        "scenes": 10,
        "min_words": 125,
        "max_words": 150,
    },
    "max": {
        "key": "max",
        "label": "Max (Extended / 180s)",
        "seconds": 180,
        "scenes": 20,
        "min_words": 375,
        "max_words": 430,
    },
}

DURATION_TO_SCENE_COUNT = [
    (30,  5),     # Min: 30s -> 5 scenes
    (60,  10),    # Medium: 60s -> 10 scenes
    (180, 20),    # Max: 180s -> 20 scenes
]


def get_duration_preset(key_or_seconds) -> dict:
    """Return preset info by key ('min', 'medium', 'max') or nearest duration seconds."""
    if isinstance(key_or_seconds, str):
        key = key_or_seconds.lower().strip()
        if key in DURATION_PRESETS:
            return DURATION_PRESETS[key]
        if "min" in key or "30" in key:
            return DURATION_PRESETS["min"]
        if "max" in key or "180" in key:
            return DURATION_PRESETS["max"]
        return DURATION_PRESETS["medium"]

    sec = int(key_or_seconds)
    if sec <= 40:
        return DURATION_PRESETS["min"]
    elif sec >= 120:
        return DURATION_PRESETS["max"]
    else:
        return DURATION_PRESETS["medium"]


def get_scene_count(duration_seconds: int) -> int:
    """Return the number of scenes/visuals to generate for a given video duration."""
    return get_duration_preset(duration_seconds)["scenes"]


def get_duration_word_bounds(duration_seconds: int) -> tuple[int, int]:
    """Return (min_words, max_words) for a target video duration based on ~2.3 words/sec."""
    preset = get_duration_preset(duration_seconds)
    return preset["min_words"], preset["max_words"]


# ---------------------------------------------------------------------------
# Style-Based Video Effect Profiles
# ---------------------------------------------------------------------------
STYLE_EFFECT_PROFILES = {
    "Documentary": {
        "transition_type": "dissolve",
        "transition_duration": 0.6,
        "zoom_speed": 0.0012,
        "max_zoom": 1.12,
        "motion_types": ["zoom_in", "zoom_out"],
        "text_style": "subtle_lower_third",
    },
    "Educational Explainer": {
        "transition_type": "fade",
        "transition_duration": 0.5,
        "zoom_speed": 0.0015,
        "max_zoom": 1.15,
        "motion_types": ["zoom_in", "pan_right", "pan_left"],
        "text_style": "clean_keyword_box",
    },
    "Storytelling": {
        "transition_type": "dissolve",
        "transition_duration": 0.8,
        "zoom_speed": 0.0010,
        "max_zoom": 1.10,
        "motion_types": ["zoom_in", "zoom_out"],
        "text_style": "subtle_lower_third",
    },
    "News": {
        "transition_type": "fade",
        "transition_duration": 0.3,
        "zoom_speed": 0.0008,
        "max_zoom": 1.06,
        "motion_types": ["zoom_in"],
        "text_style": "clean_keyword_box",
    },
    "Cinematic": {
        "transition_type": "dissolve",
        "transition_duration": 1.0,
        "zoom_speed": 0.0020,
        "max_zoom": 1.20,
        "motion_types": ["zoom_in", "zoom_out", "pan_right", "pan_left"],
        "text_style": "cinematic_center",
    },
    "Entertainment": {
        "transition_type": "fadeblack",
        "transition_duration": 0.4,
        "zoom_speed": 0.0020,
        "max_zoom": 1.18,
        "motion_types": ["zoom_in", "zoom_out", "pan_left", "pan_right"],
        "text_style": "bold_pop",
    },
    "Listicle": {
        "transition_type": "fade",
        "transition_duration": 0.35,
        "zoom_speed": 0.0016,
        "max_zoom": 1.14,
        "motion_types": ["zoom_in", "pan_right"],
        "text_style": "clean_keyword_box",
    },
    "Case Study": {
        "transition_type": "dissolve",
        "transition_duration": 0.7,
        "zoom_speed": 0.0012,
        "max_zoom": 1.10,
        "motion_types": ["zoom_in", "zoom_out"],
        "text_style": "subtle_lower_third",
    },
    # Legacy key for backward compat
    "Educational": {
        "transition_type": "fade",
        "transition_duration": 0.5,
        "zoom_speed": 0.0015,
        "max_zoom": 1.15,
        "motion_types": ["zoom_in", "pan_right", "pan_left"],
        "text_style": "clean_keyword_box",
    },
    "Motivational": {
        "transition_type": "fade",
        "transition_duration": 0.6,
        "zoom_speed": 0.0018,
        "max_zoom": 1.16,
        "motion_types": ["zoom_in", "zoom_out"],
        "text_style": "cinematic_center",
    },
}


def get_style_profile(style_name: str) -> dict:
    """Return style-based effect profile configuration."""
    clean_key = style_name.strip() if style_name else "Documentary"
    return STYLE_EFFECT_PROFILES.get(clean_key, STYLE_EFFECT_PROFILES["Documentary"])


# ---------------------------------------------------------------------------
# Local Settings Management
# ---------------------------------------------------------------------------
import json

SETTINGS_FILE = PROJECT_ROOT / "settings.json"

DEFAULT_SETTINGS = {
    "default_duration_preset": "medium",
    "default_duration": 60,
    "default_tone": "educational",
    "default_voice": "Edge-TTS (Neural)",
    "default_voice_gender": "female",
    "default_style": "Documentary",
    "output_folder": str(OUTPUT_DIR),
    "enable_n8n": False,
    "enable_transition_effects": True,
    "enable_motion_effects": True,
    "enable_text_highlights": True,
    "enable_subtitles": False,
    "enable_bg_music": True,
    "bg_music_volume": 0.10,
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
        except OSError:
            # Cloud deployments have a read-only filesystem — skip silently
            pass
        except Exception as e:
            print(f"Error saving settings: {e}")



