import asyncio
from sqlalchemy import text
from app.core.db import async_session_factory


async def check():
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_name = 'order_status_history'")
        )
        for row in result:
            print("Table exists:", row[0])

        result = await session.execute(
            text("SELECT id, status, confirmation_status, shipping_status, confirmed_at FROM orders LIMIT 5")
        )
        for row in result:
            print(row)

asyncio.run(check())
