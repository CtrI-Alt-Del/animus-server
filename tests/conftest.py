from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from animus.app import FastAPIApp
from animus.database.sqlalchemy.sqlalchemy import Sqlalchemy
from animus.pubsub.inngest.inngest_pubsub import InngestPubSub


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch,
    fake_inngest_client: Any,
    sqlalchemy_session_factory: Any,
) -> TestClient:
    def _get_session() -> Session:
        return sqlalchemy_session_factory()

    def _register_inngest(_app: FastAPI) -> Any:
        return fake_inngest_client

    monkeypatch.setattr(
        Sqlalchemy,
        'get_session',
        staticmethod(_get_session),
    )
    monkeypatch.setattr(
        InngestPubSub,
        'register',
        staticmethod(_register_inngest),
    )

    app = FastAPIApp.register()
    return TestClient(app)


pytest_plugins = [
    'fixtures.auth_fixtures',
    'fixtures.gcs_fixtures',
    'fixtures.sqlalchemy_fixtures',
    'fixtures.inngest_fixtures',
    'fixtures.redis_fixtures',
]
