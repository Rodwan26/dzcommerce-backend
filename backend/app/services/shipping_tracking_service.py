import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.order import Order
from app.models.order_status import ShippingStatus, UpdateSource
from app.models.shipment import Shipment, ShipmentStatus
from app.models.shipment_event import ShipmentEvent
from app.models.shipping_provider import ShippingProvider
from app.services.shipping_service_factory import get_shipping_service

logger = logging.getLogger(__name__)

TRACKING_INTERVAL_SECONDS = 600

_STATUS_MAPPING = {
    ShipmentStatus.PICKED_UP.value: ShippingStatus.PICKED_UP.value,
    ShipmentStatus.IN_TRANSIT.value: ShippingStatus.IN_TRANSIT.value,
    ShipmentStatus.DELIVERED.value: ShippingStatus.DELIVERED.value,
    ShipmentStatus.RETURNED.value: ShippingStatus.RETURNED.value,
    ShipmentStatus.FAILED.value: ShippingStatus.FAILED.value,
}


class ShippingTrackingService:

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def sync_cycle(self):
        async with self._session_factory() as session:
            result = await session.execute(
                select(Shipment).where(
                    Shipment.status.in_([
                        ShipmentStatus.SENT.value,
                        ShipmentStatus.PICKED_UP.value,
                        ShipmentStatus.IN_TRANSIT.value,
                    ]),
                    Shipment.tracking_code.isnot(None),
                )
            )
            shipments: list[Shipment] = list(result.scalars().all())

            for shipment in shipments:
                provider_result = await session.execute(
                    select(ShippingProvider).where(ShippingProvider.id == shipment.provider_id)
                )
                provider = provider_result.scalar_one_or_none()
                if not provider or not provider.is_active:
                    continue
                try:
                    svc = get_shipping_service(provider)
                    track_result = await svc.track_shipment(shipment.tracking_code)
                    now = datetime.now(timezone.utc)
                    changed = track_result.status.value != shipment.status

                    existing_result = await session.execute(
                        select(ShipmentEvent).where(ShipmentEvent.shipment_id == shipment.id)
                    )
                    existing_notes = {e.note for e in existing_result.scalars().all()}

                    for ev in track_result.events:
                        note = ev.get("note", "")
                        if note and note not in existing_notes:
                            event = ShipmentEvent(
                                shipment_id=shipment.id,
                                status=ev.get("status", track_result.status.value),
                                note=note,
                                occurred_at=(
                                    datetime.fromisoformat(ev["occurred_at"])
                                    if ev.get("occurred_at") else now
                                ),
                            )
                            session.add(event)
                            existing_notes.add(note)

                    if changed:
                        shipment.status = track_result.status.value
                        shipment.last_synced_at = now

                        order_result = await session.execute(
                            select(Order).where(Order.id == shipment.order_id)
                        )
                        order = order_result.scalar_one_or_none()
                        if order:
                            new_ship_status = _STATUS_MAPPING.get(shipment.status, order.shipping_status)
                            if new_ship_status != order.shipping_status:
                                order.shipping_status = new_ship_status
                                order.updated_source = UpdateSource.SHIPPING_API.value
                                order.updated_source_ref = shipment.tracking_code

                        logger.info(
                            "Shipment %s status updated: %s (tracking: %s)",
                            shipment.id, shipment.status, shipment.tracking_code,
                        )
                except Exception as e:
                    logger.exception("Tracking failed for shipment %s: %s", shipment.id, e)

            await session.commit()

    async def sync_loop(self):
        logger.info("Shipping tracking loop started (interval=%ds)", TRACKING_INTERVAL_SECONDS)
        await asyncio.sleep(30)
        while True:
            try:
                await self.sync_cycle()
            except Exception as e:
                logger.exception("Shipping tracking cycle error: %s", e)
            await asyncio.sleep(TRACKING_INTERVAL_SECONDS)
