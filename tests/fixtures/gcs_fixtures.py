import os
import socket
import time
from collections.abc import Callable, Iterator

import pytest
from google.cloud.storage import Client
from testcontainers.core.container import DockerContainer

from animus.constants import Env

UploadGcsFileFixture = Callable[[str, bytes, str], None]


def _gcs_emulator_is_ready(base_url: str) -> bool:
    try:
        host, port = base_url.removeprefix('http://').split(':', maxsplit=1)
        with socket.create_connection((host, int(port)), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture(scope='session')
def gcs_container() -> Iterator[DockerContainer]:
    with (
        DockerContainer('fsouza/fake-gcs-server:latest')
        .with_command('-scheme http')
        .with_exposed_ports(4443)
    ) as container:
        yield container


@pytest.fixture(scope='session')
def gcs_emulator_url(gcs_container: DockerContainer) -> str:
    host = gcs_container.get_container_host_ip()
    port = gcs_container.get_exposed_port(4443)
    return f'http://{host}:{port}'


@pytest.fixture(scope='session')
def gcs_client(gcs_emulator_url: str) -> Iterator[Client]:
    previous_host = Env.STORAGE_EMULATOR_HOST
    previous_env_host = os.environ.get('STORAGE_EMULATOR_HOST')
    Env.STORAGE_EMULATOR_HOST = gcs_emulator_url
    os.environ['STORAGE_EMULATOR_HOST'] = gcs_emulator_url

    try:
        for _ in range(100):
            if _gcs_emulator_is_ready(gcs_emulator_url):
                break
            time.sleep(0.1)
        else:
            msg = 'fake GCS server did not become ready in time'
            raise AssertionError(msg)

        client = Client.create_anonymous_client()
        yield client
    finally:
        Env.STORAGE_EMULATOR_HOST = previous_host
        if previous_env_host is None:
            os.environ.pop('STORAGE_EMULATOR_HOST', None)
        else:
            os.environ['STORAGE_EMULATOR_HOST'] = previous_env_host


@pytest.fixture(scope='session')
def create_gcs_bucket(gcs_client: Client) -> None:
    bucket = gcs_client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]
    gcs_client.create_bucket(bucket)  # pyright: ignore[reportUnknownMemberType]


@pytest.fixture
def patch_gcs_env(monkeypatch: pytest.MonkeyPatch, gcs_emulator_url: str) -> None:
    monkeypatch.setattr(Env, 'STORAGE_EMULATOR_HOST', gcs_emulator_url)
    monkeypatch.setenv('STORAGE_EMULATOR_HOST', gcs_emulator_url)


@pytest.fixture
def upload_gcs_file(
    gcs_client: Client,
    create_gcs_bucket: None,
    patch_gcs_env: None,
) -> UploadGcsFileFixture:
    def _upload_gcs_file(
        file_path: str,
        content: bytes,
        content_type: str = 'application/octet-stream',
    ) -> None:
        bucket = gcs_client.bucket(Env.GCS_BUCKET_NAME)  # pyright: ignore[reportUnknownMemberType]
        blob = bucket.blob(file_path)  # pyright: ignore[reportUnknownMemberType]
        blob.upload_from_string(content, content_type=content_type)  # pyright: ignore[reportUnknownMemberType]

    return _upload_gcs_file
