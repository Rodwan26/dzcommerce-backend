import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import hash_password, verify_password, create_token, decode_token
from app.models.tenant import Tenant
from app.models.tenant_request import TenantRequest
from app.models.tenant_settings import TenantSettings
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.audit_service import AuditService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)

    async def register(self, email: str, password: str, name: str, company_name: str, phone: str) -> TenantRequest:
        existing_user = await self.db.execute(select(User).where(User.email == email))
        if existing_user.scalar_one_or_none():
            raise ConflictException("Email already registered")

        existing_request = await self.db.execute(
            select(TenantRequest).where(TenantRequest.email == email, TenantRequest.status == "pending")
        )
        if existing_request.scalar_one_or_none():
            raise ConflictException("A pending request already exists for this email")

        tenant_request = TenantRequest(
            company_name=company_name,
            owner_name=name,
            email=email,
            phone=phone,
            status="pending",
        )
        self.db.add(tenant_request)
        await self.db.flush()

        return tenant_request

    async def verify_email(self, email: str, code: str) -> None:
        pass

    async def login(self, email: str, password: str) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is not active")

        access_token = create_token(
            sub=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            role=user.role,
            token_version=user.token_version,
            token_type="access",
        )
        refresh_token = create_token(
            sub=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            role=user.role,
            token_version=user.token_version,
            token_type="refresh",
        )

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")

        result = await self.db.execute(select(User).where(User.id == payload["sub"]))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        if user.token_version != payload.get("token_version"):
            raise UnauthorizedException("Token revoked")

        access_token = create_token(
            sub=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            role=user.role,
            token_version=user.token_version,
            token_type="access",
        )
        new_refresh = create_token(
            sub=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            role=user.role,
            token_version=user.token_version,
            token_type="refresh",
        )

        return TokenResponse(access_token=access_token, refresh_token=new_refresh)

    async def logout(self, user: User) -> None:
        user.token_version += 1
        await self.db.flush()

    @staticmethod
    async def approve_request(request_id: uuid.UUID, db: AsyncSession) -> Tenant:
        result = await db.execute(select(TenantRequest).where(TenantRequest.id == request_id))
        tenant_request = result.scalar_one_or_none()
        if not tenant_request:
            raise UnauthorizedException("Request not found")

        if tenant_request.status != "pending":
            raise ConflictException("Request already processed")

        tenant_request.status = "approved"

        slug = tenant_request.company_name.lower().replace(" ", "-").replace("'", "")[:200]

        tenant = Tenant(
            name=tenant_request.company_name,
            slug=slug,
            status="active",
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=settings.TRIAL_DAYS),
        )
        db.add(tenant)
        await db.flush()

        user = User(
            tenant_id=tenant.id,
            email=tenant_request.email,
            password_hash=hash_password("changeme123"),
            name=tenant_request.owner_name,
            role="owner",
            is_active=True,
        )
        db.add(user)
        await db.flush()

        tenant_settings = TenantSettings(tenant_id=tenant.id)
        db.add(tenant_settings)

        subscription = Subscription(
            tenant_id=tenant.id,
            plan="trial",
            start_date=datetime.now(timezone.utc),
            end_date=tenant.trial_ends_at,
        )
        db.add(subscription)

        await db.flush()
        return tenant

    @staticmethod
    async def reject_request(request_id: uuid.UUID, db: AsyncSession) -> None:
        result = await db.execute(select(TenantRequest).where(TenantRequest.id == request_id))
        tenant_request = result.scalar_one_or_none()
        if not tenant_request:
            raise UnauthorizedException("Request not found")

        tenant_request.status = "rejected"
        await db.flush()
