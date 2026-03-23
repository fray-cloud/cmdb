from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from auth.user.domain.repository import UserRepository
from auth.user.query.dto import UserDTO


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
