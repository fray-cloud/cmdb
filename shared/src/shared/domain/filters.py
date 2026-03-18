from typing import Any

from sqlalchemy import Select, select

from shared.domain.models import TagAssignmentModel, TagModel


def filter_by_custom_field(
    query: Select,  # type: ignore[type-arg]
    column: Any,
    field_name: str,
    value: Any,
) -> Select:  # type: ignore[type-arg]
    return query.where(column[field_name].astext == str(value))


def filter_by_tag_slugs(
    query: Select,  # type: ignore[type-arg]
    content_type: str,
    object_id_column: Any,
    tag_slugs: list[str],
) -> Select:  # type: ignore[type-arg]
    subquery = (
        select(TagAssignmentModel.object_id)
        .join(TagModel, TagAssignmentModel.tag_id == TagModel.id)
        .where(
            TagAssignmentModel.content_type == content_type,
            TagModel.slug.in_(tag_slugs),
        )
    )
    return query.where(object_id_column.in_(subquery))
