from datetime import datetime

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    price: float
    stock: int = 0
    sku: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    stock: int | None = None
    sku: str | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    sku: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
