import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, admin, dashboard, products, orders, payments, tenant, shipping, facebook, integrations
from app.core.config import settings
from app.core.db import async_session_factory
from app.middleware.tenant import resolve_tenant
from app.services.google_sheets_sync_service import GoogleSheetsSyncService
from app.services.facebook_ads_service import FacebookAdsService
from app.services.shipping_tracking_service import ShippingTrackingService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    gs_service = GoogleSheetsSyncService(async_session_factory)
    gs_task = asyncio.create_task(gs_service.sync_loop())

    fb_service = FacebookAdsService(async_session_factory)
    fb_task = asyncio.create_task(fb_service.sync_loop())

    st_service = ShippingTrackingService(async_session_factory)
    st_task = asyncio.create_task(st_service.sync_loop())

    yield

    gs_task.cancel()
    fb_task.cancel()
    st_task.cancel()
    for task in (gs_task, fb_task, st_task):
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    try:
        await resolve_tenant(request)
        return await call_next(request)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    except Exception:
        logger.exception("Unhandled exception in request")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500),
        content={"detail": str(exc) if settings.DEBUG else "Internal server error"},
    )


app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(tenant.router)
app.include_router(dashboard.router)
app.include_router(shipping.router)
app.include_router(facebook.router)
app.include_router(integrations.router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
