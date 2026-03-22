from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared.domain.exceptions import (
    AuthorizationError,
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    EntityNotFoundError,
    InfrastructureError,
    ValidationError,
)


class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str | None = None
    extensions: dict[str, Any] = {}


EXCEPTION_STATUS_MAP: dict[type[DomainError], int] = {
    EntityNotFoundError: 404,
    BusinessRuleViolationError: 422,
    AuthorizationError: 403,
    ConflictError: 409,
    ValidationError: 400,
    InfrastructureError: 503,
}


def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    status = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    problem = ProblemDetail(
        type=f"urn:cmdb:error:{exc.code}",
        title=type(exc).__name__,
        status=status,
        detail=exc.message,
        instance=str(request.url),
        extensions=exc.details,
    )
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(exclude_none=True),
    )
