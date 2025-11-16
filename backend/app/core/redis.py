"""Redis connection and utilities"""

from typing import Optional
import json
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import settings

# Sync Redis client
redis_client = Redis.from_url(
    str(settings.REDIS_URL),
    decode_responses=True,
    encoding="utf-8",
)

# Async Redis client
async_redis_client = AsyncRedis.from_url(
    str(settings.REDIS_URL),
    decode_responses=True,
    encoding="utf-8",
)


class RedisCache:
    """Redis cache utility"""

    def __init__(self, client: Redis):
        self.client = client

    def set(self, key: str, value: dict, expire: int = 3600) -> bool:
        """Set cache value"""
        try:
            self.client.setex(
                key,
                expire,
                json.dumps(value)
            )
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    def get(self, key: str) -> Optional[dict]:
        """Get cache value"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete cache value"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return bool(self.client.exists(key))


# Global cache instance
cache = RedisCache(redis_client)
