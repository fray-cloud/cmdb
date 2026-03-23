from abc import abstractmethod
from uuid import UUID

from ipam.shared.query_utils import ReadModelRepository


class IPAddressReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def exists_in_vrf(self, address: str, vrf_id: UUID | None) -> bool: ...

    @abstractmethod
    async def find_by_prefix(self, network: str, vrf_id: UUID | None) -> list[dict]: ...

    @abstractmethod
    async def find_ips_in_range(self, start_address: str, end_address: str, vrf_id: UUID | None) -> list[dict]: ...
