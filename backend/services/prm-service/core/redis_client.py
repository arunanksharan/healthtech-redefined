"""
Redis client for conversation state and caching
"""
import redis.asyncio as aioredis
from typing import Optional
from loguru import logger

from .config import settings


class RedisManager:
    """Async Redis connection manager"""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Establish Redis connection"""
        try:
            if settings.REDIS_URL:
                self.redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info(f"Connected to Redis at {settings.REDIS_URL}")
            else:
                logger.warning("Redis URL not configured")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self.redis:
            return None
        return await self.redis.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None):
        """Set key-value with optional expiry"""
        if not self.redis:
            return
        await self.redis.set(key, value, ex=ex)

    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value"""
        if not self.redis:
            return None
        return await self.redis.hget(name, key)

    async def hset(self, name: str, key: str, value: str):
        """Set hash field value"""
        if not self.redis:
            return
        await self.redis.hset(name, key, value)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False
        return await self.redis.exists(key) > 0

    async def delete(self, *keys: str):
        """Delete one or more keys"""
        if not self.redis:
            return
        await self.redis.delete(*keys)

    async def expire(self, key: str, seconds: int):
        """Set expiry on key"""
        if not self.redis:
            return
        await self.redis.expire(key, seconds)


# Global Redis manager instance
redis_manager = RedisManager()
