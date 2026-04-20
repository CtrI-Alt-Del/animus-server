from collections.abc import Iterator

import pytest
from docker.errors import DockerException
from redis import Redis
from testcontainers.redis import RedisContainer

from animus.constants import Env


@pytest.fixture(scope='session')
def redis_container() -> Iterator[RedisContainer]:
    try:
        with RedisContainer('redis:7-alpine') as redis_container:
            yield redis_container
    except DockerException as error:
        pytest.skip(f'Docker indisponivel para testes com Redis: {error}')


@pytest.fixture(scope='session')
def redis_url(redis_container: RedisContainer) -> str:
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f'redis://{host}:{port}/0'


@pytest.fixture
def redis_client(redis_url: str) -> Iterator[Redis]:
    client = Redis.from_url(  # pyright: ignore[reportUnknownMemberType]
        redis_url,
        decode_responses=True,
    )
    try:
        yield client
    finally:
        client.close()


@pytest.fixture(autouse=True)
def patch_redis_env(monkeypatch: pytest.MonkeyPatch, redis_url: str) -> None:
    monkeypatch.setattr(Env, 'REDIS_URL', redis_url)


@pytest.fixture(autouse=True)
def reset_redis(redis_client: Redis) -> Iterator[None]:
    redis_client.flushdb()  # pyright: ignore[reportUnknownMemberType]
    yield
    redis_client.flushdb()  # pyright: ignore[reportUnknownMemberType]
