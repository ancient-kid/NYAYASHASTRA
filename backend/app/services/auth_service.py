"""
NyayaShastra AI Pro - Authentication Service
Demo mode: no external auth providers required.
"""

from typing import Dict, Any
from fastapi import Request

ANONYMOUS_USER: Dict[str, Any] = {
    "user_id": None,
    "email": None,
    "role": "anonymous",
}


async def get_current_user_optional(request: Request) -> Dict[str, Any]:
    """Return an anonymous user for demo mode."""
    _ = request
    return dict(ANONYMOUS_USER)


async def get_current_user() -> Dict[str, Any]:
    """Return an anonymous user for demo mode."""
    return dict(ANONYMOUS_USER)
