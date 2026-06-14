import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.models.shipment import Shipment
from app.models.shipping_provider import ShippingProvider
from app.models.user import User
from app.schemas.shipping import (
    ShipmentCreate,
    ShipmentEventOut,
    ShipmentOut,
    ShippingProviderCreate,
    ShippingProviderOut,
    ShippingProviderUpdate,
)
from app.services.shipment_service import ShipmentService
from app.services.shipping_provider_service import ShippingProviderService
from app.services.shipping_service_factory import get_shipping_service

router = APIRouter(prefix="/shipping", tags=["shipping"])


@router.get("/providers", response_model=list[ShippingProviderOut])
async def list_providers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = ShippingProviderService(db)
    providers = await service.get_tenant_providers(tenant_id, skip=skip, limit=limit)
    return [
        ShippingProviderOut(
            id=str(p.id), name=p.name, code=p.code, provider_type=p.provider_type,
            is_active=p.is_active, last_test_at=p.last_test_at,
            last_test_success=p.last_test_success, last_error=p.last_error,
            created_at=p.created_at, updated_at=p.updated_at,
        )
        for p in providers
    ]


@router.post("/providers", response_model=ShippingProviderOut, status_code=201)
async def create_provider(
    body: ShippingProviderCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = ShippingProviderService(db)
    provider = await service.create_provider(
        tenant_id=tenant_id, user_id=current_user.id,
        name=body.name, code=body.code, provider_type=body.provider_type.value,
        credentials=body.credentials, is_active=body.is_active,
    )
    return ShippingProviderOut(
        id=str(provider.id), name=provider.name, code=provider.code,
        provider_type=provider.provider_type, is_active=provider.is_active,
        last_test_at=provider.last_test_at, last_test_success=provider.last_test_success,
        last_error=provider.last_error, created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


@router.put("/providers/{provider_id}", response_model=ShippingProviderOut)
async def update_provider(
    provider_id: str,
    body: ShippingProviderUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = ShippingProviderService(db)
    kwargs = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if "provider_type" in kwargs and isinstance(kwargs["provider_type"], str):
        kwargs["provider_type"] = kwargs["provider_type"]
    provider = await service.update_provider(
        provider_id, tenant_id, current_user.id, **kwargs
    )
    return ShippingProviderOut(
        id=str(provider.id), name=provider.name, code=provider.code,
        provider_type=provider.provider_type, is_active=provider.is_active,
        last_test_at=provider.last_test_at, last_test_success=provider.last_test_success,
        last_error=provider.last_error, created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


@router.delete("/providers/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = ShippingProviderService(db)
    await service.delete_provider(provider_id, tenant_id, current_user.id)


@router.post("/shipments", response_model=ShipmentOut, status_code=201)
async def create_shipment(
    body: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = ShipmentService(db)
    shipment = await service.create_shipment(
        tenant_id=tenant_id,
        user_id=current_user.id,
        order_id=uuid.UUID(body.order_id),
        provider_id=uuid.UUID(body.provider_id),
    )
    full = await service.get_shipment_with_events(shipment.id, tenant_id)
    return _shipment_to_out(full)


@router.get("/shipments/{shipment_id}", response_model=ShipmentOut)
async def get_shipment(
    shipment_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = ShipmentService(db)
    shipment = await service.get_shipment_with_events(uuid.UUID(shipment_id), tenant_id)
    return _shipment_to_out(shipment)


@router.get("/order-shipments", response_model=list[ShipmentOut])
async def get_order_shipments(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = ShipmentService(db)
    shipments = await service.get_order_shipments(tenant_id, uuid.UUID(order_id))
    result = []
    for s in shipments:
        full = await service.get_shipment_with_events(s.id, tenant_id)
        result.append(_shipment_to_out(full))
    return result


@router.post("/shipments/{shipment_id}/track", response_model=ShipmentOut)
async def track_shipment(
    shipment_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    service = ShipmentService(db)
    shipment = await service.track_shipment(uuid.UUID(shipment_id), tenant_id)
    full = await service.get_shipment_with_events(shipment.id, tenant_id)
    return _shipment_to_out(full)


@router.post("/shipments/{shipment_id}/cancel")
async def cancel_shipment(
    shipment_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Shipment).where(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id)
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if not shipment.tracking_code:
        raise HTTPException(status_code=400, detail="No tracking code to cancel")

    provider_result = await db.execute(
        select(ShippingProvider).where(ShippingProvider.id == shipment.provider_id)
    )
    provider = provider_result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Shipping provider not found")

    svc = get_shipping_service(provider)
    cancel_result = await svc.cancel_shipment(shipment.tracking_code)
    return {
        "success": cancel_result.success,
        "tracking_code": cancel_result.tracking_code,
        "error": cancel_result.error,
    }


@router.get("/shipments/{shipment_id}/label")
async def get_shipment_label(
    shipment_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Shipment).where(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id)
    )
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if not shipment.tracking_code:
        raise HTTPException(status_code=400, detail="No tracking code for label")

    provider_result = await db.execute(
        select(ShippingProvider).where(ShippingProvider.id == shipment.provider_id)
    )
    provider = provider_result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Shipping provider not found")

    svc = get_shipping_service(provider)
    label_result = await svc.get_label(shipment.tracking_code)
    if not label_result.success:
        raise HTTPException(status_code=502, detail=label_result.error or "Failed to fetch label")
    return {"label_url": label_result.label_url}


def _shipment_to_out(s: "Shipment") -> ShipmentOut:
    events = [
        ShipmentEventOut(
            id=str(e.id), status=e.status, note=e.note,
            occurred_at=e.occurred_at, created_at=e.created_at,
        )
        for e in (s.events or [])
    ]
    return ShipmentOut(
        id=str(s.id), order_id=str(s.order_id), provider_id=str(s.provider_id) if s.provider_id else None,
        provider_name=s.provider_name, provider_code=s.provider_code,
        external_id=s.external_id, tracking_code=s.tracking_code,
        status=s.status, label_url=s.label_url,
        customer_name=s.customer_name, customer_phone=s.customer_phone,
        customer_address=s.customer_address,
        last_synced_at=s.last_synced_at, created_at=s.created_at, updated_at=s.updated_at,
        events=events,
    )
