import uuid

from pydantic import BaseModel, ConfigDict


class TeamMemberCreate(BaseModel):
    name: str
    email: str
    password: str


class TeamMemberOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TeamMembersResponse(BaseModel):
    members: list[TeamMemberOut]
    count: int
    max_members: int
    remaining_slots: int
