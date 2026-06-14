from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.models.order import Order
from app.models.shipping_provider import ShippingProvider
from app.models.shipment import ShipmentStatus


@dataclass
class ShipmentResult:
    external_id: str
    tracking_code: str
    label_url: str | None = None
    status: ShipmentStatus = ShipmentStatus.PENDING
    raw_response: dict = field(default_factory=dict)


@dataclass
class TrackEvent:
    status: ShipmentStatus
    note: str | None = None
    occurred_at: datetime | None = None


@dataclass
class TrackResult:
    status: ShipmentStatus
    events: list[TrackEvent] = field(default_factory=list)
    raw_response: dict = field(default_factory=dict)


class ShippingGateway(ABC):
    @abstractmethod
    async def create_shipment(self, order: Order, provider: ShippingProvider) -> ShipmentResult:
        ...

    @abstractmethod
    async def track_shipment(self, tracking_code: str, provider: ShippingProvider) -> TrackResult:
        ...
