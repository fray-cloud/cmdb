from abc import abstractmethod

from shared.domain.repository import Repository

from tenant.domain.tenant import Tenant


class TenantRepository(Repository[Tenant]):
    @abstractmethod
    async def find_by_slug(self, slug: str) -> Tenant | None: ...

    @abstractmethod
    async def find_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Tenant], int]: ...
