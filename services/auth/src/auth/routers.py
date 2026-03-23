"""Aggregated router exports for the auth service."""

from auth.api_token.router import router as api_token_router
from auth.role.router import permission_router
from auth.role.router import router as role_router
from auth.shared.auth_router import router as auth_router
from auth.user.router import router as user_router

__all__ = [
    "auth_router",
    "user_router",
    "role_router",
    "api_token_router",
    "permission_router",
]
