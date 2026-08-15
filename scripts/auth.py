"""
auth.py - Clerk Authentication Integration

Provides functions to verify Clerk session tokens and fetch user details.
"""
import os
import json
import requests
import jwt
from jwt.algorithms import RSAAlgorithm
from scripts.config import get_clerk_secret_key

_clerk_jwks = None

def _get_clerk_jwks():
    """Fetch and cache Clerk JWKS for JWT verification."""
    global _clerk_jwks
    if _clerk_jwks is None:
        secret = get_clerk_secret_key()
        if not secret:
            return None
        
        # We can use the Backend API to get JWKS. The URL usually requires the secret key for auth
        # or we can construct the Frontend API URL from the publishable key.
        # A simpler way is to fetch from https://api.clerk.com/v1/jwks
        try:
            response = requests.get(
                "https://api.clerk.com/v1/jwks",
                headers={"Authorization": f"Bearer {secret}"},
                timeout=5
            )
            response.raise_for_status()
            _clerk_jwks = response.json()
        except Exception as e:
            print(f"[Auth] Failed to fetch Clerk JWKS: {e}")
            return None
    return _clerk_jwks

def verify_clerk_session(token: str) -> dict | None:
    """
    Verify a Clerk JWT token.
    Returns the decoded token payload (containing 'sub' as user_id) if valid, None otherwise.
    """
    if not token:
        return None

    jwks = _get_clerk_jwks()
    if not jwks:
        return None

    try:
        # Get unverified header to find the key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            return None

        # Find the matching key in JWKS
        key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key_data:
            return None

        public_key = RSAAlgorithm.from_jwk(json.dumps(key_data))

        # Decode and verify token
        # Clerk JWTs are signed with RS256
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False}  # Adjust if audience verification is strictly needed
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

def get_clerk_user(user_id: str) -> dict | None:
    """
    Fetch user profile from Clerk Backend API.
    """
    secret = get_clerk_secret_key()
    if not secret:
        return None
        
    try:
        response = requests.get(
            f"https://api.clerk.com/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {secret}"},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[Auth] Failed to fetch user {user_id}: {e}")
        return None

def get_hosted_sign_in_url() -> str:
    """
    Return the Clerk Account Portal URL for sign-in.
    We extract the domain from the publishable key or use a fallback.
    """
    # Use deployed URL if available, otherwise fall back to localhost
    redirect_url = os.getenv("STREAMLIT_APP_URL", "http://localhost:8501")

    pub_key = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "")
    if pub_key.startswith("pk_test_"):
        # Very simple fallback for Streamlit apps using Clerk Dev instances:
        # e.g. pk_test_c3VpdGFibGUtY29sbGllLTI2LmNsZXJrLmFjY291bnRzLmRldiQ
        import base64
        try:
            encoded_part = pub_key.split("_")[2]
            padding = len(encoded_part) % 4
            if padding:
                encoded_part += "=" * (4 - padding)
            decoded = base64.b64decode(encoded_part).decode('utf-8')
            decoded = decoded.rstrip('$')
            
            # For dev instances, FAPI is .clerk.accounts.dev but Account Portal is .accounts.dev
            if decoded.endswith('.clerk.accounts.dev'):
                accounts_domain = decoded.replace('.clerk.accounts.dev', '.accounts.dev')
                return f"https://{accounts_domain}/sign-in?redirect_url={redirect_url}"
            
            return f"https://{decoded}/sign-in?redirect_url={redirect_url}"
        except Exception:
            pass
    return "https://accounts.clerk.com/sign-in" # Fallback production URL
