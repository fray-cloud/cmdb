"""User aggregate defining identity, status, and role/group membership."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field
from shared.domain.entity import Entity
from shared.domain.exceptions import BusinessRuleViolationError
from shared.event.domain_event import DomainEvent

from auth.shared.domain import RoleAssigned, RoleRemoved, UserCreated, UserLocked


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class User(Entity):
    """User aggregate root managing authentication state and role assignments."""

    email: str
    password_hash: str
    tenant_id: UUID
    status: UserStatus = UserStatus.ACTIVE
    display_name: str | None = None
    role_ids: list[UUID] = Field(default_factory=list)
    group_ids: list[UUID] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        object.__setattr__(self, "_pending_events", [])

    def collect_events(self) -> list[DomainEvent]:
        events: list[DomainEvent] = list(self._pending_events)
        self._pending_events.clear()
        return events

    @classmethod
    def create(
        cls,
        *,
        email: str,
        password_hash: str,
        tenant_id: UUID,
        display_name: str | None = None,
    ) -> "User":
        """Create a new user and emit a UserCreated domain event."""
        user = cls(
            email=email,
            password_hash=password_hash,
            tenant_id=tenant_id,
            display_name=display_name,
        )
        user._pending_events.append(
            UserCreated(
                aggregate_id=user.id,
                version=1,
                email=email,
                tenant_id=tenant_id,
            )
        )
        return user

    def change_password(self, new_hash: str) -> None:
        if self.status == UserStatus.LOCKED:
            raise BusinessRuleViolationError("Cannot change password of a locked user")
        self.password_hash = new_hash
        self.updated_at = datetime.now()

    def assign_role(self, role_id: UUID) -> None:
        if role_id in self.role_ids:
            raise BusinessRuleViolationError(f"Role {role_id} is already assigned")
        self.role_ids.append(role_id)
        self.updated_at = datetime.now()
        self._pending_events.append(RoleAssigned(aggregate_id=self.id, version=1, user_id=self.id, role_id=role_id))

    def remove_role(self, role_id: UUID) -> None:
        if role_id not in self.role_ids:
            raise BusinessRuleViolationError(f"Role {role_id} is not assigned")
        self.role_ids.remove(role_id)
        self.updated_at = datetime.now()
        self._pending_events.append(RoleRemoved(aggregate_id=self.id, version=1, user_id=self.id, role_id=role_id))

    def lock(self) -> None:
        if self.status == UserStatus.LOCKED:
            raise BusinessRuleViolationError("User is already locked")
        self.status = UserStatus.LOCKED
        self.updated_at = datetime.now()
        self._pending_events.append(UserLocked(aggregate_id=self.id, version=1))

    def activate(self) -> None:
        if self.status == UserStatus.ACTIVE:
            raise BusinessRuleViolationError("User is already active")
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.now()
