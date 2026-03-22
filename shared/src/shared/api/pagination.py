import base64
import json
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class OffsetParams(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=200)


class CursorParams(BaseModel):
    cursor: str | None = None
    limit: int = Field(50, ge=1, le=200)


class OffsetPage(BaseModel, Generic[T]):  # noqa: UP046
    items: list[T]
    total: int
    offset: int
    limit: int


class CursorPage(BaseModel, Generic[T]):  # noqa: UP046
    items: list[T]
    next_cursor: str | None = None
    previous_cursor: str | None = None
    limit: int


def encode_cursor(values: dict[str, Any]) -> str:
    payload = json.dumps(values, default=str).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decode_cursor(cursor: str) -> dict[str, Any]:
    payload = base64.urlsafe_b64decode(cursor.encode("ascii"))
    return json.loads(payload)
