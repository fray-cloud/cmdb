"""Seed default roles and superadmin user.

Usage:
    uv run --package cmdb-auth python -m auth.infrastructure.seed
"""

import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from auth.domain.permission import Permission
from auth.domain.role import Role
from auth.domain.user import User
from auth.infrastructure.role_repository import PostgresRoleRepository
from auth.infrastructure.security import BcryptPasswordService
from auth.infrastructure.user_repository import PostgresUserRepository

DEFAULT_ROLES = [
    {
        "name": "superadmin",
        "description": "Full system access",
        "is_system": True,
        "permissions": [
            {"object_type": "ipam", "actions": ["view", "add", "change", "delete"]},
            {"object_type": "dcim", "actions": ["view", "add", "change", "delete"]},
            {"object_type": "circuit", "actions": ["view", "add", "change", "delete"]},
            {"object_type": "virtualization", "actions": ["view", "add", "change", "delete"]},
            {"object_type": "tenant", "actions": ["view", "add", "change", "delete"]},
            {"object_type": "auth", "actions": ["view", "add", "change", "delete"]},
        ],
    },
    {
        "name": "admin",
        "description": "Administrative access",
        "is_system": True,
        "permissions": [
            {"object_type": "ipam", "actions": ["view", "add", "change", "delete"]},
            {"object_type": "dcim", "actions": ["view", "add", "change", "delete"]},
            {"object_type": "auth", "actions": ["view", "add", "change"]},
        ],
    },
    {
        "name": "operator",
        "description": "Operational access",
        "is_system": True,
        "permissions": [
            {"object_type": "ipam", "actions": ["view", "add", "change"]},
            {"object_type": "dcim", "actions": ["view", "add", "change"]},
        ],
    },
    {
        "name": "viewer",
        "description": "Read-only access",
        "is_system": True,
        "permissions": [
            {"object_type": "ipam", "actions": ["view"]},
            {"object_type": "dcim", "actions": ["view"]},
            {"object_type": "circuit", "actions": ["view"]},
            {"object_type": "virtualization", "actions": ["view"]},
        ],
    },
]


async def seed(database_url: str, tenant_id: str) -> None:
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        role_repo = PostgresRoleRepository(session)
        user_repo = PostgresUserRepository(session)
        password_service = BcryptPasswordService()

        tenant_uuid = __import__("uuid").UUID(tenant_id)
        superadmin_role_id = None

        for role_def in DEFAULT_ROLES:
            existing = await role_repo.find_by_name(role_def["name"], tenant_uuid)
            if existing:
                print(f"  Role '{role_def['name']}' already exists, skipping")
                if role_def["name"] == "superadmin":
                    superadmin_role_id = existing.id
                continue

            permissions = [Permission(**p) for p in role_def["permissions"]]
            role = Role(
                name=role_def["name"],
                tenant_id=tenant_uuid,
                description=role_def["description"],
                permissions=permissions,
                is_system=role_def["is_system"],
            )
            await role_repo.save(role)
            print(f"  Created role: {role_def['name']}")
            if role_def["name"] == "superadmin":
                superadmin_role_id = role.id

        # Create superadmin user
        admin_email = os.getenv("ADMIN_EMAIL", "admin@cmdb.local")
        admin_password = os.getenv("ADMIN_PASSWORD", "changeme123")

        existing_user = await user_repo.find_by_email(admin_email, tenant_uuid)
        if existing_user:
            print(f"  Superadmin user '{admin_email}' already exists, skipping")
        else:
            password_hash = password_service.hash(admin_password)
            user = User.create(
                email=admin_email,
                password_hash=password_hash,
                tenant_id=tenant_uuid,
                display_name="System Admin",
            )
            if superadmin_role_id:
                user.role_ids.append(superadmin_role_id)
            await user_repo.save(user)
            print(f"  Created superadmin user: {admin_email}")

    await engine.dispose()
    print("Seed completed!")


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://cmdb:cmdb@localhost:5432/cmdb_auth")
    tenant_id = os.getenv("SEED_TENANT_ID", "00000000-0000-0000-0000-000000000001")
    print(f"Seeding auth database: {database_url}")
    asyncio.run(seed(database_url, tenant_id))


if __name__ == "__main__":
    main()
