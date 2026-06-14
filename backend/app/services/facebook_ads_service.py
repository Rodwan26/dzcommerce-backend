import asyncio
import logging
import random
from datetime import date, datetime, timedelta, timezone

import httpx
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.models.facebook_campaign_metric import FacebookCampaignMetric
from app.models.order_status import UpdateSource
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com"


class FacebookAdsService:
    MOCK_CAMPAIGNS = [
        {"id": "mock_001", "name": "Summer Sale 2026", "status": "ACTIVE"},
        {"id": "mock_002", "name": "Retargeting - Cart Abandoners", "status": "ACTIVE"},
        {"id": "mock_003", "name": "Brand Awareness", "status": "PAUSED"},
        {"id": "mock_004", "name": "New Collection Launch", "status": "ACTIVE"},
        {"id": "mock_005", "name": "Best Sellers Campaign", "status": "ACTIVE"},
    ]

    CAMPAIGN_PROFILES = {
        "mock_001": {"ctr_range": (1.5, 3.5), "cpc_range": (20, 50), "daily_spend": (800, 2000)},
        "mock_002": {"ctr_range": (3.0, 6.0), "cpc_range": (10, 30), "daily_spend": (500, 1200)},
        "mock_003": {"ctr_range": (0.3, 1.2), "cpc_range": (50, 120), "daily_spend": (300, 800)},
        "mock_004": {"ctr_range": (1.0, 2.5), "cpc_range": (30, 70), "daily_spend": (600, 1500)},
        "mock_005": {"ctr_range": (2.0, 4.0), "cpc_range": (15, 40), "daily_spend": (700, 1800)},
    }

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self._http = httpx.AsyncClient(timeout=30)

    def _mock_campaigns(self) -> list[dict]:
        return list(self.MOCK_CAMPAIGNS)

    def _mock_insights(self, since: str, until: str) -> list[dict]:
        start = datetime.strptime(since, "%Y-%m-%d").date()
        end = datetime.strptime(until, "%Y-%m-%d").date()
        rows = []
        current = start
        while current <= end:
            for camp in self.MOCK_CAMPAIGNS:
                cid = camp["id"]
                profile = self.CAMPAIGN_PROFILES[cid]
                rng = random.Random(f"{cid}_{current.isoformat()}")
                impressions = rng.randint(1000, 10000)
                clicks = rng.randint(max(1, int(impressions * profile["ctr_range"][0] / 100)),
                                     max(2, int(impressions * profile["ctr_range"][1] / 100)))
                spend = round(rng.uniform(*profile["daily_spend"]), 2)
                ctr = round(clicks / impressions * 100, 4) if impressions else 0
                cpc = round(spend / clicks, 4) if clicks else 0
                cpm = round(spend / impressions * 1000, 4) if impressions else 0
                rows.append({
                    "campaign_id": cid,
                    "campaign_name": camp["name"],
                    "date_start": current.isoformat(),
                    "date_stop": current.isoformat(),
                    "impressions": str(impressions),
                    "clicks": str(clicks),
                    "spend": str(spend),
                    "ctr": str(ctr),
                    "cpc": str(cpc),
                    "cpm": str(cpm),
                })
            current += timedelta(days=1)
        return rows

    async def _graph_get(self, token: str, path: str, params: dict | None = None):
        url = f"{GRAPH_API}/{settings.FACEBOOK_GRAPH_API_VERSION}/{path}"
        headers = {"Authorization": f"Bearer {token}"}
        resp = await self._http.get(url, headers=headers, params=params)
        if resp.status_code >= 400:
            error = resp.json().get("error", {})
            raise ValueError(error.get("message", f"HTTP {resp.status_code}"), error.get("code", resp.status_code))
        return resp.json()

    async def fetch_campaigns(self, tenant: Tenant) -> list[dict]:
        if settings.FACEBOOK_MOCK_MODE:
            return self._mock_campaigns()
        account_id = tenant.facebook_ad_account_id
        token = tenant.facebook_access_token
        data = await self._graph_get(
            token, f"act_{account_id}/campaigns",
            params={"fields": "id,name,status", "limit": 100, "effective_status": '["ACTIVE","PAUSED"]'},
        )
        return data.get("data", [])

    async def fetch_insights(self, tenant: Tenant, since: str, until: str) -> list[dict]:
        if settings.FACEBOOK_MOCK_MODE:
            return self._mock_insights(since, until)
        account_id = tenant.facebook_ad_account_id
        token = tenant.facebook_access_token
        data = await self._graph_get(
            token, f"act_{account_id}/insights",
            params={
                "level": "campaign",
                "fields": "campaign_id,campaign_name,impressions,clicks,spend,ctr,cpc,cpm",
                "date_preset": "last_30d",
                "time_increment": 1,
            },
        )
        return data.get("data", [])

    async def sync_tenant(self, tenant: Tenant):
        token = tenant.facebook_access_token
        account_id = tenant.facebook_ad_account_id

        if not token or not account_id:
            return

        try:
            campaigns = await self.fetch_campaigns(tenant)
            campaign_map = {c["id"]: c for c in campaigns}
            campaign_ids = list(campaign_map.keys())

            since = (date.today() - timedelta(days=30)).isoformat()
            until = date.today().isoformat()
            insights = await self.fetch_insights(tenant, since, until)

            async with self._session_factory() as session:
                for row in insights:
                    cid = row.get("campaign_id")
                    if cid not in campaign_map:
                        continue
                    campaign = campaign_map[cid]
                    try:
                        row_date = datetime.strptime(row.get("date_start"), "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        continue

                    stmt = pg_insert(FacebookCampaignMetric).values(
                        tenant_id=tenant.id,
                        campaign_id=cid,
                        campaign_name=campaign.get("name", row.get("campaign_name", "")),
                        campaign_status=campaign.get("status", "UNKNOWN"),
                        date=row_date,
                        spend=float(row.get("spend", 0) or 0),
                        currency=None,
                        impressions=int(row.get("impressions", 0) or 0),
                        clicks=int(row.get("clicks", 0) or 0),
                        ctr=float(row.get("ctr", 0) or 0),
                        cpc=float(row.get("cpc", 0) or 0),
                        cpm=float(row.get("cpm", 0) or 0),
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["tenant_id", "campaign_id", "date"],
                        set_={
                            "campaign_name": stmt.excluded.campaign_name,
                            "campaign_status": stmt.excluded.campaign_status,
                            "spend": stmt.excluded.spend,
                            "impressions": stmt.excluded.impressions,
                            "clicks": stmt.excluded.clicks,
                            "ctr": stmt.excluded.ctr,
                            "cpc": stmt.excluded.cpc,
                            "cpm": stmt.excluded.cpm,
                            "updated_at": datetime.now(timezone.utc),
                        },
                    )
                    await session.execute(stmt)

                stmt = (
                    update(Tenant)
                    .where(Tenant.id == tenant.id)
                    .values(facebook_last_sync_at=datetime.now(timezone.utc), facebook_last_error=None)
                )
                await session.execute(stmt)
                await session.commit()

            logger.info("Synced facebook data for tenant %s (%d insights)", tenant.id, len(insights))

        except ValueError as e:
            error_msg = str(e.args[0]) if e.args else "Unknown error"
            error_code = e.args[1] if len(e.args) > 1 else 0
            logger.warning("Facebook sync error for tenant %s: %s", tenant.id, error_msg)

            if error_code == 190:
                async with self._session_factory() as session:
                    stmt = (
                        update(Tenant)
                        .where(Tenant.id == tenant.id)
                        .values(facebook_sync_enabled=False, facebook_last_error=f"Token expired: {error_msg}")
                    )
                    await session.execute(stmt)
                    await session.commit()
            else:
                async with self._session_factory() as session:
                    stmt = (
                        update(Tenant)
                        .where(Tenant.id == tenant.id)
                        .values(facebook_last_error=error_msg[:500])
                    )
                    await session.execute(stmt)
                    await session.commit()
        except Exception as e:
            logger.exception("Unexpected facebook sync error for tenant %s", tenant.id)
            async with self._session_factory() as session:
                stmt = (
                    update(Tenant)
                    .where(Tenant.id == tenant.id)
                    .values(facebook_last_error=str(e)[:500])
                )
                await session.execute(stmt)
                await session.commit()

    async def sync_loop(self):
        logger.info("Facebook Ads sync loop started (interval=%ds)", settings.FACEBOOK_SYNC_INTERVAL_SECONDS)
        await asyncio.sleep(30)
        while True:
            try:
                async with self._session_factory() as session:
                    result = await session.execute(
                        select(Tenant).where(
                            Tenant.facebook_sync_enabled == True,
                            Tenant.facebook_access_token.isnot(None),
                            Tenant.facebook_ad_account_id.isnot(None),
                        )
                    )
                    tenants: list[Tenant] = list(result.scalars().all())

                for tenant in tenants:
                    try:
                        await self.sync_tenant(tenant)
                    except Exception as e:
                        logger.exception("Sync failed for tenant %s: %s", tenant.id, e)

            except Exception as e:
                logger.exception("Facebook sync cycle error: %s", e)

            await asyncio.sleep(settings.FACEBOOK_SYNC_INTERVAL_SECONDS)

    async def get_overview(self, tenant_id, session: AsyncSession, days: int = 30) -> dict:
        since = date.today() - timedelta(days=days)
        result = await session.execute(
            select(FacebookCampaignMetric)
            .where(
                FacebookCampaignMetric.tenant_id == str(tenant_id),
                FacebookCampaignMetric.date >= since,
            )
        )
        rows: list[FacebookCampaignMetric] = list(result.scalars().all())
        total_spend = sum(r.spend for r in rows)
        total_impressions = sum(r.impressions for r in rows)
        total_clicks = sum(r.clicks for r in rows)
        avg_ctr = (sum(r.ctr * r.impressions for r in rows) / total_impressions) if total_impressions else 0
        avg_cpc = (total_spend / total_clicks) if total_clicks else 0
        avg_cpm = (total_spend / total_impressions * 1000) if total_impressions else 0
        campaigns = len(set(r.campaign_id for r in rows))
        return {
            "total_spend": round(total_spend, 2),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "avg_ctr": round(avg_ctr, 2),
            "avg_cpc": round(avg_cpc, 4),
            "avg_cpm": round(avg_cpm, 4),
            "active_campaigns": campaigns,
        }

    async def get_campaigns(self, tenant_id, session: AsyncSession, days: int = 30) -> list[dict]:
        since = date.today() - timedelta(days=days)
        result = await session.execute(
            select(FacebookCampaignMetric)
            .where(
                FacebookCampaignMetric.tenant_id == str(tenant_id),
                FacebookCampaignMetric.date >= since,
            )
            .order_by(FacebookCampaignMetric.campaign_name, FacebookCampaignMetric.date)
        )
        rows: list[FacebookCampaignMetric] = list(result.scalars().all())

        agg: dict[str, dict] = {}
        for r in rows:
            if r.campaign_id not in agg:
                agg[r.campaign_id] = {
                    "campaign_id": r.campaign_id,
                    "campaign_name": r.campaign_name,
                    "campaign_status": r.campaign_status,
                    "spend": 0,
                    "impressions": 0,
                    "clicks": 0,
                    "ctr_sum": 0,
                    "cpc_sum": 0,
                    "days": 0,
                }
            a = agg[r.campaign_id]
            a["spend"] += r.spend
            a["impressions"] += r.impressions
            a["clicks"] += r.clicks
            if r.ctr:
                a["ctr_sum"] += r.ctr
                a["days"] += 1

        result_list = []
        for a in agg.values():
            result_list.append({
                "campaign_id": a["campaign_id"],
                "campaign_name": a["campaign_name"],
                "campaign_status": a["campaign_status"],
                "spend": round(a["spend"], 2),
                "impressions": a["impressions"],
                "clicks": a["clicks"],
                "ctr": round(a["ctr_sum"] / a["days"], 2) if a["days"] else 0,
                "cpc": round(a["spend"] / a["clicks"], 4) if a["clicks"] else 0,
                "cpm": round(a["spend"] / a["impressions"] * 1000, 4) if a["impressions"] else 0,
            })
        return result_list

    async def get_insights(self, tenant_id, session: AsyncSession, days: int = 30) -> list[dict]:
        overview = await self.get_overview(tenant_id, session, days)
        campaigns = await self.get_campaigns(tenant_id, session, days)
        rules = []

        if overview["avg_ctr"] < 1:
            rules.append({"type": "warning", "field": "ctr", "message": "CTR is below 1% — consider improving ad creative or targeting"})
        if overview["avg_cpc"] > 50:
            rules.append({"type": "warning", "field": "cpc", "message": "Cost per click is high — review audience targeting"})

        best = None
        worst = None
        for c in campaigns:
            if c["spend"] <= 0:
                continue
            if best is None or c["cpc"] < best["cpc"]:
                best = c
            if worst is None or c["cpc"] > worst["cpc"]:
                worst = c

        if best:
            rules.append({"type": "positive", "field": "campaign", "message": f"Best performing: {best['campaign_name']} (CPC: {best['cpc']})"})
        if worst:
            rules.append({"type": "info", "field": "campaign", "message": f"Worst performing: {worst['campaign_name']} (CPC: {worst['cpc']})"})

        return rules
