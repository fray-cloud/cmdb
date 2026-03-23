"""Shared REST API schemas for bulk operations and status changes."""

from uuid import UUID

from pydantic import BaseModel


class ChangeStatusRequest(BaseModel):
    status: str


class BulkCreateResponse(BaseModel):
    ids: list[UUID]
    count: int


class BulkDeleteRequest(BaseModel):
    ids: list[UUID]


class BulkUpdateResponse(BaseModel):
    updated: int


class BulkDeleteResponse(BaseModel):
    deleted: int
