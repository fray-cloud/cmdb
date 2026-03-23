from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import AuthorizationError

from auth.api_token.domain.repository import APITokenRepository
from auth.api_token.query.dto import APITokenDTO
from auth.shared.security import JWTService
from auth.shared.token_blacklist import RedisTokenBlacklist


class ListAPITokensHandler(QueryHandler[tuple[list[APITokenDTO], int]]):
    def __init__(self, repository: APITokenRepository) -> None:
        self._repository = repository

    async def handle(self, query: Query) -> tuple[list[APITokenDTO], int]:
        tokens, total = await self._repository.find_all_by_user(
            query.user_id,
            offset=query.offset,
            limit=query.limit,
        )
        items = [
            APITokenDTO(
                id=t.id,
                user_id=t.user_id,
                tenant_id=t.tenant_id,
                description=t.description,
                scopes=t.scopes,
                expires_at=t.expires_at,
                allowed_ips=t.allowed_ips,
                is_revoked=t.is_revoked,
                created_at=t.created_at,
            )
            for t in tokens
        ]
        return items, total


class ValidateTokenHandler(QueryHandler[dict]):
    def __init__(
        self,
        jwt_service: JWTService,
        token_blacklist: RedisTokenBlacklist,
    ) -> None:
        self._jwt_service = jwt_service
        self._token_blacklist = token_blacklist

    async def handle(self, query: Query) -> dict:
        try:
            payload = self._jwt_service.decode_token(query.token)
        except Exception as exc:
            raise AuthorizationError("Invalid token") from exc

        jti = payload.get("jti")
        if jti and await self._token_blacklist.is_blacklisted(jti):
            raise AuthorizationError("Token has been revoked")

        return payload
