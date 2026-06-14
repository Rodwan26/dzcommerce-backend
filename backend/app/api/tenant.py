import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.models.user import User
from app.schemas.tenant import FeatureFlagOut, FeatureFlagToggle, TenantSettingsOut, TenantSettingsUpdate
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenant", tags=["tenant"])


@router.get("/settings", response_model=TenantSettingsOut)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = TenantService(db)
    settings = await service.get_settings(tenant_id)
    return TenantSettingsOut(
        currency=settings.currency, cod_enabled=settings.cod_enabled, language=settings.language
    )


@router.put("/settings", response_model=TenantSettingsOut)
async def update_settings(
    body: TenantSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = TenantService(db)
    settings = await service.update_settings(
        tenant_id, currency=body.currency, cod_enabled=body.cod_enabled, language=body.language
    )
    return TenantSettingsOut(
        currency=settings.currency, cod_enabled=settings.cod_enabled, language=settings.language
    )


@router.get("/features", response_model=list[FeatureFlagOut])
async def list_features(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = TenantService(db)
    features = await service.get_features(tenant_id)
    return [
        FeatureFlagOut(id=str(f.id), feature_key=f.feature_key, enabled=f.enabled)
        for f in features
    ]


@router.post("/features/toggle", response_model=FeatureFlagOut)
async def toggle_feature(
    body: FeatureFlagToggle,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _=Depends(get_current_user),
):
    service = TenantService(db)
    feature = await service.toggle_feature(tenant_id, body.feature_key, body.enabled)
    return FeatureFlagOut(id=str(feature.id), feature_key=feature.feature_key, enabled=feature.enabled)
