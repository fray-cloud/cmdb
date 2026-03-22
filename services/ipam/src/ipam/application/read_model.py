from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from shared.api.filtering import FilterParam
from shared.api.sorting import SortParam


class ReadModelRepository(ABC):
    @abstractmethod
    async def upsert_from_aggregate(self, aggregate: Any) -> None: ...

    @abstractmethod
    async def find_by_id(self, entity_id: UUID) -> dict | None: ...

    @abstractmethod
    async def find_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        filters: list[FilterParam] | None = None,
        sort_params: list[SortParam] | None = None,
        tag_slugs: list[str] | None = None,
        custom_field_filters: dict[str, str] | None = None,
    ) -> tuple[list[dict], int]: ...

    @abstractmethod
    async def mark_deleted(self, entity_id: UUID) -> None: ...


class PrefixReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_children(self, parent_network: str, vrf_id: UUID | None) -> list[dict]: ...

    @abstractmethod
    async def find_by_vrf(self, vrf_id: UUID, *, offset: int = 0, limit: int = 50) -> tuple[list[dict], int]: ...


class IPAddressReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def exists_in_vrf(self, address: str, vrf_id: UUID | None) -> bool: ...

    @abstractmethod
    async def find_by_prefix(self, network: str, vrf_id: UUID | None) -> list[dict]: ...

    @abstractmethod
    async def find_ips_in_range(self, start_address: str, end_address: str, vrf_id: UUID | None) -> list[dict]: ...


class VRFReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_by_name(self, name: str) -> dict | None: ...


class VLANReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_by_vid(self, vid: int, group_id: UUID | None) -> dict | None: ...


class IPRangeReadModelRepository(ReadModelRepository):
    pass


class RIRReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_by_name(self, name: str) -> dict | None: ...


class ASNReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_by_asn(self, asn: int) -> dict | None: ...


class FHRPGroupReadModelRepository(ReadModelRepository):
    pass


class RouteTargetReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_by_name(self, name: str) -> dict | None: ...


class VLANGroupReadModelRepository(ReadModelRepository):
    @abstractmethod
    async def find_by_slug(self, slug: str) -> dict | None: ...


class ServiceReadModelRepository(ReadModelRepository):
    pass


class SavedFilterRepository(ABC):
    @abstractmethod
    async def find_by_id(self, filter_id: UUID) -> dict | None: ...

    @abstractmethod
    async def find_by_user(self, user_id: UUID, entity_type: str | None = None) -> list[dict]: ...

    @abstractmethod
    async def create(self, data: dict) -> UUID: ...

    @abstractmethod
    async def update(self, filter_id: UUID, data: dict) -> None: ...

    @abstractmethod
    async def delete(self, filter_id: UUID) -> None: ...

    @abstractmethod
    async def clear_default(self, user_id: UUID, entity_type: str) -> None: ...


class GlobalSearchRepository(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        entity_types: list[str] | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]: ...
