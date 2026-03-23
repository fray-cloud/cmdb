from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipam.shared.import_export.infra.models import ExportTemplateModel


class TemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: dict) -> ExportTemplateModel:
        model = ExportTemplateModel(**data)
        self._session.add(model)
        await self._session.flush()
        return model

    async def find_by_id(self, template_id: UUID) -> ExportTemplateModel | None:
        return await self._session.get(ExportTemplateModel, template_id)

    async def find_all(self, entity_type: str | None = None) -> list[ExportTemplateModel]:
        stmt = select(ExportTemplateModel)
        if entity_type is not None:
            stmt = stmt.where(ExportTemplateModel.entity_type == entity_type)
        stmt = stmt.order_by(ExportTemplateModel.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, template_id: UUID) -> None:
        model = await self._session.get(ExportTemplateModel, template_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
