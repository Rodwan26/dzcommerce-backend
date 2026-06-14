import uuid

from app.models.order import Order
from app.models.shipping_provider import ShippingProvider
from app.models.shipment import ShipmentStatus
from app.services.gateways.base import ShippingGateway, ShipmentResult, TrackResult


class YalidineGateway(ShippingGateway):
    async def create_shipment(self, order: Order, provider: ShippingProvider) -> ShipmentResult:
        return ShipmentResult(
            external_id=str(uuid.uuid4())[:12],
            tracking_code=f"YD{str(uuid.uuid4())[:8].upper()}",
            status=ShipmentStatus.PENDING,
        )

    async def track_shipment(self, tracking_code: str, provider: ShippingProvider) -> TrackResult:
        return TrackResult(
            status=ShipmentStatus.PENDING,
            events=[],
        )
