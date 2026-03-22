from uuid import UUID

from fastapi import Request
from shared.domain.exceptions import AuthorizationError

from auth.infrastructure.security import JWTService


async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthorizationError("Missing or invalid Authorization header")

    token = auth_header.removeprefix("Bearer ").strip()

    jwt_service: JWTService = request.app.state.jwt_service
    token_blacklist = request.app.state.token_blacklist

    try:
        payload = jwt_service.decode_token(token)
    except Exception as exc:
        raise AuthorizationError("Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise AuthorizationError("Invalid token type")

    jti = payload.get("jti")
    if jti and await token_blacklist.is_blacklisted(jti):
        raise AuthorizationError("Token has been revoked")

    return {
        "user_id": UUID(payload["sub"]),
        "tenant_id": UUID(payload["tenant_id"]),
        "roles": payload.get("roles", []),
    }
