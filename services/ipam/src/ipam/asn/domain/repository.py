from abc import ABC, abstractmethod
from uuid import UUID

from ipam.asn.domain.asn import ASN


class ASNRepository(ABC):
    @abstractmethod
    async def find_by_id(self, asn_id: UUID) -> ASN | None: ...

    @abstractmethod
    async def save(self, asn: ASN) -> None: ...

    @abstractmethod
    async def delete(self, asn_id: UUID) -> None: ...

    @abstractmethod
    async def find_by_asn(self, asn: int) -> ASN | None: ...
