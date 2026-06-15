import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.dependencies import get_current_user, get_tenant_id, require_owner
from app.models.user import User
from app.schemas.team import TeamMemberCreate, TeamMemberOut, TeamMembersResponse
from app.services import team_service

router = APIRouter(prefix="/team", tags=["team"])


@router.get("/members", response_model=TeamMembersResponse)
async def list_members(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: User = Depends(get_current_user),
):
    members = await team_service.list_members(db, tenant_id)
    return TeamMembersResponse(
        members=[TeamMemberOut.model_validate(m) for m in members],
        count=len(members),
        max_members=settings.MAX_TEAM_MEMBERS,
        remaining_slots=settings.MAX_TEAM_MEMBERS - len(members),
    )


@router.post("/members", response_model=TeamMemberOut)
async def create_member(
    body: TeamMemberCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    _: User = Depends(require_owner),
):
    member = await team_service.create_member(
        db, tenant_id, body.name, body.email, body.password
    )
    return TeamMemberOut.model_validate(member)


@router.delete("/members/{member_id}")
async def delete_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    current_user: User = Depends(require_owner),
):
    await team_service.delete_member(db, tenant_id, member_id, current_user.id)
    return {"message": "Member removed successfully"}
