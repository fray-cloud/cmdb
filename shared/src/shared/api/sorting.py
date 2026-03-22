from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy import Select, asc, desc


class SortParam(BaseModel):
    field: str
    direction: Literal["asc", "desc"] = "asc"


def apply_sorting(
    query: Select,  # type: ignore[type-arg]
    model: Any,
    sort_params: list[SortParam],
) -> Select:  # type: ignore[type-arg]
    for param in sort_params:
        column = getattr(model, param.field, None)
        if column is None:
            continue
        order_fn = asc if param.direction == "asc" else desc
        query = query.order_by(order_fn(column))
    return query
