"""Global search PostgreSQL repository — full-text search across all IPAM read models."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy import func, literal_column, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from ipam.asn.infra import ASNReadModel
from ipam.fhrp_group.infra import FHRPGroupReadModel
from ipam.ip_address.infra import IPAddressReadModel
from ipam.ip_range.infra import IPRangeReadModel
from ipam.prefix.infra import PrefixReadModel
from ipam.rir.infra import RIRReadModel
from ipam.route_target.infra import RouteTargetReadModel
from ipam.service_entity.infra import ServiceReadModel
from ipam.shared.search.query import GlobalSearchRepository
from ipam.vlan.infra import VLANReadModel
from ipam.vlan_group.infra import VLANGroupReadModel
from ipam.vrf.infra import VRFReadModel

SEARCHABLE_MODELS: list[tuple[str, Any, Any]] = [
    ("prefix", PrefixReadModel, PrefixReadModel.network),
    ("ip_address", IPAddressReadModel, IPAddressReadModel.address),
    ("vrf", VRFReadModel, VRFReadModel.name),
    ("vlan", VLANReadModel, VLANReadModel.name),
    ("ip_range", IPRangeReadModel, IPRangeReadModel.start_address),
    ("rir", RIRReadModel, RIRReadModel.name),
    ("asn", ASNReadModel, func.cast(ASNReadModel.asn, sa.Text)),
    ("fhrp_group", FHRPGroupReadModel, FHRPGroupReadModel.name),
    ("route_target", RouteTargetReadModel, RouteTargetReadModel.name),
    ("vlan_group", VLANGroupReadModel, VLANGroupReadModel.name),
    ("service", ServiceReadModel, ServiceReadModel.name),
]


class PostgresGlobalSearchRepository(GlobalSearchRepository):
    """PostgreSQL-backed global search using tsvector full-text search."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        query: str,
        entity_types: list[str] | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        tsquery = func.plainto_tsquery("simple", query)

        subqueries = []
        for entity_type, model_cls, display_col in SEARCHABLE_MODELS:
            if entity_types and entity_type not in entity_types:
                continue
            stmt = select(
                literal_column(f"'{entity_type}'").label("entity_type"),
                model_cls.id.label("entity_id"),
                display_col.label("display_text"),
                model_cls.description.label("description"),
                func.ts_rank(model_cls.search_vector, tsquery).label("relevance"),
            ).where(
                model_cls.search_vector.op("@@")(tsquery),
                model_cls.is_deleted == sa.false(),
            )
            subqueries.append(stmt)

        if not subqueries:
            return [], 0

        union_stmt = union_all(*subqueries)
        union_sub = union_stmt.subquery()

        count_stmt = select(func.count()).select_from(union_sub)
        total = (await self._session.execute(count_stmt)).scalar_one()

        result_stmt = select(union_sub).order_by(union_sub.c.relevance.desc()).offset(offset).limit(limit)
        result = await self._session.execute(result_stmt)
        rows = [
            {
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "display_text": str(row.display_text),
                "description": row.description or "",
                "relevance": float(row.relevance),
            }
            for row in result
        ]
        return rows, total
