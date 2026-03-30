from collections.abc import Iterator
import time

import httpx
import pytest
from qdrant_client import QdrantClient
from testcontainers.core.container import DockerContainer

from animus.constants import Env


@pytest.fixture
def qdrant_container() -> Iterator[DockerContainer]:
    with DockerContainer('qdrant/qdrant:v1.17.1').with_exposed_ports(6333) as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(6333)
        base_url = f'http://{host}:{port}'
        deadline = time.monotonic() + 30

        while time.monotonic() < deadline:
            try:
                response = httpx.get(f'{base_url}/collections', timeout=1.0)
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                pass

            time.sleep(0.5)
        else:
            msg = 'Qdrant container did not become ready in time'
            raise RuntimeError(msg)

        yield container


@pytest.fixture
def qdrant_url(qdrant_container: DockerContainer) -> str:
    host = qdrant_container.get_container_host_ip()
    port = qdrant_container.get_exposed_port(6333)
    return f'http://{host}:{port}'


@pytest.fixture
def patch_qdrant_env(monkeypatch: pytest.MonkeyPatch, qdrant_url: str) -> None:
    monkeypatch.setattr(Env, 'QDRANT_URL', qdrant_url)


@pytest.fixture
def qdrant_client(
    patch_qdrant_env: None,
    qdrant_url: str,
) -> Iterator[QdrantClient]:
    client = QdrantClient(url=qdrant_url)
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def reset_qdrant(qdrant_client: QdrantClient) -> Iterator[None]:
    collection_name = f'{Env.MODE}_precedents'

    if qdrant_client.collection_exists(collection_name=collection_name):
        qdrant_client.delete_collection(collection_name=collection_name)

    yield

    if qdrant_client.collection_exists(collection_name=collection_name):
        qdrant_client.delete_collection(collection_name=collection_name)
