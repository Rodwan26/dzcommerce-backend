from enum import Enum as PyEnum


class ConfirmationStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class ShippingStatus(str, PyEnum):
    NOT_SENT = "not_sent"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"
    FAILED = "failed"


class UpdateSource(str, PyEnum):
    MANUAL = "manual"
    GOOGLE_SHEET = "google_sheet"
    SHIPPING_API = "shipping_api"
