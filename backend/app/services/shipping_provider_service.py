import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.shipping_provider import ShippingProvider
from app.services.audit_service import AuditService
from app.services.base import BaseService


class ShippingProviderService(BaseService[ShippingProvider]):
    def __init__(self, db: AsyncSession):
        super().__init__(ShippingProvider, db)
        self.audit = AuditService(db)

    async def get_tenant_providers(self, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[ShippingProvider]:
        return await self.get_multi(skip=skip, limit=limit, filters={"tenant_id": tenant_id})

    async def create_provider(self, tenant_id: uuid.UUID, user_id: uuid.UUID, **kwargs) -> ShippingProvider:
        provider = await self.create(tenant_id=tenant_id, **kwargs)
        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="shipping_provider.created",
            entity="shipping_provider",
            entity_id=provider.id,
            details={"name": kwargs.get("name"), "code": kwargs.get("code")},
        )
        return provider

    async def update_provider(self, provider_id: uuid.UUID, tenant_id: uuid.UUID, user_id: uuid.UUID, **kwargs) -> ShippingProvider:
        provider = await self.get(provider_id)
        if provider.tenant_id != tenant_id:
            raise PermissionError("Provider does not belong to this tenant")
        updated = await self.update(provider_id, **kwargs)
        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="shipping_provider.updated",
            entity="shipping_provider",
            entity_id=provider_id,
            details=kwargs,
        )
        return updated

    async def delete_provider(self, provider_id: uuid.UUID, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        provider = await self.get(provider_id)
        if provider.tenant_id != tenant_id:
            raise PermissionError("Provider does not belong to this tenant")
        await self.delete(provider_id)
        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="shipping_provider.deleted",
            entity="shipping_provider",
            entity_id=provider_id,
        )

    async def get_active_providers(self, tenant_id: uuid.UUID) -> list[ShippingProvider]:
        result = await self.db.execute(
            select(ShippingProvider).where(
                ShippingProvider.tenant_id == tenant_id,
                ShippingProvider.is_active == True,
            )
        )
        return list(result.scalars().all())
