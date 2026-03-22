from datetime import datetime
from uuid import UUID

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from event.infrastructure.models import StoredEventModel


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, event_data: dict) -> StoredEventModel:
        model = StoredEventModel(
            aggregate_id=event_data["aggregate_id"],
            aggregate_type=event_data["aggregate_type"],
            event_type=event_data["event_type"],
            version=event_data["version"],
            payload=event_data["payload"],
            timestamp=event_data.get("timestamp", datetime.now()),
        )
        self._session.add(model)
        await self._session.commit()
        return model

    async def find_by_aggregate(
        self,
        aggregate_id: UUID,
        *,
        from_version: int = 0,
    ) -> list[StoredEventModel]:
        stmt = (
            select(StoredEventModel)
            .where(
                StoredEventModel.aggregate_id == aggregate_id,
                StoredEventModel.version >= from_version,
            )
            .order_by(StoredEventModel.version.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_all(
        self,
        *,
        aggregate_type: str | None = None,
        from_timestamp: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[StoredEventModel], int]:
        base = select(StoredEventModel)
        count_base = select(sa_func.count()).select_from(StoredEventModel)

        if aggregate_type:
            base = base.where(StoredEventModel.aggregate_type == aggregate_type)
            count_base = count_base.where(StoredEventModel.aggregate_type == aggregate_type)
        if from_timestamp:
            base = base.where(StoredEventModel.timestamp >= from_timestamp)
            count_base = count_base.where(StoredEventModel.timestamp >= from_timestamp)

        total = (await self._session.execute(count_base)).scalar_one()

        stmt = base.order_by(StoredEventModel.timestamp.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total
