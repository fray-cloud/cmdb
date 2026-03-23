from uuid import UUID

from shared.api.filtering import FilterOperator, FilterParam
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.ip_address.query.read_model import IPAddressReadModelRepository
from ipam.ip_range.domain.ip_range import IPRange
from ipam.ip_range.domain.value_objects import IPRangeStatus
from ipam.ip_range.query.dto import IPRangeDTO
from ipam.ip_range.query.read_model import IPRangeReadModelRepository
from ipam.shared.query_utils import build_common_filters, reconstruct_ip
from ipam.shared.services.ip_range_utilization import IPRangeUtilizationService
from ipam.shared.value_objects import IPAddressValue

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reconstruct_ip_range(data: dict) -> IPRange:
    """Reconstruct an IPRange domain object from read model data for domain service use."""
    ip_range = IPRange(aggregate_id=UUID(str(data["id"])))
    ip_range.start_address = IPAddressValue(address=data["start_address"]) if data.get("start_address") else None
    ip_range.end_address = IPAddressValue(address=data["end_address"]) if data.get("end_address") else None
    ip_range.vrf_id = UUID(str(data["vrf_id"])) if data.get("vrf_id") else None
    ip_range.status = IPRangeStatus(data["status"])
    ip_range.tenant_id = UUID(str(data["tenant_id"])) if data.get("tenant_id") else None
    ip_range.description = data.get("description", "")
    ip_range.custom_fields = data.get("custom_fields", {})
    ip_range.tags = [UUID(str(t)) for t in data.get("tags", [])]
    return ip_range


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


class GetIPRangeHandler(QueryHandler[IPRangeDTO]):
    def __init__(self, read_model_repo: IPRangeReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> IPRangeDTO:
        data = await self._repo.find_by_id(query.range_id)
        if data is None:
            raise EntityNotFoundError(f"IPRange {query.range_id} not found")
        return IPRangeDTO(**data)


class ListIPRangesHandler(QueryHandler[tuple[list[IPRangeDTO], int]]):
    def __init__(self, read_model_repo: IPRangeReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[IPRangeDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = build_common_filters(query)
        if query.vrf_id is not None:
            filters.append(FilterParam(field="vrf_id", operator=FilterOperator.EQ, value=str(query.vrf_id)))
        if query.status is not None:
            filters.append(FilterParam(field="status", operator=FilterOperator.EQ, value=query.status))
        if query.tenant_id is not None:
            filters.append(FilterParam(field="tenant_id", operator=FilterOperator.EQ, value=str(query.tenant_id)))
        items, total = await self._repo.find_all(
            offset=query.offset,
            limit=query.limit,
            filters=filters or None,
            sort_params=sort_params,
            tag_slugs=tag_slugs,
            custom_field_filters=custom_field_filters,
        )
        return [IPRangeDTO(**item) for item in items], total


class GetIPRangeUtilizationHandler(QueryHandler[float]):
    def __init__(
        self,
        range_repo: IPRangeReadModelRepository,
        ip_repo: IPAddressReadModelRepository,
    ) -> None:
        self._range_repo = range_repo
        self._ip_repo = ip_repo
        self._service = IPRangeUtilizationService()

    async def handle(self, query: Query) -> float:
        data = await self._range_repo.find_by_id(query.range_id)
        if data is None:
            raise EntityNotFoundError(f"IPRange {query.range_id} not found")
        ip_range = _reconstruct_ip_range(data)
        ips_data = await self._ip_repo.find_ips_in_range(data["start_address"], data["end_address"], data.get("vrf_id"))
        used_addresses = [reconstruct_ip(ip) for ip in ips_data]
        return self._service.calculate(ip_range, used_addresses)
