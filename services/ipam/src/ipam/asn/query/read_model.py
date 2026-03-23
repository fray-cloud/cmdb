"""ASN read model repository interface."""

from abc import abstractmethod

from ipam.shared.query_utils import ReadModelRepository


class ASNReadModelRepository(ReadModelRepository):
    """Abstract read model repository for ASN queries."""

    @abstractmethod
    async def find_by_asn(self, asn: int) -> dict | None: ...
