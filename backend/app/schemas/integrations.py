from datetime import datetime

from pydantic import BaseModel


class IntegrationServiceStatus(BaseModel):
    service: str
    label: str
    status: str  # connected | error | not_configured | disabled
    last_sync_at: datetime | None = None
    next_sync_at: datetime | None = None
    last_test_at: datetime | None = None
    last_test_success: bool | None = None
    last_error: str | None = None


class IntegrationProviderStatus(BaseModel):
    id: str
    name: str
    code: str
    status: str  # connected | error | not_configured
    last_test_at: datetime | None = None
    last_test_success: bool | None = None
    last_error: str | None = None


class IntegrationsStatusResponse(BaseModel):
    google_sheets: IntegrationServiceStatus | None = None
    facebook_ads: IntegrationServiceStatus | None = None
    shipping_providers: list[IntegrationProviderStatus] = []


class GoogleConfigureRequest(BaseModel):
    sheet_url: str
    enable_sync: bool = False


class GoogleConfigResponse(BaseModel):
    sheet_id: str | None = None
    sheet_url: str | None = None
    enabled: bool = False
    last_sync_at: datetime | None = None
    last_test_at: datetime | None = None
    last_test_success: bool | None = None
    last_error: str | None = None


class FacebookConfigureRequest(BaseModel):
    access_token: str | None = None
    ad_account_id: str | None = None
    enable_sync: bool = False

    def model_post_init(self, __context):
        self.access_token = self.access_token or None
        self.ad_account_id = self.ad_account_id or None


class FacebookConfigResponse(BaseModel):
    access_token: str | None = None
    ad_account_id: str | None = None
    mode: str = "live"
    enabled: bool = False
    last_sync_at: datetime | None = None
    last_test_at: datetime | None = None
    last_test_success: bool | None = None
    last_error: str | None = None


class TestResult(BaseModel):
    success: bool
    message: str
    details: dict | None = None
