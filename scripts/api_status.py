"""
api_status.py — API Connectivity Checker

Checks the status of all configured APIs and returns color-coded results
for the Streamlit dashboard sidebar.

Supported APIs:
  - Gemini (google-genai)
  - Pexels (REST API)
  - ElevenLabs (REST API)
  - FFmpeg (local binary)
"""

import os

import requests

from scripts.config import get_gemini_api_key, get_pexels_api_key, get_elevenlabs_api_key


# Status constants
STATUS_CONNECTED = "connected"
STATUS_INVALID_KEY = "invalid_key"
STATUS_MISSING_KEY = "missing_key"
STATUS_ERROR = "error"


def check_gemini() -> dict:
    """
    Check Gemini API connectivity.

    Performs a lightweight count_tokens call to verify the key works
    without consuming generation quota.
    """
    try:
        api_key = get_gemini_api_key()
    except ValueError:
        return {"status": STATUS_MISSING_KEY, "message": "API key not configured"}

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        client.models.count_tokens(
            model="gemini-2.5-flash",
            contents="test",
        )
        return {"status": STATUS_CONNECTED, "message": "Connected"}
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "401" in err:
            return {"status": STATUS_INVALID_KEY, "message": "Invalid API key"}
        if "RESOURCE_EXHAUSTED" in err or "429" in err:
            return {"status": STATUS_CONNECTED, "message": "Connected (quota limited)"}
        return {"status": STATUS_ERROR, "message": f"Error: {err[:80]}"}


def check_pexels() -> dict:
    """
    Check Pexels API connectivity.

    Performs a minimal search query to verify the key works.
    """
    try:
        api_key = get_pexels_api_key()
    except ValueError:
        return {"status": STATUS_MISSING_KEY, "message": "API key not configured"}

    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": "test", "per_page": 1},
            timeout=5,
        )
        if response.status_code == 200:
            return {"status": STATUS_CONNECTED, "message": "Connected"}
        elif response.status_code == 401:
            return {"status": STATUS_INVALID_KEY, "message": "Invalid API key"}
        else:
            return {"status": STATUS_ERROR, "message": f"HTTP {response.status_code}"}
    except requests.Timeout:
        return {"status": STATUS_ERROR, "message": "Connection timeout"}
    except Exception as e:
        return {"status": STATUS_ERROR, "message": f"Error: {str(e)[:80]}"}


def check_elevenlabs() -> dict:
    """
    Check ElevenLabs API connectivity.

    Calls the /v1/user endpoint to verify the key is valid.
    """
    try:
        api_key = get_elevenlabs_api_key()
    except ValueError:
        return {"status": STATUS_MISSING_KEY, "message": "API key not configured"}

    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": api_key},
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            # Show character usage if available
            sub = data.get("subscription", {})
            char_count = sub.get("character_count", 0)
            char_limit = sub.get("character_limit", 0)
            if char_limit > 0:
                return {
                    "status": STATUS_CONNECTED,
                    "message": f"Connected ({char_count}/{char_limit} chars used)",
                }
            return {"status": STATUS_CONNECTED, "message": "Connected"}
        elif response.status_code == 401:
            return {"status": STATUS_INVALID_KEY, "message": "Invalid API key"}
        else:
            return {"status": STATUS_ERROR, "message": f"HTTP {response.status_code}"}
    except requests.Timeout:
        return {"status": STATUS_ERROR, "message": "Connection timeout"}
    except Exception as e:
        return {"status": STATUS_ERROR, "message": f"Error: {str(e)[:80]}"}


def check_pixabay() -> dict:
    """
    Check Pixabay API connectivity.
    """
    try:
        # Import inside the function to avoid circular imports
        from scripts.config import get_pixabay_api_key
        api_key = get_pixabay_api_key()
    except ValueError:
        return {"status": STATUS_MISSING_KEY, "message": "API key not configured"}

    try:
        response = requests.get(
            "https://pixabay.com/api/",
            params={"key": api_key, "q": "test", "per_page": 3},
            timeout=5,
        )
        if response.status_code == 200:
            return {"status": STATUS_CONNECTED, "message": "Connected"}
        elif response.status_code in [400, 401]:
            return {"status": STATUS_INVALID_KEY, "message": "Invalid API key"}
        else:
            return {"status": STATUS_ERROR, "message": f"HTTP {response.status_code}"}
    except requests.Timeout:
        return {"status": STATUS_ERROR, "message": "Connection timeout"}
    except Exception as e:
        return {"status": STATUS_ERROR, "message": f"Error: {str(e)[:80]}"}


def check_ffmpeg() -> dict:
    """Check if FFmpeg is available."""
    try:
        import imageio_ffmpeg
        path = imageio_ffmpeg.get_ffmpeg_exe()
        return {"status": STATUS_CONNECTED, "message": "Available"}
    except Exception:
        return {"status": STATUS_ERROR, "message": "FFmpeg not found"}


def check_all_apis() -> dict:
    """
    Check all APIs and return a combined status dict.

    Returns:
        A dict mapping API name -> status dict with 'status' and 'message'.
    """
    return {
        "Gemini": check_gemini(),
        "Pexels": check_pexels(),
        "Pixabay": check_pixabay(),
        "ElevenLabs": check_elevenlabs(),
        "FFmpeg": check_ffmpeg(),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    results = check_all_apis()
    for name, info in results.items():
        icon = {"connected": "[OK]", "missing_key": "[--]", "invalid_key": "[!!]", "error": "[XX]"}
        print(f"  {icon.get(info['status'], '[??]')} {name}: {info['message']}")
