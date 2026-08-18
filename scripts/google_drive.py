"""
google_drive.py — Google Drive Upload Service

Handles uploading generated videos to the user's Google Drive.
Creates/finds a "MAiX-YT" folder and uploads the video there.

Requires:
  - google-api-python-client
  - google-auth
  - google-auth-oauthlib
"""

import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from scripts.config import get_env_or_secret


# Google OAuth config
GOOGLE_CLIENT_ID = get_env_or_secret("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = get_env_or_secret("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = get_env_or_secret(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/drive/callback"
)

# Scopes — drive.file only allows access to files created by this app
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Folder name in Google Drive
DRIVE_FOLDER_NAME = "MAiX-YT"


def get_oauth_url(state: str = "") -> str:
    """
    Generate the Google OAuth2 consent URL.

    Args:
        state: Opaque value to pass through the OAuth flow (e.g. user_id).

    Returns:
        The full authorization URL to redirect the user to.
    """
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI

    auth_url, _ = flow.authorization_url(
        access_type="offline",  # Get a refresh_token
        include_granted_scopes="true",
        prompt="consent",       # Always show consent to get refresh token
        state=state,
    )
    return auth_url


def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchange the OAuth2 authorization code for access + refresh tokens.

    Args:
        code: The authorization code from Google's callback.

    Returns:
        Dict with access_token, refresh_token, token_uri, client_id, client_secret.
    """
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    flow.fetch_token(code=code)

    creds = flow.credentials
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
    }


def _build_credentials(token_data: dict) -> Credentials:
    """Build a google.oauth2.credentials.Credentials object from stored token data."""
    return Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id", GOOGLE_CLIENT_ID),
        client_secret=token_data.get("client_secret", GOOGLE_CLIENT_SECRET),
        scopes=token_data.get("scopes", SCOPES),
    )


def _find_or_create_folder(service, folder_name: str) -> str:
    """
    Find the MAiX-YT folder in Google Drive, or create it if it doesn't exist.

    Args:
        service: Google Drive API service instance.
        folder_name: Name of the folder to find/create.

    Returns:
        The Google Drive folder ID.
    """
    # Search for existing folder
    query = (
        f"name = '{folder_name}' "
        f"and mimeType = 'application/vnd.google-apps.folder' "
        f"and trashed = false"
    )
    results = service.files().list(
        q=query, spaces="drive", fields="files(id, name)", pageSize=1
    ).execute()

    files = results.get("files", [])
    if files:
        folder_id = files[0]["id"]
        print(f"  [Drive] Found existing '{folder_name}' folder: {folder_id}")
        return folder_id

    # Create the folder
    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(
        body=folder_metadata, fields="id"
    ).execute()

    folder_id = folder["id"]
    print(f"  [Drive] Created '{folder_name}' folder: {folder_id}")
    return folder_id


def upload_to_drive(
    file_path: str,
    filename: str,
    token_data: dict,
    description: str = "",
) -> dict:
    """
    Upload a video file to the user's Google Drive MAiX-YT folder.

    Args:
        file_path: Local path to the video file.
        filename: Display name for the file in Drive.
        token_data: Dict with access_token, refresh_token, etc.
        description: Optional file description.

    Returns:
        Dict with:
          - drive_file_id: The Google Drive file ID
          - drive_url: Web view link for the file
          - success: True/False
          - error: Error message if failed
    """
    try:
        p = Path(file_path)
        if not p.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        # Build credentials and service
        creds = _build_credentials(token_data)
        service = build("drive", "v3", credentials=creds)

        # Find or create MAiX-YT folder
        folder_id = _find_or_create_folder(service, DRIVE_FOLDER_NAME)

        # Upload the file
        file_metadata = {
            "name": filename,
            "parents": [folder_id],
        }
        if description:
            file_metadata["description"] = description

        # Determine MIME type
        suffix = p.suffix.lower()
        mime_map = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
        }
        mime_type = mime_map.get(suffix, "video/mp4")

        media = MediaFileUpload(
            str(p),
            mimetype=mime_type,
            resumable=True,
        )

        print(f"  [Drive] Uploading '{filename}' ({p.stat().st_size / 1024 / 1024:.1f} MB)...")

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink, webContentLink",
        ).execute()

        drive_file_id = file.get("id")
        web_view_link = file.get("webViewLink", "")
        web_content_link = file.get("webContentLink", "")

        print(f"  [Drive] ✅ Upload complete! File ID: {drive_file_id}")
        print(f"  [Drive]    View: {web_view_link}")

        return {
            "success": True,
            "drive_file_id": drive_file_id,
            "drive_url": web_view_link,
            "drive_download_url": web_content_link,
        }

    except Exception as e:
        error_msg = f"Google Drive upload failed: {e}"
        print(f"  [Drive] ❌ {error_msg}")
        return {"success": False, "error": error_msg}


def check_drive_connection(token_data: dict) -> dict:
    """
    Test if stored Drive tokens are still valid.

    Returns:
        Dict with connected: True/False, email: str, error: str
    """
    try:
        creds = _build_credentials(token_data)
        service = build("drive", "v3", credentials=creds)
        about = service.about().get(fields="user").execute()
        user = about.get("user", {})
        return {
            "connected": True,
            "email": user.get("emailAddress", ""),
            "display_name": user.get("displayName", ""),
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }
"""
Description: Google Drive upload service for MAiX-YT Studio.
"""
