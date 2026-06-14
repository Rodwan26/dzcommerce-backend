from datetime import datetime

from pydantic import BaseModel


class PaymentOut(BaseModel):
    id: str
    order_id: str
    amount: float
    method: str
    status: str
    collected_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    order_id: str
    amount: float
    method: str = "COD"
