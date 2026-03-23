from abc import ABC, abstractmethod
from uuid import UUID

from ipam.vlan.domain.vlan import VLAN


class VLANRepository(ABC):
    @abstractmethod
    async def find_by_id(self, vlan_id: UUID) -> VLAN | None: ...

    @abstractmethod
    async def save(self, vlan: VLAN) -> None: ...

    @abstractmethod
    async def delete(self, vlan_id: UUID) -> None: ...

    @abstractmethod
    async def find_by_vid(self, vid: int, group_id: UUID | None) -> VLAN | None: ...
