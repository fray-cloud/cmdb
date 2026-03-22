from uuid import UUID

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from event.infrastructure.models import JournalEntryModel


class JournalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: dict) -> JournalEntryModel:
        model = JournalEntryModel(**data)
        self._session.add(model)
        await self._session.commit()
        return model

    async def find_by_id(self, entry_id: UUID) -> JournalEntryModel | None:
        return await self._session.get(JournalEntryModel, entry_id)

    async def find_all(
        self,
        *,
        object_type: str | None = None,
        object_id: UUID | None = None,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        entry_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[JournalEntryModel], int]:
        base = select(JournalEntryModel)
        count_base = select(sa_func.count()).select_from(JournalEntryModel)

        if object_type:
            base = base.where(JournalEntryModel.object_type == object_type)
            count_base = count_base.where(JournalEntryModel.object_type == object_type)
        if object_id:
            base = base.where(JournalEntryModel.object_id == object_id)
            count_base = count_base.where(JournalEntryModel.object_id == object_id)
        if tenant_id:
            base = base.where(JournalEntryModel.tenant_id == tenant_id)
            count_base = count_base.where(JournalEntryModel.tenant_id == tenant_id)
        if user_id:
            base = base.where(JournalEntryModel.user_id == user_id)
            count_base = count_base.where(JournalEntryModel.user_id == user_id)
        if entry_type:
            base = base.where(JournalEntryModel.entry_type == entry_type)
            count_base = count_base.where(JournalEntryModel.entry_type == entry_type)

        total = (await self._session.execute(count_base)).scalar_one()

        stmt = base.order_by(JournalEntryModel.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def delete(self, entry_id: UUID) -> None:
        model = await self._session.get(JournalEntryModel, entry_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.commit()
