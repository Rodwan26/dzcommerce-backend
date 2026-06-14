import json
import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.models.shipping_provider import ShippingProvider
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.integrations import (
    FacebookConfigResponse,
    FacebookConfigureRequest,
    GoogleConfigResponse,
    GoogleConfigureRequest,
    IntegrationProviderStatus,
    IntegrationServiceStatus,
    IntegrationsStatusResponse,
    TestResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])

SHEET_URL_PATTERN = re.compile(r"https?://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)")


def _extract_sheet_id(url: str) -> str | None:
    m = SHEET_URL_PATTERN.search(url)
    return m.group(1) if m else None


# ── Google Sheets ──────────────────────────────────────────────


@router.get("/google/config", response_model=GoogleConfigResponse)
async def google_config_get(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{t.google_sheet_id}" if t.google_sheet_id else None
    return GoogleConfigResponse(
        sheet_id=t.google_sheet_id,
        sheet_url=sheet_url,
        enabled=t.google_sheet_enabled,
        last_sync_at=t.google_sheet_last_sync_at,
        last_test_at=t.google_last_test_at,
        last_test_success=t.google_last_test_success,
        last_error=t.google_last_error,
    )


@router.post("/google/configure", response_model=GoogleConfigResponse)
async def google_configure(
    body: GoogleConfigureRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")

    sheet_id = _extract_sheet_id(body.sheet_url)
    if not sheet_id:
        raise HTTPException(status_code=400, detail="Invalid Google Sheet URL")

    enable = body.enable_sync and t.google_last_test_success is True

    stmt = (
        update(Tenant)
        .where(Tenant.id == tenant_id)
        .values(
            google_sheet_id=sheet_id,
            google_sheet_enabled=enable,
            google_last_error=None if enable else t.google_last_error,
        )
    )
    await db.execute(stmt)
    await db.commit()

    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    return GoogleConfigResponse(
        sheet_id=sheet_id,
        sheet_url=sheet_url,
        enabled=enable,
        last_test_at=t.google_last_test_at,
        last_test_success=t.google_last_test_success,
    )


class GoogleTestRequest(BaseModel):
    sheet_url: str | None = None


@router.post("/google/test", response_model=TestResult)
async def google_test(
    body: GoogleTestRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")

    sid = t.google_sheet_id
    if body.sheet_url:
        extracted = _extract_sheet_id(body.sheet_url)
        if not extracted:
            raise HTTPException(status_code=400, detail="Invalid Google Sheet URL")
        sid = extracted

    if not sid:
        raise HTTPException(status_code=400, detail="No sheet configured — provide a sheet URL or configure one first")

    try:
        from app.services.google_sheets_sync_service import GoogleSheetsSyncService

        from app.core.db import async_session_factory

        service = GoogleSheetsSyncService(async_session_factory)
        ws = await service._open_sheet(sid)
        header = await service._get_sheet_data(sid)
        now = datetime.now(timezone.utc)

        stmt = update(Tenant).where(Tenant.id == tenant_id).values(
            google_last_test_at=now,
            google_last_test_success=True,
            google_last_error=None,
        )
        await db.execute(stmt)
        await db.commit()

        return TestResult(
            success=True,
            message="Connected successfully",
            details={"sheet_id": sid, "rows": len(header) if header else 0},
        )
    except Exception as e:
        now = datetime.now(timezone.utc)
        stmt = update(Tenant).where(Tenant.id == tenant_id).values(
            google_last_test_at=now,
            google_last_test_success=False,
            google_last_error=str(e)[:500],
        )
        await db.execute(stmt)
        await db.commit()

        return TestResult(success=False, message=str(e)[:500])


# ── Facebook Ads ───────────────────────────────────────────────


@router.get("/facebook/config", response_model=FacebookConfigResponse)
async def facebook_config_get(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return FacebookConfigResponse(
        access_token="••••" + t.facebook_access_token[-8:] if t.facebook_access_token else None,
        ad_account_id=t.facebook_ad_account_id,
        mode="mock" if settings.FACEBOOK_MOCK_MODE else "live",
        enabled=t.facebook_sync_enabled,
        last_sync_at=t.facebook_last_sync_at,
        last_test_at=t.facebook_last_test_at,
        last_test_success=t.facebook_last_test_success,
        last_error=t.facebook_last_error,
    )


@router.post("/facebook/configure", response_model=FacebookConfigResponse)
async def facebook_configure(
    body: FacebookConfigureRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")

    enable = body.enable_sync and t.facebook_last_test_success is True

    values: dict = {
        "facebook_sync_enabled": enable,
    }
    if body.access_token:
        values["facebook_access_token"] = body.access_token
    if body.ad_account_id:
        values["facebook_ad_account_id"] = body.ad_account_id
    if enable:
        values["facebook_last_error"] = None

    stmt = update(Tenant).where(Tenant.id == tenant_id).values(**values)
    await db.execute(stmt)
    await db.commit()

    return FacebookConfigResponse(
        enabled=enable,
        last_test_at=t.facebook_last_test_at,
        last_test_success=t.facebook_last_test_success,
    )


class FacebookTestRequest(BaseModel):
    access_token: str | None = None
    ad_account_id: str | None = None

    def model_post_init(self, __context):
        self.access_token = self.access_token or None
        self.ad_account_id = self.ad_account_id or None


@router.post("/facebook/test", response_model=TestResult)
async def facebook_test(
    body: FacebookTestRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")

    token = body.access_token or t.facebook_access_token
    account = body.ad_account_id or t.facebook_ad_account_id

    if settings.FACEBOOK_MOCK_MODE:
        now = datetime.now(timezone.utc)
        values: dict = {
            "facebook_last_test_at": now,
            "facebook_last_test_success": True,
            "facebook_last_error": None,
        }
        if body.access_token:
            values["facebook_access_token"] = body.access_token
        if body.ad_account_id:
            values["facebook_ad_account_id"] = body.ad_account_id
        stmt = update(Tenant).where(Tenant.id == tenant_id).values(**values)
        await db.execute(stmt)
        await db.commit()
        return TestResult(success=True, message="Mock mode — connected successfully", details={"mode": "mock"})

    if not token or not account:
        raise HTTPException(status_code=400, detail="Access token and ad account ID are required")

    try:
        from app.services.facebook_ads_service import FacebookAdsService

        from app.core.db import async_session_factory

        service = FacebookAdsService(async_session_factory)
        data = await service._graph_get(
            token, f"act_{account}/campaigns",
            params={"fields": "id,name", "limit": 1},
        )
        campaigns = data.get("data", [])
        now = datetime.now(timezone.utc)

        values: dict = {
            "facebook_last_test_at": now,
            "facebook_last_test_success": True,
            "facebook_last_error": None,
        }
        if body.access_token:
            values["facebook_access_token"] = body.access_token
        if body.ad_account_id:
            values["facebook_ad_account_id"] = body.ad_account_id
        stmt = update(Tenant).where(Tenant.id == tenant_id).values(**values)
        await db.execute(stmt)
        await db.commit()

        details = {"campaign_count": len(campaigns)}
        if campaigns:
            details["first_campaign"] = campaigns[0].get("name")

        return TestResult(success=True, message="Connected successfully", details=details)
    except Exception as e:
        now = datetime.now(timezone.utc)
        stmt = update(Tenant).where(Tenant.id == tenant_id).values(
            facebook_last_test_at=now,
            facebook_last_test_success=False,
            facebook_last_error=str(e)[:500],
        )
        await db.execute(stmt)
        await db.commit()

        return TestResult(success=False, message=str(e)[:500])


# ── Integrations Status ────────────────────────────────────────


@router.get("/status", response_model=IntegrationsStatusResponse)
async def integrations_status(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")

    def svc_status(
        enabled: bool,
        configured: bool,
        last_test_success: bool | None,
        last_error: str | None,
    ) -> str:
        if enabled and last_test_success:
            return "connected"
        if last_error:
            return "error"
        if configured:
            return "disabled"
        return "not_configured"

    google_status = IntegrationServiceStatus(
        service="google_sheets",
        label="Google Sheets",
        status=svc_status(
            t.google_sheet_enabled,
            bool(t.google_sheet_id),
            t.google_last_test_success,
            t.google_last_error,
        ),
        last_sync_at=t.google_sheet_last_sync_at,
        last_test_at=t.google_last_test_at,
        last_test_success=t.google_last_test_success,
        last_error=t.google_last_error,
    )

    facebook_status = IntegrationServiceStatus(
        service="facebook_ads",
        label="Facebook Ads",
        status=svc_status(
            t.facebook_sync_enabled,
            bool(t.facebook_access_token and t.facebook_ad_account_id),
            t.facebook_last_test_success,
            t.facebook_last_error,
        ),
        last_sync_at=t.facebook_last_sync_at,
        last_test_at=t.facebook_last_test_at,
        last_test_success=t.facebook_last_test_success,
        last_error=t.facebook_last_error,
    )

    prov_result = await db.execute(
        select(ShippingProvider).where(ShippingProvider.tenant_id == tenant_id)
    )
    providers: list[ShippingProvider] = list(prov_result.scalars().all())

    shipping_statuses = [
        IntegrationProviderStatus(
            id=str(p.id),
            name=p.name,
            code=p.code,
            status=svc_status(p.is_active, True, p.last_test_success, p.last_error),
            last_test_at=p.last_test_at,
            last_test_success=p.last_test_success,
            last_error=p.last_error,
        )
        for p in providers
    ]

    return IntegrationsStatusResponse(
        google_sheets=google_status,
        facebook_ads=facebook_status,
        shipping_providers=shipping_statuses,
    )


# ── Shipping Provider Test ─────────────────────────────────────


@router.post("/shipping/{provider_id}/test", response_model=TestResult)
async def shipping_provider_test(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ShippingProvider).where(
            ShippingProvider.id == provider_id,
            ShippingProvider.tenant_id == tenant_id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Shipping provider not found")

    if not provider.credentials:
        raise HTTPException(status_code=400, detail="No credentials configured for this provider")

    try:
        from app.services.shipping_service_factory import test_shipping_provider

        ok, msg = await test_shipping_provider(provider)
        now = datetime.now(timezone.utc)

        stmt = (
            update(ShippingProvider)
            .where(ShippingProvider.id == provider.id)
            .values(
                last_test_at=now,
                last_test_success=ok,
                last_error=None if ok else msg[:500],
            )
        )
        await db.execute(stmt)
        await db.commit()

        return TestResult(success=ok, message=msg)
    except Exception as e:
        now = datetime.now(timezone.utc)
        stmt = (
            update(ShippingProvider)
            .where(ShippingProvider.id == provider.id)
            .values(
                last_test_at=now,
                last_test_success=False,
                last_error=str(e)[:500],
            )
        )
        await db.execute(stmt)
        await db.commit()

        return TestResult(success=False, message=str(e)[:500])
