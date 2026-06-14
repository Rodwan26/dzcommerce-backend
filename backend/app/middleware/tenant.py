import uuid
import logging

from fastapi import Request
from sqlalchemy import select

from app.core.db import async_session_factory
from app.core.security import decode_token
from app.models.user import User

logger = logging.getLogger(__name__)


async def resolve_tenant(request: Request) -> None:
    request.state.user_id = None
    request.state.tenant_id = None

    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return

        payload = decode_token(auth_header[7:])

        user_id = payload.get("sub")
        token_version = payload.get("token_version")
        if not user_id:
            return

        async with async_session_factory() as session:
            result = await session.execute(
                select(User).where(
                    User.id == uuid.UUID(user_id),
                    User.is_active.is_(True),
                )
            )
            user = result.scalar_one_or_none()
            if not user or user.token_version != token_version:
                return

            request.state.user_id = user.id
            request.state.tenant_id = user.tenant_id

    except Exception:
        logger.exception("resolve_tenant failed")
        return
