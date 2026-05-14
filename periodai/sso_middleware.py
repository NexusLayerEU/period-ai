"""
SSO JWT Middleware for PeriodAI.
Validates Bearer tokens issued by AIIdentityServer using the shared JWT secret.
Install: pip install PyJWT
"""
import os
from typing import Optional

try:
    import jwt
except ImportError:
    jwt = None

SSO_JWT_SECRET = os.getenv("SSO_JWT_SECRET", "nexuslayer-shared-sso-secret-change-in-production-64chars!!")
SSO_ALGORITHM = "HS256"
IDENTITY_SERVER_URL = os.getenv("IDENTITY_SERVER_URL", "http://192.168.68.111:3007")


def decode_sso_token(token: str) -> Optional[dict]:
    """Decode and validate an SSO JWT token. Returns claims dict or None if invalid."""
    if jwt is None:
        raise ImportError("PyJWT is required: pip install PyJWT")
    try:
        payload = jwt.decode(token, SSO_JWT_SECRET, algorithms=[SSO_ALGORITHM])
        return payload
    except Exception:
        return None


def get_current_user_from_bearer(authorization: str) -> Optional[dict]:
    """Extract user info from Authorization: Bearer <token> header."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return decode_sso_token(authorization[7:])
