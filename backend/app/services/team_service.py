import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictException, ForbiddenException
from app.core.security import hash_password
from app.models.user import User, UserRole


async def list_members(db: AsyncSession, tenant_id: uuid.UUID) -> list[User]:
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id).order_by(User.created_at)
    )
    return list(result.scalars().all())


async def create_member(
    db: AsyncSession, tenant_id: uuid.UUID, name: str, email: str, password: str
) -> User:
    count = await db.execute(
        select(func.count()).select_from(User).where(User.tenant_id == tenant_id)
    )
    current_count = count.scalar() or 0
    if current_count >= settings.MAX_TEAM_MEMBERS:
        raise ConflictException(
            f"Maximum of {settings.MAX_TEAM_MEMBERS} users per store reached"
        )

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise ConflictException("A user with this email already exists")

    user = User(
        tenant_id=tenant_id,
        email=email,
        password_hash=hash_password(password),
        name=name,
        role=UserRole.STAFF.value,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def delete_member(
    db: AsyncSession, tenant_id: uuid.UUID, member_id: uuid.UUID, current_user_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(User).where(User.id == member_id, User.tenant_id == tenant_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise ForbiddenException("Member not found in your store")

    if member.role == UserRole.OWNER.value:
        raise ForbiddenException("Cannot remove the store owner")

    if member.id == current_user_id:
        raise ForbiddenException("Cannot remove yourself")

    await db.delete(member)
    await db.flush()
