from abc import ABC, abstractmethod
from uuid import UUID

from ipam.rir.domain.rir import RIR


class RIRRepository(ABC):
    @abstractmethod
    async def find_by_id(self, rir_id: UUID) -> RIR | None: ...

    @abstractmethod
    async def save(self, rir: RIR) -> None: ...

    @abstractmethod
    async def delete(self, rir_id: UUID) -> None: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> RIR | None: ...
