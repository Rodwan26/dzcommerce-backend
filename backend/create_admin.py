from app.core.db import async_session_factory
from app.models import User, Tenant
from app.core.security import hash_password
import asyncio


async def main():
    async with async_session_factory() as db:
        tenant = Tenant(
            name="Default Tenant",
            slug="default-tenant",
            status="active",
        )
        db.add(tenant)
        await db.flush()

        admin = User(
            email="admin@dz.com",
            password_hash=hash_password("admin123"),
            name="Admin",
            role="owner",
            tenant_id=tenant.id,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print("Admin created: admin@dz.com / admin123")


asyncio.run(main())
