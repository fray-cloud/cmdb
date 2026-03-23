from abc import abstractmethod

from ipam.shared.query_utils import ReadModelRepository


class ASNReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_by_asn(self, asn: int) -> dict | None: ...
