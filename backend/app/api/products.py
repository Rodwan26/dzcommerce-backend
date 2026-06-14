import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.models.user import User
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = ProductService(db)
    products = await service.get_tenant_products(tenant_id, skip=skip, limit=limit)
    return [
        ProductOut(
            id=str(p.id),
            name=p.name,
            price=float(p.price),
            stock=p.stock,
            sku=p.sku,
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in products
    ]


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = ProductService(db)
    product = await service.create_product(
        tenant_id=tenant_id, user_id=current_user.id, name=body.name, price=body.price, stock=body.stock, sku=body.sku
    )
    return ProductOut(
        id=str(product.id),
        name=product.name,
        price=float(product.price),
        stock=product.stock,
        sku=product.sku,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = ProductService(db)
    product = await service.get(product_id)
    return ProductOut(
        id=str(product.id),
        name=product.name,
        price=float(product.price),
        stock=product.stock,
        sku=product.sku,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: str,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = ProductService(db)
    product = await service.update_product(
        product_id, tenant_id, current_user.id,
        name=body.name, price=body.price, stock=body.stock, sku=body.sku, is_active=body.is_active,
    )
    return ProductOut(
        id=str(product.id),
        name=product.name,
        price=float(product.price),
        stock=product.stock,
        sku=product.sku,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = ProductService(db)
    await service.delete_product(product_id, tenant_id, current_user.id)
