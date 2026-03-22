from abc import abstractmethod
from uuid import UUID

from auth.domain.api_token import APIToken
from auth.domain.group import Group
from auth.domain.role import Role
from auth.domain.user import User
from shared.domain.repository import Repository


class UserRepository(Repository[User]):
    @abstractmethod
    async def find_by_email(self, email: str, tenant_id: UUID) -> User | None: ...

    @abstractmethod
    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[User], int]: ...


class RoleRepository(Repository[Role]):
    @abstractmethod
    async def find_by_name(self, name: str, tenant_id: UUID) -> Role | None: ...

    @abstractmethod
    async def find_by_ids(self, role_ids: list[UUID]) -> list[Role]: ...

    @abstractmethod
    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Role], int]: ...


class GroupRepository(Repository[Group]):
    @abstractmethod
    async def find_by_name(self, name: str, tenant_id: UUID) -> Group | None: ...

    @abstractmethod
    async def find_by_ids(self, group_ids: list[UUID]) -> list[Group]: ...

    @abstractmethod
    async def find_all(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Group], int]: ...


class APITokenRepository(Repository[APIToken]):
    @abstractmethod
    async def find_by_key_hash(self, key_hash: str) -> APIToken | None: ...

    @abstractmethod
    async def find_all_by_user(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[APIToken], int]: ...
