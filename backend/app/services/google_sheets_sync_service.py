import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.models.order import Order
from app.models.order_status import UpdateSource
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

SHEET_HEADER = ["order_id", "confirmation_status", "shipping_status", "total", "updated_at"]


class GoogleSheetsSyncService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self._gc = None

    async def _get_client(self):
        if self._gc is None:
            if not settings.GOOGLE_SERVICE_ACCOUNT_INFO:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_INFO not configured")
            import gspread
            creds = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_INFO)
            self._gc = await asyncio.to_thread(gspread.service_account_from_dict, creds)
        return self._gc

    async def _open_sheet(self, sheet_id: str):
        gc = await self._get_client()
        sh = await asyncio.to_thread(gc.open_by_key, sheet_id)
        ws = await asyncio.to_thread(sh.sheet1)
        return ws

    async def _get_sheet_data(self, sheet_id: str) -> list[list[str]]:
        ws = await self._open_sheet(sheet_id)
        return await asyncio.to_thread(ws.get_all_values)

    async def _update_sheet(self, sheet_id: str, rows: list[list[str]]):
        ws = await self._open_sheet(sheet_id)
        await asyncio.to_thread(ws.clear)
        if rows:
            range_str = f"A1:{chr(64 + len(rows[0]))}{len(rows)}"
            await asyncio.to_thread(ws.update, range_str, rows)

    async def push_dirty_orders(self, session: AsyncSession, tenant: Tenant):
        query = select(Order).where(
            Order.tenant_id == tenant.id,
            and_(
                Order.updated_at > tenant.google_sheet_last_sync_at
                if tenant.google_sheet_last_sync_at
                else True,
                (Order.updated_source != UpdateSource.GOOGLE_SHEET.value)
                | (Order.updated_source.is_(None)),
            ),
        )
        result = await session.execute(query)
        dirty_orders: list[Order] = list(result.scalars().all())

        if not dirty_orders:
            return

        existing_rows = await self._get_sheet_data(tenant.google_sheet_id)
        row_map: dict[str, int] = {}
        for i, row in enumerate(existing_rows):
            if row and row[0] and row[0] != SHEET_HEADER[0]:
                row_map[row[0]] = i

        data = [SHEET_HEADER]
        seen: set[str] = set()

        for i, row in enumerate(existing_rows):
            if i == 0:
                continue
            if row and row[0]:
                seen.add(row[0])
                data.append(row)

        for order in dirty_orders:
            order_id_str = str(order.id)
            updated_at_str = (
                order.updated_at.isoformat()
                if order.updated_at
                else order.created_at.isoformat()
            )
            row = [
                order_id_str,
                order.confirmation_status,
                order.shipping_status,
                str(order.total),
                updated_at_str,
            ]
            if order_id_str in row_map:
                data[row_map[order_id_str]] = row
            else:
                data.append(row)

        await self._update_sheet(tenant.google_sheet_id, data)
        logger.info("Pushed %d dirty orders for tenant %s", len(dirty_orders), tenant.id)

    async def pull_changes(self, session: AsyncSession, tenant: Tenant):
        rows = await self._get_sheet_data(tenant.google_sheet_id)

        if not rows or len(rows) < 2:
            return

        if rows[0] != SHEET_HEADER:
            logger.warning("Sheet header mismatch for tenant %s, skipping pull", tenant.id)
            return

        updated_count = 0
        for row in rows[1:]:
            if not row or not row[0]:
                continue

            order_id, sheet_confirm, sheet_shipping, _, sheet_updated_at = row[:5]
            try:
                parsed_id = order_id
            except (ValueError, TypeError):
                continue

            result = await session.execute(
                select(Order).where(Order.id == parsed_id, Order.tenant_id == tenant.id)
            )
            order = result.scalar_one_or_none()
            if not order:
                continue

            db_updated_at = order.updated_at or order.created_at
            try:
                sheet_ts = datetime.fromisoformat(sheet_updated_at)
            except (ValueError, TypeError):
                continue

            if sheet_ts.replace(tzinfo=timezone.utc) <= db_updated_at.replace(tzinfo=timezone.utc):
                continue

            if sheet_confirm and sheet_confirm != order.confirmation_status:
                order.confirmation_status = sheet_confirm
            if sheet_shipping and sheet_shipping != order.shipping_status:
                order.shipping_status = sheet_shipping
            order.updated_source = UpdateSource.GOOGLE_SHEET.value
            order.updated_source_ref = tenant.google_sheet_id
            updated_count += 1

        if updated_count:
            await session.flush()
            logger.info("Pulled %d updates from sheet for tenant %s", updated_count, tenant.id)

    async def sync_store(self, tenant: Tenant):
        if not tenant.google_sheet_id or not tenant.google_sheet_enabled:
            return

        async with self._session_factory() as session:
            session: AsyncSession
            try:
                await self.push_dirty_orders(session, tenant)
                await self.pull_changes(session, tenant)
                stmt = (
                    update(Tenant)
                    .where(Tenant.id == tenant.id)
                    .values(google_sheet_last_sync_at=datetime.now(timezone.utc))
                )
                await session.execute(stmt)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def sync_loop(self):
        logger.info("Google Sheets sync loop started (interval=%ds)", settings.GOOGLE_SHEET_SYNC_INTERVAL_SECONDS)
        while True:
            try:
                async with self._session_factory() as session:
                    result = await session.execute(
                        select(Tenant).where(
                            Tenant.google_sheet_enabled == True,
                            Tenant.google_sheet_id.isnot(None),
                        )
                    )
                    tenants: list[Tenant] = list(result.scalars().all())

                for tenant in tenants:
                    try:
                        await self.sync_store(tenant)
                    except Exception as e:
                        logger.exception("Sync failed for tenant %s: %s", tenant.id, e)

            except Exception as e:
                logger.exception("Sync cycle error: %s", e)

            await asyncio.sleep(settings.GOOGLE_SHEET_SYNC_INTERVAL_SECONDS)
