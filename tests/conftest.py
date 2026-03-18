import pytest
from fastapi.testclient import TestClient

from animus.app import FastAPIApp


@pytest.fixture
def client() -> TestClient:
    app = FastAPIApp.register()
    return TestClient(app)


pytest_plugins = [
    'fixtures.auth_fixtures',
    'fixtures.database_fixtures',
]
