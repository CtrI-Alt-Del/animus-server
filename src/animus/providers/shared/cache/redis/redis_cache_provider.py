from redis import Redis

from animus.core.shared.domain.structures import Text, Ttl
from animus.core.shared.interfaces import CacheProvider


class RedisCacheProvider(CacheProvider):
    def __init__(self, redis_url: str) -> None:
        self._redis: Redis = Redis.from_url(  # pyright: ignore[reportUnknownMemberType]
            redis_url,
            decode_responses=True,
        )

    def get(self, key: str) -> Text | None:
        value = self._redis.get(key)
        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        return Text.create(value)

    def set(self, key: str, value: Text) -> None:
        self._redis.set(key, value.value)

    def set_with_ttl(self, key: str, value: Text, ttl: Ttl) -> None:
        self._redis.set(key, value.value, ex=ttl.seconds)

    def delete(self, key: str) -> None:
        self._redis.delete(key)
