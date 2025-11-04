import asyncpg
from typing import AsyncIterator
from core.config import get_database_url

_pool: asyncpg.Pool | None = None

async def init_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=get_database_url(),
            min_size=1,
            max_size=10,
            command_timeout=10
        )

async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

async def get_conn() -> AsyncIterator[asyncpg.Connection]:
    if _pool is None:
        await init_pool()
    assert _pool is not None
    async with _pool.acquire() as conn:
        yield conn