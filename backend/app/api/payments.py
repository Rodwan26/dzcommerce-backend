import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentOut])
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = PaymentService(db)
    payments = await service.get_tenant_payments(tenant_id, skip=skip, limit=limit)
    return [
        PaymentOut(
            id=str(p.id), order_id=str(p.order_id), amount=float(p.amount),
            method=p.method, status=p.status, collected_at=p.collected_at, created_at=p.created_at,
        )
        for p in payments
    ]


@router.post("", response_model=PaymentOut, status_code=201)
async def create_payment(
    body: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = PaymentService(db)
    payment = await service.create_payment(
        tenant_id=tenant_id, user_id=current_user.id,
        order_id=body.order_id, amount=body.amount, method=body.method,
    )
    return PaymentOut(
        id=str(payment.id), order_id=str(payment.order_id), amount=float(payment.amount),
        method=payment.method, status=payment.status, collected_at=payment.collected_at,
        created_at=payment.created_at,
    )


@router.post("/{payment_id}/collect", response_model=PaymentOut)
async def collect_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = PaymentService(db)
    payment = await service.collect_payment(payment_id, tenant_id, current_user.id)
    return PaymentOut(
        id=str(payment.id), order_id=str(payment.order_id), amount=float(payment.amount),
        method=payment.method, status=payment.status, collected_at=payment.collected_at,
        created_at=payment.created_at,
    )
