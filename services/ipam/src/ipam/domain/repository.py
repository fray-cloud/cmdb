from abc import ABC, abstractmethod
from uuid import UUID

from ipam.domain.ip_address import IPAddress
from ipam.domain.prefix import Prefix
from ipam.domain.vlan import VLAN
from ipam.domain.vrf import VRF


class PrefixRepository(ABC):
    @abstractmethod
    async def find_by_id(self, prefix_id: UUID) -> Prefix | None: ...

    @abstractmethod
    async def save(self, prefix: Prefix) -> None: ...

    @abstractmethod
    async def delete(self, prefix_id: UUID) -> None: ...

    @abstractmethod
    async def find_children(self, parent_network: str, vrf_id: UUID | None) -> list[Prefix]: ...

    @abstractmethod
    async def find_by_vrf(self, vrf_id: UUID, *, offset: int = 0, limit: int = 50) -> tuple[list[Prefix], int]: ...


class IPAddressRepository(ABC):
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


class VRFRepository(ABC):
    @abstractmethod
    async def find_by_id(self, vrf_id: UUID) -> VRF | None: ...

    @abstractmethod
    async def save(self, vrf: VRF) -> None: ...

    @abstractmethod
    async def delete(self, vrf_id: UUID) -> None: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> VRF | None: ...


class VLANRepository(ABC):
    @abstractmethod
    async def find_by_id(self, vlan_id: UUID) -> VLAN | None: ...

    @abstractmethod
    async def save(self, vlan: VLAN) -> None: ...

    @abstractmethod
    async def delete(self, vlan_id: UUID) -> None: ...

    @abstractmethod
    async def find_by_vid(self, vid: int, group_id: UUID | None) -> VLAN | None: ...
