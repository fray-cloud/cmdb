from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select

from webhook.domain.repository import WebhookLogRepository, WebhookRepository
from webhook.domain.webhook import Webhook
from webhook.domain.webhook_log import WebhookEventLog
from webhook.infrastructure.database import Database
from webhook.infrastructure.models import WebhookEventLogModel, WebhookModel


class PostgresWebhookRepository(WebhookRepository):
    def __init__(self, database: Database) -> None:
        self._db = database

    async def find_by_id(self, webhook_id: UUID) -> Webhook | None:
        async with self._db.session() as session:
            model = await session.get(WebhookModel, webhook_id)
            if model is None:
                return None
            return self._to_domain(model)

    async def find_all(
        self, *, offset: int = 0, limit: int = 50, is_active: bool | None = None, tenant_id: UUID | None = None
    ) -> tuple[list[Webhook], int]:
        async with self._db.session() as session:
            stmt = select(WebhookModel)
            count_stmt = select(func.count()).select_from(WebhookModel)

            if is_active is not None:
                stmt = stmt.where(WebhookModel.is_active == is_active)
                count_stmt = count_stmt.where(WebhookModel.is_active == is_active)
            if tenant_id is not None:
                stmt = stmt.where(WebhookModel.tenant_id == tenant_id)
                count_stmt = count_stmt.where(WebhookModel.tenant_id == tenant_id)

            stmt = stmt.order_by(WebhookModel.created_at.desc()).offset(offset).limit(limit)

            result = await session.execute(stmt)
            models = result.scalars().all()

            count_result = await session.execute(count_stmt)
            total = count_result.scalar_one()

            return [self._to_domain(m) for m in models], total

    async def find_active_for_tenant(self, tenant_id: UUID | None) -> list[Webhook]:
        async with self._db.session() as session:
            stmt = select(WebhookModel).where(WebhookModel.is_active.is_(True))

            if tenant_id is not None:
                stmt = stmt.where((WebhookModel.tenant_id == tenant_id) | (WebhookModel.tenant_id.is_(None)))

            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    async def save(self, webhook: Webhook) -> None:
        async with self._db.session() as session:
            model = self._to_model(webhook)
            await session.merge(model)
            await session.commit()

    async def delete(self, webhook_id: UUID) -> None:
        async with self._db.session() as session:
            model = await session.get(WebhookModel, webhook_id)
            if model:
                await session.delete(model)
                await session.commit()

    def _to_domain(self, model: WebhookModel) -> Webhook:
        return Webhook(
            id=model.id,
            name=model.name,
            url=model.url,
            secret=model.secret,
            event_types=model.event_types,
            is_active=model.is_active,
            tenant_id=model.tenant_id,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, webhook: Webhook) -> WebhookModel:
        return WebhookModel(
            id=webhook.id,
            name=webhook.name,
            url=webhook.url,
            secret=webhook.secret,
            event_types=webhook.event_types,
            is_active=webhook.is_active,
            tenant_id=webhook.tenant_id,
            description=webhook.description,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
        )


class PostgresWebhookLogRepository(WebhookLogRepository):
    def __init__(self, database: Database) -> None:
        self._db = database

    async def save(self, log: WebhookEventLog) -> None:
        async with self._db.session() as session:
            model = WebhookEventLogModel(
                id=log.id,
                webhook_id=log.webhook_id,
                event_type=log.event_type,
                event_id=log.event_id,
                request_url=log.request_url,
                request_body=log.request_body,
                response_status=log.response_status,
                response_body=log.response_body,
                error_message=log.error_message,
                attempt=log.attempt,
                duration_ms=log.duration_ms,
                success=log.success,
                created_at=log.created_at,
            )
            session.add(model)
            await session.commit()

    async def find_by_webhook(
        self, webhook_id: UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[list[WebhookEventLog], int]:
        async with self._db.session() as session:
            stmt = (
                select(WebhookEventLogModel)
                .where(WebhookEventLogModel.webhook_id == webhook_id)
                .order_by(WebhookEventLogModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            count_stmt = (
                select(func.count())
                .select_from(WebhookEventLogModel)
                .where(WebhookEventLogModel.webhook_id == webhook_id)
            )

            result = await session.execute(stmt)
            models = result.scalars().all()

            count_result = await session.execute(count_stmt)
            total = count_result.scalar_one()

            return [self._to_domain(m) for m in models], total

    def _to_domain(self, model: WebhookEventLogModel) -> WebhookEventLog:
        return WebhookEventLog(
            id=model.id,
            webhook_id=model.webhook_id,
            event_type=model.event_type,
            event_id=model.event_id,
            request_url=model.request_url,
            request_body=model.request_body,
            response_status=model.response_status,
            response_body=model.response_body,
            error_message=model.error_message,
            attempt=model.attempt,
            duration_ms=model.duration_ms,
            success=model.success,
            created_at=model.created_at,
        )
