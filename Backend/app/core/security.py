import secrets
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from app.core.config import Settings, get_settings


def verify_admin_key(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key", description="Admin API secret key"),
    authorization: Optional[str] = Header(None, alias="Authorization", description="Bearer <admin_key>"),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Validates administrative requests using constant-time comparison.
    Supports either 'X-Admin-Key: <secret>' header or 'Authorization: Bearer <secret>' header.
    Raises HTTP 401 Unauthorized if missing or invalid.
    """

    provided_token: Optional[str] = None
    if x_admin_key:
        provided_token = x_admin_key.strip()
    elif authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            provided_token = parts[1].strip()
        elif len(parts) == 1:
            provided_token = parts[0].strip()

    if not provided_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide valid admin credentials via 'X-Admin-Key' or 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    configured_key: Optional[str] = None
    if settings.ADMIN_API_KEY and settings.ADMIN_API_KEY.get_secret_value():
        configured_key = settings.ADMIN_API_KEY.get_secret_value()
    elif settings.SECRET_KEY and settings.SECRET_KEY.get_secret_value():
        configured_key = settings.SECRET_KEY.get_secret_value()
    else:
        try:
            import os
            configured_key = os.environ.get("ADMIN_API_KEY") or os.environ.get("SECRET_KEY")
        except Exception:
            pass

    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin authentication is not configured on the server.",
        )

    # Constant-time comparison to protect against timing attacks
    if not secrets.compare_digest(provided_token, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return provided_token
