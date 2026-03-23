from abc import abstractmethod
from uuid import UUID

from ipam.shared.query_utils import ReadModelRepository


class PrefixReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_children(self, parent_network: str, vrf_id: UUID | None) -> list[dict]: ...

    @abstractmethod
    async def find_by_vrf(self, vrf_id: UUID, *, offset: int = 0, limit: int = 50) -> tuple[list[dict], int]: ...
