from arq.connections import RedisSettings
from urllib.parse import urlparse
import redis.asyncio as aioredis
from typing import AsyncGenerator
from app.core.config import settings

def get_redis_settings() -> RedisSettings:
    url = urlparse(settings.REDIS_URL)
    return RedisSettings(
        host=url.hostname or "localhost",
        port=url.port or 6379,
        database=int((url.path or "/0").lstrip('/')) or 0,
    )

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()

