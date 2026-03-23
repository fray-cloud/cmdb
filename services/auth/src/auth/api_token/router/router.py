from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from shared.api.pagination import OffsetParams
from shared.cqrs.bus import CommandBus, QueryBus
from sqlalchemy.ext.asyncio import AsyncSession

from auth.api_token.command.commands import CreateAPITokenCommand, RevokeAPITokenCommand
from auth.api_token.command.handlers import CreateAPITokenHandler, RevokeAPITokenHandler
from auth.api_token.infra.repository import PostgresAPITokenRepository
from auth.api_token.query.handlers import ListAPITokensHandler
from auth.api_token.query.queries import ListAPITokensQuery
from auth.api_token.router.schemas import APITokenListResponse, APITokenResponse, CreateAPITokenRequest
from auth.shared.dependencies import get_current_user

router = APIRouter(prefix="/api-tokens", tags=["api-tokens"])


def _get_session(request: Request) -> AsyncSession:
    return request.app.state.database.session()


def _get_command_bus(request: Request) -> CommandBus:
    session = _get_session(request)
    token_repo = PostgresAPITokenRepository(session)

    bus = CommandBus()
    bus.register(
        CreateAPITokenCommand,
        CreateAPITokenHandler(token_repo, request.app.state.event_producer),
    )
    bus.register(
        RevokeAPITokenCommand,
        RevokeAPITokenHandler(token_repo, request.app.state.event_producer),
    )
    return bus


def _get_query_bus(request: Request) -> QueryBus:
    session = _get_session(request)
    token_repo = PostgresAPITokenRepository(session)

    bus = QueryBus()
    bus.register(ListAPITokensQuery, ListAPITokensHandler(token_repo))
    return bus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=APITokenResponse,
)
async def create_api_token(
    body: CreateAPITokenRequest,
    current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> APITokenResponse:
    result = await command_bus.dispatch(
        CreateAPITokenCommand(
            user_id=current_user["user_id"],
            tenant_id=current_user["tenant_id"],
            description=body.description,
            scopes=body.scopes,
            expires_at=body.expires_at,
            allowed_ips=body.allowed_ips,
        )
    )
    return APITokenResponse(**result.model_dump())


@router.get("", response_model=APITokenListResponse)
async def list_api_tokens(
    current_user: dict = Depends(get_current_user),  # noqa: B008
    params: OffsetParams = Depends(),  # noqa: B008
    query_bus: QueryBus = Depends(_get_query_bus),  # noqa: B008
) -> APITokenListResponse:
    items, total = await query_bus.dispatch(
        ListAPITokensQuery(
            user_id=current_user["user_id"],
            offset=params.offset,
            limit=params.limit,
        )
    )
    return APITokenListResponse(
        items=[APITokenResponse(**i.model_dump()) for i in items],
        total=total,
        offset=params.offset,
        limit=params.limit,
    )


@router.delete(
    "/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_api_token(
    token_id: UUID,
    _current_user: dict = Depends(get_current_user),  # noqa: B008
    command_bus: CommandBus = Depends(_get_command_bus),  # noqa: B008
) -> None:
    await command_bus.dispatch(RevokeAPITokenCommand(token_id=token_id))
