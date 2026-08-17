"""
auth_service.py — Clerk JWT Verification for FastAPI

Verifies Clerk bearer tokens and extracts user_id.
Every protected endpoint uses get_current_user() as a dependency.

NEVER trust user_id from the frontend — always extract from verified token.
"""

import os
import json
from typing import Optional

import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException, Request

from scripts.config import get_clerk_secret_key

_clerk_jwks = None


def _get_clerk_jwks() -> Optional[dict]:
    """Fetch and cache Clerk JWKS for JWT verification."""
    global _clerk_jwks
    if _clerk_jwks is not None:
        return _clerk_jwks

    secret = get_clerk_secret_key()
    if not secret:
        return None

    try:
        response = requests.get(
            "https://api.clerk.com/v1/jwks",
            headers={"Authorization": f"Bearer {secret}"},
            timeout=5,
        )
        response.raise_for_status()
        _clerk_jwks = response.json()
        return _clerk_jwks
    except Exception as e:
        print(f"[Auth] Failed to fetch Clerk JWKS: {e}")
        return None


def verify_clerk_token(token: str) -> Optional[dict]:
    """
    Verify a Clerk JWT token.
    Returns the decoded payload (containing 'sub' as user_id) if valid, None otherwise.
    """
    if not token:
        return None

    jwks = _get_clerk_jwks()
    if not jwks:
        return None

    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            return None

        key_data = next(
            (k for k in jwks.get("keys", []) if k.get("kid") == kid), None
        )
        if not key_data:
            return None

        public_key = RSAAlgorithm.from_jwk(json.dumps(key_data))

        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return decoded
    except jwt.ExpiredSignatureError:
        print("[Auth] Token expired.")
        return None
    except jwt.InvalidTokenError as e:
        print(f"[Auth] Invalid token: {e}")
        return None
    except Exception as e:
        print(f"[Auth] Verification error: {e}")
        return None


async def get_current_user(request: Request) -> str:
    """
    FastAPI dependency — extract and verify Clerk user_id from Authorization header.

    Usage:
        @app.get("/api/something")
        async def endpoint(user_id: str = Depends(get_current_user)):
            ...

    Returns the Clerk user_id (the 'sub' claim from the JWT).
    Raises HTTP 401 if token is missing or invalid.
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]  # Strip "Bearer "

    # In development without Clerk configured, allow bypass
    if not get_clerk_secret_key():
        # If no Clerk secret is configured, use a dev user_id
        print("[Auth] WARNING: No CLERK_SECRET_KEY — using dev user")
        return "dev_user"

    decoded = verify_clerk_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = decoded.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user ID")

    return user_id
