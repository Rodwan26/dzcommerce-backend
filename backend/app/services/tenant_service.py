import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.tenant import Tenant
from app.models.tenant_feature import TenantFeature
from app.models.tenant_settings import TenantSettings
from app.services.audit_service import AuditService


class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)

    async def get_settings(self, tenant_id: uuid.UUID) -> TenantSettings:
        result = await self.db.execute(
            select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
        )
        settings = result.scalar_one_or_none()
        if not settings:
            settings = TenantSettings(tenant_id=tenant_id, currency="DZD", language="ar", cod_enabled=True)
            self.db.add(settings)
            await self.db.flush()
            await self.db.refresh(settings)
        return settings

    async def update_settings(self, tenant_id: uuid.UUID, **kwargs) -> TenantSettings:
        settings = await self.get_settings(tenant_id)
        for key, value in kwargs.items():
            if value is not None and hasattr(settings, key):
                setattr(settings, key, value)
        await self.db.flush()
        return settings

    async def get_features(self, tenant_id: uuid.UUID) -> list[TenantFeature]:
        result = await self.db.execute(
            select(TenantFeature).where(TenantFeature.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    async def toggle_feature(self, tenant_id: uuid.UUID, feature_key: str, enabled: bool) -> TenantFeature:
        result = await self.db.execute(
            select(TenantFeature).where(
                TenantFeature.tenant_id == tenant_id,
                TenantFeature.feature_key == feature_key,
            )
        )
        feature = result.scalar_one_or_none()

        if feature:
            feature.enabled = enabled
        else:
            feature = TenantFeature(tenant_id=tenant_id, feature_key=feature_key, enabled=enabled)
            self.db.add(feature)

        await self.db.flush()
        return feature

    async def get_tenant(self, tenant_id: uuid.UUID) -> Tenant:
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundException("Tenant")
        return tenant
