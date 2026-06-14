import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.order import Order
from app.models.payment import Payment
from app.services.audit_service import AuditService


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)

    async def create_payment(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID, order_id: uuid.UUID, amount: float, method: str = "COD"
    ) -> Payment:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("Order")

        payment = Payment(
            tenant_id=tenant_id,
            order_id=order_id,
            amount=amount,
            method=method,
            status="pending",
        )
        self.db.add(payment)
        await self.db.flush()

        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="payment.created",
            entity="payment",
            entity_id=payment.id,
            details={"order_id": str(order_id), "amount": amount, "method": method},
        )

        return payment

    async def collect_payment(self, payment_id: uuid.UUID, tenant_id: uuid.UUID, user_id: uuid.UUID) -> Payment:
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id, Payment.tenant_id == tenant_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise NotFoundException("Payment")

        payment.status = "collected"
        payment.collected_at = datetime.now(timezone.utc)
        await self.db.flush()

        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="payment.collected",
            entity="payment",
            entity_id=payment_id,
        )

        return payment

    async def get_tenant_payments(self, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[Payment]:
        result = await self.db.execute(
            select(Payment)
            .where(Payment.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
