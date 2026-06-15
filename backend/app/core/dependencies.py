import uuid

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.models.user import User, UserRole


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    user_id: uuid.UUID | None = request.state.user_id
    if not user_id:
        raise UnauthorizedException()
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
        )
    )
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise UnauthorizedException("User not found or inactive")
    return db_user


def require_role(*roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(f"Requires one of: {', '.join(roles)}")
        return current_user
    return role_checker


async def require_owner(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.OWNER.value:
        raise ForbiddenException("Requires owner role")
    return current_user


async def get_tenant_id(request: Request, current_user: User = Depends(get_current_user)) -> uuid.UUID:
    tenant_id: uuid.UUID | None = request.state.tenant_id
    if not tenant_id:
        raise ForbiddenException("No tenant associated")
    return tenant_id
