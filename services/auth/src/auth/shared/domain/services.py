"""Domain services for password hashing and permission checking."""

from abc import ABC, abstractmethod

from auth.group import Group
from auth.role import Role
from auth.user import User


class PasswordService(ABC):
    """Abstract interface for password hashing and verification."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Hash a plaintext password."""
        ...

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool:
        """Verify a plaintext password against a hash."""
        ...


class PermissionChecker:
    """Evaluates whether a user has a specific permission via roles and groups."""

    def has_permission(
        self,
        user: User,
        roles: list[Role],
        groups: list[Group],
        object_type: str,
        action: str,
    ) -> bool:
        all_role_ids = set(user.role_ids)
        for group in groups:
            if group.id in user.group_ids:
                all_role_ids.update(group.role_ids)

        for role in roles:
            if role.id not in all_role_ids:
                continue
            for perm in role.permissions:
                if perm.object_type == object_type and action in perm.actions:
                    return True
        return False
