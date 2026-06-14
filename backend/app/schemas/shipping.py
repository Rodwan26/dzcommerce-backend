from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ShipmentStatusEnum(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"
    FAILED = "failed"


class ShippingProviderType(str, Enum):
    YALIDINE = "yalidine"
    ZR_EXPRESS = "zr_express"
    NOEST = "noest"
    MAYSTRO = "maystro"
    CUSTOM = "custom"


class ShippingProviderCreate(BaseModel):
    name: str
    code: str
    provider_type: ShippingProviderType = ShippingProviderType.CUSTOM
    credentials: dict | None = None
    is_active: bool = True


class ShippingProviderUpdate(BaseModel):
    name: str | None = None
    provider_type: ShippingProviderType | None = None
    credentials: dict | None = None
    is_active: bool | None = None


class ShippingProviderOut(BaseModel):
    id: str
    name: str
    code: str
    provider_type: str
    is_active: bool
    last_test_at: datetime | None = None
    last_test_success: bool | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ShipmentEventOut(BaseModel):
    id: str
    status: str
    note: str | None
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ShipmentCreate(BaseModel):
    order_id: str
    provider_id: str


class ShipmentOut(BaseModel):
    id: str
    order_id: str
    provider_id: str | None
    provider_name: str
    provider_code: str
    external_id: str | None
    tracking_code: str | None
    status: str
    label_url: str | None
    customer_name: str | None
    customer_phone: str | None
    customer_address: str | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
    events: list[ShipmentEventOut] = []

    model_config = {"from_attributes": True}
