from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.models.shipment import ShipmentStatus


@dataclass
class ShipmentRequest:
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_address: str | None = None
    product_description: str = ""
    total: float = 0
    weight: float = 0
    wilaya: str | None = None
    commune: str | None = None


@dataclass
class ShipmentTrackResult:
    status: ShipmentStatus
    tracking_code: str | None = None
    events: list[dict] = field(default_factory=list)
    raw_response: dict = field(default_factory=dict)


@dataclass
class ShipmentActionResult:
    success: bool
    external_id: str | None = None
    tracking_code: str | None = None
    label_url: str | None = None
    status: ShipmentStatus = ShipmentStatus.PENDING
    raw_response: dict = field(default_factory=dict)
    error: str | None = None


class BaseShippingService(ABC):

    def __init__(self, credentials: dict):
        self.credentials = credentials

    async def test_connection(self) -> bool:
        return True

    @abstractmethod
    async def create_shipment(self, request: ShipmentRequest) -> ShipmentActionResult:
        ...

    @abstractmethod
    async def track_shipment(self, tracking_code: str) -> ShipmentTrackResult:
        ...

    @abstractmethod
    async def cancel_shipment(self, tracking_code: str) -> ShipmentActionResult:
        ...

    @abstractmethod
    async def get_label(self, tracking_code: str) -> ShipmentActionResult:
        ...
