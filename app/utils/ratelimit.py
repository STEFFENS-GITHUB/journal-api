import logging

from fastapi import Request, HTTPException
from redis.exceptions import RedisError

from app.utils.utils import user_identifier

RATE_LIMIT_LUA = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""

class RateLimiter:
    def __init__(self, times: int, seconds: int, identifier=user_identifier):
        self.times = times
        self.seconds = seconds
        self.identifier = identifier

    async def __call__(self, request: Request):
        identifier = await self.identifier(request)
        key = f"ratelimit:{identifier}:{request.scope['route'].path}"
        redis = request.app.state.redis_client
        try:
            count = await redis.eval(RATE_LIMIT_LUA, 1, key, self.seconds)
        except RedisError:
            logging.warning("rate limit skipped: redis unavailable")
            return
        if count > self.times:
            raise HTTPException(429, "Too Many Requests",
                                headers={"Retry-After": str(self.seconds)})
