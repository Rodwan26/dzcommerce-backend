import asyncio
from sqlalchemy import text
from app.core.db import async_session_factory


async def check():
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'orders' ORDER BY ordinal_position")
        )
        for row in result:
            print(f"{row[0]:30s} {row[1]}")

asyncio.run(check())
