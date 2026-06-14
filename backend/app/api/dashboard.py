import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.models.product import Product
from app.models.order import Order

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    products_count = await db.scalar(
        select(func.count(Product.id)).where(Product.tenant_id == tenant_id)
    )

    orders_count = await db.scalar(
        select(func.count(Order.id)).where(Order.tenant_id == tenant_id)
    )

    revenue_result = await db.scalar(
        select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.tenant_id == tenant_id, Order.shipping_status == "delivered"
        )
    )

    pending_orders = await db.scalar(
        select(func.count(Order.id)).where(
            Order.tenant_id == tenant_id, Order.confirmation_status == "pending"
        )
    )

    return {
        "products_count": products_count or 0,
        "orders_count": orders_count or 0,
        "revenue": float(revenue_result or 0),
        "pending_orders": pending_orders or 0,
    }
