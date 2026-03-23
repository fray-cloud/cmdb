from pydantic import BaseModel


class ImportRowErrorSchema(BaseModel):
    row: int
    field: str
    error: str


class ImportResponse(BaseModel):
    imported: int
    failed: int
    errors: list[ImportRowErrorSchema]
