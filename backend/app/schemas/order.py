from datetime import datetime

from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = 1


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]
    shipping_provider_id: str | None = None


class OrderItemOut(BaseModel):
    id: str
    product_id: str | None
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}


class ShipmentBriefOut(BaseModel):
    id: str
    provider_name: str
    tracking_code: str | None
    status: str

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str
    user_id: str
    status: str
    confirmation_status: str
    shipping_status: str
    confirmed_at: datetime | None
    total: float
    created_at: datetime
    updated_at: datetime | None
    items: list[OrderItemOut] = []
    shipments: list[ShipmentBriefOut] = []

    model_config = {"from_attributes": True}


class ConfirmationUpdate(BaseModel):
    confirmation_status: str


class ShippingStatusUpdate(BaseModel):
    shipping_status: str
