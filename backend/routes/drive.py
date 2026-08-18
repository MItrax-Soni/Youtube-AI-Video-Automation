"""
drive.py — Google Drive OAuth & Status Routes

Endpoints:
  GET  /api/drive/auth-url    → Returns the Google OAuth consent URL
  GET  /api/drive/callback    → Handles the OAuth callback, stores tokens
  GET  /api/drive/status      → Checks if user has connected Google Drive
  POST /api/drive/disconnect  → Removes stored Google Drive tokens
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from backend.services.auth_service import get_current_user
from scripts.google_drive import (
    get_oauth_url,
    exchange_code_for_tokens,
    check_drive_connection,
    GOOGLE_CLIENT_ID,
)
from scripts.database import (
    save_user_oauth_tokens,
    get_user_oauth_tokens,
    delete_user_oauth_tokens,
)

router = APIRouter()


@router.get("/api/drive/auth-url")
async def drive_auth_url(user_id: str = Depends(get_current_user)):
    """
    Generate the Google OAuth consent URL.

    The frontend redirects the user to this URL to authorize Drive access.
    The 'state' parameter carries the user_id so we can link tokens on callback.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Google Drive not configured. Set GOOGLE_CLIENT_ID in .env",
        )

    url = get_oauth_url(state=user_id)
    return {"auth_url": url}


@router.get("/api/drive/callback")
async def drive_callback(request: Request):
    """
    Handle the Google OAuth callback.

    Google redirects here with ?code=...&state=user_id
    We exchange the code for tokens and store them in MongoDB.
    Then redirect to the frontend settings page.
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")  # user_id
    error = request.query_params.get("error")

    if error:
        # User denied access — redirect to settings with error
        return RedirectResponse(url="/settings?drive=denied")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    try:
        # Exchange authorization code for tokens
        token_data = exchange_code_for_tokens(code)

        # Store tokens in MongoDB, linked to user
        save_user_oauth_tokens(state, "google_drive", token_data)

        print(f"[Drive] ✅ Stored Google Drive tokens for user: {state}")

        # Redirect to frontend settings page with success indicator
        import os
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/settings?drive=connected")

    except Exception as e:
        print(f"[Drive] ❌ OAuth callback error: {e}")
        import os
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/settings?drive=error")


@router.get("/api/drive/status")
async def drive_status(user_id: str = Depends(get_current_user)):
    """
    Check if the current user has connected their Google Drive.

    Returns connection status, email, and display name if connected.
    """
    if not GOOGLE_CLIENT_ID:
        return {
            "configured": False,
            "connected": False,
            "message": "Google Drive not configured on the server",
        }

    token_data = get_user_oauth_tokens(user_id, "google_drive")

    if not token_data:
        return {
            "configured": True,
            "connected": False,
            "message": "Not connected",
        }

    # Verify the tokens still work
    result = check_drive_connection(token_data)

    if result.get("connected"):
        return {
            "configured": True,
            "connected": True,
            "email": result.get("email", ""),
            "display_name": result.get("display_name", ""),
        }
    else:
        return {
            "configured": True,
            "connected": False,
            "message": f"Token expired or revoked: {result.get('error', '')}",
        }


@router.post("/api/drive/disconnect")
async def drive_disconnect(user_id: str = Depends(get_current_user)):
    """Remove stored Google Drive tokens for the current user."""
    delete_user_oauth_tokens(user_id, "google_drive")
    return {"status": "disconnected"}
