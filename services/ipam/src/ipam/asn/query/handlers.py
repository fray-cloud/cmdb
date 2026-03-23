from shared.api.filtering import FilterOperator, FilterParam
from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from ipam.asn.query.dto import ASNDTO
from ipam.asn.query.read_model import ASNReadModelRepository
from ipam.shared.query_utils import build_common_filters


class GetASNHandler(QueryHandler[ASNDTO]):
    def __init__(self, read_model_repo: ASNReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> ASNDTO:
        data = await self._repo.find_by_id(query.asn_id)
        if data is None:
            raise EntityNotFoundError(f"ASN {query.asn_id} not found")
        return ASNDTO(**data)


class ListASNsHandler(QueryHandler[tuple[list[ASNDTO], int]]):
    def __init__(self, read_model_repo: ASNReadModelRepository) -> None:
        self._repo = read_model_repo

    async def handle(self, query: Query) -> tuple[list[ASNDTO], int]:
        filters, sort_params, tag_slugs, custom_field_filters = build_common_filters(query)
        if query.rir_id is not None:
            filters.append(FilterParam(field="rir_id", operator=FilterOperator.EQ, value=str(query.rir_id)))
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
        return [ASNDTO(**item) for item in items], total
