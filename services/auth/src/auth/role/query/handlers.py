"""Query handlers for retrieving roles and checking permissions."""

from pydantic import BaseModel
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from auth.group import GroupRepository
from auth.role.domain import RoleRepository
from auth.role.query.dto import RoleDTO
from auth.shared.domain import PermissionChecker
from auth.user import UserRepository


class GetRoleHandler(QueryHandler[RoleDTO]):
    """Handles fetching a single role by ID."""

    def __init__(self, repository: RoleRepository) -> None:
        self._repository = repository

    async def handle(self, query: Query) -> RoleDTO:
        """Retrieve a role by ID or raise EntityNotFoundError."""
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
    """Handles paginated listing of roles within a tenant."""

    def __init__(self, repository: RoleRepository) -> None:
        self._repository = repository

    async def handle(self, query: Query) -> tuple[list[RoleDTO], int]:
        """Return a paginated list of roles and total count."""
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


class PermissionCheckDTO(BaseModel):
    allowed: bool


class CheckPermissionHandler(QueryHandler[PermissionCheckDTO]):
    """Handles permission checks by aggregating user, role, and group permissions."""

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
        """Check whether a user has the specified permission."""
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
