from abc import ABC, abstractmethod

from auth.group.domain.group import Group
from auth.role.domain.role import Role
from auth.user.domain.user import User


class PasswordService(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool: ...


class PermissionChecker:
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
