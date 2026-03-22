from enum import StrEnum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Select


class FilterOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    CONTAINS = "contains"
    STARTSWITH = "startswith"
    ILIKE = "ilike"


class FilterParam(BaseModel):
    field: str
    operator: FilterOperator = FilterOperator.EQ
    value: Any


_OPERATOR_MAP = {
    FilterOperator.EQ: lambda col, val: col == val,
    FilterOperator.NEQ: lambda col, val: col != val,
    FilterOperator.GT: lambda col, val: col > val,
    FilterOperator.GTE: lambda col, val: col >= val,
    FilterOperator.LT: lambda col, val: col < val,
    FilterOperator.LTE: lambda col, val: col <= val,
    FilterOperator.IN: lambda col, val: col.in_(val),
    FilterOperator.CONTAINS: lambda col, val: col.contains(val),
    FilterOperator.STARTSWITH: lambda col, val: col.startswith(val),
    FilterOperator.ILIKE: lambda col, val: col.ilike(f"%{val}%"),
}


def apply_filters(
    query: Select,  # type: ignore[type-arg]
    model: Any,
    filters: list[FilterParam],
) -> Select:  # type: ignore[type-arg]
    for f in filters:
        column = getattr(model, f.field, None)
        if column is None:
            continue
        op_fn = _OPERATOR_MAP.get(f.operator)
        if op_fn:
            query = query.where(op_fn(column, f.value))
    return query
