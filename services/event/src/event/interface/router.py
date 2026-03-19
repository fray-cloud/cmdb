from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from event.infrastructure.changelog_repository import ChangeLogRepository
from event.infrastructure.event_repository import EventRepository
from event.interface.schemas import (
    ChangeLogListResponse,
    ChangeLogResponse,
    EventListResponse,
    StoredEventResponse,
)
from shared.api.pagination import OffsetParams

router = APIRouter(tags=["events"])


def _get_session(request: Request) -> AsyncSession:
    return request.app.state.database.session()


# =============================================================================
# Events (Event Stream)
# =============================================================================


@router.get("/events/stream/{aggregate_id}", response_model=list[StoredEventResponse])
async def get_event_stream(
    aggregate_id: UUID,
    from_version: int = Query(0, ge=0),
    session: AsyncSession = Depends(_get_session),  # noqa: B008
) -> list[StoredEventResponse]:
    repo = EventRepository(session)
    events = await repo.find_by_aggregate(aggregate_id, from_version=from_version)
    return [
        StoredEventResponse(
            id=e.id,
            aggregate_id=e.aggregate_id,
            aggregate_type=e.aggregate_type,
            event_type=e.event_type,
            version=e.version,
            payload=e.payload,
            timestamp=e.timestamp,
        )
        for e in events
    ]


@router.get("/events", response_model=EventListResponse)
async def list_events(
    aggregate_type: str | None = None,
    from_timestamp: datetime | None = None,
    params: OffsetParams = Depends(),  # noqa: B008
    session: AsyncSession = Depends(_get_session),  # noqa: B008
) -> EventListResponse:
    repo = EventRepository(session)
    events, total = await repo.find_all(
        aggregate_type=aggregate_type,
        from_timestamp=from_timestamp,
        offset=params.offset,
        limit=params.limit,
    )
    return EventListResponse(
        items=[
            StoredEventResponse(
                id=e.id,
                aggregate_id=e.aggregate_id,
                aggregate_type=e.aggregate_type,
                event_type=e.event_type,
                version=e.version,
                payload=e.payload,
                timestamp=e.timestamp,
            )
            for e in events
        ],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


# =============================================================================
# Change Log
# =============================================================================


@router.get("/changelog/{aggregate_id}", response_model=ChangeLogListResponse)
async def get_changelog_by_aggregate(
    aggregate_id: UUID,
    params: OffsetParams = Depends(),  # noqa: B008
    session: AsyncSession = Depends(_get_session),  # noqa: B008
) -> ChangeLogListResponse:
    repo = ChangeLogRepository(session)
    entries, total = await repo.find_by_aggregate(aggregate_id, offset=params.offset, limit=params.limit)
    return ChangeLogListResponse(
        items=[
            ChangeLogResponse(
                id=e.id,
                aggregate_id=e.aggregate_id,
                aggregate_type=e.aggregate_type,
                action=e.action,
                event_type=e.event_type,
                user_id=e.user_id,
                tenant_id=e.tenant_id,
                correlation_id=e.correlation_id,
                timestamp=e.timestamp,
            )
            for e in entries
        ],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.get("/changelog", response_model=ChangeLogListResponse)
async def list_changelog(
    aggregate_type: str | None = None,
    tenant_id: UUID | None = None,
    user_id: UUID | None = None,
    from_timestamp: datetime | None = None,
    params: OffsetParams = Depends(),  # noqa: B008
    session: AsyncSession = Depends(_get_session),  # noqa: B008
) -> ChangeLogListResponse:
    repo = ChangeLogRepository(session)
    entries, total = await repo.find_all(
        aggregate_type=aggregate_type,
        tenant_id=tenant_id,
        user_id=user_id,
        from_timestamp=from_timestamp,
        offset=params.offset,
        limit=params.limit,
    )
    return ChangeLogListResponse(
        items=[
            ChangeLogResponse(
                id=e.id,
                aggregate_id=e.aggregate_id,
                aggregate_type=e.aggregate_type,
                action=e.action,
                event_type=e.event_type,
                user_id=e.user_id,
                tenant_id=e.tenant_id,
                correlation_id=e.correlation_id,
                timestamp=e.timestamp,
            )
            for e in entries
        ],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )
