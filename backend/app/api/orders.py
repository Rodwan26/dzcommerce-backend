import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.models.order import Order
from app.models.user import User
from app.schemas.order import ConfirmationUpdate, OrderCreate, OrderOut, ShippingStatusUpdate
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


async def _load_and_out(db, o: Order) -> OrderOut:
    await db.refresh(o, ["items", "shipments"])
    items = [
        {"id": str(i.id), "product_id": str(i.product_id) if i.product_id else None,
         "quantity": i.quantity, "unit_price": float(i.unit_price)}
        for i in (o.items or [])
    ]
    shipments = [
        {"id": str(s.id), "provider_name": s.provider_name,
         "tracking_code": s.tracking_code, "status": s.status}
        for s in (o.shipments or [])
    ]
    return OrderOut(
        id=str(o.id), user_id=str(o.user_id),
        status=o.status,
        confirmation_status=o.confirmation_status,
        shipping_status=o.shipping_status,
        confirmed_at=o.confirmed_at,
        total=float(o.total), created_at=o.created_at, updated_at=o.updated_at,
        items=items, shipments=shipments,
    )


@router.get("", response_model=list[OrderOut])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = OrderService(db)
    orders = await service.get_tenant_orders(tenant_id, skip=skip, limit=limit)
    return [await _load_and_out(db, o) for o in orders]


@router.post("", response_model=OrderOut, status_code=201)
async def create_order(
    body: OrderCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = OrderService(db)
    order = await service.create_order(tenant_id=tenant_id, user_id=current_user.id, data=body)
    return await _load_and_out(db, order)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = OrderService(db)
    order = await service.get(order_id)
    return await _load_and_out(db, order)


@router.patch("/{order_id}/confirmation-status", response_model=OrderOut)
async def update_order_confirmation_status(
    order_id: str,
    body: ConfirmationUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = OrderService(db)
    order = await service.update_confirmation_status(
        order_id=uuid.UUID(order_id),
        tenant_id=tenant_id,
        user_id=current_user.id,
        new_status=body.confirmation_status,
    )
    return await _load_and_out(db, order)


@router.patch("/{order_id}/shipping-status", response_model=OrderOut)
async def update_order_shipping_status(
    order_id: str,
    body: ShippingStatusUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = OrderService(db)
    order = await service.update_shipping_status(
        order_id=uuid.UUID(order_id),
        tenant_id=tenant_id,
        user_id=current_user.id,
        new_status=body.shipping_status,
    )
    return await _load_and_out(db, order)
