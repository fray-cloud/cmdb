"""Shared infrastructure query helpers — filter, sort, tag, and custom field application."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from shared.api.filtering import FilterParam, apply_filters
from shared.api.sorting import SortParam, apply_sorting
from shared.domain.filters import filter_by_custom_field
from sqlalchemy import Select


def _apply_advanced_filters(
    stmt: Select,  # type: ignore[type-arg]
    model: Any,
    *,
    filters: list[FilterParam] | None = None,
    sort_params: list[SortParam] | None = None,
    tag_slugs: list[str] | None = None,
    custom_field_filters: dict[str, str] | None = None,
) -> Select:  # type: ignore[type-arg]
    """Apply standard filters, sorting, tag slug filtering, and custom field filtering."""
    if filters:
        stmt = apply_filters(stmt, model, filters)
    if tag_slugs:
        tag_uuids = [UUID(s) if len(s) == 36 else s for s in tag_slugs]
        for tag_val in tag_uuids:
            stmt = stmt.where(model.tags.contains([str(tag_val)]))
    if custom_field_filters:
        for field_name, value in custom_field_filters.items():
            stmt = filter_by_custom_field(stmt, model.custom_fields, field_name, value)
    if sort_params:
        stmt = apply_sorting(stmt, model, sort_params)
    return stmt


def _find_all_common(
    stmt: Select,  # type: ignore[type-arg]
    model: Any,
    *,
    offset: int,
    limit: int,
    filters: list[FilterParam] | None,
    sort_params: list[SortParam] | None,
    tag_slugs: list[str] | None,
    custom_field_filters: dict[str, str] | None,
    default_order: Any,
) -> Select:  # type: ignore[type-arg]
    """Build a paginated, filtered, sorted query."""
    stmt = _apply_advanced_filters(
        stmt,
        model,
        filters=filters,
        sort_params=sort_params,
        tag_slugs=tag_slugs,
        custom_field_filters=custom_field_filters,
    )
    if not sort_params:
        stmt = stmt.order_by(default_order)
    return stmt.offset(offset).limit(limit)
