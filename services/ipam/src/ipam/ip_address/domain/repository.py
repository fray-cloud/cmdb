"""Abstract repository interface for the IPAddress aggregate."""

from abc import ABC, abstractmethod
from uuid import UUID

from ipam.ip_address.domain.ip_address import IPAddress


class IPAddressRepository(ABC):
    """Domain repository interface for persisting and retrieving IPAddress aggregates."""

    @abstractmethod
    async def find_by_id(self, ip_id: UUID) -> IPAddress | None: ...

    @abstractmethod
    async def save(self, ip_address: IPAddress) -> None: ...

    @abstractmethod
    async def delete(self, ip_id: UUID) -> None: ...

    @abstractmethod
    async def find_by_prefix(self, network: str, vrf_id: UUID | None) -> list[IPAddress]: ...

    @abstractmethod
    async def exists_in_vrf(self, address: str, vrf_id: UUID | None) -> bool: ...
