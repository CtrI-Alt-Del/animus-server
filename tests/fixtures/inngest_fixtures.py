import json
import random
import socket
import threading
import time
from collections.abc import Callable, Iterator
from http.client import HTTPResponse
from typing import Any, cast
from urllib import request

import pytest
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.core.container import DockerContainer
from uvicorn import Config, Server

from animus.app import FastAPIApp
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy


class InngestTestRuntime:
    def __init__(self, *, base_url: str) -> None:
        self.base_url = base_url

    def post_event(self, *, name: str, data: dict[str, Any]) -> HTTPResponse:
        payload = json.dumps({'name': name, 'data': data}).encode()
        response = request.urlopen(  # noqa: S310
            request.Request(  # noqa: S310
                url=f'{self.base_url}/e/test',
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST',
            ),
            timeout=10,
        )
        return cast('HTTPResponse', response)


class FakeInngestClient:
    def __init__(self) -> None:
        self.sent_events: list[Any] = []

    def send_sync(self, event: Any) -> None:
        self.sent_events.append(event)


SessionFactory = sessionmaker[Session]


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _find_free_port_in_range(
    *,
    host: str = '127.0.0.1',
    start: int = 20000,
    end: int = 40000,
    attempts: int = 50,
) -> int:
    for _ in range(attempts):
        candidate = random.randint(start, end)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, candidate))
                sock.listen(1)
                return candidate
            except OSError:
                continue

    msg = 'could not find free port in allowed range'
    raise RuntimeError(msg)


def _wait_until(
    predicate: Callable[[], bool],
    *,
    timeout_seconds: float = 15,
    interval_seconds: float = 0.1,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            if predicate():
                return
        except (ConnectionError, OSError, RuntimeError):
            continue
        time.sleep(interval_seconds)

    msg = 'condition not satisfied before timeout'
    raise AssertionError(msg)


def _can_connect(*, host: str, port: int) -> bool:
    with socket.create_connection((host, port), timeout=1):
        return True


@pytest.fixture
def inngest_runtime(
    monkeypatch: pytest.MonkeyPatch,
    sqlalchemy_session_factory: SessionFactory,
) -> Iterator[InngestTestRuntime]:
    app_port = _find_free_port()
    inngest_port = _find_free_port_in_range()

    def _get_session() -> Session:
        return sqlalchemy_session_factory()

    monkeypatch.setattr(
        Sqlalchemy,
        'get_session',
        staticmethod(_get_session),
    )
    monkeypatch.setenv('INNGEST_DEV', '1')
    monkeypatch.setenv('INNGEST_BASE_URL', f'http://127.0.0.1:{inngest_port}')

    app = FastAPIApp.register()
    server = Server(
        Config(
            app=app,
            host='0.0.0.0',  # noqa: S104
            port=app_port,
            log_level='warning',
        )
    )
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    try:
        _wait_until(lambda: server.started)

        with (
            DockerContainer('inngest/inngest:v0.27.0')
            .with_command(
                'inngest dev '
                f'-u http://host.docker.internal:{app_port}/api/inngest '
                '--no-discovery'
            )
            .with_bind_ports(8288, inngest_port)
            .with_kwargs(extra_hosts={'host.docker.internal': 'host-gateway'})
        ) as _inngest_container:
            _wait_until(
                lambda: _can_connect(host='127.0.0.1', port=inngest_port),
                timeout_seconds=30,
            )
            time.sleep(5)

            yield InngestTestRuntime(base_url=f'http://127.0.0.1:{inngest_port}')
    finally:
        server.should_exit = True
        server_thread.join(timeout=10)


@pytest.fixture
def fake_inngest_client() -> FakeInngestClient:
    return FakeInngestClient()
