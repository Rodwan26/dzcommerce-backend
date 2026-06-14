from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import require_role
from app.models.tenant_request import TenantRequest
from app.schemas.tenant import ApproveRequest, RejectRequest, TenantOut, TenantRequestOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tenant-requests", response_model=list[TenantRequestOut])
async def list_requests(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("owner")),
):
    result = await db.execute(
        select(TenantRequest).where(TenantRequest.status == "pending").order_by(TenantRequest.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/approve-request", response_model=TenantOut)
async def approve_request(
    body: ApproveRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("owner")),
):
    tenant = await AuthService.approve_request(body.request_id, db)
    return TenantOut(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        trial_ends_at=tenant.trial_ends_at,
        created_at=tenant.created_at,
    )


@router.post("/reject-request", response_model=dict)
async def reject_request(
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("owner")),
):
    await AuthService.reject_request(body.request_id, db)
    return {"message": "Request rejected"}
