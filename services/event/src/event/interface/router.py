from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from event.infrastructure.changelog_repository import ChangeLogRepository
from event.infrastructure.event_repository import EventRepository
from event.infrastructure.journal_repository import JournalRepository
from event.interface.schemas import (
    ChangeLogListResponse,
    ChangeLogResponse,
    CreateJournalEntryRequest,
    EventListResponse,
    JournalEntryListResponse,
    JournalEntryResponse,
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


# =============================================================================
# Journal Entries
# =============================================================================


def _journal_response(e) -> JournalEntryResponse:  # type: ignore[no-untyped-def]
    return JournalEntryResponse(
        id=e.id,
        object_type=e.object_type,
        object_id=e.object_id,
        entry_type=e.entry_type,
        comment=e.comment,
        user_id=e.user_id,
        tenant_id=e.tenant_id,
        created_at=e.created_at,
    )


@router.post("/journal-entries", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    body: CreateJournalEntryRequest,
    request: Request,
    session: AsyncSession = Depends(_get_session),  # noqa: B008
) -> JournalEntryResponse:
    user_id_str = getattr(request.state, "user_id", None)
    user_id = UUID(user_id_str) if user_id_str else None
    tenant_id_str = request.headers.get("X-Tenant-ID")
    tenant_id = UUID(tenant_id_str) if tenant_id_str else None

    repo = JournalRepository(session)
    entry = await repo.create(
        {
            "id": uuid4(),
            "object_type": body.object_type,
            "object_id": body.object_id,
            "entry_type": body.entry_type,
            "comment": body.comment,
            "user_id": user_id,
            "tenant_id": tenant_id,
        }
    )
    return _journal_response(entry)


@router.get("/journal-entries", response_model=JournalEntryListResponse)
async def list_journal_entries(
    object_type: str | None = None,
    object_id: UUID | None = None,
    tenant_id: UUID | None = None,
    user_id: UUID | None = None,
    entry_type: str | None = None,
    params: OffsetParams = Depends(),  # noqa: B008
    session: AsyncSession = Depends(_get_session),  # noqa: B008
) -> JournalEntryListResponse:
    repo = JournalRepository(session)
    entries, total = await repo.find_all(
        object_type=object_type,
        object_id=object_id,
        tenant_id=tenant_id,
        user_id=user_id,
        entry_type=entry_type,
        offset=params.offset,
        limit=params.limit,
    )
    return JournalEntryListResponse(
        items=[_journal_response(e) for e in entries],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.delete("/journal-entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal_entry(
    entry_id: UUID,
    request: Request,
    session: AsyncSession = Depends(_get_session),  # noqa: B008
) -> None:
    repo = JournalRepository(session)
    entry = await repo.find_by_id(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"JournalEntry {entry_id} not found")

    current_user = getattr(request.state, "user_id", None)
    if entry.user_id is not None and current_user is not None and str(entry.user_id) != current_user:
        raise HTTPException(status_code=403, detail="Only the author can delete this journal entry")

    await repo.delete(entry_id)
