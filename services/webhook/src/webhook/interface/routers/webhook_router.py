import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus
from webhook.application.command_handlers import CreateWebhookHandler, DeleteWebhookHandler, UpdateWebhookHandler
from webhook.application.commands import CreateWebhookCommand, DeleteWebhookCommand, UpdateWebhookCommand
from webhook.application.queries import GetWebhookQuery, ListWebhookLogsQuery, ListWebhooksQuery
from webhook.application.query_handlers import GetWebhookHandler, ListWebhookLogsHandler, ListWebhooksHandler
from webhook.domain.webhook_log import WebhookEventLog
from webhook.infrastructure.repository import PostgresWebhookLogRepository, PostgresWebhookRepository
from webhook.interface.schemas import (
    CreateWebhookRequest,
    UpdateWebhookRequest,
    WebhookListResponse,
    WebhookLogListResponse,
    WebhookLogResponse,
    WebhookResponse,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _get_command_bus(request: Request) -> CommandBus:
    database = request.app.state.database
    repo = PostgresWebhookRepository(database)
    cache = getattr(request.app.state, "webhook_cache", None)
    bus = CommandBus()
    bus.register(CreateWebhookCommand, CreateWebhookHandler(repo, cache))
    bus.register(UpdateWebhookCommand, UpdateWebhookHandler(repo, cache))
    bus.register(DeleteWebhookCommand, DeleteWebhookHandler(repo, cache))
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    database = request.app.state.database
    repo = PostgresWebhookRepository(database)
    log_repo = PostgresWebhookLogRepository(database)
    bus = QueryBus()
    bus.register(GetWebhookQuery, GetWebhookHandler(repo))
    bus.register(ListWebhooksQuery, ListWebhooksHandler(repo))
    bus.register(ListWebhookLogsQuery, ListWebhookLogsHandler(log_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WebhookResponse,
)
async def create_webhook(
    body: CreateWebhookRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> WebhookResponse:
    webhook_id = await command_bus.dispatch(CreateWebhookCommand(**body.model_dump()))
    dto = await query_bus.dispatch(GetWebhookQuery(webhook_id=webhook_id))
    return WebhookResponse(**dto.model_dump(exclude={"secret"}))


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    params: OffsetParams = Depends(),  # noqa: B008
    is_active: bool | None = None,
    tenant_id: UUID | None = None,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> WebhookListResponse:
    items, total = await query_bus.dispatch(
        ListWebhooksQuery(
            offset=params.offset,
            limit=params.limit,
            is_active=is_active,
            tenant_id=tenant_id,
        )
    )
    return WebhookListResponse(
        items=[WebhookResponse(**i.model_dump(exclude={"secret"})) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> WebhookResponse:
    dto = await query_bus.dispatch(GetWebhookQuery(webhook_id=webhook_id))
    return WebhookResponse(**dto.model_dump(exclude={"secret"}))


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    body: UpdateWebhookRequest,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> WebhookResponse:
    await command_bus.dispatch(UpdateWebhookCommand(webhook_id=webhook_id, **body.model_dump(exclude_unset=True)))
    dto = await query_bus.dispatch(GetWebhookQuery(webhook_id=webhook_id))
    return WebhookResponse(**dto.model_dump(exclude={"secret"}))


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(DeleteWebhookCommand(webhook_id=webhook_id))


@router.get("/{webhook_id}/logs", response_model=WebhookLogListResponse)
async def list_webhook_logs(
    webhook_id: UUID,
    params: OffsetParams = Depends(),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> WebhookLogListResponse:
    items, total = await query_bus.dispatch(
        ListWebhookLogsQuery(
            webhook_id=webhook_id,
            offset=params.offset,
            limit=params.limit,
        )
    )
    return WebhookLogListResponse(
        items=[WebhookLogResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.post("/{webhook_id}/test", response_model=WebhookLogResponse)
async def test_webhook(
    webhook_id: UUID,
    request: Request,
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> WebhookLogResponse:
    dto = await query_bus.dispatch(GetWebhookQuery(webhook_id=webhook_id))
    payload = {
        "event_type": "webhook.test",
        "webhook_id": str(webhook_id),
        "timestamp": datetime.now().isoformat(),
        "message": "Test event from CMDB Webhook Service",
    }

    delivery_service = request.app.state.delivery_service
    result = await delivery_service.deliver(
        url=dto.url,
        payload=payload,
        secret=dto.secret,
        event_type="webhook.test",
        webhook_id=str(webhook_id),
    )

    # Log the test delivery
    log = WebhookEventLog(
        webhook_id=webhook_id,
        event_type="webhook.test",
        event_id="test",
        request_url=dto.url,
        request_body=json.dumps(payload),
        response_status=result.status_code,
        response_body=result.response_body,
        error_message=result.error_message,
        attempt=1,
        duration_ms=result.duration_ms,
        success=result.success,
    )

    database = request.app.state.database
    log_repo = PostgresWebhookLogRepository(database)
    await log_repo.save(log)

    return WebhookLogResponse(
        id=log.id,
        webhook_id=log.webhook_id,
        event_type=log.event_type,
        event_id=log.event_id,
        request_url=log.request_url,
        response_status=log.response_status,
        error_message=log.error_message,
        attempt=log.attempt,
        duration_ms=log.duration_ms,
        success=log.success,
        created_at=log.created_at,
    )
