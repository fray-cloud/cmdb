from shared.cqrs.query import Query, QueryHandler
from shared.domain.exceptions import EntityNotFoundError

from tenant.application.dto import TenantDTO
from tenant.domain.repository import TenantRepository


class GetTenantHandler(QueryHandler[TenantDTO]):
    def __init__(self, repository: TenantRepository) -> None:
        self._repository = repository

    async def handle(self, query: Query) -> TenantDTO:
        tenant = await self._repository.find_by_id(query.tenant_id)
        if tenant is None:
            raise EntityNotFoundError(f"Tenant {query.tenant_id} not found")
        return TenantDTO(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            status=tenant.status,
            settings=tenant.settings.model_dump(),
            db_name=tenant.db_config.db_name if tenant.db_config else None,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )


class ListTenantsHandler(QueryHandler[tuple[list[TenantDTO], int]]):
    def __init__(self, repository: TenantRepository) -> None:
        self._repository = repository

    async def handle(self, query: Query) -> tuple[list[TenantDTO], int]:
        tenants, total = await self._repository.find_all(
            offset=query.offset,
            limit=query.limit,
        )
        items = [
            TenantDTO(
                id=t.id,
                name=t.name,
                slug=t.slug,
                status=t.status,
                settings=t.settings.model_dump(),
                db_name=t.db_config.db_name if t.db_config else None,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in tenants
        ]
        return items, total
