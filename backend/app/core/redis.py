from arq.connections import RedisSettings
from urllib.parse import urlparse
from app.core.config import settings

def get_redis_settings() -> RedisSettings:
    url = urlparse(settings.REDIS_URL)
    return RedisSettings(
        host=url.hostname or "localhost",
        port=url.port or 6379,
        database=int((url.path or "/0").lstrip('/')) or 0,
    )
