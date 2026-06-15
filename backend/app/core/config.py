from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "DzCommerce"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://dzcommerce:dzcommerce@localhost:5432/dzcommerce"
    DATABASE_SYNC_URL: str = "postgresql://dzcommerce:dzcommerce@localhost:5432/dzcommerce"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    TRIAL_DAYS: int = 15

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@dzcommerce.dz"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    REDIS_URL: str = "redis://localhost:6379/0"

    WHATSAPP_API_KEY: str = ""
    WHATSAPP_PHONE_NUMBER: str = ""

    GOOGLE_SERVICE_ACCOUNT_INFO: str | None = None
    GOOGLE_SHEET_SYNC_INTERVAL_SECONDS: int = 120

    FACEBOOK_GRAPH_API_VERSION: str = "v25.0"
    FACEBOOK_SYNC_INTERVAL_SECONDS: int = 1800
    FACEBOOK_MOCK_MODE: bool = False

    MAX_TEAM_MEMBERS: int = 3


settings = Settings()
