import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status import ConfirmationStatus, ShippingStatus
from app.models.order_status_history import OrderStatusHistory
from app.models.product import Product
from app.schemas.order import OrderCreate
from app.services.audit_service import AuditService
from app.services.base import BaseService
from app.services.shipment_service import ShipmentService

VALID_TRANSITIONS_CONFIRMATION = {
    ConfirmationStatus.PENDING.value: [
        ConfirmationStatus.CONFIRMED.value,
        ConfirmationStatus.CANCELLED.value,
    ],
    ConfirmationStatus.CONFIRMED.value: [],
    ConfirmationStatus.CANCELLED.value: [],
}

VALID_TRANSITIONS_SHIPPING = {
    ShippingStatus.NOT_SENT.value: [ShippingStatus.PICKED_UP.value],
    ShippingStatus.PICKED_UP.value: [ShippingStatus.IN_TRANSIT.value],
    ShippingStatus.IN_TRANSIT.value: [
        ShippingStatus.DELIVERED.value,
        ShippingStatus.RETURNED.value,
    ],
    ShippingStatus.DELIVERED.value: [ShippingStatus.RETURNED.value],
    ShippingStatus.RETURNED.value: [],
    ShippingStatus.FAILED.value: [],
}


class OrderService(BaseService[Order]):
    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)
        self.audit = AuditService(db)

    async def create_order(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        data: OrderCreate,
    ) -> Order:
        total = Decimal("0")
        items_to_create = []

        for item in data.items:
            result = await self.db.execute(
                select(Product).where(Product.id == item.product_id, Product.tenant_id == tenant_id)
            )
            product = result.scalar_one_or_none()
            if not product:
                raise NotFoundException(f"Product {item.product_id}")

            unit_price = Decimal(str(product.price))
            line_total = unit_price * item.quantity
            total += line_total

            items_to_create.append({
                "product_id": product.id,
                "quantity": item.quantity,
                "unit_price": unit_price,
            })

        order = Order(
            tenant_id=tenant_id,
            user_id=user_id,
            status="pending",
            confirmation_status=ConfirmationStatus.PENDING.value,
            shipping_status=ShippingStatus.NOT_SENT.value,
            total=float(total),
        )
        self.db.add(order)
        await self.db.flush()

        for item_data in items_to_create:
            order_item = OrderItem(order_id=order.id, **item_data)
            self.db.add(order_item)

        await self.db.flush()

        if data.shipping_provider_id:
            shipment_service = ShipmentService(self.db)
            await shipment_service.create_shipment(
                tenant_id=tenant_id,
                user_id=user_id,
                order_id=order.id,
                provider_id=uuid.UUID(data.shipping_provider_id),
            )

        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="order.created",
            entity="order",
            entity_id=order.id,
            details={"total": str(total), "items_count": len(items_to_create)},
        )

        return order

    async def update_confirmation_status(
        self,
        order_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        new_status: str,
        source: str = "manual",
        source_ref: str | None = None,
        force: bool = False,
    ) -> Order:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("Order")

        old_status = order.confirmation_status
        allowed = VALID_TRANSITIONS_CONFIRMATION.get(old_status, [])

        if new_status not in allowed and not force:
            raise ValueError(
                f"Cannot transition confirmation from '{old_status}' to '{new_status}'. "
                f"Allowed: {allowed}"
            )

        order.confirmation_status = new_status

        if new_status == ConfirmationStatus.CONFIRMED.value:
            order.confirmed_at = datetime.now(timezone.utc)

        now = datetime.now(timezone.utc)
        history = OrderStatusHistory(
            order_id=order_id,
            field_name="confirmation_status",
            old_value=old_status,
            new_value=new_status,
            source=source,
            source_ref=source_ref,
            created_at=now,
        )
        self.db.add(history)

        order.updated_source = source
        order.updated_by_user_id = user_id if source == "manual" else None
        order.updated_source_ref = source_ref
        await self.db.flush()

        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="order.confirmation_status_changed",
            entity="order",
            entity_id=order_id,
            details={"from": old_status, "to": new_status},
        )

        return order

    async def update_shipping_status(
        self,
        order_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        new_status: str,
        source: str = "manual",
        source_ref: str | None = None,
    ) -> Order:
        return await self._change_shipping_status(
            order_id=order_id,
            tenant_id=tenant_id,
            user_id=user_id,
            new_status=new_status,
            source=source,
            source_ref=source_ref,
            check_transition=True,
        )

    async def sync_shipping_status(
        self,
        order_id: uuid.UUID,
        tenant_id: uuid.UUID,
        new_status: str,
        source: str = "shipping_api",
        source_ref: str | None = None,
    ) -> Order:
        return await self._change_shipping_status(
            order_id=order_id,
            tenant_id=tenant_id,
            user_id=uuid.UUID(int=0),
            new_status=new_status,
            source=source,
            source_ref=source_ref,
            check_transition=False,
        )

    async def _change_shipping_status(
        self,
        order_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        new_status: str,
        source: str,
        source_ref: str | None,
        check_transition: bool,
    ) -> Order:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("Order")

        old_status = order.shipping_status

        if check_transition:
            allowed = VALID_TRANSITIONS_SHIPPING.get(old_status, [])
            if new_status not in allowed:
                raise ValueError(
                    f"Cannot transition shipping from '{old_status}' to '{new_status}'. "
                    f"Allowed: {allowed}"
                )

        order.shipping_status = new_status

        now = datetime.now(timezone.utc)
        history = OrderStatusHistory(
            order_id=order_id,
            field_name="shipping_status",
            old_value=old_status,
            new_value=new_status,
            source=source,
            source_ref=source_ref,
            created_at=now,
        )
        self.db.add(history)

        order.updated_source = source
        order.updated_by_user_id = user_id if source == "manual" else None
        order.updated_source_ref = source_ref
        await self.db.flush()

        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="order.shipping_status_changed",
            entity="order",
            entity_id=order_id,
            details={"from": old_status, "to": new_status},
        )

        return order

    async def get_tenant_orders(self, tenant_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[Order]:
        return await self.get_multi(skip=skip, limit=limit, filters={"tenant_id": tenant_id})
