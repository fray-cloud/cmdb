from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import AuthorizationError, EntityNotFoundError

from auth.application.dto import (
    APITokenDTO,
    PermissionCheckDTO,
    RoleDTO,
    UserDTO,
)
from auth.domain.repository import (
    APITokenRepository,
    GroupRepository,
    RoleRepository,
    UserRepository,
)
from auth.domain.services import PermissionChecker
from auth.infrastructure.security import JWTService
from auth.infrastructure.token_blacklist import RedisTokenBlacklist


class GetUserHandler(QueryHandler[UserDTO]):
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def handle(self, query: Query) -> UserDTO:
        user = await self._repository.find_by_id(query.user_id)
        if user is None:
            raise EntityNotFoundError(f"User {query.user_id} not found")
        return UserDTO(
            id=user.id,
            email=user.email,
            tenant_id=user.tenant_id,
            status=user.status,
            display_name=user.display_name,
            role_ids=user.role_ids,
            group_ids=user.group_ids,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class ListUsersHandler(QueryHandler[tuple[list[UserDTO], int]]):
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def handle(self, query: Query) -> tuple[list[UserDTO], int]:
        users, total = await self._repository.find_all(
            query.tenant_id,
            offset=query.offset,
            limit=query.limit,
        )
        items = [
            UserDTO(
                id=u.id,
                email=u.email,
                tenant_id=u.tenant_id,
                status=u.status,
                display_name=u.display_name,
                role_ids=u.role_ids,
                group_ids=u.group_ids,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in users
        ]
        return items, total


class GetRoleHandler(QueryHandler[RoleDTO]):
    def __init__(self, repository: RoleRepository) -> None:
        self._repository = repository

    async def handle(self, query: Query) -> RoleDTO:
        role = await self._repository.find_by_id(query.role_id)
        if role is None:
            raise EntityNotFoundError(f"Role {query.role_id} not found")
        return RoleDTO(
            id=role.id,
            name=role.name,
            tenant_id=role.tenant_id,
            description=role.description,
            permissions=[p.model_dump() for p in role.permissions],
            is_system=role.is_system,
            created_at=role.created_at,
            updated_at=role.updated_at,
        )


class ListRolesHandler(QueryHandler[tuple[list[RoleDTO], int]]):
    def __init__(self, repository: RoleRepository) -> None:
        self._repository = repository

    async def handle(self, query: Query) -> tuple[list[RoleDTO], int]:
        roles, total = await self._repository.find_all(
            query.tenant_id,
            offset=query.offset,
            limit=query.limit,
        )
        items = [
            RoleDTO(
                id=r.id,
                name=r.name,
                tenant_id=r.tenant_id,
                description=r.description,
                permissions=[p.model_dump() for p in r.permissions],
                is_system=r.is_system,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in roles
        ]
        return items, total


class CheckPermissionHandler(QueryHandler[PermissionCheckDTO]):
    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        group_repository: GroupRepository,
    ) -> None:
        self._user_repository = user_repository
        self._role_repository = role_repository
        self._group_repository = group_repository
        self._checker = PermissionChecker()

    async def handle(self, query: Query) -> PermissionCheckDTO:
        user = await self._user_repository.find_by_id(query.user_id)
        if user is None:
            return PermissionCheckDTO(allowed=False)

        roles = await self._role_repository.find_by_ids(user.role_ids)
        groups = await self._group_repository.find_by_ids(user.group_ids)

        allowed = self._checker.has_permission(
            user=user,
            roles=roles,
            groups=groups,
            object_type=query.object_type,
            action=query.action,
        )
        return PermissionCheckDTO(allowed=allowed)


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
