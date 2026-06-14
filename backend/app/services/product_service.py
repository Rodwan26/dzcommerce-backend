import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.services.audit_service import AuditService
from app.services.base import BaseService


class ProductService(BaseService[Product]):
    def __init__(self, db: AsyncSession):
        super().__init__(Product, db)
        self.audit = AuditService(db)

    async def create_product(self, tenant_id: uuid.UUID, user_id: uuid.UUID, **kwargs) -> Product:
        product = await self.create(tenant_id=tenant_id, **kwargs)
        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="product.created",
            entity="product",
            entity_id=product.id,
            details={"name": kwargs.get("name")},
        )
        return product

    async def get_tenant_products(self, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[Product]:
        return await self.get_multi(skip=skip, limit=limit, filters={"tenant_id": tenant_id})

    async def update_product(self, product_id: uuid.UUID, tenant_id: uuid.UUID, user_id: uuid.UUID, **kwargs) -> Product:
        product = await self.get(product_id)
        if product.tenant_id != tenant_id:
            raise PermissionError("Product does not belong to this tenant")
        updated = await self.update(product_id, **kwargs)
        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="product.updated",
            entity="product",
            entity_id=product_id,
            details=kwargs,
        )
        return updated

    async def delete_product(self, product_id: uuid.UUID, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        product = await self.get(product_id)
        if product.tenant_id != tenant_id:
            raise PermissionError("Product does not belong to this tenant")
        await self.delete(product_id)
        await self.audit.log(
            tenant_id=tenant_id, user_id=user_id, action="product.deleted", entity="product", entity_id=product_id
        )
