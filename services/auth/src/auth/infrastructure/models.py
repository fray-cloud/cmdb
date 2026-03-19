from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime as SADateTime
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class AuthBase(DeclarativeBase):
    pass


class UserRoleModel(AuthBase):
    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class UserGroupModel(AuthBase):
    __tablename__ = "user_groups"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)


class GroupRoleModel(AuthBase):
    __tablename__ = "group_roles"

    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class UserModel(AuthBase):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", "tenant_id", name="uq_user_email_tenant"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    tenant_id: Mapped[UUID] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    roles: Mapped[list["RoleModel"]] = relationship(secondary="user_roles", lazy="selectin", viewonly=True)
    groups: Mapped[list["GroupModel"]] = relationship(secondary="user_groups", lazy="selectin", viewonly=True)


class RoleModel(AuthBase):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("name", "tenant_id", name="uq_role_name_tenant"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    tenant_id: Mapped[UUID] = mapped_column(index=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    permissions: Mapped[list] = mapped_column(JSONB, default=list)
    is_system: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GroupModel(AuthBase):
    __tablename__ = "groups"
    __table_args__ = (UniqueConstraint("name", "tenant_id", name="uq_group_name_tenant"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    tenant_id: Mapped[UUID] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    roles: Mapped[list["RoleModel"]] = relationship(secondary="group_roles", lazy="selectin", viewonly=True)


class APITokenModel(AuthBase):
    __tablename__ = "api_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tenant_id: Mapped[UUID] = mapped_column(index=True)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    scopes: Mapped[list] = mapped_column(JSONB, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)
    allowed_ips: Mapped[list] = mapped_column(JSONB, default=list)
    last_used_at: Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), server_default=func.now())
