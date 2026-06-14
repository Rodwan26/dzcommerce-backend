import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.models.tenant import Tenant
from app.models.user import User
from app.services.facebook_ads_service import FacebookAdsService

router = APIRouter(prefix="/facebook", tags=["facebook"])


async def get_fb_service() -> FacebookAdsService:
    from app.core.db import async_session_factory
    return FacebookAdsService(async_session_factory)


@router.get("/config")
async def facebook_config(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {
        "mode": "mock" if settings.FACEBOOK_MOCK_MODE else "live",
        "sync_enabled": t.facebook_sync_enabled,
        "last_sync_at": t.facebook_last_sync_at,
        "last_error": t.facebook_last_error,
    }


@router.get("/overview")
async def facebook_overview(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    service = await get_fb_service()
    return await service.get_overview(tenant_id, db, days)


@router.get("/campaigns")
async def facebook_campaigns(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    service = await get_fb_service()
    return await service.get_campaigns(tenant_id, db, days)


@router.get("/insights")
async def facebook_insights(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    service = await get_fb_service()
    return await service.get_insights(tenant_id, db, days)


@router.post("/sync")
async def facebook_sync(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if not tenant.facebook_access_token or not tenant.facebook_ad_account_id:
        raise HTTPException(status_code=400, detail="Facebook not configured — set access token and ad account ID in settings")

    service = await get_fb_service()
    await service.sync_tenant(tenant)
    return {"status": "ok", "message": "Facebook sync completed"}



