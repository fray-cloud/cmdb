from datetime import datetime
from uuid import UUID

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from event.infrastructure.models import ChangeLogModel


class ChangeLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entry_data: dict) -> ChangeLogModel:
        model = ChangeLogModel(
            aggregate_id=entry_data["aggregate_id"],
            aggregate_type=entry_data["aggregate_type"],
            action=entry_data["action"],
            event_type=entry_data["event_type"],
            user_id=entry_data.get("user_id"),
            tenant_id=entry_data.get("tenant_id"),
            correlation_id=entry_data.get("correlation_id"),
            timestamp=entry_data.get("timestamp", datetime.now()),
        )
        self._session.add(model)
        await self._session.commit()
        return model

    async def find_by_aggregate(
        self,
        aggregate_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[ChangeLogModel], int]:
        count_stmt = (
            select(sa_func.count()).select_from(ChangeLogModel).where(ChangeLogModel.aggregate_id == aggregate_id)
        )
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(ChangeLogModel)
            .where(ChangeLogModel.aggregate_id == aggregate_id)
            .order_by(ChangeLogModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def find_all(
        self,
        *,
        aggregate_type: str | None = None,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        from_timestamp: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[ChangeLogModel], int]:
        base = select(ChangeLogModel)
        count_base = select(sa_func.count()).select_from(ChangeLogModel)

        if aggregate_type:
            base = base.where(ChangeLogModel.aggregate_type == aggregate_type)
            count_base = count_base.where(ChangeLogModel.aggregate_type == aggregate_type)
        if tenant_id:
            base = base.where(ChangeLogModel.tenant_id == tenant_id)
            count_base = count_base.where(ChangeLogModel.tenant_id == tenant_id)
        if user_id:
            base = base.where(ChangeLogModel.user_id == user_id)
            count_base = count_base.where(ChangeLogModel.user_id == user_id)
        if from_timestamp:
            base = base.where(ChangeLogModel.timestamp >= from_timestamp)
            count_base = count_base.where(ChangeLogModel.timestamp >= from_timestamp)

        total = (await self._session.execute(count_base)).scalar_one()

        stmt = base.order_by(ChangeLogModel.timestamp.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total
