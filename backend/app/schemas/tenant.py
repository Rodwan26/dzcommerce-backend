from datetime import datetime

from pydantic import BaseModel


class TenantRequestOut(BaseModel):
    id: str
    company_name: str
    owner_name: str
    email: str
    phone: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantOut(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    trial_ends_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApproveRequest(BaseModel):
    request_id: str


class RejectRequest(BaseModel):
    request_id: str


class TenantSettingsOut(BaseModel):
    currency: str
    cod_enabled: bool
    language: str

    model_config = {"from_attributes": True}


class TenantSettingsUpdate(BaseModel):
    currency: str | None = None
    cod_enabled: bool | None = None
    language: str | None = None


class FeatureFlagOut(BaseModel):
    id: str
    feature_key: str
    enabled: bool

    model_config = {"from_attributes": True}


class FeatureFlagToggle(BaseModel):
    feature_key: str
    enabled: bool
