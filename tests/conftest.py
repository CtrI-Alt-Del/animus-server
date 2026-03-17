from animus.app import FastAPIApp
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session


@pytest.fixture
def client(mocker: MockerFixture, sqlalchemy_session: Session) -> TestClient:
    app = FastAPIApp.register()
    return TestClient(app)


pytest_plugins = [
    'fixtures.auth_fixtures',
    'fixtures.database_fixtures',
]
