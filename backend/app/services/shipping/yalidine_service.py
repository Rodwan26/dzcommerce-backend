import logging

import httpx

from app.models.shipment import ShipmentStatus
from app.services.shipping.base import (
    BaseShippingService,
    ShipmentActionResult,
    ShipmentRequest,
    ShipmentTrackResult,
)

logger = logging.getLogger(__name__)

YALIDINE_BASE = "https://api.yalidine.app/v1"


class YalidineService(BaseShippingService):

    async def test_connection(self) -> bool:
        try:
            await self._get("account")
            return True
        except Exception:
            return False

    async def _post(self, path: str, json: dict | None = None) -> dict:
        api_id = self.credentials.get("api_id")
        api_token = self.credentials.get("api_token")
        if not api_id or not api_token:
            raise ValueError("Missing Yalidine credentials: api_id and api_token required")
        url = f"{YALIDINE_BASE}/{path.lstrip('/')}"
        headers = {"X-API-ID": api_id, "X-API-Token": api_token}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json=json)
            if resp.status_code >= 400:
                detail = resp.json().get("message", resp.text)
                raise ValueError(f"Yalidine API error ({resp.status_code}): {detail}")
            return resp.json()

    async def _get(self, path: str) -> dict:
        api_id = self.credentials.get("api_id")
        api_token = self.credentials.get("api_token")
        if not api_id or not api_token:
            raise ValueError("Missing Yalidine credentials: api_id and api_token required")
        url = f"{YALIDINE_BASE}/{path.lstrip('/')}"
        headers = {"X-API-ID": api_id, "X-API-Token": api_token}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code >= 400:
                detail = resp.json().get("message", resp.text)
                raise ValueError(f"Yalidine API error ({resp.status_code}): {detail}")
            return resp.json()

    async def _delete(self, path: str) -> dict:
        api_id = self.credentials.get("api_id")
        api_token = self.credentials.get("api_token")
        if not api_id or not api_token:
            raise ValueError("Missing Yalidine credentials: api_id and api_token required")
        url = f"{YALIDINE_BASE}/{path.lstrip('/')}"
        headers = {"X-API-ID": api_id, "X-API-Token": api_token}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(url, headers=headers)
            if resp.status_code >= 400:
                detail = resp.json().get("message", resp.text)
                raise ValueError(f"Yalidine API error ({resp.status_code}): {detail}")
            return resp.json()

    def _map_status(self, yalidine_status: str) -> ShipmentStatus:
        mapping = {
            "pending": ShipmentStatus.PENDING,
            "sent": ShipmentStatus.SENT,
            "picked_up": ShipmentStatus.PICKED_UP,
            "in_transit": ShipmentStatus.IN_TRANSIT,
            "delivered": ShipmentStatus.DELIVERED,
            "returned": ShipmentStatus.RETURNED,
            "failed": ShipmentStatus.FAILED,
            "waiting": ShipmentStatus.PENDING,
            "processing": ShipmentStatus.PENDING,
            "shipped": ShipmentStatus.IN_TRANSIT,
            "completed": ShipmentStatus.DELIVERED,
            "cancelled": ShipmentStatus.FAILED,
        }
        return mapping.get(yalidine_status.lower(), ShipmentStatus.PENDING)

    async def create_shipment(self, request: ShipmentRequest) -> ShipmentActionResult:
        try:
            payload = {
                "customer_name": request.customer_name or "",
                "customer_phone": request.customer_phone or "",
                "customer_address": request.customer_address or "",
                "product_description": request.product_description,
                "total": request.total,
                "weight": request.weight,
                "wilaya": request.wilaya or "",
                "commune": request.commune or "",
            }
            data = await self._post("shipments", json=payload)
            return ShipmentActionResult(
                success=True,
                external_id=str(data.get("id", "")),
                tracking_code=data.get("tracking_code", ""),
                label_url=data.get("label_url"),
                status=self._map_status(data.get("status", "pending")),
                raw_response=data,
            )
        except Exception as e:
            logger.exception("Yalidine create_shipment failed")
            return ShipmentActionResult(success=False, error=str(e))

    async def track_shipment(self, tracking_code: str) -> ShipmentTrackResult:
        try:
            data = await self._get(f"shipments/{tracking_code}")
            events_raw = data.get("events", data.get("history", []))
            events = []
            for ev in events_raw:
                events.append({
                    "status": ev.get("status", ""),
                    "note": ev.get("note", ev.get("description", "")),
                    "occurred_at": ev.get("date", ev.get("created_at")),
                })
            return ShipmentTrackResult(
                status=self._map_status(data.get("status", "pending")),
                tracking_code=tracking_code,
                events=events,
                raw_response=data,
            )
        except Exception as e:
            logger.exception("Yalidine track_shipment failed")
            return ShipmentTrackResult(status=ShipmentStatus.FAILED, raw_response={"error": str(e)})

    async def cancel_shipment(self, tracking_code: str) -> ShipmentActionResult:
        try:
            data = await self._delete(f"shipments/{tracking_code}")
            return ShipmentActionResult(
                success=True,
                external_id=str(data.get("id", "")),
                tracking_code=tracking_code,
                status=ShipmentStatus.FAILED,
                raw_response=data,
            )
        except Exception as e:
            logger.exception("Yalidine cancel_shipment failed")
            return ShipmentActionResult(success=False, error=str(e))

    async def get_label(self, tracking_code: str) -> ShipmentActionResult:
        try:
            data = await self._get(f"shipments/{tracking_code}/label")
            return ShipmentActionResult(
                success=True,
                tracking_code=tracking_code,
                label_url=data.get("url", data.get("label_url")),
                raw_response=data,
            )
        except Exception as e:
            logger.exception("Yalidine get_label failed")
            return ShipmentActionResult(success=False, error=str(e))
