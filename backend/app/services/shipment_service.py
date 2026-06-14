import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.order import Order
from app.models.order_status import ShippingStatus, UpdateSource
from app.models.shipping_provider import ShippingProvider
from app.models.shipment import Shipment, ShipmentStatus
from app.models.shipment_event import ShipmentEvent
from app.services.audit_service import AuditService
from app.services.base import BaseService
from app.services.shipping import ShipmentRequest
from app.services.shipping_service_factory import get_shipping_service


class ShipmentService(BaseService[Shipment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Shipment, db)
        self.audit = AuditService(db)

    async def create_shipment(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID, order_id: uuid.UUID, provider_id: uuid.UUID
    ) -> Shipment:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("Order")

        result = await self.db.execute(
            select(ShippingProvider).where(
                ShippingProvider.id == provider_id, ShippingProvider.tenant_id == tenant_id
            )
        )
        provider = result.scalar_one_or_none()
        if not provider:
            raise NotFoundException("ShippingProvider")
        if not provider.is_active:
            raise ValueError("Provider is not active")

        svc = get_shipping_service(provider)

        request = ShipmentRequest(
            customer_name=getattr(order, "customer_name", None),
            customer_phone=getattr(order, "customer_phone", None),
            customer_address=getattr(order, "customer_address", None),
            product_description=f"Order #{order_id}",
            total=float(order.total) if hasattr(order, "total") and order.total else 0,
            weight=0,
        )
        result = await svc.create_shipment(request)

        now = datetime.now(timezone.utc)
        shipment_status = result.status.value if result.success else ShipmentStatus.PENDING.value

        shipment = Shipment(
            tenant_id=tenant_id,
            order_id=order_id,
            provider_id=provider.id,
            provider_name=provider.name,
            provider_code=provider.code,
            external_id=result.external_id,
            tracking_code=result.tracking_code,
            status=shipment_status,
            label_url=result.label_url,
            customer_name=getattr(order, "customer_name", None),
            customer_phone=getattr(order, "customer_phone", None),
            customer_address=getattr(order, "customer_address", None),
            raw_data=result.raw_response,
        )
        self.db.add(shipment)
        await self.db.flush()

        if result.success:
            event = ShipmentEvent(
                shipment_id=shipment.id,
                status=shipment_status,
                note="Shipment created",
                occurred_at=now,
            )
            self.db.add(event)

        await self.audit.log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="shipment.created",
            entity="shipment",
            entity_id=shipment.id,
            details={
                "order_id": str(order_id),
                "provider": provider.code,
                "tracking": result.tracking_code,
                "success": result.success,
                "error": result.error,
            },
        )

        return shipment

    async def track_shipment(self, shipment_id: uuid.UUID, tenant_id: uuid.UUID) -> Shipment:
        result = await self.db.execute(
            select(Shipment).where(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id)
        )
        shipment = result.scalar_one_or_none()
        if not shipment:
            raise NotFoundException("Shipment")
        if not shipment.tracking_code:
            raise ValueError("Shipment has no tracking code to track")

        result = await self.db.execute(
            select(ShippingProvider).where(ShippingProvider.id == shipment.provider_id)
        )
        provider = result.scalar_one_or_none()
        if not provider:
            raise NotFoundException("ShippingProvider")

        svc = get_shipping_service(provider)
        track_result = await svc.track_shipment(shipment.tracking_code)

        now = datetime.now(timezone.utc)
        new_status = track_result.status.value

        if track_result.events:
            existing = await self.db.execute(
                select(ShipmentEvent).where(ShipmentEvent.shipment_id == shipment_id)
            )
            existing_notes = {e.note for e in existing.scalars().all()}

            for ev in track_result.events:
                note = ev.get("note", "")
                if note not in existing_notes:
                    event = ShipmentEvent(
                        shipment_id=shipment.id,
                        status=ev.get("status", new_status),
                        note=note,
                        occurred_at=datetime.fromisoformat(ev["occurred_at"]) if ev.get("occurred_at") else now,
                    )
                    self.db.add(event)
                    existing_notes.add(note)

        if new_status != shipment.status:
            shipment.status = new_status

        shipment.last_synced_at = now
        await self.db.flush()

        result = await self.db.execute(
            select(Order).where(Order.id == shipment.order_id, Order.tenant_id == tenant_id)
        )
        order = result.scalar_one_or_none()
        if order:
            new_shipping_status = _shipment_to_shipping_status(track_result.status)
            if new_shipping_status.value != order.shipping_status:
                order.shipping_status = new_shipping_status.value
                order.updated_source = UpdateSource.SHIPPING_API.value
                order.updated_source_ref = shipment.tracking_code
            await self.db.flush()

        return shipment

    async def get_order_shipments(self, tenant_id: uuid.UUID, order_id: uuid.UUID) -> list[Shipment]:
        result = await self.db.execute(
            select(Shipment).where(
                Shipment.tenant_id == tenant_id,
                Shipment.order_id == order_id,
            )
        )
        return list(result.scalars().all())

    async def get_shipment_with_events(self, shipment_id: uuid.UUID, tenant_id: uuid.UUID) -> Shipment:
        result = await self.db.execute(
            select(Shipment).where(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id)
        )
        shipment = result.scalar_one_or_none()
        if not shipment:
            raise NotFoundException("Shipment")
        return shipment


def _shipment_to_shipping_status(s: ShipmentStatus) -> ShippingStatus:
    mapping = {
        ShipmentStatus.PENDING: ShippingStatus.NOT_SENT,
        ShipmentStatus.SENT: ShippingStatus.NOT_SENT,
        ShipmentStatus.PICKED_UP: ShippingStatus.PICKED_UP,
        ShipmentStatus.IN_TRANSIT: ShippingStatus.IN_TRANSIT,
        ShipmentStatus.DELIVERED: ShippingStatus.DELIVERED,
        ShipmentStatus.RETURNED: ShippingStatus.RETURNED,
        ShipmentStatus.FAILED: ShippingStatus.FAILED,
    }
    return mapping.get(s, ShippingStatus.NOT_SENT)
