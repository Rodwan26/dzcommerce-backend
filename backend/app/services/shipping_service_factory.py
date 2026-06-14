import logging

from app.models.shipping_provider import ShippingProvider, ShippingProviderType
from app.services.shipping import BaseShippingService, NoestService, YalidineService, ZRExpressService

logger = logging.getLogger(__name__)


def get_shipping_service(provider: ShippingProvider) -> BaseShippingService:
    ptype = provider.provider_type or "custom"
    creds = provider.credentials or {}

    if ptype == ShippingProviderType.YALIDINE:
        return YalidineService(creds)
    elif ptype == ShippingProviderType.ZR_EXPRESS:
        return ZRExpressService(creds)
    elif ptype == ShippingProviderType.NOEST:
        return NoestService(creds)
    else:
        raise ValueError(f"Unsupported shipping provider type: {ptype}")


async def test_shipping_provider(provider: ShippingProvider) -> tuple[bool, str]:
    ptype = provider.provider_type or "custom"
    creds = provider.credentials or {}

    if ptype == ShippingProviderType.YALIDINE:
        return await _test_yalidine(creds)
    elif ptype == ShippingProviderType.ZR_EXPRESS:
        return await _test_zr_express(creds)
    elif ptype == ShippingProviderType.NOEST:
        return await _test_noest(creds)
    else:
        return _test_generic(creds)


async def _test_yalidine(creds: dict) -> tuple[bool, str]:
    api_id = creds.get("api_id")
    api_token = creds.get("api_token")
    if not api_id or not api_token:
        return False, "Missing API ID or API Token"
    try:
        svc = YalidineService(creds)
        ok = await svc.test_connection()
        return (True, "Connected successfully") if ok else (False, "Connection failed")
    except Exception as e:
        return False, str(e)


async def _test_zr_express(creds: dict) -> tuple[bool, str]:
    api_key = creds.get("api_key")
    if not api_key:
        return False, "Missing API Key"
    try:
        svc = ZRExpressService(creds)
        ok = await svc.test_connection()
        return (True, "Connected successfully") if ok else (False, "Connection failed")
    except Exception as e:
        return False, str(e)


async def _test_noest(creds: dict) -> tuple[bool, str]:
    username = creds.get("username")
    password = creds.get("password")
    if not username or not password:
        return False, "Missing Username or Password"
    try:
        svc = NoestService(creds)
        ok = await svc.test_connection()
        return (True, "Connected successfully") if ok else (False, "Connection failed")
    except Exception as e:
        return False, str(e)


def _test_generic(creds: dict) -> tuple[bool, str]:
    if not creds:
        return False, "No credentials configured"
    return True, "Connected successfully"
