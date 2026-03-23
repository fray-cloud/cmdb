"""Shared query utilities — base list query, read model repository ABC, and filter builder."""

from datetime import datetime
from typing import Any
from uuid import UUID

from shared.api.filtering import FilterOperator, FilterParam
from shared.api.sorting import SortParam
from shared.cqrs.query import Query

from ipam.ip_address import IPAddress
from ipam.shared.value_objects import IPAddressValue

# ---------------------------------------------------------------------------
# Base list query
# ---------------------------------------------------------------------------


class BaseListQuery(Query):
    """Base query with common pagination, filtering, and sorting parameters."""

    offset: int = 0
    limit: int = 50
    description_contains: str | None = None
    tag_slugs: list[str] | None = None
    custom_field_filters: dict[str, Any] | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    updated_after: datetime | None = None
    updated_before: datetime | None = None
    sort_by: str | None = None
    sort_dir: str = "asc"


# ---------------------------------------------------------------------------
# Read model repository base ABC
# ---------------------------------------------------------------------------

from abc import ABC, abstractmethod  # noqa: E402


class ReadModelRepository(ABC):
    """Abstract base for all IPAM read model repositories."""

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


# ---------------------------------------------------------------------------
# Common filter builder
# ---------------------------------------------------------------------------


def build_common_filters(
    query: BaseListQuery,
) -> tuple[list[FilterParam], list[SortParam] | None, list[str] | None, dict[str, str] | None]:
    """Build common filters, sort params, tag_slugs, and custom_field_filters from BaseListQuery."""
    filters: list[FilterParam] = []

    if query.description_contains is not None:
        filters.append(
            FilterParam(field="description", operator=FilterOperator.ILIKE, value=query.description_contains)
        )
    if query.created_after is not None:
        filters.append(
            FilterParam(field="created_at", operator=FilterOperator.GTE, value=query.created_after.isoformat())
        )
    if query.created_before is not None:
        filters.append(
            FilterParam(field="created_at", operator=FilterOperator.LTE, value=query.created_before.isoformat())
        )
    if query.updated_after is not None:
        filters.append(
            FilterParam(field="updated_at", operator=FilterOperator.GTE, value=query.updated_after.isoformat())
        )
    if query.updated_before is not None:
        filters.append(
            FilterParam(field="updated_at", operator=FilterOperator.LTE, value=query.updated_before.isoformat())
        )

    sort_params: list[SortParam] | None = None
    if query.sort_by is not None:
        sort_params = [SortParam(field=query.sort_by, direction=query.sort_dir)]

    return filters, sort_params, query.tag_slugs, query.custom_field_filters


# ---------------------------------------------------------------------------
# Shared reconstruct helper — used by prefix and ip_range handlers
# ---------------------------------------------------------------------------


def reconstruct_ip(data: dict) -> IPAddress:
    """Reconstruct an IPAddress domain object from read model data for domain service use."""
    from ipam.ip_address.domain.value_objects import IPAddressStatus

    ip = IPAddress(aggregate_id=UUID(str(data["id"])))
    ip.address = IPAddressValue(address=data["address"]) if data.get("address") else None
    ip.vrf_id = UUID(str(data["vrf_id"])) if data.get("vrf_id") else None
    ip.status = IPAddressStatus(data["status"])
    ip.dns_name = data.get("dns_name", "")
    ip.tenant_id = UUID(str(data["tenant_id"])) if data.get("tenant_id") else None
    ip.description = data.get("description", "")
    ip.custom_fields = data.get("custom_fields", {})
    ip.tags = [UUID(str(t)) for t in data.get("tags", [])]
    return ip
