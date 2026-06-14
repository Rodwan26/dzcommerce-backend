from app.services.gateways.base import ShippingGateway, ShipmentResult, TrackResult
from app.services.gateways.yalidine import YalidineGateway

GATEWAYS: dict[str, type[ShippingGateway]] = {
    "yalidine": YalidineGateway,
}
