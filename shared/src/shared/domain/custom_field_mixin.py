from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class CustomFieldMixin:
    custom_field_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    @declared_attr
    @classmethod
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_custom_fields",  # type: ignore[attr-defined]
                "custom_field_data",
                postgresql_using="gin",
            ),
        )
